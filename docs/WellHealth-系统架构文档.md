# 康伴(WellHealth) - 系统架构文档

## 1. 项目概述

### 1.1 项目简介
康伴(WellHealth)是一款专注于慢性病管理的AI平台，通过多Agent协作、干预效果仿真预测、医疗级安全评估等核心技术，为慢病患者提供专业、个性化的健康管理服务。

### 1.2 核心特性
- 🤖 **多Agent协作** - 8个专科Agent协同服务（糖尿病、高血压、营养、运动、用药、心理、康复、通用）
- 📊 **干预效果仿真** - AI预测不同干预方案的效果
- 🛡️ **医疗级安全评估** - 系统性安全红线+红队测试
- 🔬 **深度慢病专科** - 专注糖尿病、高血压等专病管理

## 2. 业务架构

### 2.1 核心业务流程

```
用户提问 → Agent智能选择 → 多Agent并行/串行执行 → 质量门控 → 综合建议 → 安全检查 → 返回结果
```

### 2.2 Agent角色体系

| Agent类型 | 角色 | 专业领域 | 触发关键词 |
|-----------|------|----------|------------|
| diabetes | 糖尿病专家 | 血糖管理、并发症预防、用药指导 | 血糖、糖尿病、胰岛素 |
| hypertension | 高血压专家 | 血压监测、心血管健康、生活方式干预 | 血压、高血压 |
| nutrition | 营养师 | 饮食评估、食谱推荐、GI查询 | 饮食、食物、营养、食谱 |
| coach | 健康教练 | 运动处方、习惯养成、目标设定 | 运动、锻炼、跑步 |
| medication | 用药顾问 | 药物咨询、相互作用检查、用药依从性 | 药、用药、服用 |
| psychology | 心理支持 | 情绪疏导、压力管理、放松技巧 | 焦虑、抑郁、失眠、情绪 |
| rehabilitation | 康复专家 | 康复训练、功能恢复、术后指导 | 康复、脑梗、偏瘫、训练 |
| general | 健康助手 | 通用健康咨询、知识科普 | 默认兜底 |

### 2.3 咨询模式

#### 2.3.1 单Agent模式
- 用户提问 → 系统匹配最相关Agent → 返回专业回答
- 适用场景：简单明确的健康问题

#### 2.3.2 多Agent会诊模式（Multi-Agent）
- 用户提问 → 自动/手动选择多个相关Agent → 并行执行 → 综合汇总
- 适用场景：复杂综合性健康问题
- **Agent数量：无限制**（仅限制轮数）
- 支持SSE流式输出

#### 2.3.3 Agent对话模式（Dialogue）
- 用户提问 → 多个Agent轮流讨论 → 多轮交互 → 最终共识
- 适用场景：需要深入讨论的复杂问题
- **Agent数量：无限制**
- **轮数限制：可配置（默认2轮）**

### 2.4 示例问题覆盖

| 示例问题 | 触发Agent |
|----------|-----------|
| 我空腹血糖8.5，餐后14，服用二甲双胍和格列美脲，血糖还是控制不好 | diabetes + medication + nutrition + coach |
| 我父亲脑梗康复出院2周了，左侧肢体偏瘫，说话不清 | rehabilitation + coach + psychology + medication |
| 最近工作压力大，失眠焦虑，血压也不稳定 | psychology + hypertension + coach + nutrition |
| 我妈妈有高血压和糖尿病，饮食上要注意什么？ | nutrition + diabetes + hypertension + general |

## 3. 技术架构

### 3.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Frontend)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Vue 3    │  │Element+ │  │ Pinia    │  │ Vite/ECharts     │  │
│  │ TypeScript│  │ UI      │  │ Store    │  │ 可视化           │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/SSE/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         后端 (Backend)                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Web Framework                   │  │
│  ├─────────────┬─────────────┬─────────────┬─────────────────┤  │
│  │ /api/v1/chat│ /api/v1/    │ /api/v1/    │ /api/v1/        │  │
│  │ 问答模块    │ patients    │ simulation  │ evaluation      │  │
│  │             │ 患者模块    │ 仿真模块    │ 评估模块        │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ AgentExecutor│  │ LLM Client   │  │ KnowledgeBase  │  │  │
│  │  │ Agent执行器  │  │ LLM客户端    │  │ 知识库/RAG     │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────────┘  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ SafetyChecker│  │ Intervention │  │ Workflow       │  │  │
│  │  │ 安全检查     │  │ Simulator    │  │ Orchestrator   │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │  MySQL   │ │  Redis   │ │  Neo4j   │
            │ 数据库   │ │ 缓存     │ │ 知识图谱 │
            └──────────┘ └──────────┘ └──────────┘
                    │
                    ▼
            ┌──────────────────┐
            │     Qdrant       │
            │    向量数据库    │
            └──────────────────┘
