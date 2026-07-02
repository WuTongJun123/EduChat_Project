# EduChat AutoDL 部署指南

本指南帮助你将 EduChat 智能作业批改系统部署到 AutoDL GPU 云平台，并加载真实的 EduChat-R1 教育大模型。

---

## 一、AutoDL 实例配置建议

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| GPU | RTX 3060 12GB | RTX 3090 24GB / A100 |
| CUDA | 11.8+ | 12.1+ |
| 系统盘 | 30GB | 50GB |
| 数据盘 | 30GB | 50GB+（存放模型） |
| 镜像 | PyTorch 2.0+ | PyTorch 2.1 + CUDA 12.1 |

> **显存说明**：4-bit 量化模式需要约 8-10GB 显存；非量化模式需要约 18-20GB 显存。

---

## 二、快速部署（一键脚本）

### 1. 创建 AutoDL 实例

1. 登录 [AutoDL 控制台](https://www.autodl.com/)
2. 选择「算力市场」-> 选择合适的 GPU（推荐 RTX 3090 24GB）
3. 镜像选择：`PyTorch 2.1.0 / Python 3.10 / CUDA 12.1`
4. 创建实例

### 2. 上传项目代码

通过 AutoDL 提供的 SSH 或 JupyterLab 上传项目：

```bash
# SSH 登录后，克隆你的项目
cd /root
git clone https://github.com/WuTongJun123/EduChat_Project.git EduChat
cd EduChat
```

或者通过 JupyterLab 的文件上传功能直接上传项目压缩包。

### 3. 执行一键部署

```bash
cd /root/EduChat
chmod +x deploy/deploy_autodl.sh
bash deploy/deploy_autodl.sh
```

脚本会自动完成：
- 环境检查（GPU / Python / 磁盘空间）
- 安装系统依赖（Node.js / pnpm / Git LFS）
- 下载 EduChat-R1 模型（约 15GB，优先使用 ModelScope）
- 安装后端依赖（PyTorch / Transformers / FastAPI 等）
- 构建前端
- 配置环境变量
- 验证模型加载

### 4. 启动服务

```bash
cd /root/EduChat/backend
python main.py
```

看到以下输出表示启动成功：
```
🚀 启动 EduChat 预览服务在端口 8000
正在加载 EduChat-R1 模型...
模型加载完成
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. 配置公网访问

1. 进入 AutoDL 控制台 -> 容器实例
2. 点击「自定义服务」
3. 添加端口 `8000`
4. AutoDL 会生成一个公网访问链接，格式类似：`https://district-xxxxx-8000.westx.seetacloud.com`

---

## 三、手动部署（分步操作）

如果一键脚本失败，可按以下步骤手动操作。

### Step 1: 安装系统依赖

```bash
# 更新包管理器
apt-get update

# 安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# 安装 pnpm
npm install -g pnpm

# 安装 Git LFS
apt-get install -y git-lfs
git lfs install
```

### Step 2: 下载模型

```bash
cd /root/EduChat
mkdir -p models

# 方式一：ModelScope（国内推荐，速度快）
pip install modelscope
python3 deploy/download_model.py --source modelscope --target models/educhat-r1-001-8b-qwen3.0

# 方式二：HuggingFace
pip install huggingface_hub
python3 deploy/download_model.py --source hf --target models/educhat-r1-001-8b-qwen3.0

# 方式三：直接 git clone（需要 Git LFS）
git lfs install
git clone https://huggingface.co/ecnu-icalk/educhat-r1-001-8b-qwen3.0 models/educhat-r1-001-8b-qwen3.0
```

### Step 3: 安装后端依赖

```bash
cd /root/EduChat/backend

# 安装 PyTorch（根据 CUDA 版本选择）
# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# CUDA 11.8
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装其他依赖
pip install -r requirements.txt
```

### Step 4: 构建前端

```bash
cd /root/EduChat/frontend
pnpm install
pnpm run build
```

构建产物在 `frontend/dist/` 目录，后端会自动托管。

### Step 5: 配置环境变量

```bash
# 创建环境变量文件
cat > /root/EduChat/backend/.env << 'EOF'
EDUCHAT_DEMO_MODE=false
EDUCHAT_MODEL_PATH=/root/EduChat/models/educhat-r1-001-8b-qwen3.0
USE_4BIT=true
MAX_NEW_TOKENS=1024
TEMPERATURE=0.3
TOP_P=0.9
EOF
```

### Step 6: 启动服务

```bash
cd /root/EduChat/backend
python main.py
```

---

## 四、模型下载说明

### 模型信息

| 属性 | 值 |
|------|-----|
| 模型名称 | EduChat-R1 (educhat-r1-001-8b-qwen3.0) |
| 基座模型 | Qwen3.0 8B |
| 开发团队 | 华东师范大学 EduNLP 团队 |
| 模型大小 | 约 15GB |
| 许可协议 | Apache 2.0 |
| HuggingFace | https://huggingface.co/ecnu-icalk/educhat-r1-001-8b-qwen3.0 |
| GitHub | https://github.com/icalk-nlp/EduChat |
| 论文 | https://arxiv.org/abs/2308.02773 |

### 下载源对比

| 下载源 | 速度 | 适用场景 |
|--------|------|----------|
| ModelScope（魔搭） | 快（国内 CDN） | AutoDL 国内节点首选 |
| HuggingFace | 中等 | 国际节点或备用 |
| Git LFS Clone | 慢 | 需要完整仓库历史 |

### 使用下载脚本

```bash
# 自动选择最优下载源
python3 deploy/download_model.py --source auto

# 指定 ModelScope
python3 deploy/download_model.py --source modelscope

# 指定 HuggingFace
python3 deploy/download_model.py --source hf

# 自定义保存路径
python3 deploy/download_model.py --target /data/models/educhat
```

---

## 五、常见问题

### Q1: 模型下载中断怎么办？

ModelScope 和 HuggingFace 都支持断点续传，重新运行下载命令即可：

```bash
python3 deploy/download_model.py --source modelscope --target models/educhat-r1-001-8b-qwen3.0
```

### Q2: 显存不足（OOM）？

1. 确保使用 4-bit 量化模式（默认已启用）：
   ```bash
   # 在 .env 文件中设置
   USE_4BIT=true
   ```

2. 如果仍然 OOM，尝试减少 `MAX_NEW_TOKENS`：
   ```bash
   MAX_NEW_TOKENS=512
   ```

3. 终极方案：更换更大显存的 GPU 实例

### Q3: 模型加载很慢？

首次加载需要将模型权重从磁盘加载到 GPU 显存，通常需要 1-3 分钟。加载完成后推理速度正常。

### Q4: 如何以演示模式启动（不加载模型）？

```bash
# 设置环境变量
export EDUCHAT_DEMO_MODE=true
python main.py
```

### Q5: 如何让服务在后台持续运行？

```bash
# 使用 nohup
nohup python main.py > server.log 2>&1 &

# 或使用 screen
screen -S educhat
python main.py
# 按 Ctrl+A+D 分离会话

# 或使用 tmux
tmux new -s educhat
python main.py
# 按 Ctrl+B+D 分离会话
```

### Q6: 如何更新项目代码？

```bash
cd /root/EduChat
git pull origin main

# 重新构建前端
cd frontend && pnpm install && pnpm run build

# 重启服务
cd ../backend
# 杀掉旧进程
pkill -f "python main.py"
# 重新启动
nohup python main.py > server.log 2>&1 &
```

### Q7: AutoDL 关机后模型还在吗？

- **系统盘**：项目代码在系统盘，关机不丢失
- **数据盘**：模型文件建议存放在数据盘（`/root/autodl-tmp/`），关机不丢失
- **关机不计费**：AutoDL 关机后只收少量存储费，不收 GPU 费

建议将模型存放在数据盘：
```bash
# 修改模型路径
export EDUCHAT_MODEL_PATH=/root/autodl-tmp/models/educhat-r1-001-8b-qwen3.0
```

---

## 六、性能参考

| GPU 型号 | 显存 | 加载时间 | 推理速度（4-bit） | 推理速度（FP16） |
|----------|------|----------|-------------------|------------------|
| RTX 3060 | 12GB | ~3min | ~15 tokens/s | OOM |
| RTX 3090 | 24GB | ~2min | ~30 tokens/s | ~25 tokens/s |
| A100 40GB | 40GB | ~1min | ~50 tokens/s | ~45 tokens/s |
| A100 80GB | 80GB | ~1min | ~50 tokens/s | ~45 tokens/s |

> 推理速度取决于输入长度、生成长度和 GPU 型号，以上为参考值。

---

## 七、相关链接

- [EduChat 官网](http://educhat.top/)
- [EduChat GitHub](https://github.com/icalk-nlp/EduChat)
- [EduChat HuggingFace](https://huggingface.co/ecnu-icalk)
- [EduChat 论文](https://arxiv.org/abs/2308.02773)
- [AutoDL 官网](https://www.autodl.com/)
- [ModelScope 魔搭](https://www.modelscope.cn/)
