import os
import time
from typing import Optional, Generator

# 检查是否启用演示模式（沙箱环境无GPU/模型文件时使用）
DEMO_MODE = os.getenv("EDUCHAT_DEMO_MODE", "true").lower() == "true"

# 系统提示词（作业批改专用）
SYSTEM_PROMPT = """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：作业批改

## 作业批改要求：
你是一位经验丰富的教师，现在需要批改学生提交的作业（可以是作文、数学解答、代码等）。请遵循以下步骤：
1. **整体评价**：简要评价作业质量，指出主要优点和不足。
2. **错误分析**：逐条列出错误内容（语法、逻辑、计算、结构等），并给出正确解释或修改建议。
3. **评分**：给出百分制分数，并说明扣分点。
4. **学习建议**：针对薄弱点提供2-3条具体学习建议。
5. **鼓励性结尾**：用积极语气鼓励学生继续努力。

请保持专业且亲切的语气，确保反馈清晰、可操作。"""

# ============================================================
# 模型缓存（全局单例，避免每次请求重复加载）
# ============================================================
_model = None
_tokenizer = None
_model_loading = False


def _load_model():
    """加载模型和 tokenizer（带缓存，进程生命周期内只加载一次）"""
    global _model, _tokenizer, _model_loading

    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer

    if _model_loading:
        # 等待其他线程加载完成
        while _model_loading:
            time.sleep(0.5)
        return _model, _tokenizer

    _model_loading = True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from config import MODEL_PATH, USE_4BIT, MAX_NEW_TOKENS, TEMPERATURE, TOP_P

        print(f"正在加载 EduChat-R1 模型: {MODEL_PATH}")
        print(f"  - 4-bit 量化: {USE_4BIT}")
        print(f"  - PyTorch 版本: {torch.__version__}")
        print(f"  - CUDA 可用: {torch.cuda.is_available()}")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

        if USE_4BIT:
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
            )

        model.eval()

        if torch.cuda.is_available():
            gpu_mem = torch.cuda.memory_allocated() / 1024**3
            print(f"模型加载完成，GPU 显存占用: {gpu_mem:.1f} GB")
        else:
            print("模型加载完成（CPU 模式）")

        _model = model
        _tokenizer = tokenizer
        return _model, _tokenizer

    finally:
        _model_loading = False


def grade_sync(content: str, max_tokens: int = 1024) -> str:
    """同步批改作业"""
    if DEMO_MODE:
        demo_result = f"""
## 整体评价
您提交的作业内容为："【{content[:50]}...】"
整体来看，作业提交完整，格式规范，展现了良好的学习态度。

## 错误分析
1. 部分内容需要进一步验证准确性
2. 建议加强逻辑推理过程的展示

## 评分
**总分：85分**
- 扣分点：逻辑推理不够详细（-10分）、缺少实例说明（-5分）

## 学习建议
1. 加强基础概念的理解和记忆
2. 多做练习题，提高解题速度和准确性
3. 注意答题的完整性，确保每个步骤都有详细说明

## 鼓励性结尾
继续保持认真的学习态度，相信通过努力你的成绩会越来越好！加油！

---
**提示：当前为演示模式，真实批改需要加载 EduChat-R1 教育大模型（约15GB模型文件 + GPU支持）**
"""
        return demo_result

    try:
        import torch
        from config import MODEL_PATH, USE_4BIT, TEMPERATURE, TOP_P

        model, tokenizer = _load_model()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=TEMPERATURE,
                do_sample=True,
                top_p=TOP_P,
            )
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
        )
        return response

    except Exception as e:
        return f"模型推理失败：{str(e)}\n\n请检查模型文件是否存在，或设置环境变量 EDUCHAT_DEMO_MODE=true 使用演示模式"


def grade_stream(content: str, max_tokens: int = 1024) -> Generator[str, None, None]:
    """流式批改作业，返回生成器"""
    if DEMO_MODE:
        demo_result = grade_sync(content, max_tokens)
        for char in demo_result:
            yield char
            time.sleep(0.02)
        return

    try:
        import torch
        from transformers import TextIteratorStreamer
        import threading
        from config import MODEL_PATH, USE_4BIT, TEMPERATURE, TOP_P

        model, tokenizer = _load_model()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        streamer = TextIteratorStreamer(
            tokenizer, skip_special_tokens=True, skip_prompt=True
        )
        generation_kwargs = {
            "input_ids": inputs.input_ids,
            "attention_mask": inputs.attention_mask,
            "max_new_tokens": max_tokens,
            "temperature": TEMPERATURE,
            "do_sample": True,
            "top_p": TOP_P,
            "streamer": streamer,
        }

        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        for chunk in streamer:
            yield chunk

    except Exception as e:
        yield f"模型推理失败：{str(e)}\n\n请检查模型文件是否存在，或设置环境变量 EDUCHAT_DEMO_MODE=true 使用演示模式"
