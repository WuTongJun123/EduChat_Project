#!/usr/bin/env python3
"""
EduChat-R1 模型下载脚本
支持从 HuggingFace 或 ModelScope 下载模型
"""

import os
import sys
import argparse

MODEL_REPO_HF = "ecnu-icalk/educhat-r1-001-8b-qwen3.0"
MODEL_REPO_MS = "ECNU-ICALK/educhat-r1-001-8b-qwen3.0"

def download_from_huggingface(target_dir: str):
    """从 HuggingFace 下载模型"""
    print(f"[HuggingFace] 开始下载模型: {MODEL_REPO_HF}")
    print(f"[HuggingFace] 目标目录: {target_dir}")

    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=MODEL_REPO_HF,
            local_dir=target_dir,
            resume_download=True,
        )
        print(f"[HuggingFace] 模型下载完成: {target_dir}")
    except ImportError:
        print("[HuggingFace] 未安装 huggingface_hub，正在安装...")
        os.system("pip install -U huggingface_hub")
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=MODEL_REPO_HF,
            local_dir=target_dir,
            resume_download=True,
        )
        print(f"[HuggingFace] 模型下载完成: {target_dir}")

def download_from_modelscope(target_dir: str):
    """从 ModelScope（魔搭）下载模型（国内推荐）"""
    print(f"[ModelScope] 开始下载模型: {MODEL_REPO_MS}")
    print(f"[ModelScope] 目标目录: {target_dir}")

    try:
        from modelscope import snapshot_download
        snapshot_download(
            model_id=MODEL_REPO_MS,
            local_dir=target_dir,
        )
        print(f"[ModelScope] 模型下载完成: {target_dir}")
    except ImportError:
        print("[ModelScope] 未安装 modelscope，正在安装...")
        os.system("pip install modelscope")
        from modelscope import snapshot_download
        snapshot_download(
            model_id=MODEL_REPO_MS,
            local_dir=target_dir,
        )
        print(f"[ModelScope] 模型下载完成: {target_dir}")

def verify_model(model_dir: str):
    """验证模型文件完整性"""
    print(f"\n[验证] 检查模型目录: {model_dir}")

    required_files = []
    optional_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "generation_config.json",
        "model.safetensors",
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
        choices=["hf", "modelscope", "auto"],
        default="auto",
        help="下载源: hf=HuggingFace, modelscope=魔搭(国内推荐), auto=自动选择",
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
        # 检测网络环境，优先使用 ModelScope（国内更快）
        print("\n[自动检测] 尝试选择最优下载源...")
        import socket
        try:
            socket.create_connection(("www.modelscope.cn", 443), timeout=3)
            source = "modelscope"
            print("[自动检测] 选择 ModelScope（国内网络优先）")
        except (socket.timeout, ConnectionRefusedError, OSError):
            source = "hf"
            print("[自动检测] 选择 HuggingFace")

    # 执行下载
    if source == "hf":
        download_from_huggingface(args.target)
    else:
        download_from_modelscope(args.target)

    # 验证
    verify_model(args.target)

    print("\n" + "=" * 60)
    print("  下载完成！")
    print(f"  模型路径: {os.path.abspath(args.target)}")
    print("\n  配置环境变量:")
    print(f"    export EDUCHAT_MODEL_PATH={os.path.abspath(args.target)}")
    print(f"    export EDUCHAT_DEMO_MODE=false")
    print("=" * 60)
