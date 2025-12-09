import sys
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import get_emotion_label

def main():
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

    # 1. 配置路径
    RAW_DIR = PROJECT_ROOT / "data" / "raw"
    PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
    
    # 根据类型选择输入文件
    if data_type == "comment":
        INPUT_FILE = RAW_DIR / "comments.csv"
        OUTPUT_FILE = PROCESSED_DIR / "comments_predicted.csv"
    else:
        INPUT_FILE = RAW_DIR / "danmaku.csv"
        OUTPUT_FILE = PROCESSED_DIR / "danmaku_predicted.csv"

    # 2. 检查输入文件是否存在
    if not INPUT_FILE.exists():
        print(f"❌ 没有找到对应文件: {INPUT_FILE}")
        print("请先运行爬虫进行爬取")
        return

    # 3. 加载模型 (从 model.py 导入)
    print("🚀 正在加载模型 (来自 src.analysis.model)...")
    try:
        # 动态导入，以便在用户选择后再加载模型
        from src.analysis.model import model, tokenizer, device
        print(f"💻 使用设备: {device}")
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        print("请检查 src/analysis/model.py 中的配置，或确保模型文件存在。")
        return

    # 4. 加载数据
    print(f"📂 读取数据: {INPUT_FILE} ...")
    try:
        # 使用 utf-8-sig 读取，跳过格式错误的行
        df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig', on_bad_lines='skip')
    except Exception as e:
        print(f"❌ 读取 CSV 文件失败: {e}")
        return
    
    # 确保有 content 列
    if 'content' not in df.columns:
        print("❌ CSV 文件中缺少 'content' 列，无法进行预测。")
        return

    print(f"✅ 加载了 {len(df)} 条数据")

    # 5. 定义批量预测函数
    def predict_batch(texts, batch_size=32):
        model.eval()
        all_preds = []
        
        # 处理空值
        texts = [str(t) if pd.notna(t) else "" for t in texts]
        
        for i in tqdm(range(0, len(texts), batch_size), desc="预测进度"):
            batch_texts = texts[i : i + batch_size]
            
            inputs = tokenizer(
                batch_texts, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=128
            ).to(device)

            with torch.no_grad():
                logits = model(**inputs).logits
            
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            
        return all_preds

    # 6. 执行预测
    print("🔮 开始预测...")
    predictions = predict_batch(df['content'].tolist(), batch_size=32)

    # 7. 添加结果到 DataFrame
    df['predicted_label_id'] = predictions
    df['predicted_emotion'] = df['predicted_label_id'].apply(lambda x: get_emotion_label(x, use_zh=True))

    # 8. 保存结果
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # 显式指定 mode='w' 以覆盖旧文件
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig', mode='w')
    
    print(f"\n✅ 预测完成！结果已保存至: {OUTPUT_FILE}")
    print("\n👀 预览前 5 条结果:")
    print(df[['content', 'predicted_emotion']].head())

if __name__ == "__main__":
    main()
