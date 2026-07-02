#!/usr/bin/env python3
"""
EduChat-R1 模型下载脚本
支持从 HuggingFace 或 hf-mirror（国内镜像）下载模型
"""

import os
import sys
import argparse

MODEL_REPO = "ecnu-icalk/educhat-r1-001-8b-qwen3.0"

def download_from_huggingface(target_dir: str, use_mirror: bool = False):
    """从 HuggingFace 下载模型"""
    source_name = "hf-mirror (国内镜像)" if use_mirror else "HuggingFace"
    print(f"[{source_name}] 开始下载模型: {MODEL_REPO}")
    print(f"[{source_name}] 目标目录: {target_dir}")

    # 如果使用镜像，设置环境变量
    if use_mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print(f"[{source_name}] 已设置 HF_ENDPOINT=https://hf-mirror.com")

    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=target_dir,
            resume_download=True,
        )
        print(f"[{source_name}] 模型下载完成: {target_dir}")
        return True
    except ImportError:
        print(f"[{source_name}] 未安装 huggingface_hub，正在安装...")
        os.system("pip install -U huggingface_hub")
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=target_dir,
            resume_download=True,
        )
        print(f"[{source_name}] 模型下载完成: {target_dir}")
        return True
    except Exception as e:
        print(f"[{source_name}] 下载失败: {e}")
        return False

def download_from_modelscope(target_dir: str):
    """尝试从 ModelScope 下载（该模型可能不在 ModelScope 上）"""
    print(f"[ModelScope] 模型 {MODEL_REPO} 可能不在 ModelScope 上，建议使用 HuggingFace 镜像")
    return False

def verify_model(model_dir: str):
    """验证模型文件完整性"""
    print(f"\n[验证] 检查模型目录: {model_dir}")

    optional_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "generation_config.json",
    ]

    all_files = os.listdir(model_dir) if os.path.exists(model_dir) else []

    # 检查 safetensors 分片文件
    st_files = [f for f in all_files if f.endswith(".safetensors")]
    bin_files = [f for f in all_files if f.endswith(".bin")]

    print(f"  - 目录文件数: {len(all_files)}")
    print(f"  - safetensors 文件: {len(st_files)} 个")
    print(f"  - bin 文件: {len(bin_files)} 个")

    # 计算总大小
    total_size = 0
    for f in all_files:
        fpath = os.path.join(model_dir, f)
        if os.path.isfile(fpath):
            total_size += os.path.getsize(fpath)
    print(f"  - 总大小: {total_size / (1024**3):.2f} GB")

    # 检查关键文件
    for f in optional_files:
        if f in all_files:
            print(f"  [OK] {f}")
        else:
            print(f"  [SKIP] {f} (可能不需要)")

    if len(st_files) == 0 and len(bin_files) == 0:
        print("\n  [WARNING] 未找到模型权重文件！下载可能不完整。")
        return False

    print("\n[验证] 模型文件检查完成")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduChat-R1 模型下载工具")
    parser.add_argument(
        "--source",
        choices=["hf", "mirror", "modelscope", "auto"],
        default="auto",
        help="下载源: hf=HuggingFace, mirror=hf-mirror国内镜像, modelscope=魔搭, auto=自动选择",
    )
    parser.add_argument(
        "--target",
        default="./models/educhat-r1-001-8b-qwen3.0",
        help="模型保存目录 (默认: ./models/educhat-r1-001-8b-qwen3.0)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  EduChat-R1 模型下载工具")
    print("  模型: educhat-r1-001-8b-qwen3.0 (基于 Qwen3.0 8B)")
    print("  来源: 华东师范大学 EduNLP 团队")
    print("=" * 60)

    # 创建目标目录
    os.makedirs(args.target, exist_ok=True)

    # 选择下载源
    source = args.source
    if source == "auto":
        # 优先使用 hf-mirror 国内镜像
        print("\n[自动检测] 优先使用 hf-mirror 国内镜像...")
        source = "mirror"

    # 执行下载
    success = False
    if source == "hf":
        success = download_from_huggingface(args.target, use_mirror=False)
    elif source == "mirror":
        success = download_from_huggingface(args.target, use_mirror=True)
        if not success:
            print("\n[重试] 镜像下载失败，尝试 HuggingFace 直连...")
            success = download_from_huggingface(args.target, use_mirror=False)
    elif source == "modelscope":
        success = download_from_modelscope(args.target)
        if not success:
            print("\n[重试] ModelScope 不可用，切换到 hf-mirror 镜像...")
            success = download_from_huggingface(args.target, use_mirror=True)

    if not success:
        print("\n[ERROR] 所有下载源均失败，请检查网络连接")
        print("[ERROR] 手动下载命令:")
        print(f"  pip install -U huggingface_hub")
        print(f"  export HF_ENDPOINT=https://hf-mirror.com")
        print(f"  huggingface-cli download {MODEL_REPO} --local-dir {args.target}")
        sys.exit(1)

    # 验证
    verify_model(args.target)

    print("\n" + "=" * 60)
    print("  下载完成！")
    print(f"  模型路径: {os.path.abspath(args.target)}")
    print("\n  配置环境变量:")
    print(f"    export EDUCHAT_MODEL_PATH={os.path.abspath(args.target)}")
    print(f"    export EDUCHAT_DEMO_MODE=false")
    print("=" * 60)
