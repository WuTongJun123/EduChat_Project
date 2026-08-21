import os
import time
from typing import Optional, Generator

# 先导入 config，确保 .env 文件被加载后再读取环境变量
from config import DEMO_MODE, MODEL_PATH, USE_4BIT, MAX_NEW_TOKENS, TEMPERATURE, TOP_P

# 系统提示词（作业批改专用）
SYSTEM_PROMPT = """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：作业批改

## 作业批改要求：
你是一位经验丰富的教师，现在需要批改学生提交的作业（可以是作文、数学解答、代码等）。

你必须严格按照以下格式输出，不要使用其他格式：

## 整体评价
（简要评价作业质量，指出主要优点和不足）

## 错误分析
（逐条列出错误内容，无错误则说明"未发现明显错误"。每条错误给出正确解释或修改建议）

## 评分
**总分：XX分**
（百分制评分，必须给出具体分数。说明扣分点，如：计算错误-5分。完全正确也给满分并说明理由）

## 学习建议
（针对薄弱点提供2-3条具体学习建议）

## 鼓励性结尾
（用积极语气鼓励学生继续努力）

请保持专业且亲切的语气，确保反馈清晰、可操作。

重要：每个章节标题（如 ## 整体评价）必须单独占一行，标题和内容之间必须换行。不要把所有内容写在一行里。"""

# 学科专属提示词
SUBJECT_PROMPTS = {
    "数学": """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：数学作业批改

## 数学作业批改要求：
你是一位经验丰富的数学教师，现在需要批改学生提交的数学作业。

⚠️ 严禁幻觉（最重要规则）：
1. 只能基于学生实际提交的内容进行批改，绝不允许编造学生没有写的内容
2. 如果你引用学生的某一步，必须逐字引用原文，不得修改或添加
3. 如果学生没有提到某个概念（如导数、积分等），你绝不能说学生使用了该概念
4. 错误分析只能针对学生实际写出的步骤，不能分析学生没有写的步骤

你必须严格按照以下格式输出，不要使用其他格式（如【学情诊断】等）：

## 整体评价
（评价解题思路是否清晰、方法是否得当、计算是否准确。必须基于学生实际写的步骤）

## 错误分析
（逐步检查学生实际写的解题过程，逐字引用出错的原句，标出具体错误位置。无错误则说明"未发现明显错误，解题过程完全正确"。如需给出正确解法，必须先说明学生的哪一步有错）

## 评分
**总分：XX分**
（百分制评分，必须给出具体分数。说明扣分点，如：计算错误-5分、步骤不完整-3分。完全正确给满分并说明理由）

## 学习建议
（针对薄弱知识点提供2-3条具体学习建议，推荐相关练习方向）

## 鼓励性结尾
（用积极语气鼓励学生继续努力）

请保持专业且亲切的语气，数学符号使用规范。

重要：每个章节标题（如 ## 整体评价）必须单独占一行，标题和内容之间必须换行。不要把所有内容写在一行里。""",

    "语文": """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：语文作业批改

## 语文作业批改要求：
你是一位经验丰富的语文教师，现在需要批改学生提交的语文作业（可能是作文、阅读理解、古文翻译等）。

⚠️ 严禁幻觉：只能基于学生实际提交的内容批改，绝不允许编造学生没有写的句子。引用学生原文时必须逐字引用。

你必须严格按照以下格式输出，不要使用其他格式：

## 整体评价
（评价文章结构、语言表达、思想内容、文采修辞等方面）

## 错误分析
（指出错别字、语病、标点错误、用词不当等问题，并给出修改建议。无错误则说明"未发现明显错误"）

## 评分
**总分：XX分**
（百分制评分，必须给出具体分数。按内容、结构、语言、创意等维度分别评分并说明）

## 学习建议
（针对写作薄弱环节提供2-3条具体建议，推荐阅读方向）

## 鼓励性结尾
（用积极语气鼓励学生继续努力）

请保持专业且亲切的语气，注重文学素养的培养。

重要：每个章节标题必须单独占一行，标题和内容之间必须换行。""",

    "编程": """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：编程作业批改

## 编程作业批改要求：
你是一位经验丰富的计算机科学教师，现在需要批改学生提交的编程作业。

⚠️ 严禁幻觉：只能基于学生实际提交的代码批改，绝不允许编造学生没有写的代码或函数。引用学生代码时必须逐字引用。

你必须严格按照以下格式输出，不要使用其他格式：

## 整体评价
（评价代码结构、算法思路、代码风格、可读性）

## 错误分析
（检查语法错误、逻辑错误、边界条件处理、潜在Bug等，给出修改建议和正确代码片段。无错误则说明"未发现明显错误"）

## 评分
**总分：XX分**
（百分制评分，必须给出具体分数。按功能正确性、代码质量、算法效率等维度评分）

## 学习建议
（针对编程薄弱点提供2-3条建议，推荐练习方向）

## 鼓励性结尾
（用积极语气鼓励学生继续努力）

请保持专业且亲切的语气，代码建议使用规范的代码块格式。

重要：每个章节标题必须单独占一行，标题和内容之间必须换行。""",

    "英语": """# 背景
你是一个人工智能助手，名字叫EduChat，是一个由华东师范大学开发的教育领域大语言模型。
# 对话主题：英语作业批改

## 英语作业批改要求：
你是一位经验丰富的英语教师，现在需要批改学生提交的英语作业（可能是作文、翻译、语法练习等）。

⚠️ 严禁幻觉：只能基于学生实际提交的内容批改，绝不允许编造学生没有写的句子。引用学生原文时必须逐字引用。

你必须严格按照以下格式输出，不要使用其他格式：

## Overall Evaluation
（Evaluate the content, structure, vocabulary, grammar, and coherence）

## 错误分析
（指出语法错误、拼写错误、用词不当、时态问题等，给出正确表达。无错误则说明"未发现明显错误"）

## 评分
**总分：XX分**
（百分制评分，必须给出具体分数。按内容、语言、结构等维度分别评分）

## 学习建议
（针对英语薄弱环节提供2-3条具体建议）

## 鼓励性结尾
（用积极语气鼓励学生继续努力）

Please maintain a professional yet encouraging tone. 中文和英文可以混合使用。

重要：每个章节标题必须单独占一行，标题和内容之间必须换行。""",
}

