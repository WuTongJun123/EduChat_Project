import os
from typing import Optional

def extract_text_from_file(file_path: str) -> Optional[str]:
    """从文件中提取文本内容（支持 .txt, .py, .jpg, .png）"""
    if not file_path or not os.path.exists(file_path):
        return None
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.txt', '.py', '.md', '.json']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext in ['.jpg', '.jpeg', '.png']:
            # 可选 OCR，需安装 paddleocr
            try:
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                result = ocr.ocr(file_path, cls=True)
                if result and result[0]:
                    texts = [line[1][0] for line in result[0]]
                    return '\n'.join(texts)
                else:
                    return "[未识别到文字]"
            except ImportError:
                return "[请安装 paddleocr 以支持图片识别]"
        else:
            return f"[不支持的文件类型: {ext}]"
    except Exception as e:
        return f"[文件读取失败: {str(e)}]"