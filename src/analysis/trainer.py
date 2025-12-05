# train_trainer.py
import os
import numpy as np
from pathlib import Path
from datasets import load_from_disk
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding
from sklearn.metrics import f1_score, accuracy_score

# 自动找到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MODEL_ID = "hfl/chinese-roberta-wwm-ext"
OUTPUT_DIR = str(PROJECT_ROOT / "trained_models")

# 超参（可按需调整）
NUM_LABELS = 8
BATCH = 16
EPOCHS = 4      #训练轮数
LR = 3e-5       #学习率
DATA_TYPE = "comment"  # 对应 preprocess.py 生成的数据集名称

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# 直接加载 preprocess.py 生成的数据集
dataset_path = DATA_PROCESSED_DIR / f"{DATA_TYPE}_tokenized_dataset"
print(f"📁 加载数据集: {dataset_path}")

if not dataset_path.exists():
    print(f"❌ 数据集不存在: {dataset_path}")
    print(f"请先运行: python src/analysis/preprocess.py")
    exit(1)

tokenized = load_from_disk(str(dataset_path))

model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=NUM_LABELS)

data_collator = DataCollatorWithPadding(tokenizer)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "macro_f1": f1_score(labels, preds, average="macro")
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=LR,
    per_device_train_batch_size=BATCH,
    per_device_eval_batch_size=BATCH*2,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    greater_is_better=True,
    fp16=False  # 若 GPU 支持可改为 True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)