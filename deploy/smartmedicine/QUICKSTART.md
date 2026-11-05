# SmartMedicine 会诊服务部署速查手册

本手册是端到端可执行步骤，覆盖 **API Key 生成 → 容器构建 → 启动 → 验证 → 运维** 全流程。
面向"只部署一个适配 smartmedicine 的后端服务"的场景（替换原 18100 端口服务）。

> 完整技术背景见 `deploy/SMARTMEDICINE-CONSULTATION.md`，日常运维命令见 `deploy/smartmedicine/README.md`。

---

## 一、架构与边界

```
外部项目（SmartMedicine JAR）
    │  X-API-Key + X-External-Subject
    ▼
┌──────────────────────────────────────────┐
│  wellhealth-backend 容器（18100）         │
│  入口：app.integrations.smartmedicine.app │
│  认证：API Key（SHA256 摘要校验）          │
│  数据：独立 integration_consultation_* 表  │
│  加密：Fernet 对称加密敏感字段              │
└──────────────────────────────────────────┘
    │  executor.py 复用主应用 AgentExecutor
    ▼
已有中间件（MySQL/Redis/Qdrant/LLM）
```

**关键约束**：
- `WEB_CONCURRENCY=1` 强制单 worker（会诊编排器用进程内 `asyncio.Task`）
- 原 WellHealth 登录/患者/管理 API **不再由本容器提供**（这是替换部署）
- 容器只绑定 `127.0.0.1:18100`，外部项目同机 HTTP 直连，不走公网

---

## 二、生成 API Key（可执行步骤）

`deploy/smartmedicine/prepare_config.py` 是项目自带的配置生成工具，**一次性生成全部密钥**，不打印到终端，不写入 Git。

### 步骤 1：执行 prepare（生成密钥与配置）

```bash
# 在仓库根目录执行，使用默认路径
python3 deploy/smartmedicine/prepare_config.py prepare \
  --config-dir /etc/wellhealth-smartmedicine \
  --state-dir /data/wellhealth-smartmedicine \
  --base-url http://127.0.0.1:18100 \
  --namespace smartmedicine-test \
  --database-url sqlite:////var/lib/smartmedicine/consultation.db
```

**生成的文件**（均在 `/etc/wellhealth-smartmedicine/`，权限 600）：

| 文件 | 内容 | 用途 |
|------|------|------|
| `credentials.json` | API Key 原文、Fernet Key、Subject Secret | **只备份，不给前端，不入 Git** |
| `consultation.env` | `SM_CONSULT_*` 环境变量（含 SHA256 摘要） | Docker 容器加载 |
| `application-wellhealth.yml` | Java 配置（已填好真实 Key） | 合入 SmartMedicine JAR |
| `compose.env` | Compose 路径与端口参数 | run.sh 使用 |

**密钥生成算法**（`prepare_config.py:120-126`）：
- API Key：`secrets.token_hex(32)` → 64 字符十六进制明文（给 Java）
- Fernet Key：`base64.urlsafe_b64encode(secrets.token_bytes(32))` → 数据加密密钥
- Subject Secret：`secrets.token_hex(32)` → 主体派生密钥
- SHA256 摘要：`hashlib.sha256(api_key.encode()).hexdigest()` → 存入 `SM_CONSULT_KEY_HASHES`

### 步骤 2：查看生成的 API Key 原文（仅运维，安全终端）

```bash
# credentials.json 含 api_key 原文，仅在安全终端查看
cat /etc/wellhealth-smartmedicine/credentials.json
```

`api_key` 字段是给 SmartMedicine JAR 的明文 Key；`consultation.env` 里的 `SM_CONSULT_KEY_HASHES` 是它的 SHA256 摘要，容器只存摘要。

### 步骤 3：轮换 Key（如需）

重新 prepare 会**拒绝覆盖**已有配置（`prepare_config.py:111-115`）。轮换流程：
1. 备份 `/etc/wellhealth-smartmedicine/credentials.json`
2. 删除该文件后重新 prepare（会生成新 Key，**历史数据用旧 Fernet Key 仍可解密**）
3. 在 `consultation.env` 的 `SM_CONSULT_KEY_HASHES` 中同时配置新旧两个摘要
4. 重启容器，用 CLI 吊销旧 key_id：`docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli revoke-key smartmedicine-test-v1`

---

## 三、构建镜像

镜像构建用项目自带的 `backend/Dockerfile`（两阶段构建：builder 装 Poetry 导出依赖 → runtime 复制 venv + 代码）。**同一个镜像既能跑主应用也能跑 smartmedicine**，通过覆盖 CMD 切换入口，不需要改 Dockerfile。