# Prompt 变体（用于 A/B 测试）
PROMPT_VARIANTS = {
    "basic": "",  # 使用默认（即 SUBJECT_PROMPTS 或 SYSTEM_PROMPT）
    "structured": """

【结构化批改模式】
请严格按照以下结构输出批改结果，每个部分必须完整：

1️⃣ 整体评价
- 内容完整性：[高/中/低]
- 格式规范性：[高/中/低]
- 一句话总结：...

2️⃣ 逐题分析
对每一题单独分析：
- 题目：...
- 正确性：[正确/部分正确/错误]
- 扣分点：...（如有）
- 解题建议：...

3️⃣ 评分明细
| 评分维度 | 得分 | 满分 | 说明 |
|----------|------|------|------|
| ... | ... | ... | ... |

4️⃣ 总分：XX/100

5️⃣ 学习建议
（3条以上具体建议）

6️⃣ 鼓励
（积极正面的一句话）

重要：每个章节标题必须单独占一行，标题和内容之间必须换行。""",

    "cot": """

【思维链批改模式（Chain-of-Thought）】
请按以下思维链逐步推理后再给出批改结果：

Step 1 - 理解题目：先复述题目要求，确认理解正确
Step 2 - 分析解答：逐步检查学生的每一步解答
Step 3 - 识别错误：标注具体哪一步出现了什么问题
Step 4 - 计算扣分：根据错误严重程度计算每个扣分点
Step 5 - 综合评分：汇总得出总分
Step 6 - 生成建议：针对每个错误给出具体改进方法

然后按以下格式输出：
## 整体评价
（基于思维链分析的综合评价）

## 错误分析
（列出所有发现的错误及其原因）

## 评分
**总分：XX分**
（每个扣分点的详细说明）

## 学习建议
（针对错误的具体改进建议）

## 鼓励性结尾
（积极鼓励）

重要：每个章节标题必须单独占一行，标题和内容之间必须换行。"""
}


