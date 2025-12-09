import os
import sys
import torch
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import get_emotion_label

def main():
    # 1. 配置路径
    MODEL_PATH = PROJECT_ROOT / "trained_models"
    
    # 尝试自动查找输入文件
    raw_dir = PROJECT_ROOT / "data" / "raw"
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ 在 {raw_dir} 中未找到任何 CSV 文件")
        return
        
    # 默认使用第一个找到的 CSV 文件，或者您可以手动指定
    INPUT_FILE = csv_files[0]
    print(f"📄 使用输入文件: {INPUT_FILE.name}")
    
    OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / f"{INPUT_FILE.stem}_predicted.csv"

    # 检查模型是否存在
    if not MODEL_PATH.exists():
        print(f"❌ 未找到训练好的模型: {MODEL_PATH}")
        print("请先运行 src/analysis/trainer.py 进行训练，或将模型文件放入 trained_models 文件夹。")
        return

    # 检查输入文件
    if not INPUT_FILE.exists():
        print(f"❌ 未找到输入文件: {INPUT_FILE}")
        return

    # 2. 加载模型和分词器
    print(f"🚀 正在加载模型: {MODEL_PATH} ...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"💻 使用设备: {device}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        return

    # 3. 加载数据
    print(f"📂 读取数据: {INPUT_FILE} ...")
    # 自动检测表头，这里假设第一行是表头，如果不是请根据实际情况调整
    df = pd.read_csv(INPUT_FILE)
    
    # 确保有 content 列
    if 'content' not in df.columns:
        print("❌ CSV 文件中缺少 'content' 列，无法进行预测。")
        print(f"当前列名: {df.columns.tolist()}")
        return

    print(f"✅ 加载了 {len(df)} 条评论")

    # 4. 定义预测函数
    def predict_batch(texts, batch_size=32):
        model.eval()
        all_preds = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="预测中"):
            batch_texts = texts[i : i + batch_size]
            # 处理非字符串数据
            batch_texts = [str(t) if pd.notna(t) else "" for t in batch_texts]
            
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

    # 5. 执行预测
    print("🔮 开始批量预测...")
    # 批量预测以提高速度
    predictions = predict_batch(df['content'].tolist(), batch_size=32)

    # 6. 添加结果到 DataFrame
    df['predicted_label_id'] = predictions
    df['predicted_emotion'] = df['predicted_label_id'].apply(lambda x: get_emotion_label(x, use_zh=True))

    # 7. 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 预测完成！结果已保存至: {OUTPUT_FILE}")
    print("\n👀 预览前 5 条结果:")
    print(df[['content', 'predicted_emotion']].head())

if __name__ == "__main__":
    main()
