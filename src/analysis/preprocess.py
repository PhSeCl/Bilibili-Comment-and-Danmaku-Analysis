import os
import json
import argparse  # 新增：命令行参数支持
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

# ============ 默认配置区 ============
# 自动找到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_MODEL_ID = "hfl/chinese-roberta-wwm-ext"
DEFAULT_MAX_LEN = 128
OUTPUT_BASE_DIR = str(DATA_PROCESSED_DIR)
TEST_SIZE = 0.2
RANDOM_STATE = 42
# ===================================

def parse_args():
    parser = argparse.ArgumentParser(description="数据预处理脚本")
    parser.add_argument("--input", type=str, default=str(DATA_RAW_DIR / "comments.csv"), 
                        help="原始 CSV 文件路径")
    parser.add_argument("--type", type=str, default="comment", choices=["comment", "danmaku"], 
                        help="数据类型: comment 或 danmaku")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_ID, help="HuggingFace 模型 ID")
    parser.add_argument("--num_labels", type=int, default=8, help="分类标签数")
    return parser.parse_args()

def detect_header_row(filepath):
    """自动寻找 CSV 的表头行（跳过 # 开头的元数据）"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        # 找到第一行不以 # 开头且非空的行，这就是表头
        if line.strip() and not line.strip().startswith('#'):
            return i
    return 0

def parse_time(s: str):
    """增强版时间解析，适配 B 站爬虫格式"""
    s = str(s).strip()
    if not s or s.lower() == 'nan':
        return {"hour": -1, "weekday": -1}
    
    # 常见格式列表
    formats = [
        "%Y-%m-%d %H:%M:%S", # 爬虫标准格式 2025-01-01 12:00:00
        "%Y/%m/%d %H:%M", 
        "%Y-%m-%d %H:%M", 
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return {"hour": dt.hour, "weekday": dt.weekday()}
        except ValueError:
            continue
            
    # 兜底：如果只是日期没有时间，或者格式太怪
    return {"hour": -1, "weekday": -1}

def main():
    args = parse_args()
    NUM_LABELS = args.num_labels  # 获取标签数
    
    print(f"🚀 开始预处理: {args.input} (类型: {args.type})")
    
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        return

    # 1. 智能读取 CSV
    header_row = detect_header_row(args.input)
    print(f"🔍 检测到表头在第 {header_row} 行")
    
    df = pd.read_csv(args.input, skiprows=header_row, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"])
    print(f"📊 原始数据量: {len(df)} 条")

    # 2. 列名标准化 (根据数据类型不同)
    # 创建一个新的标准 DataFrame
    new_df = pd.DataFrame()
    
    # 通用列
    if 'content' in df.columns:
        new_df['content'] = df['content']
    elif 'message' in df.columns:
        new_df['content'] = df['message']
    else:
        print("❌ 找不到 content 列！请检查 CSV 表头。")
        return

    # 处理标签列（如果有的话）
    if 'label' in df.columns:
        new_df['label'] = df['label'].astype(int)
    else:
        print("⚠️  未找到 label 列，使用随机标签进行演示")
        new_df['label'] = np.random.randint(0, NUM_LABELS, len(df))

    # 类型特定列处理
    if args.type == 'comment':
        # 评论数据映射
        new_df['time'] = df['date'] if 'date' in df.columns else ""
        new_df['location'] = df['location'] if 'location' in df.columns else "unknown"
        new_df['user_level'] = df['level'] if 'level' in df.columns else "0"
        new_df['likes'] = df['likes'] if 'likes' in df.columns else "0"
        new_df['username'] = df['username'] if 'username' in df.columns else "unknown"
        
    elif args.type == 'danmaku':
        # 弹幕数据映射
        new_df['time'] = df['real_time'] if 'real_time' in df.columns else ""
        # 弹幕没有 location, likes, level，给默认值
        new_df['location'] = "unknown"
        new_df['user_level'] = "0"
        new_df['likes'] = "0"
        new_df['username'] = df['user_hash'] if 'user_hash' in df.columns else "unknown"

    # 3. 基础清洗
    # 去除空内容
    new_df["content"] = new_df["content"].fillna("").astype(str)
    new_df = new_df[new_df["content"].str.strip() != ""].reset_index(drop=True)
    
    # 去除 "回复 @xxx :" (这对情感分析很重要)
    import re
    new_df["content"] = new_df["content"].apply(lambda x: re.sub(r'^回复 @.*? :', '', x).strip())
    new_df = new_df[new_df["content"] != ""] # 再次清洗可能变空的行

    print(f"🧹 清洗后数据量: {len(new_df)} 条")

    # 4. 特征工程
    # A. 时间特征
    parsed = new_df["time"].apply(parse_time)
    new_df["hour"] = parsed.apply(lambda x: x["hour"])
    new_df["weekday"] = parsed.apply(lambda x: x["weekday"])

    # B. 地点特征 (Mapping)
    new_df["location"] = new_df["location"].fillna("").replace("", "unknown")
    # 简单清洗：去除 "IP属地："
    new_df["location"] = new_df["location"].apply(lambda x: str(x).replace("IP属地：", ""))
    
    unique_locs = new_df["location"].unique().tolist()
    loc2id = {loc: idx for idx, loc in enumerate(unique_locs)}
    new_df["loc_id"] = new_df["location"].map(loc2id).fillna(-1).astype(int)

    # 保存 loc 映射
    loc_map_path = os.path.join(OUTPUT_BASE_DIR, f"{args.type}_loc2id.json")
    os.makedirs(os.path.dirname(loc_map_path), exist_ok=True)
    with open(loc_map_path, "w", encoding="utf-8") as f:
        json.dump(loc2id, f, ensure_ascii=False, indent=2)

    # C. 用户等级 & 点赞 (数值化 + 标准化)
    def safe_float(x):
        try:
            return float(x)
        except:
            return 0.0
            
    new_df["user_level_num"] = new_df["user_level"].apply(safe_float)
    new_df["likes_num"] = new_df["likes"].apply(safe_float)
    
    # Z-Score 标准化 (防止除以0)
    def standardize(series):
        std = series.std()
        if std == 0: return series - series.mean()
        return (series - series.mean()) / std

    new_df["user_level_norm"] = standardize(new_df["user_level_num"])
    # 点赞数长尾分布，先 log 再归一化
    new_df["likes_log"] = np.log1p(new_df["likes_num"]) 
    new_df["likes_norm"] = standardize(new_df["likes_log"])

    # 5. 构造 extra 向量 [hour, weekday, loc_id, level, likes]
    # 注意：BERT 模型只接受 Tensor，所以所有值必须是 float/int
    def make_extra(row):
        return [
            float(row["hour"]), 
            float(row["weekday"]), 
            float(row["loc_id"]),
            float(row["user_level_norm"]), 
            float(row["likes_norm"])
        ]

    new_df["extra"] = new_df.apply(make_extra, axis=1)

    # 6. 划分数据集 (Train/Val)
    # 只有数据量足够大时才划分，否则全量作为 train
    if len(new_df) > 10:
        train_df, val_df = train_test_split(new_df, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    else:
        train_df, val_df = new_df, new_df.iloc[:0] # 空的 val
        
    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    # 7. 转为 HF Dataset 并 Tokenize
    ds_train = Dataset.from_pandas(train_df[["content", "extra", "username", "label"]])
    ds_val = Dataset.from_pandas(val_df[["content", "extra", "username", "label"]])
    ds = DatasetDict({"train": ds_train, "validation": ds_val})

    print("⏳ 正在 Tokenize (使用模型: {})...".format(args.model))
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)

    def tokenize_fn(examples):
        out = tokenizer(examples["content"], truncation=True, max_length=DEFAULT_MAX_LEN)
        out["extra"] = examples["extra"]
        out["labels"] = examples["label"]  # 转换为 "labels"（模型训练需要）
        out["username"] = examples.get("username", [""] * len(examples["content"]))
        return out

    remove_cols = ["content", "extra", "username", "label"]
    # 某些版本 datasets 可能需要 remove_columns 参数来清除原始文本列以节省空间
    tokenized = ds.map(tokenize_fn, batched=True, remove_columns=remove_cols)

    # 8. 保存
    save_path = os.path.join(OUTPUT_BASE_DIR, f"{args.type}_tokenized_dataset")
    tokenized.save_to_disk(save_path)
    
    print("✅ 预处理完成！")
    print(f"📁 Dataset 保存路径: {save_path}")
    print(f"📁 Location 映射路径: {loc_map_path}")
    print(f"📊 训练集样本数: {len(tokenized['train'])}")

if __name__ == "__main__":
    main()