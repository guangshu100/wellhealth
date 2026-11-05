# 同服务器部署：替换原WellHealth后端，保留18100端口

## 部署结果

- 沿用仓库已有 `backend/Dockerfile` 和 `wellhealth-backend:latest` 镜像名称。
- 原容器 `wellhealth-backend` 被停止并改名保留，新容器仍叫 `wellhealth-backend`。
- 宿主机只绑定 `127.0.0.1:18100`，SmartMedicine JAR直接HTTP访问，不需要HTTPS/Nginx。
- 新入口为 `app.integrations.smartmedicine.app:app`，原WellHealth登录、患者、管理等API不再由该容器提供。原前端可能因此不可用；这是替换部署，不是无损并存。
- 当前功能支持多专家/多轮讨论与历史，传输是poll；不是SSE，脚本不伪称部署了SSE。

## 一、本目录需要放在哪里

WellHealth仓库中的文件结构应为：

```text
wellhealth/
  backend/Dockerfile                     # 已有，不需要新建
  deploy/docker-compose.yml              # 已有，保留
  deploy/smartmedicine/
    run.sh
    prepare_config.py
    docker-compose.replace.yml
    application-wellhealth.yml.example
    consultation.env.example
    tests/test_deployment.py
    README.md
```

SmartMedicine仓库 `deploy/wellhealth-smartmedicine/` 保留同一套可上传文件，真正使用时放在WellHealth的上述目录；不要在SmartMedicine目录直接执行Docker替换。

## 二、只需运行这三条命令

先把**包含本次集成模块的WellHealth代码**发布到服务器原仓库。以下在WellHealth仓库根目录执行：

```bash
# 1. 首次准备配置：只生成一次，后续不重新生成密钥
bash deploy/smartmedicine/run.sh prepare

# 2. 构建、初始化、替换原18100后端并验证
bash deploy/smartmedicine/run.sh deploy

# 3. 查看运行状态
bash deploy/smartmedicine/run.sh status
```

命令需要部署账户有Docker和目标配置目录写权限；脚本仅用Bash、Python3标准库和现有Docker Compose V2，不需要部署账户安装WellHealth虚拟环境。替换有维护窗口，会中断原服务正在处理的请求；先确认原服务允许替换。

如果目录不是标准布局，显式指定仓库绝对路径：

```bash
WH_REPO=/opt/wellhealth bash /opt/wellhealth/deploy/smartmedicine/run.sh deploy
```

若原部署使用 `deploy/.env` 的中间件覆盖参数，脚本会先加载该文件，再加载新增的Compose参数；`backend/.env`作为原服务env_file继续保留，不修改它。

## 三、prepare到底创建哪些文件

