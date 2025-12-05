# 当前数据流与存储分析

## 📊 完整的数据流向

```
1. 原始数据
   └─ data/raw/comments.csv (140条爬虫数据)
      ├─ rpid, username, level, content, likes, location, date
      └─ 【无标签】

2. 数据预处理 (preprocess.py)
   └─ 输入：data/raw/comments.csv
   └─ 处理：
      ├─ 智能表头检测（跳过元数据）
      ├─ 列名标准化
      ├─ 数据清洗（去空值、去回复引用）
      ├─ 特征工程（时间、地点、用户等级、点赞数）
      ├─ Tokenize（使用 BERT 分词器）
      └─ 生成 HF Dataset 格式
   └─ 输出：
      ├─ data/processed/comment_tokenized_dataset/
      │  ├─ train/ (112条)
      │  │  ├─ input_ids
      │  │  ├─ token_type_ids
      │  │  ├─ attention_mask
      │  │  ├─ labels (★ 随机生成的标签)
      │  │  └─ extra (时间、地点、用户特征向量)
      │  └─ validation/ (28条)
      └─ data/processed/comment_loc2id.json (地点映射表)

3. 模型推理（当前还未实现）
   ├─ model.py 中定义了推理函数
   ├─ 但还没有真正的情感分类输出
   └─ 需要完整的模型训练才能生成真实的情感标签

4. 当前可视化 (demo_emotion_distribution.py)
   ├─ 输入：data/processed/comment_tokenized_dataset/
   ├─ 使用的数据：labels 列（★ 随机标签）
   ├─ 处理：
   │  ├─ 加载 train + validation 数据
   │  ├─ 计算 labels 分布
   │  ├─ 映射为情感标签
   │  └─ 绘制图表
   └─ 输出：docs/images/emotion_distribution_pie_bar.png
```

---

## 🔍 当前的问题与解决方案

### ❌ 问题 1：标签是随机生成的

**现象：**
- preprocess.py 在找不到 label 列时，使用 `np.random.randint(0, 8, len(df))` 生成随机标签
- 这导致可视化的数据没有实际意义

**流程：**
```
原始数据 (无标签)
  ↓
预处理 ① 检查 label 列 ✓ 不存在
  ↓
② 随机生成 labels = [3, 5, 1, 7, ...]
  ↓
③ 保存到 HF Dataset
  ↓
可视化基于这些随机标签
```

**当前现状：**
- ✅ 可视化代码本身**完全正确**
- ❌ 但展示的数据没有**真实意义**（只是随机分布）

---

## 🎯 应该如何改进

### 方案 A：使用真实的模型推理（推荐）

```
原始数据 (无标签)
  ↓
① 数据预处理 (preprocess.py)
   └─ 输出：tokenized_dataset （暂时 labels 留空或设为 -1）
  ↓
② 模型推理 (model.py 的 predict 函数)
   ├─ 加载预训练的 BERT 模型
   ├─ 对每条评论进行推理
   └─ 得到 emotion_code (0-7)
  ↓
③ 生成带标签的数据
   ├─ CSV 格式：content + emotion_code + emotion_label
   └─ 保存到：data/processed/comments_with_emotions.csv
  ↓
④ 可视化（从 CSV 加载数据）
   └─ 输出：emotion_distribution_pie_bar.png
```

### 方案 B：手动标注小样本

```
原始数据 (140 条)
  ↓
①  人工标注 30-50 条
   └─ 生成：data/raw/labeled_comments.csv
  ↓
② 用这部分数据训练模型 (trainer.py)
  ↓
③ 用训练好的模型推理全部数据
  ↓
④ 可视化分析
```

---

## 📁 当前数据存储位置详细说明

| 步骤 | 文件位置 | 内容 | 用途 |
|------|---------|------|------|
| 1 | `data/raw/comments.csv` | 原始爬虫数据（无标签） | 源数据 |
| 2 | `data/processed/comment_tokenized_dataset/` | HF Dataset 格式（包含随机 labels） | 模型训练用 |
| 3 | `data/processed/comment_loc2id.json` | 地点编码映射表 | 特征解码 |
| 4 | `docs/images/emotion_distribution_pie_bar.png` | 情感分布图表 | 可视化展示 |
| ❌ 缺失 | `data/processed/comments_with_emotions.csv` | 带情感标签的评论（应该有但没有） | 后续分析基础 |

---

## 🔧 需要你做的决定

**请选择一个方案：**

### 方案 A：快速方案（推荐新手）
使用已有的开源情感分析模型（如 HuggingFace 的预训练模型），快速对 140 条评论进行分类，输出带标签的 CSV 文件。
- ✅ 速度快（几秒钟）
- ✅ 无需训练
- ❌ 可能不够准确（因为是通用模型）

### 方案 B：完整方案（推荐）
1. 先手动标注 30-50 条评论
2. 用 trainer.py 微调 BERT 模型
3. 用微调后的模型推理所有数据
4. 输出带准确标签的 CSV 文件
- ✅ 更准确
- ✅ 学习价值高
- ❌ 需要标注时间

### 方案 C：演示方案
继续使用当前的随机标签进行可视化演示，但明确标注"演示数据"
- ✅ 最快
- ❌ 没有实际意义

---

## 💡 我的建议

1. **短期**（本周）：
   - 使用方案 A 快速生成带标签的数据
   - 完成剩余的可视化模块（时间序列、地域分析）
   - 这样整个项目框架就完成了

2. **中期**（下周）：
   - 如果有时间，手动标注 30-50 条数据（方案 B）
   - 重新训练和推理
   - 替换数据并更新图表

3. **长期**（后续）：
   - 持续改进模型
   - 收集更多标注数据

---

你倾向于哪个方案？我可以立即帮你实现！
