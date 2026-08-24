# 康伴 (WellHealth)

> 慢病管理AI平台 — 多Agent协作 + 干预效果仿真 + 医疗级安全评估

## 项目介绍

康伴(WellHealth)是一款专注于慢性病管理的AI平台，以糖尿病、高血压为核心，通过9个专业化AI Agent协作、干预效果仿真预测、医疗级安全评估等核心技术，为慢病患者提供专业、个性化的健康管理服务。

**定位**：做慢病领域的专科AI专家，而不是健康领域的全能助手。

## 核心特性

- **多Agent协作** — 9个专科Agent（糖尿病、高血压、营养、运动、用药、心理、康复、认知、通用）协同服务，支持会诊/辩论/协作三种编排模式
- **干预效果仿真** — AI预测不同干预方案30天/90天的效果，支持多方案对比
- **医疗级安全评估** — 三层防护：安全红线检查 + 质量门控 + 自动免责声明，含红队测试
- **深度慢病专科** — GI/GL食物库、碳水计算、胰岛素剂量计算、血糖趋势分析、药物相互作用检查
- **认知健康管理** — LLM驱动的认知评估 + 4种互动训练游戏 + 进度追踪
- **家庭关怀体系** — 家庭管理、隐私控制、关怀消息、用药依从性监控、健康预警通知
- **Per-Agent LLM配置** — 每个Agent可独立配置LLM Provider/Model，支持5种Provider和降级策略

## 技术架构

### 后端

| 组件 | 技术 | 说明 |
|------|------|------|
| Web框架 | FastAPI | 异步高性能，自动生成API文档 |
| ORM | SQLAlchemy | 数据库操作 |
| LLM编排 | LangChain / LangGraph | Agent编排与RAG |
| 主数据库 | MySQL 8.0 | 业务数据（26张表） |
| 知识图谱 | Neo4j 5.x | 疾病-药物-食物关系网络 |
| 缓存 | Redis 7.0 | 会话缓存与消息队列 |
| 向量检索 | Qdrant | RAG语义检索 |
| 任务队列 | Celery | 异步任务处理 |

### 前端

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | Composition API |
| UI库 | Element Plus | 企业级组件库 |
| 状态管理 | Pinia | 轻量级Store |
| 图表 | ECharts | 数据可视化 |
| 桌面端 | Tauri 2.x | 跨平台桌面应用 |
| 构建工具 | Vite 6 | 快速开发与构建 |

### LLM Provider支持

| Provider | 模型示例 | 适用场景 |
|----------|---------|---------|
| OpenAI | gpt-4o / gpt-4o-mini | 通用对话、多模态 |
| Anthropic | claude-3-5-sonnet | 用药咨询、心理支持 |
| SiliconFlow | Qwen2.5-7B-Instruct | 高频低成本调用 |
| DashScope | qwen-plus | 国内合规场景 |
| Ollama | llama3 | 本地私有化部署 |

## 系统架构

```
用户请求
   │
   ▼
┌──────────┐    ┌─────────────────────────────────────────┐
│ Chat API │───▶│ Agent选择（关键词 / LLM智能路由）         │
└──────────┘    └────────────────┬────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ 单Agent  │   │ 多Agent  │   │  RAG增强     │
        │ 对话     │   │ 会诊     │   │  检索+生成   │
        └────┬─────┘   └────┬─────┘   └──────┬───────┘
             │              │                │
             ▼              ▼                ▼
        ┌─────────────────────────────────────────┐
        │         LLMRouter（多Provider路由）       │
        │   OpenAI / Anthropic / SiliconFlow /     │
        │   DashScope / Ollama + 降级策略          │
        └────────────────┬────────────────────────┘
                        │
                        ▼
        ┌─────────────────────────────────────────┐
        │  QualityGate 质量门控 → SafetyChecker    │
        │  （7条通用规则 + 6条健康规则 + 安全红线）  │
        └────────────────┬────────────────────────┘
                        │
                        ▼
                   安全响应输出
```

## 9个专业Agent

| Agent | 角色 | 专长 | 可用工具 |
|-------|------|------|---------|
| 健康助手 | 健康顾问 | 健康咨询、生活方式 | knowledge_search |
| 糖尿病专科 | 内分泌科医生助手 | 糖尿病、肾病、视网膜病变 | knowledge_search, drug_interaction_check, vitals_analysis |
| 高血压专科 | 心内科医生助手 | 高血压、心血管健康、脑卒中预防 | knowledge_search, drug_interaction_check, vitals_analysis |
| 营养咨询 | 临床营养师 | 糖尿病/高血压饮食、营养评估 | knowledge_search, food_database |
| 健康教练 | 健康管理师 | 运动处方、习惯养成、体重管理 | knowledge_search |
| 用药咨询 | 临床药师助手 | 药物咨询、相互作用、依从性 | knowledge_search, drug_interaction_check |
| 心理支持 | 心理咨询师助手 | 压力管理、情绪疏导、慢病心理 | knowledge_search |
| 康复指导 | 康复治疗师助手 | 康复训练、运动处方、功能恢复 | knowledge_search, vitals_analysis |
| 认知评估 | 认知评估师助手 | 认知评估、训练建议、早期衰退检测 | knowledge_search, cognitive_assessment |

