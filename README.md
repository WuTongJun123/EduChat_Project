# 📝 EduChat 智能作业批改系统

![Python Version](https://img.shields.io/badge/python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)
![License](https://img.shields.io/badge/license-Apache%202.0-orange)

> 基于 EduChat-R1 教育大模型的自动化作业批改平台，支持多学科、多模态输入，提供流式反馈与智能评分。

<div align="center">
  <img src="docs/demo.gif" width="90%">
</div>

---

## ✨ 功能特点

- **多学科支持**：语文作文、数学解答、代码编程、英语作文等自动批改
- **多模态输入**：支持文本粘贴、代码文件（.txt/.py）及图片（.jpg/.png），图片自动 OCR 识别
- **智能反馈**：提供整体评价、错误分析、评分（百分制）、学习建议与鼓励性结尾
- **流式输出**：实时展示模型思维链（思考过程）与批改结果，交互流畅
- **一键部署**：提供批处理脚本，可快速启动前后端服务

---

## 🛠️ 技术架构

| 层级       | 技术选型                                                                 |
|------------|--------------------------------------------------------------------------|
| 前端       | Vue3、Element Plus、Vite、Axios                                          |
| 后端       | FastAPI、Uvicorn、Transformers、BitsAndBytes、PaddleOCR（可选）          |
| 模型       | EduChat-R1-8B（华东师范大学开源教育大模型，支持4-bit量化）                |
| 部署       | Docker（可选）、Nginx（生产环境）                                         |

---

## 📋 环境要求

### 硬件
- **CPU**：4 核及以上（推荐）
- **内存**：16 GB 以上
- **GPU**（推荐）：NVIDIA GPU，显存 ≥ 8 GB（启用4-bit量化后约8-10 GB）
  - 无 GPU 可使用 CPU 推理（速度较慢，约5-10分钟/次）

### 软件
- **操作系统**：Windows 10/11、Linux（Ubuntu 20.04+）、macOS（需支持 GPU）
- **Python**：3.10 或更高版本
- **Node.js**：18.0 或更高版本（含 npm）
- **Git**（可选，用于克隆仓库）

---

## 🚀 安装与部署

### 1. 克隆项目
```bash
git clone https://github.com/your-username/EduChat_Project.git
cd EduChat_Project
```
### 2. 下载模型
模型文件约 15 GB，请确保磁盘空间充足。

- 使用 Hugging Face 命令行工具：
  ```bash
  pip install huggingface_hub
  huggingface-cli download ecnu-icalk/educhat-r1-001-8b-qwen3.0 --local-dir ./models/educhat-r1-001-8b-qwen3.0
  ```
- 国内用户可使用镜像加速：
  ```bash
  export HF_ENDPOINT=https://hf-mirror.com
  huggingface-cli download ecnu-icalk/educhat-r1-001-8b-qwen3.0 --local-dir ./models/educhat-r1-001-8b-qwen3.0
  ```

### 3. 配置后端
进入 `backend` 目录，安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

### 4. 配置前端
进入 `frontend` 目录，安装依赖并构建：

```bash
cd ../frontend
npm install
npm run build
```

### 5. 启动服务
#### 方式一：生产模式（后端托管前端）
```bash
cd ../backend
python main.py
```

#### 方式二：开发模式（前后端分离）
```bash
cd backend
python main.py
```
```bash
cd frontend
npm run dev
```
