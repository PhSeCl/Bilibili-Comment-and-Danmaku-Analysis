# preprocess_with_extra.py
import os
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

# ============ 配置区 ============
RAW_CSV = "data/raw/raw.csv"            # 你的原始文件路径
MODEL_ID = "bert-base-chinese"          # 你要用的 tokenizer（可换为 hfl/chinese-roberta-wwm-ext）
MAX_LEN = 128
OUTPUT_DIR = "data/processed" # 保存 tokenized dataset 的目录
LOC_MAP_PATH = "data/processed/loc2id.json"
TEST_SIZE = 0.2                         # 划分比例（因为无标签，我们只做 train/validation 划分）
RANDOM_STATE = 42
# ================================

os.makedirs(Path(OUTPUT_DIR), exist_ok=True)

# 1. 读取 CSV，尝试兼容列名差异
df = pd.read_csv(RAW_CSV, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"])

# 兼容常见列名：尝试把列名映射到标准名
col_map = {}
cols_lower = {c.lower(): c for c in df.columns}

def find_col(*candidates):
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None

# 你截图中的列名示例： content, date/time, location/ip, level/user_level, likes, username
col_map['content'] = find_col("content", "视频标题", "text", "content")
col_map['time'] = find_col("time", "date", "datetime", "date_time", "publish_time")
col_map['location'] = find_col("location", "ip", "ip_location", "location", "地区")
col_map['user_level'] = find_col("level", "user_level", "等级")
col_map['likes'] = find_col("likes", "点赞", "likes_count", "like")
col_map['username'] = find_col("username", "user", "author", "username", "昵称")

# 若部分列找不到，创建默认空列避免后续报错
for k, v in col_map.items():
    if v is None:
        df[k] = ""
    else:
        # 将原列重命名为标准列名
        df[k] = df[v].astype(str)
# 只保留标准列
df = df[["content", "time", "location", "user_level", "likes", "username"]].copy()

# 清洗 content（去掉空白行）
df["content"] = df["content"].fillna("").astype(str)
df = df[df["content"].str.strip() != ""].reset_index(drop=True)

# 2. 解析时间列 -> hour, weekday
def parse_time(s: str):
    s = (s or "").strip()
    if not s:
        return {"hour": -1, "weekday": -1}
    formats = ["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
               "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S", "%m/%d/%Y %H:%M", "%Y/%m/%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return {"hour": dt.hour, "weekday": dt.weekday()}
        except Exception:
            continue
    # 解析失败尝试提取小时数字
    import re
    m = re.search(r"(\d{1,2}):\d{2}", s)
    if m:
        try:
            hour = int(m.group(1))
            return {"hour": hour, "weekday": -1}
        except:
            pass
    return {"hour": -1, "weekday": -1}

parsed = df["time"].apply(parse_time)
df["hour"] = parsed.apply(lambda x: x["hour"])
df["weekday"] = parsed.apply(lambda x: x["weekday"])

# 3. location 编码为 loc_id（类别编码），同时保存映射
df["location"] = df["location"].fillna("").replace("", "unknown")
unique_locs = df["location"].unique().tolist()
loc2id = {loc: idx for idx, loc in enumerate(unique_locs)}
df["loc_id"] = df["location"].map(loc2id).fillna(-1).astype(int)

# 保存 loc 映射
os.makedirs(os.path.dirname(LOC_MAP_PATH), exist_ok=True)
with open(LOC_MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(loc2id, f, ensure_ascii=False, indent=2)

# 4. user_level 数值化与归一化
def to_numeric(x):
    try:
        return float(x)
    except:
        # 可能是字符串里带非数字，尝试提取数字
        import re
        m = re.search(r"\d+", str(x))
        if m:
            return float(m.group())
        return 0.0

df["user_level_num"] = df["user_level"].apply(to_numeric)
# 标准化（z-score）
ul_mean = df["user_level_num"].mean()
ul_std = df["user_level_num"].std() if df["user_level_num"].std() > 0 else 1.0
df["user_level_norm"] = (df["user_level_num"] - ul_mean) / (ul_std + 1e-9)

# 5. likes -> 数值化 -> log1p -> 标准化
df["likes_num"] = df["likes"].apply(lambda x: pd.to_numeric(x, errors="coerce")).fillna(0.0)
df["likes_log1p"] = np.log1p(df["likes_num"].astype(float))
lk_mean = df["likes_log1p"].mean()
lk_std = df["likes_log1p"].std() if df["likes_log1p"].std() > 0 else 1.0
df["likes_norm"] = (df["likes_log1p"] - lk_mean) / (lk_std + 1e-9)

# 6. 构造 extra 列（list of floats）
def make_extra(row):
    return [float(row["hour"]), float(row["weekday"]), float(row["loc_id"]),
            float(row["user_level_norm"]), float(row["likes_norm"])]

df["extra"] = df.apply(make_extra, axis=1)

# 7. 划分 train / validation（因为无 label，做随机划分以便后续调参）
train_df, val_df = train_test_split(df, test_size=TEST_SIZE, random_state=RANDOM_STATE)
train_df = train_df.reset_index(drop=True)
val_df = val_df.reset_index(drop=True)

# 8. 转为 Hugging Face Dataset
ds_train = Dataset.from_pandas(train_df[["content", "extra", "username"]])
ds_val = Dataset.from_pandas(val_df[["content", "extra", "username"]])
ds = DatasetDict({"train": ds_train, "validation": ds_val})

# 9. tokenizer 批量化（batched=True），不做 padding（保留 list），保留 extra
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

def tokenize_fn(examples):
    # examples["content"] 是 list of strings
    out = tokenizer(examples["content"], truncation=True, max_length=MAX_LEN)
    # 把 extra 直接回传（datasets 会把 list of lists 保留）
    out["extra"] = examples["extra"]
    # 也保留 username 方便后续分析
    out["username"] = examples.get("username", [""] * len(examples["content"]))
    return out

# 移除原始不必要大列，保留 tokenization 产生的字段 + extra
remove_cols = list(ds["train"].column_names)  # columns from original (content, extra, username) will be removed and replaced
tokenized = ds.map(tokenize_fn, batched=True, remove_columns=remove_cols)

# 10. 保存到磁盘（Trainer 可直接 load_from_disk）
tokenized.save_to_disk(OUTPUT_DIR)
print("Processed dataset saved to:", OUTPUT_DIR)
print("Location->id map saved to:", LOC_MAP_PATH)
print("Sample columns in tokenized dataset:", tokenized["train"].column_names)