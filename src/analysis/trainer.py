# train_trainer.py
import os
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding
from sklearn.metrics import f1_score, accuracy_score

MODEL_ID = "hfl/chinese-roberta-wwm-ext"   # or "hfl/chinese-roberta-wwm-ext"
OUTPUT_DIR = "./trained_models"

# 超参（可按需调整）
NUM_LABELS = 8
BATCH = 16
EPOCHS = 4      #训练轮数
LR = 3e-5       #学习率

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

def preprocess_function(examples):
    return tokenizer(examples["content"], truncation=True)

# 加载 CSV（确保 CSV 有 content,label 列）
data_files = {"train":"data/processed/train.csv","validation":"data/processed/dev.csv"}
raw_datasets = load_dataset("csv", data_files=data_files)

# tokenization
tokenized = raw_datasets.map(preprocess_function, batched=True)
# 设置 format
tokenized = tokenized.map(lambda x: {"labels": x["label"]}, batched=True)
tokenized.set_format(type="torch", columns=["input_ids","token_type_ids","attention_mask","labels"])

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