# 康伴健康项目 - 配色规范 V3

## 一、配色理念

**设计师视角：配色的决策逻辑**
- 先定"基调"，而非先选"主色"
- 用"功能"倒推"颜色"
- 建立"色彩层级"，而非颜色堆砌
- 让"无障碍"成为默认

**用户视角：什么颜色"看着舒服、顺眼"**
- 不刺眼 - 没有纯黑、纯白、高饱和蓝紫
- 不"AI感" - 避开科技蓝紫+大面积玻璃拟态
- 不疲劳 - 界面像"休息"而不像"工作"
- 正向暗示 - 绿色、暖米色让人放松

## 二、基础色板

### 颜色参数表

| 颜色名称 | 十六进制色值 | RGB 数值 | 用途 | 设计说明 |
|----------|--------------|----------|------|----------|
| 主色-鼠尾草绿 | `#5E8B5A` | R:94, G:139, B:90 | 按钮、标题、功能强调区 | 沉稳且带有生命力，对比度达标 |
| 主色浅色 | `#7CA878` | R:124, G:168, B:120 | 悬停状态、浅色背景 | - |
| 主色深色 | `#4C7048` | R:76, G:112, B:72 | 点击状态、深色背景 | - |
| 辅助色-亚麻色 | `#DDCFB0` | R:221, G:207, B:176 | 次要按钮、标签、分割线 | 不争抢主色，但能构建层次 |
| 强调色-暖金色 | `#E7B83E` | R:231, G:184, B:62 | 进度、成就，正向反馈 | 传递"鼓励"而非"警告" |
| 警示色-陶土橙 | `#CD8B5B` | R:205, G:139, B:91 | 注意、边界值提醒 | 比红色更温和，仍能引起注意 |
| 背景基底 | `#FCF8F0` | R:252, G:248, B:240 | 全局背景 | 模拟天然纸张，比纯白降低30%蓝光刺激 |
| 卡片/面板 | `#FFFFFF` | R:255, G:255, B:255 | 卡片、弹窗、表单区域 | 略带暖感的白 |
| 正文文字 | `#2F2E2A` | R:47, G:46, B:42 | 标题，正文 | 极深灰褐，比纯黑柔和 |
| 辅助文字 | `#7F7D74` | R:127, G:125, B:116 | 说明、占位符、时间戳 | 暖灰，清晰但不抢眼 |

## 三、统一主题配置

### 配置文件位置

```
wellhealth/
├── config/
│   ├── theme.js          # 统一主题配置 (新增)
│   └── colors.js        # 颜色常量
├── frontend/
│   └── src/assets/styles/
│       └── main.scss     # Web 主题变量
├── miniapp/
│   └── uni.scss         # 小程序主题变量
└── docs/
    └── COLOR_SPEC.md    # 本文档
```

### 主题配置结构 (config/theme.js)

```javascript
themes = {
  sagegreen: {           // 当前使用
    name: '鼠尾草绿',
    colors: {
      primary: '#5E8B5A',
      primaryLight: '#7CA878',
      primaryDark: '#4C7048',
      bgPage: '#FCF8F0',
      bgCard: '#FFFFFF',
      // ... 更多颜色
    },
    elementPlus: {       // Web 专用
      '--el-color-primary': '#5E8B5A',
      // ...
    },
    uniApp: {           // 小程序专用
      '$uni-color-primary': '#5E8B5A',
      // ...
    },
  },
  // 可扩展更多主题...
}
```

## 四、应用场景

### Web前端 (Vue3 + Element Plus)
- 全局样式: `src/assets/styles/main.scss`
- 登录页: `src/views/LoginView.vue`
- 注册页: `src/views/RegisterView.vue`
- 找回密码: `src/views/ResetPasswordView.vue`
- 首页: `src/views/HomeView.vue`
- AI聊天: `src/views/ChatView.vue`

### 小程序端 (UniApp)
- 全局配置: `pages.json`
- 登录页: `pages/login/login.vue`
- 注册页: `pages/register/register.vue`
- 找回密码: `pages/reset-password/reset-password.vue`

## 五、配色层级

- **基底色**（70%）：`#FCF8F0` 全局背景
- **主色**（20%）：`#5E8B5A` 关键操作
- **辅色**（8%）：`#DDCFB0` 区分不同模块
- **点缀色**（2%）：`#E7B83E` 提醒、激励

## 六、避坑指南

1. **渐变**：仅允许同色系极微渐变，禁止高对比跨色相渐变
2. **阴影**：统一用 `rgba(60, 55, 45, 0.06)` 到 `0.12`
3. **文字**：正文用 `#2F2E2A`，绝不用纯黑
4. **老年适配**：按钮底色用主色，文字用白色

## 七、渐变与阴影规则

- **渐变示例**: `linear-gradient(135deg, #5E8B5A, #7CA878)`
- **阴影示例**: `box-shadow: 0 2px 8px rgba(60, 55, 45, 0.08)`

## 八、一键换肤实现

### 方式一：命令行换肤（推荐，完整生效）

```bash
# 进入项目根目录
cd wellhealth

# 切换到鼠尾草绿主题
node scripts/build-theme.js sagegreen

# 切换到柔雾蓝主题
node scripts/build-theme.js mistblue

# 构建所有主题
node scripts/build-theme.js --all
```

**注意**：命令行换肤后需要重新编译：
- Web: `cd frontend && npm run build`
- 小程序: 在 HBuilderX 中重新编译

### 方式二：网页点击换肤（部分生效）

Web 端点击"切换主题"按钮后，会：
1. 设置 CSS 变量（影响使用 var() 的样式）
2. 尝试替换页面中硬编码的颜色（部分生效）

**限制**：组件中硬编码的颜色可能不会完全替换，需要重新编译才能完全生效。

### 方式三：小程序端

小程序端 SCSS 变量在编译时确定，运行时无法动态切换。选择主题后会提示需要在开发工具中重新编译。

### 主题配置原理

1. **静态文件替换**：运行 `build-theme.js` 会修改：
   - `frontend/src/assets/styles/theme.scss`
   - `miniapp/uni-theme.scss`

2. **运行时切换**：点击按钮只能修改 CSS 变量，无法改变编译后的样式

## 九、主题列表

| 主题ID | 名称 | 状态 |
|--------|------|------|
| sagegreen | 鼠尾草绿 | ✅ 当前使用 |
| mistblue | 柔雾蓝 | 🔸 备选 |
| cypress | 浅杉绿 | 🔸 备选 |

## 十、扩展新主题

在 `config/theme.js` 中添加新主题：

```javascript
themes.newtheme: {
  name: '新主题名',
  id: 'newtheme',
  colors: {
    primary: '#xxxxxx',
    // ... 其他颜色
  },
  elementPlus: {
    '--el-color-primary': '#xxxxxx',
    // ... Element Plus 变量
  },
  uniApp: {
    '$uni-color-primary': '#xxxxxx',
    // ... UniApp 变量
  },
}
```
