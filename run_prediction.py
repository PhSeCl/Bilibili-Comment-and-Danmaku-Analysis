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
# Since this file is in the root, PROJECT_ROOT is just the current directory
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Try importing visualization module
try:
    from src.visualization.distribution import plot_emotion_distribution, print_emotion_statistics
except ImportError:
    # If relative import fails, we might need to help python find the modules
    sys.path.append(str(PROJECT_ROOT / "src"))
    try:
        from visualization.distribution import plot_emotion_distribution, print_emotion_statistics
    except ImportError:
        print("⚠️ Could not import visualization modules. Please ensure src is a package.")
        sys.exit(1)

def run_prediction_pipeline(input_path=None, output_path=None, model_path=None):
    """
    运行预测流水线：读取数据 -> 加载模型 -> 预测 -> 保存结果 -> 返回 DataFrame
    """
    # Paths
    if input_path is None:
        input_path = PROJECT_ROOT / "data" / "raw" / "comments.csv"
    else:
        input_path = Path(input_path)
        
    if output_path is None:
        output_path = PROJECT_ROOT / "data" / "processed" / "comments_with_predictions.csv"
    else:
        output_path = Path(output_path)

    # Model Path Logic
    if model_path is None:
        LOCAL_MODEL_DIR = PROJECT_ROOT / "trained_models"
        HF_MODEL_ID = "ScarletShinku/bilibili-sentiment-bert"
        
        if LOCAL_MODEL_DIR.exists():
            model_path = LOCAL_MODEL_DIR
            print(f"🚀 Loading model from local directory: {model_path}")
        else:
            model_path = HF_MODEL_ID
            print(f"🚀 Loading model from Hugging Face: {model_path}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None

    print(f"📖 Reading data from {input_path}...")
    try:
        # Try to find the header row if it's not the first one (like in preprocess.py)
        header_row = 0
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    header_row = i
                    break
        
        df = pd.read_csv(input_path, skiprows=header_row)
        
        # Check for content column
        if 'content' not in df.columns and 'message' in df.columns:
             df['content'] = df['message']
             
        if 'content' not in df.columns:
            print("❌ 'content' column not found in CSV.")
            print(f"Columns found: {df.columns.tolist()}")
            return None
            
        # Clean data
        df['content'] = df['content'].fillna("").astype(str)
        df = df[df['content'].str.strip() != ""]
        
        # Remove "回复 @xxx :"
        df["content"] = df["content"].apply(lambda x: re.sub(r'^回复 @.*? :', '', x).strip())
        df = df[df["content"] != ""]
        
        print(f"📊 Total comments to analyze: {len(df)}")
        
    except Exception as e:
        print(f"❌ Failed to read data: {e}")
        return None

    # Inference
    print("🔮 Running inference...")
    batch_size = 32
    predictions = []
    
    model.eval()
    
    # Process in batches
    for i in tqdm(range(0, len(df), batch_size)):
        batch_texts = df['content'].iloc[i:i+batch_size].tolist()
        
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
        
        with torch.no_grad():
            logits = model(**inputs).logits
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            predictions.extend(preds)
            
    df['labels'] = predictions
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saved predictions to {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    return df

def main():
    df = run_prediction_pipeline()
    
    if df is not None:
        # Visualization
        print("🎨 Generating visualization...")
        try:
            plot_emotion_distribution(df, save_path=PROJECT_ROOT / "docs" / "images" / "emotion_distribution_pie_bar.png")
            print_emotion_statistics(df)
        except Exception as e:
            print(f"⚠️ Visualization failed: {e}")

if __name__ == "__main__":
    main()
