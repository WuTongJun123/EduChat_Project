#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 启动后端服务（托管前端静态文件，监听 5000 端口）
cd backend
exec uvicorn main:app --host 0.0.0.0 --port 5000
