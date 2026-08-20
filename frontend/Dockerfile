# syntax=docker/dockerfile:1
# ============================================================
# Stage 1: 前端构建
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制依赖清单，利用缓存层
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# 复制源码并构建（TAURI_ENV 不设置，即纯 Web 构建）
COPY . .
RUN npm run build

# ============================================================
# Stage 2: nginx 运行镜像
# ============================================================
FROM nginx:1.27-alpine AS runtime

# 自定义 nginx 配置（含 /api 反向代理到后端）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 1893

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:1893/ || exit 1