import sys
import os
from pathlib import Path
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
import numpy as np
import re

# Add project root to sys.path
# This file is in src/analysis/, so PROJECT_ROOT is ../../
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.utils import get_emotion_label

def run_prediction_pipeline(input_path=None, output_path=None, model_path=None, model=None, tokenizer=None):
    """
    运行预测流水线：读取数据 -> 加载模型 -> 预测 -> 保存结果 -> 返回 DataFrame
    
    Args:
        input_path: 输入 CSV 路径
        output_path: 输出 CSV 路径
        model_path: 模型路径 (可选)
        model: 预加载的模型对象 (可选，推荐)
        tokenizer: 预加载的分词器对象 (可选，推荐)
    """
    # 1. 路径处理
    if input_path is None:
        input_path = PROJECT_ROOT / "data" / "raw" / "comments.csv"
    else:
        input_path = Path(input_path)
        
    if output_path is None:
        # 默认输出路径，根据输入文件名自动生成
        output_path = PROJECT_ROOT / "data" / "processed" / f"{input_path.stem}_predicted.csv"
    else:
        output_path = Path(output_path)

    # 2. 模型加载逻辑
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"💻 Using device: {device}")

    # 如果没有传入预加载的模型，则尝试加载
    if model is None or tokenizer is None:
        # 尝试从 src.analysis.model 导入 (如果未指定 model_path)
        if model_path is None:
            try:
                print("🚀 Loading model from src.analysis.model configuration...")
                from src.analysis.model import model as loaded_model, tokenizer as loaded_tokenizer
                model = loaded_model
                tokenizer = loaded_tokenizer
            except Exception as e:
                print(f"⚠️ Failed to import from src.analysis.model: {e}")
        
        # 如果导入失败或指定了 model_path，则手动加载
        if model is None:
            if model_path is None:
                LOCAL_MODEL_DIR = PROJECT_ROOT / "trained_models"
                HF_MODEL_ID = "ScarletShinku/bilibili-sentiment-bert"
                
                if LOCAL_MODEL_DIR.exists():
                    model_path = LOCAL_MODEL_DIR
                else:
                    model_path = HF_MODEL_ID
            
            print(f"🚀 Loading model from: {model_path}")
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                return None
    
    # 确保模型在正确的设备上
    model = model.to(device)

    # 3. 读取数据
    print(f"📖 Reading data from {input_path}...")
    try:
        # 尝试读取，跳过可能的坏行
        # 自动检测表头：如果第一行看起来不像表头（比如是注释），尝试跳过
        header_row = 0
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    header_row = i
                    break
        
        df = pd.read_csv(input_path, skiprows=header_row, encoding='utf-8-sig', on_bad_lines='skip')
        
        # 统一列名：确保有 'content' 列
        if 'content' not in df.columns:
            if 'message' in df.columns:
                df['content'] = df['message']
            elif 'text' in df.columns:
                df['content'] = df['text']
            
        if 'content' not in df.columns:
            print("❌ 'content' column not found in CSV.")
            print(f"Columns found: {df.columns.tolist()}")
            return None
            
        # 数据清洗
        df['content'] = df['content'].fillna("").astype(str)
        # 移除空白内容
        df = df[df['content'].str.strip() != ""]
        # 移除 "回复 @xxx :" 或 "@xxx :" (兼容不同格式)
        # 正则解释: ^(?:回复\s*)? 匹配开头可选的"回复"和空格
        # @.*? 匹配 @用户名 (非贪婪)
        # [：:]\s* 匹配中英文冒号和后续空格
        df["content"] = df["content"].apply(lambda x: re.sub(r'^(?:回复\s*)?@.*?[：:]\s*', '', x).strip())
        df = df[df["content"] != ""]
        
        print(f"📊 Total items to analyze: {len(df)}")
        
    except Exception as e:
        print(f"❌ Failed to read data: {e}")
        return None

    # 4. 执行预测
    print("🔮 Running inference...")
    batch_size = 32
    predictions = []
    
    model.eval()
    
    # 批量预测
    texts = df['content'].tolist()
    for i in tqdm(range(0, len(texts), batch_size), desc="Predicting"):
        batch_texts = texts[i : i + batch_size]
        
        inputs = tokenizer(
            batch_texts, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=128
        ).to(device)
        
        with torch.no_grad():
            logits = model(**inputs).logits
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            predictions.extend(preds)
            
    df['predicted_label_id'] = predictions
    # 获取中文情感标签
    df['predicted_emotion'] = df['predicted_label_id'].apply(lambda x: get_emotion_label(x, use_zh=True))
    
    # 兼容旧代码，可能需要 'labels' 列
    df['labels'] = predictions

    # 5. 保存结果
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving predictions to {output_path}")
    # 使用 mode='w' 覆盖写入
    df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='w')
    
    return df

def main():
    """
    CLI 入口函数
    """
    print("========================================")
    print("   Bilibili 情感分析 - 交互式预测工具")
    print("========================================")
    print("请选择要预测的数据类型:")
    print("1. comments (评论)")
    print("2. danmaku (弹幕)")
    
    while True:
        choice = input("请输入您的选择 (输入 comments 或 danmaku): ").strip().lower()
        
        if choice in ['1', 'comments', 'comment']:
            data_type = 'comment'
            break
        elif choice in ['2', 'danmaku']:
            data_type = 'danmaku'
            break
        else:
            print("❌ 输入无效，请输入 'comments' 或 'danmaku'")

    # 配置路径
    RAW_DIR = PROJECT_ROOT / "data" / "raw"
    PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
    
    if data_type == "comment":
        INPUT_FILE = RAW_DIR / "comments.csv"
        OUTPUT_FILE = PROCESSED_DIR / "comments_predicted.csv"
    else:
        INPUT_FILE = RAW_DIR / "danmaku.csv"
        OUTPUT_FILE = PROCESSED_DIR / "danmaku_predicted.csv"

    # 检查输入文件
    if not INPUT_FILE.exists():
        print(f"❌ 没有找到对应文件: {INPUT_FILE}")
        print("请先运行爬虫进行爬取")
        return

    # 调用流水线函数
    df = run_prediction_pipeline(input_path=INPUT_FILE, output_path=OUTPUT_FILE)
    
    if df is not None:
        print(f"✅ 预测完成！结果已保存至: {OUTPUT_FILE}")
        print("👀 预览前 5 条结果:")
        print(df[['content', 'predicted_emotion']].head())

if __name__ == "__main__":
    main()