## 功能模块

| 模块 | 功能 | 前端页面 |
|------|------|---------|
| AI咨询 | 单Agent/多Agent会诊/Agent对话(SSE流式) | ChatView |
| 干预仿真 | 干预效果预测、多方案对比 | SimulationView |
| 慢病管理 | 食物GI/GL查询、碳水计算、血糖趋势分析、食谱生成 | ChronicDiseaseView |
| 认知健康 | 文本认知评估、4种训练游戏、进度报告 | CognitiveAssessmentView / CognitiveTrainingView / CognitiveReportView |
| 健康数据 | 体征记录、趋势分析、健康预警 | HealthDataView |
| 健康预测 | 血糖预测、并发症预测、干预效果预测 | PredictionView |
| 用药管理 | 用药提醒、服药记录、依从性监控 | MedicationReminderView |
| 处方查询 | 处方查询、购药记录 | PrescriptionView / PurchaseView |
| 家庭关怀 | 家庭管理、关怀消息、隐私控制、预警通知 | FamilyView |
| 拍照做菜 | 食材识别(图片/文字)、菜谱生成、营养计算 | RecipeView |
| 卡路里跟踪 | 饮食热量记录与分析 | CalorieView |
| 知识库 | 医学知识检索与推荐 | KnowledgeView |
| 患者管理 | 患者信息CRUD、生命体征管理 | PatientView / PatientManageView |
| 系统管理 | Agent配置、LLM配置、系统监控 | AdminView / AgentConfigView |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Redis 7.0
- Neo4j 5.x
- Qdrant

### 本地开发

1. 克隆项目
```bash
git clone https://github.com/your-org/wellhealth.git
cd wellhealth
```

2. 后端启动
```bash
cd backend
cp .env.example .env
# 编辑 .env 配置数据库和LLM API Key
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. 前端启动（Web模式）
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:8443
```

4. 前端启动（Tauri桌面模式）
```bash
cd frontend
npm install
npm run tauri:dev
```

5. Docker一键启动（后台运行）
```bash
# 一键后台启动（构建 + 启动 + 迁移全自动）
bash deploy/start.sh                    # Linux/macOS
.\deploy\start.ps1                      # Windows PowerShell
# 或手动分步：详细说明见 deploy/README.md
```

### 环境变量配置

复制 `backend/.env.example` 为 `.env`，主要配置项：

```env
# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=wellhealth
MYSQL_PASSWORD=wellhealth123
MYSQL_DATABASE=wellhealth

# LLM Provider（至少配置一个）
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key        # 可选
ANTHROPIC_API_KEY=your-api-key     # 可选

# 安全
SECRET_KEY=your-secret-key          # 生产环境必须更换
```

## 项目结构

