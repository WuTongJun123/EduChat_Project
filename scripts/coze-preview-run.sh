#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 从环境变量读取端口（沙箱规范）
PORT="${DEPLOY_RUN_PORT:-5000}"

echo "🚀 启动 EduChat 预览服务在端口 $PORT"

# 启动后端 FastAPI 服务（同时提供 API 和前端静态文件）
cd backend
exec python main.py
