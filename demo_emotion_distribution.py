"""
情感分布可视化演示脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from src.utils import add_emotion_labels, get_emotion_distribution_percent
from src.visualization import (
    plot_emotion_distribution,
    print_emotion_statistics,
    get_emotion_summary,
)

def main():
    print("🚀 开始情感分布可视化演示...\n")
    
    # 1. 加载数据
    print("📁 加载数据...")
    from datasets import load_from_disk
    
    # 直接使用相对项目根的路径
    dataset_path = Path("data/processed/comment_tokenized_dataset")
    
    # 确保我们在项目根目录
    if not dataset_path.exists():
        # 如果相对路径不存在，尝试从当前文件所在目录构建
        current_dir = Path(__file__).resolve().parent
        dataset_path = current_dir / "data" / "processed" / "comment_tokenized_dataset"
    
    print(f"📂 查找数据集路径: {dataset_path.resolve()}")
    
    if not dataset_path.exists():
        print(f"❌ 数据集不存在: {dataset_path}")
        print("请先运行: python src/analysis/preprocess.py")
        return
    
    # 加载数据集
    ds = load_from_disk(str(dataset_path))
    
    # 转换为 DataFrame
    train_df = pd.DataFrame({
        'labels': ds['train']['labels'],
    })
    
    val_df = pd.DataFrame({
        'labels': ds['validation']['labels'],
    })
    
    # 合并训练集和验证集
    df = pd.concat([train_df, val_df], ignore_index=True)
    print(f"✅ 加载 {len(df)} 条数据\n")
    
    # 2. 添加情感标签
    print("🏷️  添加情感标签...")
    df = add_emotion_labels(df)
    print("✅ 添加完成\n")
    
    # 3. 打印统计信息
    print_emotion_statistics(df)
    
    # 4. 绘制可视化图表
    print("🎨 绘制可视化图表...")
    fig, axes = plot_emotion_distribution(df, emotion_col='labels', use_zh=True)
    print("✅ 图表生成完成")
    
    # 5. 获取摘要信息
    print("\n📊 情感分布摘要:")
    summary = get_emotion_summary(df)
    print(f"总评论数: {summary['total_count']}")
    for code, info in summary['distribution'].items():
        print(f"  {info['label']:12} - {info['count']:3d} 条 ({info['percentage']:5.2f}%)")
    
    print("\n✅ 演示完成！")

if __name__ == "__main__":
    main()
