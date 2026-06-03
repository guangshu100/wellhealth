# WellHealth Android/iOS App 打包指南

本项目使用 **uni-app + Vue 3** 框架，基于 src/ 标准目录结构开发，**与原 pages/ 外层微信小程序构建并存，互不影响**。

## 一、目录结构

```
miniapp/
├── src/                    # uni-app Vue3 + Vite 标准项目（Android/iOS/小程序）
│   ├── App.vue            # 应用入口
│   ├── main.ts            # 启动文件（含 Pinia）
│   ├── pages.json         # 路由 + tabBar + 全局样式
│   ├── manifest.json      # 应用清单（关键：app-plus Android/iOS 配置）
│   ├── pages/             # 20 个业务页面
│   ├── static/            # 静态资源（图标、样式）
│   ├── stores/            # Pinia 状态管理
│   ├── utils/             # API 工具
│   └── components/        # 公共组件
├── pages/                 # 旧版 uni-app 结构（保留兼容）
├── utils/                 # 旧版工具
├── App.vue                # 旧版入口
├── main.js                # 旧版启动
├── manifest.json          # 旧版清单
├── pages.json             # 旧版路由
├── package.json           # 依赖与脚本
├── vite.config.ts         # Vite 配置
└── project.config.json    # HBuilderX 项目配置
```

## 二、三端构建命令

### 2.1 微信小程序

```bash
cd miniapp
npm install
npm run dev:mp-weixin       # 开发（微信开发者工具打开 dist/dev/mp-weixin/）
npm run build:mp-weixin     # 生产构建（输出 dist/build/mp-weixin/）
```

> 使用外层 `pages/` + `manifest.json`（旧版）打包微信小程序，**默认 AppID 为 wx...f8d**

### 2.2 Android App（云打包）

> 强烈推荐使用 HBuilderX 进行云打包，避免本地 Android SDK 配置

#### 步骤 1：使用 HBuilderX 打开本项目
1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（标准版即可）
2. 文件 → 打开目录 → 选择 `miniapp/`
3. 顶部菜单：**发行 → 原生 App-云打包**

#### 步骤 2：配置 Android 证书
- 第一次打包：HBuilderX 会引导生成自有证书（免费、自动）
- 正式发布：建议使用自有证书（在 DCloud 证书管理中上传 `.keystore` 文件）

#### 步骤 3：选择 manifest.json 中的 app-plus 配置
- 应用名称：康伴健康
- 包名：`com.wellhealth.client`（在 src/manifest.json `app-plus` 中可调整）
- 版本号：1.0.0 (versionCode: 100)
- 最低支持：Android 7.0 (API 24)
- ABI 架构：armeabi-v7a / arm64-v8a / x86 / x86_64（全平台）

#### 步骤 4：云打包
- 等待 3-5 分钟，生成 `app-debug.apk` 或 `app-release.apk`
- 包体积约 10-20 MB
- 直接下载到本地进行真机测试或上架

#### CLI 方式（命令行）
```bash
# 需先安装 @dcloudio/uni-cli-i18n
npm install -g @dcloudio/uni-cli

# 同步 src 目录到 HBuilderX 工程结构（仅首次需要）
# 然后在 HBuilderX 中执行云打包
```

> 注意：CLI 方式打 Android 包需要本地配置 Android SDK 完整环境，**推荐使用 HBuilderX 云打包**。

### 2.3 iOS App（仅 macOS）

```bash
# 1. 在 macOS 上安装 Xcode
# 2. 用 HBuilderX 打开本项目
# 3. 顶部菜单：发行 → 原生 App-云打包 → iOS

# 需要 Apple Developer 账号（$99/年）
# 步骤：
#  - 在 manifest.json 中配置 bundleId（com.wellhealth.client）
#  - 在 App Store Connect 创建应用
#  - 在 HBuilderX 中输入 Apple ID 登录
#  - 选择描述文件（Provisioning Profile）
#  - 云打包生成 ipa 文件
#  - 使用 Xcode → Window → Organizer → Distribute App 上传至 App Store
```

### 2.4 H5（移动 Web）

```bash
npm run dev:h5          # 开发服务器
npm run build:h5        # 生产构建（输出 dist/build/h5/）
```

## 三、与原项目的隔离设计

### 3.1 不影响 Web 端部署
- Web 端（`frontend/`）使用 Vue3 + Vite + Element Plus，**与 miniapp 完全独立**
- Web 端构建：`cd frontend && npm run build`，输出 `frontend/dist/`
- 部署方式不变（可继续走 Tauri 桌面打包或 Nginx 静态托管）

### 3.2 不影响 Tauri 桌面端
- Tauri 工程位于 `frontend/src-tauri/`
- Tauri 构建：`cd frontend && npm run tauri:build`
- **与 miniapp 互不影响**，可独立发布

### 3.3 小程序端两套结构共存
- **外层 `pages/` + `App.vue` + `manifest.json`**：传统 uni-app 结构，**专门用于微信小程序打包**（`mp-weixin` 平台）
- **src/ + App.vue + manifest.json**：标准 uni-app Vue3 结构，**用于 Android/iOS App 打包**（`app-android` / `app-ios` 平台）
- HBuilderX 会根据 `manifest.json` 所在位置自动识别项目结构