```
wellhealth/
├── backend/                        # Python后端
│   ├── app/
│   │   ├── agents/definitions/    # 9个Agent定义（YAML+MD）
│   │   │   ├── coach/            # 健康教练Agent
│   │   │   ├── cognitive/        # 认知评估Agent
│   │   │   ├── diabetes/         # 糖尿病专科Agent
│   │   │   ├── general/          # 通用健康助手
│   │   │   ├── hypertension/     # 高血压专科Agent
│   │   │   ├── medication/       # 用药咨询Agent
│   │   │   ├── nutrition/        # 营养咨询Agent
│   │   │   ├── psychology/       # 心理支持Agent
│   │   │   └── rehabilitation/   # 康复指导Agent
│   │   ├── api/                  # API路由（20+模块）
│   │   ├── services/             # 业务逻辑
│   │   │   ├── agents/          # 多Agent框架
│   │   │   │   ├── core/       # Agent定义/加载/执行/LLM路由
│   │   │   │   ├── orchestrator/ # 工作流编排/多Agent对话
│   │   │   │   └── quality/    # 质量门控
│   │   │   ├── agent_manager.py # Agent管理/选择/意图分类
│   │   │   ├── chronic_disease_manager.py  # 慢病管理
│   │   │   ├── cognitive_service.py        # 认知评估与训练
│   │   │   ├── family_service.py           # 家庭关怀体系
│   │   │   ├── health_prediction_service.py # 健康预测
│   │   │   ├── intervention_simulator.py    # 干预仿真
│   │   │   ├── knowledge_base.py           # 知识图谱+RAG
│   │   │   ├── llm_client.py              # 统一LLM客户端
│   │   │   ├── recipe_service.py           # 食谱服务
│   │   │   └── safety_checker.py           # 安全检查
│   │   ├── models/               # 数据模型（26张表）
│   │   └── utils/                # 工具类（数据库/认证/邮件）
│   ├── scripts/                  # 数据库脚本
│   └── pyproject.toml
├── frontend/                       # Vue3前端 + Tauri桌面端
│   ├── src/
│   │   ├── views/                # 24个页面视图
│   │   │   └── cognitive/       # 4个认知训练游戏
│   │   ├── components/           # 公共组件
│   │   ├── stores/              # Pinia状态管理（4个Store）
│   │   ├── api/                 # API客户端封装
│   │   ├── router/              # 路由配置（27条路由）
│   │   ├── config/              # 应用配置
│   │   └── assets/              # 静态资源与样式
│   ├── src-tauri/                # Tauri桌面端配置
│   └── package.json
├── deploy/                         # Docker部署
│   ├── docker-compose.yml        # 前后端编排（+可选Ollama）
│   └── README.md                 # 部署文档
├── docs/                           # 项目文档
│   ├── init.sql                  # 数据库初始化（26张表+种子数据）
│   ├── neo4j_init.cypher         # 知识图谱初始化
│   └── WellHealth-系统架构文档.md
├── config/                         # 主题配置
├── constraints/                    # 约束规则（后端/前端/安全）
└── agents.md                       # AI Agent操作手册
```

## API文档

启动后端服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### 主要API端点

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/api/v1/chat` | AI咨询 | 消息发送、多Agent会诊、SSE流式对话 |
| `/api/v1/patients` | 患者管理 | 患者CRUD、生命体征、用药提醒、体检报告 |
| `/api/v1/chronic` | 慢病管理 | 食物查询、碳水计算、血糖分析、食谱生成 |
| `/api/v1/cognitive` | 认知健康 | 认知评估、训练生成、进度查询 |
| `/api/v1/simulation` | 干预仿真 | 模拟运行、方案对比 |
| `/api/v1/prediction` | 健康预测 | 血糖/并发症/干预效果预测 |
| `/api/v1/prescriptions` | 处方管理 | 处方查询与详情 |
| `/api/v1/knowledge` | 知识库 | 知识检索与推荐 |
| `/api/v1/admin` | 系统管理 | Agent配置、系统监控 |
| `/api/v1/users` | 用户管理 | 注册、登录、权限 |

## 数据架构

### MySQL（26张表）

- **核心业务**：users, patients, doctors, disease_records, medication_records, vital_records 等
- **AI对话**：agents, chat_sessions, chat_messages, evaluations
- **慢病管理**：food_database(91种食物), glucose_records, meal_plans, insulin_records 等
- **家庭关怀**：families, family_members, care_messages, health_alerts, encourage_cards 等

### Neo4j知识图谱

- **实体**：疾病、药物(13种)、症状、食物(20种)、运动、并发症、检查项目
- **关系**：治疗、导致、并发、药物相互作用(含风险等级)、推荐、属于等
- **特色**：药物相互作用标注风险等级(high/moderate/low)与处理建议

## 安全体系

- **SafetyChecker**：红线规则（禁止诊断、禁止具体剂量、紧急症状检测）+ 警告规则 + 三级安全等级
- **QualityGate**：7条通用规则 + 6条健康领域规则，STRICT/NORMAL/LENIENT三级验证
- **RBAC权限**：4种角色（admin/doctor/patient/family）+ 细粒度权限控制
- **数据安全**：敏感数据加密存储、SQL注入防护、XSS防护
- **医疗合规**：所有AI建议自动添加免责声明，禁止生成诊断结论和具体用药剂量

## 路线图

- [x] 项目框架搭建
- [x] 9个Agent角色库定义
- [x] 多Agent协作引擎（会诊/辩论/协作模式）
- [x] Per-Agent LLM配置与降级策略
- [x] RAG检索系统（向量+知识图谱）
- [x] 安全评估模块（红线+质量门控+红队测试）
- [x] SSE流式输出
- [x] 认知评估与训练
- [x] 家庭关怀体系
- [ ] 知识图谱完善
- [ ] 干预效果仿真增强
- [ ] 工作流编排器增强
- [ ] 多模态支持（语音/影像）
- [ ] 实时健康数据集成
- [ ] 管理后台完善

## 许可证

Apache License 2.0
