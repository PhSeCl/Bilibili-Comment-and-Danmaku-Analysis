# train_trainer.py
import os
import numpy as np
from pathlib import Path
from datasets import load_from_disk
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding, EarlyStoppingCallback
from sklearn.metrics import f1_score, accuracy_score, classification_report
import torch
from torch import nn

# 自动找到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MODEL_ID = "hfl/chinese-roberta-wwm-ext"
OUTPUT_DIR = str(PROJECT_ROOT / "trained_models")

# 超参（可按需调整）
NUM_LABELS = 8
BATCH = 32      # RTX 4060 + FP16 显存充足，由 16 提升到 32，训练更快
EPOCHS = 15     # 增加轮数，因为加权训练通常需要更久收敛
LR = 2e-5       # 微调常用 2e-5 到 5e-5，这里选 2e-5 比较稳健
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

# === 计算类别权重 ===
# 统计训练集中各标签的数量
train_labels = tokenized["train"]["labels"]
label_counts = np.bincount(train_labels, minlength=NUM_LABELS)
total_samples = len(train_labels)

print(f"📊 标签分布: {label_counts}")

# 计算权重: total / (num_classes * count)
# 加上一个小 epsilon 防止除以零
raw_weights = total_samples / (NUM_LABELS * (label_counts + 1))

# 【优化】对权重开根号，进行平滑处理
# 原始权重差异太大（0.3 到 20），容易矫枉过正。开根号后差异变小（0.5 到 4.5），更温和。
class_weights = np.sqrt(raw_weights)

# 【手动干预】
# 目标：让预测分布更接近正态分布（中间高，两头低），并减少对正面的过度偏好
# 0:非常负面, 1:负面, 2:略微负面, 3:中立, 4:略微正面, 5:正面, 6:非常正面, 7:惊喜

# 1. 稍微提高中立(3)和微负(2)、微正(4)的权重，鼓励模型往中间靠
class_weights[2] *= 1.2
class_weights[3] *= 1.3
class_weights[4] *= 1.2

# 2. 降低极端情感(0, 1, 6, 7)的权重，避免模型太激进
class_weights[0] *= 0.8
class_weights[1] *= 0.9
class_weights[6] *= 0.9
class_weights[7] *= 0.9

# 3. 关键：降低正面(5)的权重
# 之前是 * 1.5，导致模型疯狂预测正面。现在改为 * 0.8，抑制其倾向。
class_weights[5] *= 0.8

# 转为 Tensor 并移到 GPU (如果可用)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

print(f"⚖️  类别权重: {class_weights.cpu().numpy()}")

# === 自定义 Trainer 以支持加权 Loss ===
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.get("labels")
        # forward pass
        outputs = model(**inputs)
        logits = outputs.get("logits")
        # compute custom loss (CrossEntropy with weights)
        loss_fct = nn.CrossEntropyLoss(weight=class_weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=NUM_LABELS)

data_collator = DataCollatorWithPadding(tokenizer)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    
    # 打印详细的分类报告 (仅在主进程打印)
    if trainer.is_world_process_zero():
        print("\n" + "="*30)
        print("📊 Classification Report:")
        print(classification_report(labels, preds, digits=4))
        print("="*30 + "\n")
        
    return {
        "accuracy": accuracy_score(labels, preds),
        "macro_f1": f1_score(labels, preds, average="macro")
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=LR,
    per_device_train_batch_size=BATCH,
    per_device_eval_batch_size=BATCH*2,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    greater_is_better=True,
    fp16=True,  # 若 GPU 支持可改为 True
    logging_steps=10,       # 每10步打印一次日志，实时监控训练状态
    save_total_limit=2,     # 只保留最近/最好的2个模型检查点，防止硬盘爆满
    label_smoothing_factor=0.1, # 【新增】标签平滑，防止模型过度自信，有助于生成更平滑的分布
    load_best_model_at_end=True, # 必须开启，配合 EarlyStopping
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)] # 【新增】早停机制，如果验证集指标3个epoch不提升则停止
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)