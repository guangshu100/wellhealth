# Tauri 桌面端打包指南

## 项目结构

```
frontend/
├── src-tauri/                    # Tauri Rust 后端
│   ├── Cargo.toml               # Rust 依赖配置
│   ├── tauri.conf.json          # Tauri 配置
│   ├── build.rs                 # 构建脚本
│   ├── src/
│   │   ├── main.rs             # 入口文件
│   │   └── lib.rs              # 库文件
│   └── icons/                   # 应用图标
├── src/
│   └── config/
│       └── app.ts              # API 配置（自动检测 Tauri 环境）
├── app-icon.svg                 # 源图标
└── package.json                # 添加了 Tauri 脚本
```

## 快速开始

### 1. 开发模式

```bash
cd frontend

# 开发 Web 版本
npm run dev

# 开发桌面版本（自动打开桌面窗口）
npm run tauri:dev
```

### 2. 构建发布版本

```bash
cd frontend

# 构建 Web 版本
npm run build
# 输出: dist/

# 构建桌面版本
npm run tauri:build
# 输出: src-tauri/target/release/bundle/
```

### 3. 构建输出

| 平台 | 输出位置 | 文件类型 |
|------|---------|---------|
| Windows | `src-tauri/target/release/bundle/nsis/` | `.exe` / `.msi` |
| macOS | `src-tauri/target/release/bundle/app/` | `.app` / `.dmg` |
| Linux | `src-tauri/target/release/bundle/deb/` | `.deb` / `.AppImage` |

## 命令说明

```bash
npm run dev           # Web 开发服务器
npm run build         # Web 生产构建
npm run preview        # 预览 Web 构建
npm run tauri          # Tauri CLI
npm run tauri:dev     # 启动桌面开发模式
npm run tauri:build   # 构建桌面安装包
npm run tauri:build:debug  # Debug 构建
```

## API 配置

Tauri 桌面版会自动连接本地后端服务：

```typescript
// src/config/app.ts
const isTauri = typeof window !== 'undefined' && '__TAURI__' in window

export const API_BASE_URL = isTauri 
  ? 'http://localhost:8000'  // 桌面版
  : import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'  // Web版
```

## 后端服务

桌面版需要 FastAPI 后端服务在后台运行：

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 配置修改

### 修改窗口大小

编辑 `src-tauri/tauri.conf.json`：

```json
{
  "app": {
    "windows": [{
      "title": "康伴健康",
      "width": 1200,
      "height": 800,
      "minWidth": 900,
      "minHeight": 600
    }]
  }
}
```

### 修改应用信息

```json
{
  "productName": "康伴健康",
  "version": "1.0.0",
  "identifier": "com.wellhealth.app"
}
```

### 修改图标

1. 修改 `app-icon.svg`
2. 重新生成图标：

```bash
cd frontend
npx tauri icon app-icon.svg -o src-tauri/icons
```

## 部署后端

桌面版安装后，需要配置后端 API 地址：

1. 部署 FastAPI 后端到云服务器
2. 修改桌面客户端的 API 地址（或添加配置界面）

## 常见问题

### Q: 编译报错 "unknown field `devtools`"
A: 确保 `tauri.conf.json` 中的 `devtools` 字段已删除（仅在 CLI 2.x 中支持）

### Q: Windows 找不到 WebView2
A: Tauri 会自动下载 WebView2Bootstrapper，如需手动安装：
- 下载地址：https://developer.microsoft.com/en-us/microsoft-edge/webview2/

### Q: 桌面版无法访问 API
A: 检查：
1. 后端服务是否在 localhost:8000 运行
2. 防火墙是否允许该端口
3. API 地址配置是否正确
