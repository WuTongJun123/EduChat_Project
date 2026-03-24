EduChat 智能作业批改系统
基于 EduChat-R1 教育大模型开发的自动化作业批改平台，支持文本、代码、图像（OCR）多类型作业的智能评分与反馈。系统采用前后端分离架构，前端使用 Vue3 + Element Plus，后端使用 FastAPI + Transformers，提供流式响应与友好的交互界面。

✨ 功能特点
多学科支持：语文作文、数学解答、代码编程、英语作文等自动批改

多模态输入：支持文本粘贴、代码文件（.py/.txt）、图片（.jpg/.png）上传，图片自动 OCR 识别

智能反馈：提供整体评价、错误分析、评分、学习建议与鼓励性结尾

流式输出：实时展示模型思考过程（思维链）与批改结果，体验流畅

一键部署：支持本地运行与云端部署，提供批处理脚本快速启动

🛠️ 技术架构
层级	技术选型
前端	Vue3、Element Plus、Vite、Axios
后端	FastAPI、Uvicorn、Transformers、BitsAndBytes、PaddleOCR（可选）
模型	EduChat-R1-8B（华东师范大学开源教育大模型）
部署	Docker（可选）、Nginx（生产环境）
📋 环境要求
硬件
CPU：4 核以上（推荐）

内存：16GB 以上

GPU（推荐）：NVIDIA GPU，显存 ≥ 8GB（启用 4-bit 量化）

无 GPU 可使用 CPU 推理（速度较慢）

软件
操作系统：Windows 10/11、Linux（Ubuntu 20.04+）、macOS（需支持 GPU）

Python：3.10 或更高版本

Node.js：18.0 或更高版本（含 npm）

Git（可选，用于克隆仓库）

🚀 安装与部署
1. 克隆项目
bash

复制

下载
git clone https://github.com/your-repo/EduChat_Project.git
cd EduChat_Project
2. 下载模型
从 Hugging Face 下载模型（约 15GB）到 models/educhat-r1-001-8b-qwen3.0：

bash

复制

下载
pip install huggingface_hub
huggingface-cli download ecnu-icalk/educhat-r1-001-8b-qwen3.0 --local-dir ./models/educhat-r1-001-8b-qwen3.0
国内用户可使用镜像加速：

bash

复制

下载
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download ecnu-icalk/educhat-r1-001-8b-qwen3.0 --local-dir ./models/educhat-r1-001-8b-qwen3.0
3. 配置后端
进入 backend 目录，安装依赖：

bash

复制

下载
cd backend
pip install -r requirements.txt
如需 GPU 加速，确保已安装对应 CUDA 版本的 PyTorch。

修改 config.py 中的模型路径（如果模型位置与默认不符）：

python

复制

下载
MODEL_PATH = "../models/educhat-r1-001-8b-qwen3.0"  # 相对路径
4. 配置前端
进入 frontend 目录，安装依赖：

bash

复制

下载
cd ../frontend
npm install
构建前端静态文件（用于生产环境）：

bash

复制

下载
npm run build
5. 启动服务
开发模式（前后端分离）：

bash

复制

下载
# 终端1：启动后端
cd backend
python main.py

# 终端2：启动前端开发服务器
cd frontend
npm run dev
访问 http://localhost:5173

生产模式（后端托管前端）：

确保前端已构建（npm run build）

直接启动后端，访问 http://localhost:8000

6. 一键启动（Windows）
在项目根目录创建 start.bat：

batch

复制

下载
@echo off
echo 启动后端服务...
start cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul
echo 启动前端服务...
start cmd /k "cd frontend && npm run dev"
echo 前后端启动完成，请访问 http://localhost:5173
双击运行即可。

📖 使用说明
打开网页：访问 http://localhost:8000（生产模式）或 http://localhost:5173（开发模式）

输入作业：在文本框中粘贴内容，或点击上传文件（支持 .txt、.py、.jpg、.png）

调节详细程度：拖动滑块控制批改结果的详细程度（最大 token 数）

点击批改：等待几秒，流式结果将实时显示在下方

查看结果：包含评分、错误分析、修改建议等，鼓励学生继续努力

样例作业
可尝试以下内容进行测试：

语文作文

《我的理想》
每个人都有自己的理想，我的理想是成为一名科学家。因为科学家可以发明很多有用的东西，帮助人们生活得更好。我会努力学习，将来实现这个理想。

数学解答

计算 1+2+3+…+100 的和，并写出步骤。
1+2+3+…+100 = 5050
步骤：高斯公式 (1+100)×100÷2 = 5050

Python 代码

python

复制

下载
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
print(factorial(5))
🔧 API 文档
启动后端后，访问 http://localhost:8000/docs 可查看自动生成的 Swagger UI 文档。

主要接口：

POST /api/grade/sync：同步批改，返回完整结果

POST /api/grade/stream：流式批改，返回 Server-Sent Events

POST /api/grade/file：文件上传批改

GET /api/health：健康检查

请求体示例（JSON）：

json

复制

下载
{
  "content": "作业内容",
  "max_tokens": 1024,
  "subject": "数学"
}