```bash
# 在仓库根目录执行
docker build -t wellhealth-backend:latest backend/
```

构建产物含完整 `backend/app/` 代码（`executor.py` 复用主应用 `AgentExecutor`/`SafetyChecker`，需要全部代码）。

### 验证镜像

```bash
# 看镜像大小
docker images wellhealth-backend:latest

# 确认 smartmedicine 入口可加载
docker run --rm wellhealth-backend:latest python -c "from app.integrations.smartmedicine.app import app; print('smartmedicine OK')"

# 确认主应用入口可加载（如需回退）
docker run --rm wellhealth-backend:latest python -c "from app.main import app; print('main OK')"
```

### 常见构建问题

| 问题 | 解决 |
|------|------|
| 构建慢 | 首次装全部依赖（langchain/neo4j/qdrant 等），后续只改 `app/` 代码走 `COPY . .` 缓存层，几秒完成 |
| Poetry export 失败 | `poetry.lock` 与 `pyproject.toml` 不同步，先 `cd backend && poetry lock` 更新再构建 |
| 想精简镜像 | 不建议：`executor.py:26-27` 复用主应用类，精简会缺依赖；用覆盖 CMD 切换入口即可 |

---

## 四、部署（两种方式任选其一）

### 方式 A：用独立 compose 文件（推荐，本手册新增）

独立 compose 文件为 `deploy/smartmedicine/docker-compose.yml.txt`（因写入工具对 `.yml` 验证有环境限制，以 `.txt` 提供）。**首次使用前重命名**：

```bash
cp deploy/smartmedicine/docker-compose.yml.txt deploy/smartmedicine/docker-compose.yml
```

该文件是完整独立的编排，不依赖 `deploy/docker-compose.yml` base，可直接 `docker compose -f` 使用。内容覆盖：复用 `backend/Dockerfile` 镜像、覆盖 CMD 为 smartmedicine 入口、注入全部 `SM_CONSULT_*` 与主应用 LLM/中间件配置、持久化卷、健康检查、资源限制。

```bash
# 1. 构建镜像（复用 backend/Dockerfile，不新建 Dockerfile）
docker compose -f deploy/smartmedicine/docker-compose.yml \
  --env-file /etc/wellhealth-smartmedicine/consultation.env \
  build backend

# 2. 初始化数据库表（必须显式执行，绝不自动建表）
docker compose -f deploy/smartmedicine/docker-compose.yml \
  --env-file /etc/wellhealth-smartmedicine/consultation.env \
  run --rm backend python -m app.integrations.smartmedicine.cli init-db

# 3. 启动
docker compose -f deploy/smartmedicine/docker-compose.yml \
  --env-file /etc/wellhealth-smartmedicine/consultation.env \
  up -d backend

# 4. 启用运行时开关
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli set-mode enabled
```

### 方式 B：用 run.sh（带自动回滚，适合替换已有容器）

```bash
# 1. 首次准备配置（等同步骤一）
bash deploy/smartmedicine/run.sh prepare

# 2. 构建 + 初始化 + 替换原 18100 容器 + 验证（失败自动回滚）
bash deploy/smartmedicine/run.sh deploy

# 3. 查看状态
bash deploy/smartmedicine/run.sh status
```

`run.sh` 会把原容器改名为 `wellhealth-backend-before-sm-时间戳` 保留，验证失败自动恢复。

---

## 五、验证

### 4.1 健康检查（无需认证）

```bash
curl http://127.0.0.1:18100/health
# 期望：{"service":"smartmedicine-consultation","enabled":true}
```

### 4.2 认证 API 验证（用 prepare 生成的 Key）

```bash
# 从 credentials.json 取 api_key
API_KEY=$(python3 -c "import json; print(json.load(open('/etc/wellhealth-smartmedicine/credentials.json'))['api_key'])")

curl -H "X-API-Key: $API_KEY" \
     -H "X-External-Subject: deployment-probe-0001" \
     http://127.0.0.1:18100/api/v1/integrations/smartmedicine/capabilities
# 期望：含 schema_version=1, enabled=true, transport="poll", agents 列表
```

或直接用自带工具：
```bash
python3 deploy/smartmedicine/prepare_config.py verify --config-dir /etc/wellhealth-smartmedicine
```

### 4.3 端到端验收（见 SMARTMEDICINE-CONSULTATION.md 第 9 节）

1. 用 SmartMedicine 登录账号建会诊、选 2-3 专家、两轮讨论、查看总结
2. 用第二个账号尝试第一个账号的 session → 应被拒绝（owner-scoped）
3. 重复相同 Idempotency-Key → 不重复调用模型

---