```

### 3.2 技术栈

#### 后端
| 组件 | 技术 | 用途 |
|------|------|------|
| Web框架 | FastAPI | REST API + SSE流式响应 |
| ORM | SQLAlchemy | 数据库操作 |
| LLM编排 | LangChain/LangGraph | Agent编排（规划中） |
| LLM客户端 | 自定义 + 多Provider | OpenAI/Anthropic/硅基流动/通义千问/Ollama |
| 数据库 | MySQL 8.0 | 主数据存储 |
| 缓存 | Redis 7.0 | 会话缓存、限流 |
| 知识图谱 | Neo4j 5.x | 医学知识关系存储 |
| 向量检索 | Qdrant | RAG语义检索 |

#### 前端
| 组件 | 技术 | 用途 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | 响应式UI |
| UI库 | Element Plus | 组件库 |
| 状态管理 | Pinia | 状态管理 |
| 构建工具 | Vite | 快速构建 |
| 可视化 | ECharts | 数据图表 |
| 桌面应用 | Tauri | 跨平台桌面 |

### 3.3 核心模块设计

#### 3.3.1 Agent执行引擎 (AgentExecutor)

```python
class AgentExecutor:
    """Agent执行器 - 核心编排引擎"""
    
    async def execute()           # 单Agent执行
    async def execute_with_rag()   # RAG增强执行
    async def multi_agent_consultation()  # 多Agent会诊
    def _select_multiple_agents() # Agent自动选择
    def _call_llm_with_config()    # Per-Agent LLM配置
```

#### 3.3.2 Per-Agent LLM配置

每个Agent可以配置独立的LLM provider和model：

```yaml
# backend/app/agents/definitions/{agent_type}/llm_config.yaml
provider: siliconflow    # 或 openai/anthropic/dashscope/ollama
model: Qwen/Qwen2.5-7B-Instruct
temperature: 0.7
max_tokens: 2000
```

| Agent | 默认Provider | 默认Model |
|-------|-------------|-----------|
| diabetes | openai | gpt-4o |
| hypertension | siliconflow | Qwen/Qwen2.5-7B-Instruct |
| nutrition | siliconflow | Qwen/Qwen2.5-7B-Instruct |
| coach | siliconflow | Qwen/Qwen2.5-7B-Instruct |
| medication | anthropic | claude-3-5-sonnet-latest |
| psychology | anthropic | claude-3-5-sonnet-latest |
| rehabilitation | siliconflow | Qwen/Qwen2.5-7B-Instruct |
| general | siliconflow | Qwen/Qwen.5-7B-Instruct |

#### 3.3.3 质量门控 (Quality Gate)

```
EvidenceCollector → EvidenceQA → AgentSpawner
     ↓                 ↓              ↓
  收集证据         质量评估       触发新Agent
```

#### 3.3.4 工作流编排器 (WorkflowOrchestrator)

支持复杂工作流编排，包括条件分支、并行执行、循环等。

### 3.4 API设计

#### 核心API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/chat/send` | POST | 单Agent问答 |
| `/api/v1/chat/multi-agent` | POST | 多Agent会诊 |
| `/api/v1/chat/agent-dialogue/stream` | GET | Agent对话(SSE流式) |
| `/api/v1/chat/agents` | GET | 获取所有Agent列表 |
| `/api/v1/chat/agent/select` | POST | 智能选择Agent |
| `/api/v1/chat/history/{session_id}` | GET | 获取对话历史 |
| `/api/v1/chat/sessions` | GET | 获取会话列表 |

#### API响应示例 - 多Agent会诊

```json
{
  "session_id": "xxx",
  "query": "用户问题",
  "individual_results": [
    {
      "agent_type": "diabetes",
      "agent_name": "糖尿病专家",
      "response": "...",
      "sources": [...]
    },
    ...
  ],
  "summary": "综合建议"
}
```

### 3.5 数据模型

#### 3.5.1 核心实体

```
Patient (患者)
├── id, name, age, gender
├── diseases[], medications[], allergies[]
└── vital_records[]

ChatSession (会话)
├── id, patient_id, agent_type
├── title, status, message_count
└── created_at, updated_at

ChatMessage (消息)
├── id, session_id, role
├── content, agent_type
├── sources, safety_level
└── created_at
```

#### 3.5.2 知识库实体

```
KnowledgeItem
├── id, title, content
├── type (disease/drug/food/exercise/guideline)
├── tags[], source
└── embedding[]

KnowledgeGraph
├── Disease ←TREATS→ Drug
├── Disease ←COMPLICATES→ Complication
├── Drug ←INTERACTS_WITH→ Drug
└── Food ←HAS_GI→ GI_Value
```

