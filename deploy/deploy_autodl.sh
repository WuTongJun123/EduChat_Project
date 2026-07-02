#!/usr/bin/env bash
set -euo pipefail

#=============================================================
# EduChat 智能作业批改系统 - AutoDL 一键部署脚本
# 使用方法: bash deploy_autodl.sh
#=============================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

#=============================================================
# 配置项（可按需修改）
#=============================================================
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODEL_DIR="${PROJECT_DIR}/models/educhat-r1-001-8b-qwen3.0"
BACKEND_PORT=8000
PYTHON_VERSION="3.10"

#=============================================================
# Step 0: 环境检查
#=============================================================
print_info "========== Step 0: 环境检查 =========="

# 检查 GPU
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)
    print_ok "检测到 GPU: ${GPU_INFO}"
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [ "$GPU_MEM" -lt 8000 ]; then
        print_warn "GPU 显存不足 8GB，4-bit 量化模式可能无法运行"
        print_warn "建议使用 RTX 3090 (24GB) 或更高配置"
    else
        print_ok "GPU 显存充足: ${GPU_MEM}MB"
    fi
else
    print_warn "未检测到 GPU，将使用 CPU 模式（速度较慢）"
fi

# 检查 Python
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version 2>&1)
    print_ok "Python: ${PY_VER}"
else
    print_error "未找到 Python3，请安装 Python ${PYTHON_VERSION}+"
    exit 1
fi

# 检查磁盘空间
DISK_AVAIL=$(df -BG "${PROJECT_DIR}" | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "$DISK_AVAIL" -lt 30 ]; then
    print_warn "可用磁盘空间不足 30GB（当前: ${DISK_AVAIL}GB），模型文件约 15GB"
else
    print_ok "磁盘空间充足: ${DISK_AVAIL}GB"
fi

#=============================================================
# Step 1: 安装系统依赖
#=============================================================
print_info "========== Step 1: 安装系统依赖 =========="

# 安装 Node.js（前端构建需要）
if ! command -v node &> /dev/null; then
    print_info "安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi
print_ok "Node.js: $(node --version)"

# 安装 pnpm
if ! command -v pnpm &> /dev/null; then
    print_info "安装 pnpm..."
    npm install -g pnpm
fi
print_ok "pnpm: $(pnpm --version)"

# 安装 Git LFS（模型下载需要）
if ! command -v git lfs &> /dev/null; then
    print_info "安装 Git LFS..."
    apt-get update -qq && apt-get install -y git-lfs
    git lfs install
fi
print_ok "Git LFS 已安装"

#=============================================================
# Step 2: 下载 EduChat-R1 模型
#=============================================================
print_info "========== Step 2: 下载 EduChat-R1 模型 =========="

