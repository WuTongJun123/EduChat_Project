# EduChat 智能作业批改系统 - 项目规范

## 项目概述

基于 EduChat-R1 教育大模型的自动化作业批改平台，支持多学科（语文、数学、编程、英语）批改，提供流式反馈与智能评分。

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3.3、Element Plus 2.4、Vite 4.4、Axios 1.6 |
| 后端 | FastAPI 0.104、Uvicorn、Pydantic 2.5、Transformers |
| 模型 | EduChat-R1-8B（4-bit 量化） |
| 包管理 | pnpm (前端)、pip (后端) |

## 目录结构

```
/workspace/projects/          # 工作区根目录 = 技术项目根目录
├── .coze                     # 根配置（同时承担子项目职责）
├── AGENTS.md                 # 本文件
├── README.md
├── backend/                  # Python FastAPI 后端
│   ├── main.py               # 入口，FastAPI 应用
│   ├── models.py             # LLM 模型调用
│   ├── schemas.py            # Pydantic 数据模型
│   ├── utils.py              # 工具函数
│   └── requirements.txt      # Python 依赖
├── frontend/                 # Vue3 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js           # Vue 入口
│       ├── App.vue           # 根组件
│       ├── api/index.js      # API 调用封装
│       └── components/       # UI 组件
└── docs/
    └── demo.png
```

## 关键入口 / 核心模块

### 后端 API
- **启动命令**: `python backend/main.py`
- **端口**: 8000
- **健康检查**: `GET /api/health`
- **同步批改**: `POST /api/grade/sync`
- **流式批改**: `POST /api/grade/stream`
- **文件上传批改**: `POST /api/grade/file`

### 前端
- **开发服务器**: `pnpm run dev`（默认 5173 端口）
- **构建命令**: `pnpm run build`
- **生产模式**: 后端通过 `StaticFiles` 托管前端构建产物

## 运行与预览

### 前端开发
```bash
cd frontend
pnpm install
pnpm run dev
```

### 后端开发
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 生产模式（后端托管前端）
```bash
cd backend
pip install -r requirements.txt
python main.py
# 访问 http://localhost:8000
```

## 用户偏好与长期约束

1. **包管理器强制**: 前端项目必须使用 `pnpm`，禁止 `npm` 或 `yarn`
2. **端口约定**: 
   - 前端开发服务器: 5173
   - 后端 API: 8000
   - 预览服务: 5000
3. **跨域**: 后端配置了 `allow_origins=["*"]`，开发环境允许所有来源

## 常见问题和预防

1. **模型未下载**: 后端依赖本地模型文件，首次部署需下载 ~15GB 模型
2. **GPU 显存不足**: 使用 4-bit 量化，显存需求约 8-10GB；CPU 模式可运行但速度慢
3. **CORS 问题**: 开发模式下前端 5173 端口需后端 CORS 配置支持
