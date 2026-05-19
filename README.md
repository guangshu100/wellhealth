# 康伴 (WellHealth)

> 慢病管理AI平台 - 多Agent协作 + 干预效果仿真 + 医疗级安全评估

## 项目介绍

康伴(WellHealth)是一款专注于慢性病管理的AI平台，通过多Agent协作、干预效果仿真预测、医疗级安全评估等核心技术，为慢病患者提供专业、个性化的健康管理服务。

## 核心特性

- 🤖 **多Agent协作** - 医生、营养师、健康教练Agent协同服务
- 📊 **干预效果仿真** - AI预测不同干预方案的效果
- 🛡️ **医疗级安全评估** - 系统性安全红线+红队测试
- 🔬 **深度慢病专科** - 专注糖尿病、高血压等专病管理

## 技术架构

### 后端
- Python 3.11+
- FastAPI (Web框架)
- LangChain/LangGraph (LLM编排)
- MySQL (主数据库)
- Neo4j (知识图谱)
- Redis (缓存)
- Qdrant (向量检索)

### 前端
- Vue 3 + TypeScript
- Element Plus
- Vite

## 快速开始

### 环境要求

- Python 3.11+
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
# 编辑 .env 配置数据库等信息
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. 前端启动
```bash
cd frontend
npm install
npm run dev
```

4. Docker启动
```bash
cd deploy
docker-compose up -d
```

## 项目结构

```
wellhealth/
├── backend/                 # Python后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── services/       # 业务逻辑
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具类
│   ├── scripts/            # 脚本
│   └── pyproject.toml      # 项目配置
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── views/         # 页面视图
│   │   ├── components/    # 组件
│   │   ├── api/           # API客户端
│   │   └── router/        # 路由配置
│   └── package.json
├── deploy/                 # 部署配置
│   └── docker-compose.yml
└── docs/                   # 项目文档
```

## API文档

启动后端服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 路线图

- [x] 项目框架搭建
- [ ] Agent角色库定义
- [ ] 多Agent协作引擎
- [ ] 知识图谱构建
- [ ] RAG检索系统
- [ ] 安全评估模块
- [ ] 干预效果仿真
- [ ] 管理后台

## 许可证

MIT License
