import torch
import threading
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig
from config import MODEL_PATH, USE_4BIT

_model: Optional[AutoModelForCausalLM] = None
_tokenizer: Optional[AutoTokenizer] = None

def load_model() -> None:
    """加载模型（只执行一次）"""
    global _model, _tokenizer
    if _model is not None:
        return
    print("正在加载模型...")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if USE_4BIT:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
    else:
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
    _model.eval()
    print("模型加载完成")

def get_model():
    """获取已加载的模型和分词器（确保已加载）"""
    load_model()  # 内部已做判空，不会重复加载
    # 使用断言帮助 IDE 识别类型不为 None
    assert _model is not None
    assert _tokenizer is not None
    return _model, _tokenizer

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

def build_prompt(content: str) -> str:
    """构建完整的输入 prompt"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ]
    model, tokenizer = get_model()
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

def grade_sync(content: str, max_tokens: int = 1024) -> str:
    """同步批改（适用于短文本或简单场景）"""
    model, tokenizer = get_model()
    text = build_prompt(content)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,
            do_sample=True,
            top_p=0.9
        )
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response

def grade_stream(content: str, max_tokens: int = 1024):
    """流式批改，返回生成器"""
    model, tokenizer = get_model()
    text = build_prompt(content)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, skip_prompt=True)
    generation_kwargs = {
        "input_ids": inputs.input_ids,
        "attention_mask": inputs.attention_mask,
        "streamer": streamer,
        "max_new_tokens": max_tokens,
        "temperature": 0.3,
        "do_sample": True,
        "top_p": 0.9,
    }
    thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for chunk in streamer:
        yield chunk