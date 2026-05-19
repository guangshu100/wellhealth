# AGENTS.md

> **WellHealth 慢病管理AI平台 - AI Agent 操作手册**
> 
> 本文件是项目给 AI 的专属操作手册，与 README.md 分工（README 给人看，AGENTS.md 给 AI 看）。
> 
> 兼容：Cursor、Claude Code、GitHub Copilot、Aider、Gemini CLI、Windsurf 等。

---

## 项目概览

### 技术栈
| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | FastAPI + SQLAlchemy + Python | 3.11+ |
| **小程序** | uni-app + Vue 3 + TypeScript | - |
| **桌面端** | Vue 3 + Tauri + Element Plus | - |
| **数据库** | MySQL + Redis + Neo4j + Qdrant | 8.0 / 7.0 / 5.x |
| **AI** | Multi-Agent + LLM + RAG | - |

### 目录结构
```
wellhealth/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── api/               # API 路由（主要工作区）
│   │   ├── services/          # 业务逻辑
│   │   ├── models/            # 数据模型
│   │   └── utils/             # 工具类
│   ├── tests/                 # 测试文件
│   └── .env                   # 环境配置（禁止修改）
│
├── miniapp/                    # 小程序前端
│   ├── pages/                 # 页面（主要工作区）
│   │   ├── chat/             # AI 咨询页面
│   │   ├── health/           # 健康档案
│   │   └── ...
│   ├── utils/                 # 工具类
│   │   ├── api.ts            # API 封装（重要）
│   │   └── theme.js          # 主题配置
│   ├── static/               # 静态资源
│   │   └── styles/           # 样式文件
│   └── pages.json            # 页面配置（谨慎修改）
│
├── frontend/                   # 桌面端（Vue 3 + Tauri）
│   └── src/
│
└── constraints/                # 约束规则库
    ├── coding-constraints.md   # 编码规范
    └── security-constraints.md # 安全规范
```

### 入口文件
- **后端入口**: `backend/app/main.py`
- **小程序入口**: `miniapp/App.vue`
- **API 封装**: `miniapp/utils/api.ts`

---

## 安装与构建

### 后端
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 开发启动（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 访问 API 文档
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### 小程序
```bash
# 进入小程序目录
cd miniapp

# 使用 HBuilderX 或微信开发者工具打开项目
# 开发调试：在微信开发者工具中导入项目

# 编译到微信小程序
# 使用 HBuilderX: 发行 -> 小程序-微信
```

### 桌面端
```bash
# 进入桌面端目录
cd frontend

# 安装依赖
npm install

# 开发启动
npm run tauri:dev

# 生产构建
npm run tauri:build
```

---

## 测试指令

### 后端测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_chat.py -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html

# 覆盖率要求：≥ 80%
```

### 代码检查
```bash
# Python Lint（使用 ruff）
ruff check backend/app/

# Python 格式化
black backend/app/
isort backend/app/

# TypeScript 类型检查
cd frontend && npm run typecheck

# ESLint
cd frontend && npm run lint
```

---

## 代码风格

### Python 后端规范

#### 命名规范
```python
# ✅ 正确
class PatientService:           # 类名：大驼峰
    def get_patient_by_id():    # 函数名：小写下划线
        patient_id = "xxx"      # 变量名：小写下划线
        MAX_RETRY = 3           # 常量：大写下划线

# ❌ 错误
class patientService:           # 类名不能用小驼峰
    def GetPatientById():       # 函数名不能用大驼峰
```

#### API 路由规范
```python
# ✅ 正确
from fastapi import APIRouter

router = APIRouter()

@router.get("/sessions")                    # 列表查询
async def list_sessions(): ...

@router.post("/session/create")             # 创建操作
async def create_session(): ...

@router.put("/session/{session_id}")        # 更新操作
async def update_session(session_id: str): ...

@router.delete("/session/{session_id}")     # 删除操作
async def delete_session(session_id: str): ...
```

#### 响应格式规范
```python
# ✅ 正确 - 成功响应
return {
    "sessions": sessions,
    "count": len(sessions)
}

# ✅ 正确 - 错误响应
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="会话不存在"
)
```

#### 数据库操作规范
```python
# ✅ 正确 - 使用上下文管理器
from app.utils.database import get_db_session

with get_db_session() as db:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    db.commit()

