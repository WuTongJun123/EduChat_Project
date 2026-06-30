#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 1. 构建前端
cd frontend
pnpm install
pnpm run build

# 2. 安装后端依赖
cd ../backend
pip install -r requirements.txt
