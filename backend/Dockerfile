# syntax=docker/dockerfile:1
# ============================================================
# Stage 1: 依赖构建
# ============================================================
FROM python:3.11-slim AS builder

ENV POETRY_HOME=/opt/poetry \
    POETRY_VERSION=2.4.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

WORKDIR /build

# 安装 curl 与编译工具（部分依赖需编译），再安装 poetry，最后清理
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# 只复制依赖声明文件，利用 Docker 层缓存
COPY pyproject.toml poetry.lock ./

# 依据 poetry.lock 安装主依赖到全局 site-packages（规避 poetry export 的插件依赖）
RUN poetry install --no-root --without dev --no-ansi

# ============================================================
# Stage 2: 运行镜像
# ============================================================
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 复制 Stage 1 安装好的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18100/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18100"]