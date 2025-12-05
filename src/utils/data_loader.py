"""
数据加载和处理工具
"""
import pandas as pd
import numpy as np
from pathlib import Path
import os

# 自动找到项目根目录
def get_project_root():
    """获取项目根目录"""
    current_dir = Path(__file__).resolve().parent
    # 从 src/utils 往上找三级到达项目根目录
    return current_dir.parent.parent

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_dataset(data_type="comment"):
    """
    加载预处理后的数据集
    
    Args:
        data_type: str，数据类型 "comment" 或 "danmaku"
        
    Returns:
        pd.DataFrame，加载的数据
    """
    dataset_path = DATA_PROCESSED_DIR / f"{data_type}_tokenized_dataset"
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"数据集不存在: {dataset_path}")
    
    from datasets import load_from_disk
    ds = load_from_disk(str(dataset_path))
    
    # 转换为 DataFrame
    df = pd.DataFrame({
        'input_ids': ds['train']['input_ids'] + ds['validation']['input_ids'],
        'labels': ds['train']['labels'] + ds['validation']['labels'],
        'extra': ds['train']['extra'] + ds['validation']['extra'],
    })
    
    return df

def add_emotion_labels(df, emotion_mapping=None):
    """
    为 DataFrame 添加情感标签列
    
    Args:
        df: pd.DataFrame，包含 'labels' 列的数据框
        emotion_mapping: dict，情感代码到标签的映射（可选）
        
    Returns:
        pd.DataFrame，添加了情感标签的数据框
    """
    if emotion_mapping is None:
        from .emotion_mapper import get_emotion_label
        emotion_mapping = {i: get_emotion_label(i, use_zh=True) for i in range(8)}
    
    df['emotion_label'] = df['labels'].map(emotion_mapping)
    return df

def get_emotion_distribution(df, column='labels'):
    """
    计算情感分布
    
    Args:
        df: pd.DataFrame，数据框
        column: str，要统计的列名（默认 'labels'）
        
    Returns:
        dict，{emotion_code: count}
    """
    return df[column].value_counts().to_dict()

def get_emotion_distribution_percent(df, column='labels'):
    """
    计算情感分布百分比
    
    Args:
        df: pd.DataFrame，数据框
        column: str，要统计的列名（默认 'labels'）
        
    Returns:
        dict，{emotion_code: percentage}
    """
    total = len(df)
    dist = df[column].value_counts()
    return {code: (count / total * 100) for code, count in dist.items()}