# 详细程度追加指令
DETAIL_LEVEL_INSTRUCTIONS = {
    "brief": """

【反馈详细程度：简洁】
请精简输出，每部分不超过1-2句话。错误分析只需一句话概括，学习建议1条即可。整体控制在3-5行内。""",

    "normal": """

【反馈详细程度：标准】
请按标准详细程度输出：整体评价2-3句、错误分析逐条列出、学习建议2-3条。确保反馈信息完整且可操作。""",

    "detailed": """

【反馈详细程度：详细】
请非常详细地输出批改反馈：
- 整体评价：从多个维度（思路、方法、计算、格式等）逐一点评，每维度至少2句
- 错误分析：即使无错误，也要详细说明为什么每一步都是正确的，逐步验证；如果有错误，逐一引用原文并给出正确解法的完整推导过程
- 评分：按维度逐项列出扣分/加分理由，给出分项得分表
- 学习建议：提供3-5条具体建议，每条附带推荐练习方向或参考资源
- 鼓励性结尾：结合具体表现给予有针对性的鼓励
请确保内容充实丰富，总输出不少于500字。""",

    "deep": """

【反馈详细程度：深度分析】
请进行深度、全面的批改分析：
- 整体评价：从知识掌握、解题策略、计算准确性、逻辑严密性、表达规范性等多维度深入分析，每维度3句以上
- 错误分析：逐步验证每一个步骤，对正确的步骤说明其原理和依据，对错误的步骤给出完整的正确推导过程；分析错误产生的根本原因（概念混淆、计算失误、逻辑跳跃等）
- 评分：给出分项评分表（含权重、得分、扣分理由），并与满分答案进行对比说明
- 学习建议：5条以上具体建议，每条包含问题描述、改进方法、推荐练习、预期提升效果
- 鼓励性结尾：结合本次作业表现和进步方向给予个性化鼓励
- 知识拓展：指出本题涉及的核心知识点，推荐相关进阶内容
请确保分析深入透彻，总输出不少于800字。"""
}


def _get_system_prompt(subject: Optional[str] = None, prompt_type: Optional[str] = None, detail_level: Optional[str] = None) -> str:
    """根据学科、prompt类型和详细程度获取对应的系统提示词"""
    base_prompt = SYSTEM_PROMPT
    if subject and subject in SUBJECT_PROMPTS:
        base_prompt = SUBJECT_PROMPTS[subject]

    # 如果指定了 prompt_type 变体，追加到基础提示词
    if prompt_type and prompt_type in PROMPT_VARIANTS and PROMPT_VARIANTS[prompt_type]:
        base_prompt = base_prompt + PROMPT_VARIANTS[prompt_type]

    # 追加详细程度指令
    if detail_level and detail_level in DETAIL_LEVEL_INSTRUCTIONS:
        base_prompt = base_prompt + DETAIL_LEVEL_INSTRUCTIONS[detail_level]

    return base_prompt

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


def grade_sync(content: str, max_tokens: int = 1024, subject: Optional[str] = None, temperature: Optional[float] = None, prompt_type: Optional[str] = None, detail_level: Optional[str] = None) -> str:
    """同步批改作业"""
    system_prompt = _get_system_prompt(subject, prompt_type, detail_level)

    if DEMO_MODE:
        subject_label = f"【{subject}】" if subject else ""
        demo_result = f"""
## 整体评价
您提交的{subject_label}作业内容为："【{content[:50]}...】"
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

        model, tokenizer = _load_model()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        actual_temp = temperature if temperature is not None else TEMPERATURE
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=actual_temp,
                do_sample=True,
                top_p=TOP_P,
            )
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
        )
        return response

    except Exception as e:
        return f"模型推理失败：{str(e)}\n\n请检查模型文件是否存在，或设置环境变量 EDUCHAT_DEMO_MODE=true 使用演示模式"


def grade_stream(content: str, max_tokens: int = 1024, subject: Optional[str] = None, temperature: Optional[float] = None, prompt_type: Optional[str] = None, detail_level: Optional[str] = None) -> Generator[str, None, None]:
    """流式批改作业，返回生成器"""
    system_prompt = _get_system_prompt(subject, prompt_type, detail_level)

    if DEMO_MODE:
        demo_result = grade_sync(content, max_tokens, subject)
        for char in demo_result:
            yield char
            time.sleep(0.02)
        return

    try:
        import torch
        from transformers import TextIteratorStreamer
        import threading

        model, tokenizer = _load_model()

        messages = [
            {"role": "system", "content": system_prompt},
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