## 4. 安全架构

### 4.1 安全评估体系

1. **输入安全检查** - 敏感词过滤、恶意检测
2. **输出安全检查** - 内容安全审核
3. **医疗红线** - 紧急情况识别、就医提醒
4. **免责声明** - 自动附加健康提示

### 4.2 安全检查流程

```
用户输入 → 敏感词过滤 → 风险评估 → Agent执行 → 输出审核 → 返回结果
     ↓           ↓           ↓
  拦截/警告   等级标识    紧急转介
```

## 5. 部署架构

### 5.1 Docker Compose部署

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [mysql, redis, neo4j, qdrant]
    
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    
  mysql:
  redis:
  neo4j:
  qdrant:
```

### 5.2 环境配置

```env
# LLM配置
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=xxx
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct

# 数据库
MYSQL_HOST=mysql
MYSQL_DATABASE=wellhealth

# 缓存
REDIS_HOST=redis

# 知识图谱
NEO4J_URI=bolt://neo4j:7687

# 向量检索
QDRANT_HOST=qdrant
```

## 6. 项目结构

```
wellhealth/
├── backend/
│   ├── app/
│   │   ├── api/                    # API路由
│   │   │   ├── chat.py             # 问答API
│   │   │   ├── patients.py         # 患者API
│   │   │   ├── simulation.py        # 仿真API
│   │   │   └── ...
│   │   ├── services/               # 业务逻辑
│   │   │   ├── agent_executor.py   # Agent执行器
│   │   │   ├── agent_manager.py    # Agent管理器
│   │   │   ├── llm_client.py       # LLM客户端
│   │   │   ├── knowledge_base.py   # 知识库
│   │   │   ├── safety_checker.py   # 安全检查
│   │   │   └── agents/             # Agent核心模块
│   │   │       ├── core/           # 核心组件
│   │   │       │   ├── agent_definition.py
│   │   │       │   ├── agent_loader.py
│   │   │       │   ├── llm_router.py
│   │   │       │   └── agent_executor.py
│   │   │       ├── orchestrator/   # 编排器
│   │   │       │   ├── workflow_orchestrator.py
│   │   │       │   └── multi_agent_dialogue.py
│   │   │       └── quality/        # 质量门控
│   │   │           └── quality_gate.py
│   │   ├── models/                # 数据模型
│   │   ├── utils/                  # 工具类
│   │   ├── config.py               # 配置
│   │   └── main.py                 # 应用入口
│   └── agents/definitions/          # Agent定义
│       ├── diabetes/
│       │   ├── metadata.yaml
│       │   ├── system_prompt.md
│       │   └── llm_config.yaml
│       ├── hypertension/
│       ├── nutrition/
│       ├── coach/
│       ├── medication/
│       ├── psychology/
│       ├── rehabilitation/
│       └── general/
├── frontend/
│   ├── src/
│   │   ├── views/                  # 页面视图
│   │   │   └── ChatView.vue
│   │   ├── components/             # 组件
│   │   ├── stores/                 # Pinia状态
│   │   │   └── agent.ts
│   │   ├── api/                    # API客户端
│   │   ├── router/                 # 路由
│   │   └── main.ts
│   └── package.json
├── deploy/
│   └── docker-compose.yml
└── docs/                           # 文档
```

## 7. 快速开始

### 7.1 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0
- Redis 7.0
- Docker (可选)

### 7.2 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/your-org/wellhealth.git
cd wellhealth

# 2. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env 配置API密钥

# 3. 启动后端
pip install -r requirements.txt
uvicorn app.main:app --reload

# 4. 启动前端
cd ../frontend
npm install
npm run dev
```

### 7.3 Docker部署

```bash
cd deploy
docker-compose up -d
```

## 8. 路线图

### 已完成 ✅
- [x] 项目框架搭建
- [x] Agent角色库定义 (8个Agent)
- [x] 多Agent协作引擎
- [x] Per-Agent LLM配置
- [x] RAG检索系统
- [x] 安全评估模块
- [x] SSE流式输出

### 进行中 🔄
- [ ] 知识图谱构建
- [ ] 干预效果仿真
- [ ] 管理后台

### 计划中 📋
- [ ] Agent工作流编排器增强
- [ ] 多模态支持（图像识别）
- [ ] 实时健康数据集成
- [ ] Tauri桌面应用

## 9. 许可证

MIT License

## 10. 联系方式

- 项目地址: https://github.com/your-org/wellhealth
- 问题反馈: https://github.com/your-org/wellhealth/issues