默认在服务器 **/etc/wellhealth-smartmedicine/** 生成：

| 文件 | 用途 |
|---|---|
| credentials.json | 原始服务Key、Fernet数据Key、固定主体secret与部署元信息；只备份，不发送到前端 |
| consultation.env | Python专用配置，保存API Key的SHA256摘要，不含服务Key原文 |
| application-wellhealth.yml | 已填好HTTP地址和真实Key的Java配置，可直接合入JAR外部YAML |
| compose.env | 替换部署所需路径与回环端口映射 |

所有文件以600权限创建，目录默认700。真实Key不会预置在源码、示例文件或脚本输出中。重复prepare保持密钥与内容不变；检测到手工修改或不完整配置时拒绝覆盖，不会偷偷旋转Key。

如果已有老部署的密钥/加密历史，不要另起prepare覆盖其身份域；先明确迁移旧数据和凭据。生成器默认处理本套部署首次配置。

默认持久数据目录是 **/data/wellhealth-smartmedicine/**，其中包含SQLite会诊数据库及动态控制文件；容器重建不会删除它。原模型配置/原业务数据库/知识库仍沿用既有部署，不由本脚本迁移。

可选自定义目录（prepare和deploy必须使用一致的值）：

```bash
SM_CONFIG_DIR=/etc/my-consultation SM_STATE_DIR=/data/my-consultation \
  bash deploy/smartmedicine/run.sh prepare
SM_CONFIG_DIR=/etc/my-consultation SM_STATE_DIR=/data/my-consultation \
  bash deploy/smartmedicine/run.sh deploy
```

## 四、SmartMedicine JAR配置怎么使用

prepare已经在服务器生成：

```text
/etc/wellhealth-smartmedicine/application-wellhealth.yml
```

内容已填好，不需要再手工计算摘要或复制环境变量。**其中服务Key原文与Python摘要自动匹配。**

方法A：把该文件的wellhealth段合并到JAR已经加载的外部application.yml，保留数据库/Redis等原配置；已有wellhealth节点则合并，不能重复顶层节点。

方法B：将该文件安全复制为独立配置，例如 `/etc/smartmedicine/application-wellhealth.yml`，保证JAR运行用户有读取权限，保持密钥文件私有。在原JAR命令的配置列表追加该文件：

```text
--spring.config.additional-location=file:/etc/smartmedicine/application-wellhealth.yml
```

原命令已有additional-location时，将文件追加到同一逗号分隔列表；不要重复参数覆盖原列表，不要丢弃原数据库配置。重启JAR即可。若JAR不含新增ConsultationController等代码，需先更新JAR；配置文件不会补出不存在的接口。

Java配置的有效形态如下（实际值由脚本生成）：

```yaml
wellhealth:
  consultation:
    enabled: true
    base-url: "http://127.0.0.1:18100"
    api-key: "脚本已生成并填写"
    subject-secret: "脚本已生成并填写的稳定Secret"
    subject-namespace: "smartmedicine-test"
    allow-insecure-local: true
    connect-timeout-ms: 3000
    request-timeout-ms: 15000
```

Fernet数据Key和subject-secret丢失/改变会影响历史解密或归属。不要每次发布都重新生成。Web与小程序只配置SmartMedicine的业务地址，不拿任何服务Key。

## 五、脚本如何保护现有容器

1. 先按已有Dockerfile构建，并用一次性CLI验证集成数据库/建表，失败时不停止原服务。
2. 把原容器停止并改名为 `wellhealth-backend-before-sm-时间戳`，不删除。
3. 每次发布使用独立Compose project，避免Docker Compose根据旧labels自动找到并重建已改名的备份容器。
4. 用相同镜像名称启动新入口，仍叫wellhealth-backend、仍用18100。
5. 用正确API Key调用新capabilities，而不只检查旧/health。验证失败自动恢复旧容器。
6. 不执行docker rm、整栈down、数据库清空或密钥轮换。

备份容器保留原配置及镜像引用。旧原镜像不包含集成代码时，回退旧容器意味着回到旧平台，新会诊应在Java侧关闭。脚本不承诺零停机；回退也不代表自动转换不同版本数据库结构。

## 六、验证和常用操作

```bash
# 校验服务Key和新API已真正生效；不会打印Key
bash deploy/smartmedicine/run.sh verify

# 停止接收新任务，已有会诊可完成
bash deploy/smartmedicine/run.sh drain

# 禁用集成，活动任务在检查点停止
bash deploy/smartmedicine/run.sh disable

# 停止当前后端，不删容器和数据
bash deploy/smartmedicine/run.sh stop

# 保留新容器并恢复上一次替换前的旧容器
bash deploy/smartmedicine/run.sh rollback
```

更新版本：先drain并等待当前会诊结束，将新版代码发布到原目录，再运行deploy；不要重新prepare密钥。不要一边运行两次deploy，避免容器名与发布记录冲突。

通过SmartMedicine登录后进入 `/consultation`，发起真实两轮会诊并追问、刷新恢复。verify只证明新API与凭据有效，不证明真实模型可用。模型失败要核对原Agent数据库优先配置/模型凭据和默认汇总Provider；本套脚本不更改模型业务配置。

## 七、本次交付的验证边界

源码中提供生成器和文件契约测试。执行：

```bash
python3 -m unittest discover -s deploy/smartmedicine/tests -v
```

该测试文件使用PyYAML解析模板；部署脚本和生成器运行本身不需要PyYAML。测试不调用真实Docker、生产数据库或模型。实际镜像构建与容器替换只应在目标服务器由部署人员执行。