## 六、SmartMedicine JAR 对接

JAR 包部署在 `/opt/soft/smartmedicine` 路径下启动。prepare 已生成 `/etc/wellhealth-smartmedicine/application-wellhealth.yml`，含真实 Key。

**方法 A**：合入 JAR 已加载的外部 `application.yml` 的 `wellhealth` 段。

**方法 B**：独立加载（推荐，不动原配置）：
```bash
# 在 /opt/soft/smartmedicine 目录下启动
cd /opt/soft/smartmedicine
java -jar smartmedicine.jar \
  --spring.config.additional-location=file:/etc/wellhealth-smartmedicine/application-wellhealth.yml
```

若原启动命令已有 `additional-location`，把该文件追加到同一逗号分隔列表，不要重复参数覆盖原列表。

JAR 侧配置项（`deploy/SMARTMEDICINE-CONSULTATION.md` 第 5 节）：

| Spring 属性 | 环境变量 | 说明 |
|-------------|---------|------|
| `wellhealth.consultation.enabled` | `WELLHEALTH_CONSULTATION_ENABLED` | 总开关 |
| `wellhealth.consultation.base-url` | `WELLHEALTH_CONSULTATION_BASEURL` | `http://127.0.0.1:18100` |
| `wellhealth.consultation.api-key` | `WELLHEALTH_CONSULTATION_APIKEY` | prepare 生成的明文 Key |
| `wellhealth.consultation.subject-secret` | `WELLHEALTH_CONSULTATION_SUBJECTSECRET` | ≥32 字符，稳定不变 |
| `wellhealth.consultation.subject-namespace` | `WELLHEALTH_CONSULTATION_SUBJECTNAMESPACE` | 主体命名空间 |

---

## 七、日常运维

```bash
# 查看运行状态（不打印凭据）
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli status

# 停止接收新任务（已有会诊可完成）
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli set-mode draining

# 完全禁用（活动任务在检查点停止）
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli set-mode disabled

# 吊销某个 API Key（立即生效，无需重启）
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli revoke-key smartmedicine-test-v1

# 清理过期会话（按 SM_CONSULT_RETENTION_DAYS，不自动执行）
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli purge --confirm

# 查看日志
docker logs wellhealth-backend -f --tail 100
```

---

## 八、配置项完整清单

### 会诊服务专用（`SM_CONSULT_*` 前缀）

| 变量 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `SM_CONSULT_ENABLED` | ✅ | `false` | 总开关，fail-closed |
| `SM_CONSULT_DATABASE_URL` | ✅ | - | 独立数据库连接串 |
| `SM_CONSULT_DATA_KEY` | ✅ | - | Fernet 加密密钥（prepare 生成） |
| `SM_CONSULT_KEY_HASHES` | ✅ | - | API Key 的 SHA256 摘要 JSON |
| `SM_CONSULT_CLIENT_ID` | ❌ | `smartmedicine` | 客户端标识 |
| `SM_CONSULT_CONTROL_FILE` | 推荐 | - | kill switch 文件路径 |
| `SM_CONSULT_MAX_CONCURRENT_RUNS` | ❌ | `2` | 全局并发上限 `[1,8]` |
| `SM_CONSULT_EXPERT_TIMEOUT` | ❌ | `60` | 单专家超时（秒） |
| `SM_CONSULT_RUN_TIMEOUT` | ❌ | `420` | 整次会诊超时（秒） |
| `SM_CONSULT_RETENTION_DAYS` | ❌ | `7` | 数据保留天数 `[1,365]` |

### 主应用透传（executor.py 复用）

`LLM_PROVIDER` / `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` / `MYSQL_*` / `REDIS_*` / `QDRANT_*` / `NEO4J_*` —— 与主应用相同，用于读取 Agent 定义和调用 LLM。

---

## 九、安全红线

- 🚫 `credentials.json`、`consultation.env` **严禁入 Git**（prepare 已设 600 权限）
- 🚫 API Key 原文**只给 SmartMedicine JAR**，Python 容器只存 SHA256 摘要
- 🚫 `SM_CONSULT_DATA_KEY` 丢失后**历史数据无法解密**，必须安全备份
- 🚫 `subject-secret` 改变会生成不同主体，旧历史对用户不可见
- 🚫 不要把 Key 放入 `VITE_*`、小程序、请求 URL、日志
- ✅ 容器只绑定 `127.0.0.1:18100`，跨机访问必须走 TLS 网关
- ✅ 控制文件损坏时 fail-closed（`settings.py:69-77`）

---

## 十、故障排查