# ✅ 正确 - FastAPI 依赖注入
from app.utils.database import get_db

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Patient).filter(Patient.id == patient_id).first()
```

#### 类型注解规范
```python
# ✅ 正确
from typing import Optional, List

def get_patients(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
) -> List[Patient]:
    ...
```

### TypeScript 小程序规范

#### 命名规范
```typescript
// ✅ 正确
interface ChatSession {          // 接口名：大驼峰
  id: string
  title: string
}

const sessionId = ref('')        // 变量名：小驼峰
const loadSessions = async () => {}  // 函数名：小驼峰
```

#### API 调用规范
```typescript
// ✅ 正确 - 统一在 utils/api.ts 中封装
// utils/api.ts
export const chatApi = {
  getSessions: (patientId?: string, limit?: number) => request<{
    sessions: Array<ChatSession>
  }>({
    url: '/chat/sessions',
    method: 'GET',
    data: { patient_id: patientId, limit }
  })
}

// 页面中使用
import { chatApi } from '@/utils/api'
const res = await chatApi.getSessions()

// ❌ 错误 - 直接在页面中调用
const res = await uni.request({
  url: 'http://localhost:8000/api/v1/chat/sessions'
})
```

#### 错误处理规范
```typescript
// ✅ 正确
try {
  const res = await chatApi.getSessions()
  sessionList.value = res.sessions
} catch (e) {
  console.error('Load sessions failed:', e)
  uni.showToast({ title: '加载失败', icon: 'none' })
}
```

#### 组件规范
```vue
<!-- ✅ 正确 -->
<template>
  <view class="page">
    <!-- 模板内容 -->
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 响应式数据
const loading = ref(false)

// 方法
const loadData = async () => {
  loading.value = true
  // ...
  loading.value = false
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page {
  /* 样式 */
}
</style>
```

---

## 前端主题与布局规范

### 主题系统

项目支持**运行时主题切换**，当前支持 3 种主题：

| 主题 ID | 名称 | 主色调 | 适用场景 |
|---------|------|--------|---------|
| `sagegreen` | 鼠尾草绿 | #5E8B5A | 默认主题，健康自然 |
| `mistblue` | 柔雾蓝 | #7BA7B9 | 专业医疗 |
| `cypress` | 浅杉绿 | #5A9E87 | 清新活力 |

### 配色规范

#### CSS 变量体系
```scss
/* 必须使用 CSS 变量，禁止硬编码颜色 */
page {
  /* 主色系 */
  --color-primary: #5E8B5A;           /* 主色 */
  --color-primary-light: #7CA878;     /* 主色浅 */
  --color-primary-dark: #4C7048;      /* 主色深 */
  
  /* 背景色 */
  --color-bg-page: #FCF8F0;           /* 页面背景 */
  --color-bg-card: #FFFFFF;           /* 卡片背景 */
  --color-bg-card-light: #FCF8F0;     /* 卡片背景浅 */
  --color-bg-hover: #E8F0E6;          /* 悬停背景 */
  
  /* 文字色 */
  --color-text-primary: #2F2E2A;      /* 主要文字 */
  --color-text-secondary: #7F7D74;    /* 次要文字 */
  --color-text-placeholder: #A5A49C;  /* 占位文字 */
  --color-text-inverse: #FFFFFF;      /* 反色文字 */
  
  /* 边框色 */
  --color-border: #DDCFB0;            /* 边框 */
  --color-border-light: #E8DFD0;      /* 边框浅 */
  
  /* 状态色 */
  --color-success: #5E8B5A;           /* 成功 */
  --color-warning: #E7B83E;           /* 警告 */
  --color-danger: #CD8B5B;            /* 危险 */
  --color-error: #CD8B5B;             /* 错误 */
}
```

#### 使用规范
```scss
// ✅ 正确 - 使用 CSS 变量
.button {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.card {
  background: var(--color-bg-card);
  border: 1rpx solid var(--color-border);
}

// ❌ 错误 - 硬编码颜色
.button {
  background: #5E8B5A;  // 禁止硬编码
}
```

### 布局规范

#### 页面结构
```vue
<!-- 标准页面结构 -->
<template>
  <view class="page">
    <!-- 页面头部（可选） -->
    <view class="page-header">
      <!-- 头部内容 -->
    </view>
    
    <!-- 页面内容 -->
    <view class="page-content">
      <!-- 主要内容 -->
    </view>
    
    <!-- 页面底部（可选） -->
    <view class="page-footer">
      <!-- 底部内容 -->
    </view>
  </view>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-bg-page);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-primary);
  padding: 24rpx 30rpx;
}