if [ -d "${MODEL_DIR}" ] && [ "$(ls -A ${MODEL_DIR} 2>/dev/null)" ]; then
    print_ok "模型目录已存在，跳过下载: ${MODEL_DIR}"
    # 验证模型文件
    ST_COUNT=$(ls ${MODEL_DIR}/*.safetensors 2>/dev/null | wc -l)
    BIN_COUNT=$(ls ${MODEL_DIR}/*.bin 2>/dev/null | wc -l)
    if [ "$ST_COUNT" -gt 0 ] || [ "$BIN_COUNT" -gt 0 ]; then
        print_ok "模型权重文件存在 (safetensors: ${ST_COUNT}, bin: ${BIN_COUNT})"
    else
        print_warn "模型目录存在但未找到权重文件，重新下载..."
        rm -rf "${MODEL_DIR}"
    fi
fi

if [ ! -d "${MODEL_DIR}" ] || [ -z "$(ls -A ${MODEL_DIR} 2>/dev/null)" ]; then
    print_info "开始下载 EduChat-R1 模型（约 15GB）..."
    print_info "模型: ecnu-icalk/educhat-r1-001-8b-qwen3.0 (基于 Qwen3.0 8B)"
    print_info "使用 hf-mirror 国内镜像下载..."

    mkdir -p "${PROJECT_DIR}/models"

    # 安装 huggingface_hub
    pip install -q huggingface_hub

    # 使用 hf-mirror 国内镜像下载（模型仅在 HuggingFace 上）
    python3 "${PROJECT_DIR}/deploy/download_model.py" --source mirror --target "${MODEL_DIR}"

    if [ $? -eq 0 ]; then
        print_ok "模型下载完成"
    else
        print_error "模型下载失败，请检查网络连接"
        print_error "手动下载命令:"
        print_error "  pip install -U huggingface_hub"
        print_error "  export HF_ENDPOINT=https://hf-mirror.com"
        print_error "  huggingface-cli download ecnu-icalk/educhat-r1-001-8b-qwen3.0 --local-dir ${MODEL_DIR}"
        exit 1
    fi
fi

#=============================================================
# Step 3: 安装后端依赖
#=============================================================
print_info "========== Step 3: 安装后端依赖 =========="

cd "${PROJECT_DIR}/backend"

# 安装 PyTorch（根据 CUDA 版本）
print_info "安装 PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    print_info "检测到 CUDA ${CUDA_VERSION}"
    # 安装对应 CUDA 版本的 PyTorch
    if [[ "$CUDA_VERSION" =~ ^12 ]]; then
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    elif [[ "$CUDA_VERSION" =~ ^11 ]]; then
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        pip install torch torchvision torchaudio
    fi
else
    print_warn "无 GPU，安装 CPU 版 PyTorch..."
    pip install torch torchvision torchaudio
fi
print_ok "PyTorch 安装完成"

# 安装其他后端依赖
print_info "安装后端 Python 依赖..."
pip install -r requirements.txt
print_ok "后端依赖安装完成"

#=============================================================
# Step 4: 构建前端
#=============================================================
print_info "========== Step 4: 构建前端 =========="

cd "${PROJECT_DIR}/frontend"
print_info "安装前端依赖..."
pnpm install
print_ok "前端依赖安装完成"

print_info "构建前端..."
pnpm run build
print_ok "前端构建完成"

#=============================================================
# Step 5: 配置环境变量
#=============================================================
print_info "========== Step 5: 配置环境变量 =========="

# 写入环境变量到 .env 文件
ENV_FILE="${PROJECT_DIR}/backend/.env"
cat > "${ENV_FILE}" << EOF
# EduChat 生产环境配置
EDUCHAT_DEMO_MODE=false
EDUCHAT_MODEL_PATH=${MODEL_DIR}
USE_4BIT=true
MAX_NEW_TOKENS=1024
TEMPERATURE=0.3
TOP_P=0.9
EOF

print_ok "环境变量已写入: ${ENV_FILE}"
print_info "  - EDUCHAT_DEMO_MODE=false (关闭演示模式)"
print_info "  - EDUCHAT_MODEL_PATH=${MODEL_DIR}"
print_info "  - USE_4BIT=true (4-bit 量化)"

#=============================================================
# Step 6: 验证模型加载
#=============================================================
print_info "========== Step 6: 验证模型加载 =========="

cd "${PROJECT_DIR}/backend"
print_info "测试模型加载（首次加载需要 1-3 分钟）..."

python3 -c "
import os
os.environ['EDUCHAT_DEMO_MODE'] = 'false'
from config import MODEL_PATH, USE_4BIT
print(f'模型路径: {MODEL_PATH}')
print(f'4-bit 量化: {USE_4BIT}')

import torch
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'显存: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')

from transformers import AutoTokenizer, AutoModelForCausalLM
print('正在加载 tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
print('正在加载模型...')
if USE_4BIT:
    from transformers import BitsAndBytesConfig
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=quantization_config,
        device_map='auto',
        trust_remote_code=True
    )
else:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        device_map='auto',
        trust_remote_code=True
    )
model.eval()
print('模型加载成功！')

# 简单测试
messages = [{'role': 'user', 'content': '1+1等于几？'}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors='pt').to(model.device)
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=50, do_sample=True, temperature=0.3)
response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(f'测试回复: {response[:100]}')
print('模型验证通过！')
" 2>&1

if [ $? -eq 0 ]; then
    print_ok "模型加载验证通过！"
else
    print_error "模型加载失败，请检查模型文件和 GPU 配置"
    print_warn "可以设置 EDUCHAT_DEMO_MODE=true 先以演示模式启动"
    exit 1
fi

#=============================================================
# Step 7: 启动服务
#=============================================================
print_info "========== Step 7: 启动服务 =========="

print_ok "部署完成！"
print_info "启动命令:"
print_info "  cd ${PROJECT_DIR}/backend"
print_info "  python main.py"
print_info ""
print_info "服务地址:"
print_info "  http://0.0.0.0:${BACKEND_PORT}"
print_info ""
print_info "AutoDL 端口映射:"
print_info "  在 AutoDL 控制台 -> 容器实例 -> 自定义服务"
print_info "  添加端口 ${BACKEND_PORT} 即可通过公网访问"
print_info ""
print_info "首次启动模型加载需要 1-3 分钟，请耐心等待..."

# 询问是否立即启动
read -p "是否立即启动服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "${PROJECT_DIR}/backend"
    exec python main.py
fi
