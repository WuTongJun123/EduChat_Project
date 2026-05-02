# 📝 EduChat 智能作业批改系统

![Python Version](https://img.shields.io/badge/python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)
![License](https://img.shields.io/badge/license-Apache%202.0-orange)

> 基于 EduChat-R1 教育大模型的自动化作业批改平台，支持多学科、多模态输入，提供流式反馈与智能评分。

<div align="center">
  <img src="docs/demo.png" width="90%">
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
| 后端       | FastAPI, Uvicorn, Pydantic                                            |
| 模型       | EduChat-R1-8B（华东师范大学开源教育大模型，支持4-bit量化）                |
| OCR       | PaddleOCR                                                              |
| 部署       | AutoDL GPU 云服务 / 本地部署                                            |

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
git clone https://github.com/WuTongJun123/EduChat_Project.git
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

#### 方式三：一键启动（Windows）
在项目根目录创建 start.bat：
```bash
@echo off
echo 启动后端服务...
start cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul
echo 启动前端服务...
start cmd /k "cd frontend && npm run dev"
echo 前后端启动完成，请访问 http://localhost:5173
```
双击运行即可。

---

## 📖 使用说明

1. 打开浏览器，访问 `http://localhost:8000`（或 `http://localhost:5173`）。
2. 在文本框中粘贴作业内容，或点击“上传文件”选择 `.txt`、`.py`、`.jpg`、`.png` 文件。
3. 调节“详细程度”滑块控制批改结果的详细程度（最大 token 数）。
4. 点击 **“开始批改”**，稍等片刻即可看到流式输出的批改结果，包含：
   - 思考过程（思维链）
   - 整体评价
   - 错误分析（逐条列出）
   - 评分（百分制）
   - 学习建议
   - 鼓励性结尾

### 样例作业（可复制测试）

**语文作文**  
> 《我的理想》  
> 每个人都有自己的理想，我的理想是成为一名科学家。因为科学家可以发明很多有用的东西，帮助人们生活得更好。我会努力学习，将来实现这个理想。

**数学解答**  
> 计算 1+2+3+…+100 的和，并写出步骤。  
> 1+2+3+…+100 = 5050  
> 步骤：高斯公式 (1+100)×100÷2 = 5050

**Python 代码**  
```python
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
print(factorial(5))
```

---

## 🔌 API 文档

启动后端后，访问 `http://localhost:8000/docs` 可查看自动生成的 Swagger UI 文档。

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/grade/sync` | 同步批改，返回完整结果（JSON） |
| POST | `/api/grade/stream` | 流式批改，返回 Server-Sent Events |
| POST | `/api/grade/file` | 文件上传批改 |
| GET  | `/api/health`  | 健康检查 |

### 请求示例

**同步批改**：
```bash
curl -X POST "http://localhost:8000/api/grade/sync" \
  -H "Content-Type: application/json" \
  -d '{"content": "请批改这篇作文：我的理想...", "max_tokens": 1024}'
```

**文件上传批改**：
```bash
curl -X POST "http://localhost:8000/api/grade/file" \
  -F "file=@/path/to/homework.txt" \
  -F "max_tokens=1024"
```

**响应格式**：
```json
{
  "result": "整体评价：...\n错误分析：...\n评分：85\n学习建议：...\n鼓励性结尾：..."
}
```

---

## 📄 许可证

本项目基于 **Apache 2.0** 协议开源，您可以自由使用、修改和分发，但需保留版权声明并说明修改情况。  
模型 **EduChat-R1** 的版权归华东师范大学所有，使用时请遵守其官方许可证（详见 [Hugging Face 模型页](https://huggingface.co/ecnu-icalk/educhat-r1-001-8b-qwen3.0)）。

**Apache 2.0 许可摘要**：
- ✅ 允许商用
- ✅ 允许修改
- ✅ 允许分发
- ⚠️ 需保留版权和许可声明
- ⚠️ 修改需注明变更