.page-content {
  flex: 1;
  padding: 30rpx;
}

.page-footer {
  position: sticky;
  bottom: 0;
  background: var(--color-bg-card);
  border-top: 1rpx solid var(--color-border-light);
}
</style>
```

#### 卡片规范
```vue
<!-- 标准卡片 -->
<view class="card">
  <view class="card-header">
    <text class="card-title">标题</text>
  </view>
  <view class="card-body">
    <!-- 内容 -->
  </view>
  <view class="card-footer">
    <!-- 底部操作 -->
  </view>
</view>

<style scoped>
.card {
  background: var(--color-bg-card);
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.card-header {
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.card-body {
  color: var(--color-text-secondary);
}

.card-footer {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid var(--color-border-light);
}
</style>
```

#### 按钮规范
```vue
<!-- 主要按钮 -->
<button class="btn-primary">主要操作</button>

<!-- 次要按钮 -->
<button class="btn-secondary">次要操作</button>

<!-- 文字按钮 -->
<button class="btn-text">文字按钮</button>

<style scoped>
.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 16rpx;
  padding: 24rpx 48rpx;
}

.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-primary);
  border: 1rpx solid var(--color-primary);
  border-radius: 16rpx;
}

.btn-text {
  background: transparent;
  color: var(--color-primary);
}
</style>
```

### 间距规范
```scss
// 标准间距（使用 30rpx 为基础单位）
$spacing-xs: 10rpx;    // 极小间距
$spacing-sm: 20rpx;    // 小间距
$spacing-md: 30rpx;    // 中等间距（默认）
$spacing-lg: 40rpx;    // 大间距
$spacing-xl: 60rpx;    // 极大间距

// 页面内边距
padding: 30rpx;

// 卡片间距
margin-bottom: 30rpx;

// 元素间距
gap: 20rpx;
```

### 字体规范
```scss
// 字体大小
$font-size-xs: 22rpx;    // 极小
$font-size-sm: 24rpx;    // 小
$font-size-md: 28rpx;    // 中等（默认）
$font-size-lg: 32rpx;    // 大
$font-size-xl: 36rpx;    // 极大

// 行高
$line-height: 1.5;
```

---

## 架构约束

### API 约束
- **路由前缀**: 所有 API 必须以 `/api/v1` 为前缀
- **认证要求**: 所有 API 必须有 JWT 认证（除登录注册）
- **响应格式**: 统一使用 JSON 格式

### 分层约束
```
API 层 (app/api/)
    ↓ 只能调用
Service 层 (app/services/)
    ↓ 只能调用
Model 层 (app/models/)
    ↓ 只能调用
Utils 层 (app/utils/)
```

### 禁止跨层调用
```python
# ❌ 错误 - API 直接操作数据库
@router.get("/patients")
async def list_patients():
    return db.query(Patient).all()  # 应该调用 Service

# ✅ 正确 - API 调用 Service
@router.get("/patients")
async def list_patients():
    return await patient_service.list_patients()
```

### 依赖方向
```
frontend → api → services → models → utils
```

---

## 安全规则

### 认证与授权
- **JWT 认证**: 所有 API（除登录注册）必须有 JWT 认证
- **权限检查**: 敏感操作必须检查用户权限
- **数据归属**: 患者只能访问自己的数据

### 数据安全
- **敏感字段**: 密码、身份证、手机号必须加密/脱敏
- **SQL 注入**: 禁止 SQL 拼接，必须使用 ORM 或参数化查询
- **XSS 防护**: 使用 `rich-text` 渲染，禁止 `v-html`

### 医疗安全
- **安全检查**: 所有 AI 生成的医疗建议必须经过安全检查
- **免责声明**: 所有医疗建议必须包含免责声明
- **禁止事项**: 
  - ❌ 具体用药剂量
  - ❌ 诊断结论
  - ❌ 替代医生治疗

### 敏感文件（禁止修改）
```
.env
.env.*
backend/app/config.py
backend/app/main.py
miniapp/manifest.json
miniapp/pages.json
secrets/
*.pem
*.key
```

---

## 协作流程

### 标准开发流程
```
1. 需求输入
    ↓
