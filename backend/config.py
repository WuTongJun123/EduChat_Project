import os

# 尝试从 .env 文件加载环境变量（AutoDL 部署时使用）
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"已加载环境变量配置: {env_path}")
except ImportError:
    # python-dotenv 未安装时跳过，直接使用系统环境变量
    pass

# 模型配置
MODEL_PATH = os.getenv(
    "EDUCHAT_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "educhat-r1-001-8b-qwen3.0")
)
USE_4BIT = os.getenv("USE_4BIT", "true").lower() == "true"
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "1024"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
TOP_P = float(os.getenv("TOP_P", "0.9"))

# 服务配置
DEMO_MODE = os.getenv("EDUCHAT_DEMO_MODE", "true").lower() == "true"
PORT = int(os.getenv("DEPLOY_RUN_PORT", os.getenv("BACKEND_PORT", "8000")))