## 四、Android 关键配置说明（src/manifest.json）

### 4.1 包名与版本
```json
{
  "name": "wellhealth",
  "appid": "__UNI__6C9CD3A",     // uni-app 应用标识（不可改）
  "versionName": "1.0.0",
  "versionCode": "100"             // 必须递增，用于应用市场更新
}
```

### 4.2 Android 权限
在 `app-plus.distribute.android.permissions` 中声明，包含：
- `INTERNET` - 网络请求
- `CAMERA` - 拍照识别食材
- `BLUETOOTH` - 连接健康设备
- `SCHEDULE_EXACT_ALARM` - 定时用药提醒
- `POST_NOTIFICATIONS` - 推送通知（Android 13+）

### 4.3 Android 最低版本
- `minSdkVersion`: 24 (Android 7.0)
- `targetSdkVersion`: 33 (Android 13)
- 支持 ABI：armeabi-v7a / arm64-v8a / x86 / x86_64

### 4.4 iOS 隐私描述
在 `app-plus.distribute.ios.privacyDescription` 中声明所有需要用户授权的隐私用途：
- 相机、相册、麦克风、位置、健康数据、蓝牙、通知、日历、通讯录

## 五、发布到应用市场

### 5.1 上架 Google Play（海外）

```bash
# 1. 注册 Google Play Developer 账号（一次性 $25）
# 2. 在 HBuilderX 中选择「Android → 制作 App Bundle」
# 3. 产出 .aab 文件
# 4. 在 Google Play Console 上传 .aab
# 5. 填写应用信息、隐私政策、截图
# 6. 提交审核（通常 1-3 天）
```

### 5.2 上架国内安卓市场

```bash
# 1. 产出 .apk 文件
# 2. 注册各市场开发者账号：
#    - 应用宝（腾讯）
#    - 华为应用市场
#    - 小米应用商店
#    - OPPO 软件商店
#    - VIVO 应用商店
#    - 阿里应用分发平台
# 3. 上传 .apk，提交审核
```

### 5.3 上架 App Store（iOS）

```bash
# 1. 注册 Apple Developer Program（$99/年）
# 2. 在 App Store Connect 创建应用
# 3. 在 HBuilderX 中选择「iOS → 制作 ipa」
# 4. 使用 Xcode 打开并通过 Organizer 上传
# 5. 等待审核（通常 1-3 天）
```

## 六、调试与日志

### 6.1 真机调试
```bash
# Android 真机：
# 1. 打开手机 USB 调试
# 2. 连接电脑
# 3. HBuilderX → 运行 → 运行到手机或模拟器

# iOS 真机（仅 macOS）：
# 1. 安装 iTunes，确保手机已连接
# 2. HBuilderX → 运行 → 运行到 iOS App 基座
```

### 6.2 查看日志
```bash
# HBuilderX 控制台会自动显示 console.log 输出
# 也可使用 adb logcat（Android）：
adb logcat | grep -i "wellhealth"
```

## 七、常见问题

### Q1：HBuilderX 打开项目看不到 src/ 目录？
A：HBuilderX 标准版默认识别根目录的 `manifest.json`。本项目根目录与 src/ 目录都有 manifest.json，HBuilderX 会优先识别根目录的。如需切换到 src/，可在 HBuilderX 中：
- 菜单 → 发行 → 原生 App-云打包（自动使用 src/manifest.json）

### Q2：本地 npm run build:app-android 报错？
A：CLI 方式打 Android 包需要完整 Android SDK 环境（SDK、NDK、Gradle）。**推荐使用 HBuilderX 云打包**，无需本地配置。

### Q3：Android 包名 com.wellhealth.client 与 Tauri 桌面端冲突？
A：不冲突。Android 包名是 Java 命名空间，Tauri 桌面端是 Rust crate 名称，两者运行在完全独立的设备上。Android 与微信小程序的 `__UNI__6C9CD3A` 也不冲突。

### Q4：后端 API 地址 localhost 在手机上无法访问？
A：手机访问后端需要将 API 地址改为后端实际 IP（如 `http://192.168.1.100:8000`）。在 `src/utils/api.ts` 中修改 `BASE_URL`，或使用运行时配置：

```typescript
// src/utils/config.ts
export const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://192.168.1.100:8000/api/v1'  // 开发时使用局域网 IP
  : 'https://api.wellhealth.com/api/v1'   // 生产环境
```

### Q5：如何同时开发微信小程序和 Android App？
A：互不影响。使用 HBuilderX 切换项目即可：
- 项目根目录（外层）→ 微信小程序
- src/ 目录 → Android/iOS App

## 八、版本与更新

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0.0 | 2025-12-10 | 初始版本，20 个核心页面、Android/iOS 打包配置 |

## 九、相关链接

- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [HBuilderX 下载](https://www.dcloud.io/hbuilderx.html)
- [DCloud 开发者中心](https://dev.dcloud.net.cn/)
- [WellHealth 后端 API 文档](http://localhost:8000/docs)
