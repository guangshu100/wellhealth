#!/usr/bin/env bash
# ============================================================
# WellHealth 一键后台启动脚本（Linux/macOS）
# 用法: bash deploy/start.sh [--with-ollama]
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="deploy/docker-compose.yml"
ARGS=()

if [[ "${1:-}" == "--with-ollama" ]]; then
  ARGS+=(--profile ollama)
fi

echo ">>> [1/3] 后台构建并启动 backend + frontend ..."
docker compose -f "$COMPOSE" ${ARGS[@]+"${ARGS[@]}"} up -d --build

echo ">>> [2/3] 后台执行数据库迁移 (alembic upgrade head) ..."
docker compose -f "$COMPOSE" run -d --rm backend alembic upgrade head

echo ">>> [3/3] 等待 backend 健康检查通过 ..."
for i in $(seq 1 30); do
  if curl -fsS http://localhost:18100/health >/dev/null 2>&1; then
    echo "    backend 已就绪 ✓"
    break
  fi
  sleep 2
done

echo
echo "服务已后台运行:"
echo "  前端 Web    http://localhost:1893"
echo "  后端 API    http://localhost:18100"
echo "  Swagger     http://localhost:18100/docs"
echo
echo "查看日志: docker compose -f $COMPOSE logs -f"
echo "停止服务: docker compose -f $COMPOSE down"