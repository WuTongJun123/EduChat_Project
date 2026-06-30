import os

MODEL_PATH = os.getenv("EDUCHAT_MODEL_PATH", "../models/educhat-r1-001-8b-qwen3.0")
USE_4BIT = os.getenv("USE_4BIT", "true").lower() == "true"   # 是否启用4-bit量化
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.3
TOP_P = 0.9