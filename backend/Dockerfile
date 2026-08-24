# syntax=docker/dockerfile:1

# ============================================================
# Stage 1: 依赖构建
# ============================================================
FROM python:3.11-slim AS builder

ENV POETRY_VERSION=2.4.1 \
    POETRY_NO_INTERACTION=1

WORKDIR /build

# 安装编译工具，创建 venv，安装 poetry 及 export 插件
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir "poetry==${POETRY_VERSION}" poetry-plugin-export \
    && rm -rf /var/lib/apt/lists/*

# 只复制依赖声明，利用缓存
COPY pyproject.toml poetry.lock ./

# 导出 requirements 并安装，失败时构建停止
RUN /opt/venv/bin/poetry export -f requirements.txt --without dev --no-ansi -o /tmp/requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================================
# Stage 2: 运行镜像
# ============================================================
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 复制已安装依赖的虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY . .

EXPOSE 18100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18100/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18100"]