| 现象 | 排查 |
|------|------|
| 启动报 `Integration tables missing` | 未执行 `cli init-db`，见步骤三 |
| 启动报 `Demo runner requires exactly one worker` | `WEB_CONCURRENCY` 不是 1 |
| 401 `INVALID_SERVICE_KEY` | API Key 长度不在 `[24,256]` 或摘要不匹配 |
| 400 `INVALID_SUBJECT` | `X-External-Subject` 不匹配 `[A-Za-z0-9_-]{16,128}` |
| 429 `CAPACITY_EXCEEDED` | 全局并发达上限，调 `SM_CONSULT_MAX_CONCURRENT_RUNS` |
| 503 `SERVICE_UNAVAILABLE` | 内部异常，看 `docker logs`，对外不暴露详情 |
| `enabled: false` | `SM_CONSULT_ENABLED` 不是 `true`，或控制文件 mode=disabled |


已完成 40s

两个问题分别回答。

问题一：Dockerfile 不需要改，在启动命令中覆盖即可

现有 backend/Dockerfile:51 的 CMD 是主应用入口：

dockerfile
 
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18100"]


smartmedicine 入口是 app.integrations.smartmedicine.app:app，只需覆盖 CMD，不需要改 Dockerfile。两种方式：

方式 A：docker run（直接覆盖）
bash
 
docker run -d --name wellhealth-backend \
  -p 127.0.0.1:18100:18100 \
  --env-file /etc/wellhealth-smartmedicine/consultation.env \
  -v smartmedicine_state:/var/lib/smartmedicine \
  wellhealth-backend:latest \
  python -m uvicorn app.integrations.smartmedicine.app:app --host 0.0.0.0 --port 18100 --workers 1


末尾的 python -m uvicorn ... 会覆盖 Dockerfile 的 CMD。

方式 B：docker-compose（我新建的文件已处理）

deploy/smartmedicine/docker-compose.yml.txt 中已用 command: 覆盖：

yaml
 
command:
  - python
  - -m
  - uvicorn
  - app.integrations.smartmedicine.app:app
  - --host
  - 0.0.0.0
  - --port
  - "18100"
  - --workers
  - "1"


为什么不建议改 Dockerfile：

同一个镜像 wellhealth-backend:latest 既能跑主应用也能跑 smartmedicine，改 Dockerfile 会破坏主应用部署
executor.py:26-27 复用主应用的 AgentExecutor/SafetyChecker，需要完整的 backend/app/ 代码，所以镜像不能精简
覆盖 CMD 是 Docker 的标准做法，比维护两个 Dockerfile 更清晰
问题二：停止 API Key 使用的四种方式（从轻到重）

按"影响范围从小到大、是否中断活动任务"排列：

1. 吊销单个 Key（不停止服务，推荐）
bash
 
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli revoke-key smartmedicine-test-v1

效果：该 Key 立即返回 401（auth.py:52），其他 Key 不受影响
活动任务：在下一个检查点停止（service.py:58-65 每 0.25s 检查）
无需重启容器，控制文件原子更新（cli.py:13-28）
可逆：编辑控制文件从 revoked_key_ids 移除该 key_id 即恢复
2. draining 模式（停止接新任务，已有任务完成）
bash
 
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli set-mode draining

效果：拒绝新建会诊，已有会诊允许完成（app.py:75 require_creation() 检查）
历史读取：仍可查询历史
适用场景：计划停机前的优雅排空
3. disabled 模式（完全禁用，活动任务停止）
bash
 
docker exec wellhealth-backend python -m app.integrations.smartmedicine.cli set-mode disabled

效果：所有请求返回 503（auth.py:44-45），活动任务在检查点取消
无需重启容器，进程还活着，可随时 set-mode enabled 恢复
适用场景：紧急止血，但想保留容器和状态
4. 停止容器（最直接，活动任务 interrupted）
bash
 
docker stop wellhealth-backend

效果：进程退出，活动任务被标记为 interrupted（app.py:35 recover_interrupted()）
重启后：interrupted 的任务不会自动重试（避免重复计费，service.py:76 注释）
数据不丢：SQLite/MySQL 持久化，控制文件在卷中
适用场景：彻底停服
决策建议
场景	用哪个
只想停某个调用方的 Key	revoke-key
计划停机，想等现有会诊跑完	set-mode draining
紧急止血，但想保留快速恢复能力	set-mode disabled
彻底停服、释放资源	docker stop

最简单的"停止使用"操作：如果只是不再让外部项目调用，用 revoke-key 即可——一行命令、立即生效、不中断服务、可逆。直接 docker stop 会中断活动任务且重启后不自动恢复，除非确实要停服否则不必走到这一步。

预估Token消耗: 82.2K
11:48