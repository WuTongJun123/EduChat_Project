#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 显式声明关键环境变量
export PORT=5000

# 清理 5000 端口残留进程（幂等）
fuser -k 5000/tcp 2>/dev/null || true
sleep 1

# 使用后端 Python 静态文件服务器在 5000 端口提供前端预览
cd backend
exec python -c "
import http.server
import socketserver
import os

PORT = 5000
os.chdir('../frontend/dist')
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(('', PORT), Handler) as httpd:
    print(f'Serving at http://0.0.0.0:{PORT}')
    httpd.serve_forever()
"