2. 分析需求 → 理解业务场景，识别技术要点
    ↓
3. 设计方案 → 输出技术设计（可选：人工审核）
    ↓
4. 生成代码 → 遵循约束，生成代码
    ↓
5. 自动验证 → 运行测试、Lint、格式化
    ↓
6. 反馈修正 → 如果验证失败，自动修正并重试（最多 3 次）
    ↓
7. 人工审核 → 关键功能需要人工确认
    ↓
8. 完成交付 → 输出变更报告
```

### 人机协作节点
以下情况**必须暂停，等待人工确认**：
- 🔴 涉及数据库 schema 变更
- 🔴 涉及安全认证逻辑修改
- 🔴 涉及医疗建议生成逻辑
- 🔴 涉及 .env 或配置文件修改
- 🔴 删除文件或大量代码重构

---

## 禁止操作

### 绝对禁止
- 🚫 修改 `.env` 文件
- 🚫 修改 `backend/app/config.py`
- 🚫 修改 `backend/app/main.py`（路由注册除外）
- 🚫 硬编码敏感信息（密码、密钥等）
- 🚫 使用 `eval()`、`exec()`
- 🚫 直接拼接 SQL
- 🚫 绕过安全检查直接输出医疗建议

### 需要确认
- ⚠️ 新增依赖
- ⚠️ 修改数据库 schema
- ⚠️ 删除文件
- ⚠️ 大量代码重构

---

## 工具权限

### 允许的操作
- ✅ 在 `backend/app/api/` 下新增/修改 API
- ✅ 在 `backend/app/services/` 下新增/修改服务
- ✅ 在 `miniapp/pages/` 下新增/修改页面
- ✅ 在 `miniapp/utils/` 下新增/修改工具
- ✅ 编写/修改测试文件
- ✅ 更新文档

### 禁止的操作
- ❌ 修改敏感文件（见安全规则）
- ❌ 删除现有文件（需人工确认）
- ❌ 绕过安全检查

---

## 质量门禁

代码提交前，AI Agent 必须自检：

- [ ] 命名符合规范
- [ ] 有类型注解（TypeScript/Python）
- [ ] 有文档字符串（关键函数）
- [ ] 有错误处理
- [ ] 没有硬编码颜色（使用 CSS 变量）
- [ ] 没有安全风险
- [ ] 文件大小合理（≤ 500 行）
- [ ] 测试覆盖率 ≥ 80%

---

## 快速参考

### 常用命令
```bash
# 后端开发
cd backend && uvicorn app.main:app --reload

# 运行测试
pytest tests/ -v

# 代码格式化
black backend/app/ && isort backend/app/

# Lint 检查
ruff check backend/app/
```

### 关键文件路径
- API 路由：`backend/app/api/`
- 业务服务：`backend/app/services/`
- 小程序页面：`miniapp/pages/`
- API 封装：`miniapp/utils/api.ts`
- 主题配置：`miniapp/utils/theme.js`
- 全局样式：`miniapp/static/styles/index.scss`

### API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 示例场景

### 场景 1：新增 API 接口
**输入**：
```
为 AI 咨询添加消息撤回功能
```

**执行**：
1. 分析需求 → 需要后端 API + 前端按钮
2. 检查约束 → API 需要 JWT 认证，需要软删除
3. 生成代码 → 
   - `backend/app/api/chat.py` 新增 `delete_message`
   - `miniapp/pages/chat/chat.vue` 新增撤回按钮
   - `miniapp/utils/api.ts` 新增 API 调用
4. 生成测试 → `tests/test_chat.py`
5. 运行验证 → 测试通过
6. 输出报告 → 变更文件 + 测试结果

### 场景 2：修复 Bug
**输入**：
```
会话历史在页面刷新后丢失
```

**执行**：
1. 定位问题 → `onShow` 没有恢复当前会话
2. 分析原因 → `sessionId` 被清空，没有从 storage 恢复
3. 修复代码 → 在 `onShow` 中恢复 `current_session_id`
4. 验证修复 → 测试刷新场景
5. 输出报告 → 问题原因 + 修复方案

---

**记住**：你的目标不是"完成任务"，而是"安全、高质量地完成任务"。
