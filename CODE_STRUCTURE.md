# Bilibili评论分析系统 - 代码结构文档

本文档详细说明了Bilibili评论分析项目的代码结构、模块功能和数据流程。

## 📁 项目概述

这是一个基于Python的Bilibili视频评论情感分析系统，使用深度学习模型（BERT）进行情感分类，并提供多维度的数据可视化。

## 🏗️ 整体架构

```
数据采集 → 数据预处理 → 情感分类 → 可视化展示
(Crawler) → (Preprocess) → (Model) → (Visualization)
```

## 📂 目录结构详解

### 1. 数据目录 (`data/`)

#### `data/raw/`
- **用途**: 存放原始数据
- **文件**: 
  - `sample_comments.csv` - 示例评论数据（140+条）
  - `comments.csv` - 爬虫获取的评论数据
  - `danmaku.csv` - 爬虫获取的弹幕数据

#### `data/processed/`
- **用途**: 存放预处理后的数据
- **文件**:
  - `comment_tokenized_dataset/` - HuggingFace格式的分词数据集
    - `train/` - 训练集（80%）
    - `validation/` - 验证集（20%）
  - `comment_loc2id.json` - 地域编码映射表

### 2. 源代码目录 (`src/`)

#### `src/analysis/` - 核心分析模块

##### `preprocess.py` - 数据预处理脚本
**功能**:
- 智能表头检测（跳过CSV元数据行）
- 数据清洗（去除空值、回复引用）
- 特征工程：
  - 时间特征（小时、星期）
  - 地域特征（地点编码）
  - 用户特征（等级、点赞数归一化）
- BERT分词（Tokenization）
- 生成HuggingFace Dataset格式

**使用方法**:
```bash
python src/analysis/preprocess.py --input data/raw/comments.csv --type comment
```

**参数**:
- `--input`: 输入CSV文件路径
- `--type`: 数据类型（comment/danmaku）
- `--model`: BERT模型ID（默认: bert-base-chinese）
- `--num_labels`: 情感分类数（默认: 8）

##### `model.py` - 模型推理接口
**功能**:
- 加载预训练BERT模型
- 对单条文本进行情感分类预测
- 返回情感代码（0-7）

**核心函数**:
```python
def predict(text: str) -> int:
    """
    预测文本的情感类别
    Returns: 情感代码 (0-7)
    """
```

##### `trainer.py` - 模型训练脚本
**功能**:
- 加载预处理数据集
- 使用HuggingFace Trainer训练BERT模型
- 支持多GPU训练
- 保存最佳模型

**使用方法**:
```bash
python src/analysis/trainer.py
```

**超参数**:
- 模型: `hfl/chinese-roberta-wwm-ext`
- 学习率: 3e-5
- Batch Size: 16
- Epochs: 4

#### `src/crawler/` - 数据爬虫模块

##### `main_crawler.py` - 爬虫主程序
**功能**:
- 从Bilibili视频页面爬取评论
- 从Bilibili弹幕API获取弹幕
- 支持Cookie认证
- 导出为CSV格式

**核心函数**:
```python
def check_cookie() -> bool:
    """检查Cookie有效性"""

def get_video_info(bv: str) -> dict:
    """获取视频信息（aid, cid）"""
```

##### `config.py` - 爬虫配置
**包含**:
- Cookie配置
- BV号列表
- 请求头设置

#### `src/utils/` - 工具模块

##### `emotion_mapper.py` - 情感映射工具
**定义**:
- 8类情感映射表（EMOTION_MAP）:
  - 0: 非常负面 (Very Negative) - 深红色
  - 1: 负面 (Negative) - 橙红色
  - 2: 略微负面 (Slightly Negative) - 浅橙色
  - 3: 中立 (Neutral) - 灰色
  - 4: 略微正面 (Slightly Positive) - 浅蓝色
  - 5: 正面 (Positive) - 蓝色
  - 6: 非常正面 (Very Positive) - 绿色
  - 7: 惊喜 (Surprise) - 紫色

**核心函数**:
```python
def get_emotion_label(emotion_code: int, use_zh: bool) -> str:
    """获取情感标签"""

def get_emotion_color(emotion_code: int) -> str:
    """获取情感对应颜色"""
```

##### `data_loader.py` - 数据加载工具
**功能**:
- 加载预处理数据集
- 添加情感标签
- 计算情感分布统计

**核心函数**:
```python
def load_dataset(data_type: str) -> pd.DataFrame:
    """加载数据集"""

def add_emotion_labels(df: pd.DataFrame) -> pd.DataFrame:
    """添加情感标签列"""
```

##### `time_series.py` - 时间序列分析工具
**功能**:
- 计算加权情感指数（-3到+3）
- 按时间聚合（日/周/月）
- 置信区间计算

**情感权重**:
```python
SENTIMENT_WEIGHTS = {
    0: -3.0,  # 非常负面
    1: -2.0,  # 负面
    2: -1.0,  # 略微负面
    3:  0.0,  # 中立
    4: +1.0,  # 略微正面
    5: +2.0,  # 正面
    6: +3.0,  # 非常正面
    7: +2.5,  # 惊喜
}
```

**核心函数**:
```python
def calculate_sentiment_index(emotion_codes: List[int]) -> float:
    """计算情感指数"""

def aggregate_by_time(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """按时间聚合"""
```

#### `src/visualization/` - 可视化模块

##### `distribution.py` - 情感分布可视化
**功能**:
- 绘制饼图展示情感占比
- 绘制柱状图展示情感数量
- 输出统计信息

**核心函数**:
```python
def plot_emotion_distribution(df: pd.DataFrame) -> tuple:
    """绘制情感分布图（饼图+柱状图）"""

def print_emotion_statistics(df: pd.DataFrame):
    """打印统计信息"""
```

##### `timeline.py` - 时间序列可视化
**功能**:
- 绘制情感时间序列趋势图
- 显示置信区间
- 平滑曲线拟合（样条插值）
- 双时间维度分析（评论时间/视频时间）

**核心函数**:
```python
def plot_comment_timeline(df: pd.DataFrame, freq: str) -> tuple:
    """绘制时间序列图"""
```

### 3. 演示脚本

#### `demo_emotion_distribution.py`
**用途**: 演示情感分布可视化
**输出**: `docs/images/emotion_distribution_pie_bar.png`

**运行方式**:
```bash
python demo_emotion_distribution.py
```

#### `demo_emotion_timeline.py`
**用途**: 演示时间序列分析
**功能**: 生成样本数据并展示情感随时间变化
**输出**: `docs/images/comment_timeline_weekly.png`

**运行方式**:
```bash
python demo_emotion_timeline.py
```

### 4. 文档目录 (`docs/`)

#### `docs/images/`
- 存放生成的可视化图表
- PNG格式，300 DPI高清输出

### 5. Jupyter Notebooks (`notebooks/`)

#### `explorative_analysis.ipynb`
- 探索性数据分析
- 交互式数据展示
- 模型实验

## 🔄 完整数据流程

### 阶段1: 数据采集
```
爬虫 (src/crawler/main_crawler.py)
  ↓
原始CSV (data/raw/comments.csv)
  - 字段: content, username, time, ip_location, user_level, likes
```

### 阶段2: 数据预处理
```
预处理 (src/analysis/preprocess.py)
  ↓
1. 表头检测 & 列名标准化
2. 数据清洗（去空值、去回复引用）
3. 特征工程
   - 时间特征: hour, weekday
   - 地域特征: location → loc_id
   - 用户特征: user_level_norm, likes_norm
4. BERT分词
  ↓
HF Dataset (data/processed/comment_tokenized_dataset/)
  - train/: input_ids, attention_mask, labels, extra
  - validation/: 同上
```

### 阶段3: 模型训练（可选）
```
训练 (src/analysis/trainer.py)
  ↓
模型参数保存 (trained_models/)
  - pytorch_model.bin
  - config.json
  - tokenizer files
```

### 阶段4: 情感推理
```
推理 (src/analysis/model.py)
  ↓
带标签CSV (data/processed/comments_with_emotions.csv)
  - 字段: 原字段 + emotion_code + emotion_label
```

### 阶段5: 可视化分析
```
可视化 (src/visualization/)
  ↓
图表输出 (docs/images/)
  - emotion_distribution_pie_bar.png
  - comment_timeline_weekly.png
```

## 🎯 数据格式规范

### 输入格式 (原始CSV)

#### 评论数据
```csv
content,username,time,ip_location,user_level,likes
我永远喜欢有地绫！,橘文乃,2024-07-29 19:47:19,江苏,5,4003
```

#### 弹幕数据
```csv
danmaku_id,user_hash,content,real_time,video_time
1,user_abc123,弹幕内容,2024-11-20 21:56:54,01:23:45
```

### 输出格式 (带情感标签)

```csv
content,username,time,ip_location,user_level,likes,emotion_code,emotion_label
我永远喜欢有地绫！,橘文乃,2024-07-29 19:47:19,江苏,5,4003,6,非常正面
```

## 📊 情感分类体系

### 8类情感分类
| 代码 | 英文标签 | 中文标签 | 权重 | 颜色 |
|------|---------|---------|------|------|
| 0 | Very Negative | 非常负面 | -3.0 | #d62728 |
| 1 | Negative | 负面 | -2.0 | #ff7f0e |
| 2 | Slightly Negative | 略微负面 | -1.0 | #ffbb78 |
| 3 | Neutral | 中立 | 0.0 | #7f7f7f |
| 4 | Slightly Positive | 略微正面 | +1.0 | #aec7e8 |
| 5 | Positive | 正面 | +2.0 | #1f77b4 |
| 6 | Very Positive | 非常正面 | +3.0 | #2ca02c |
| 7 | Surprise | 惊喜 | +2.5 | #9467bd |

## 🛠️ 依赖库

### 核心依赖 (requirements.txt)
```
torch                # 深度学习框架
transformers         # BERT模型
datasets            # HuggingFace数据集
pandas              # 数据处理
matplotlib          # 可视化
scikit-learn        # 机器学习工具
```

### 可选依赖
```
scipy               # 科学计算（样条插值）
numpy               # 数值计算
requests            # HTTP请求（爬虫）
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 数据预处理
```bash
python src/analysis/preprocess.py
```

### 3. 运行可视化演示
```bash
# Note: Run from the project root directory
cd /path/to/Bilibili-Comment-Analysis
python demo_emotion_distribution.py
python demo_emotion_timeline.py
```

### 4. 查看结果
```bash
ls docs/images/
```

## 📝 注意事项

### 当前已知问题
1. **随机标签问题**: 原始数据没有情感标签，预处理时使用随机标签
   - 解决方案A: 使用预训练模型推理
   - 解决方案B: 手动标注部分数据后训练模型

2. **时间跨度问题**: 示例数据集时间跨度较小
   - demo_emotion_timeline.py 生成模拟数据用于演示

3. **模型未训练**: trainer.py 存在但模型未训练
   - 需要标注数据后才能训练

### 开发建议
1. 先使用demo脚本熟悉系统功能
2. 获取真实数据后运行完整流程
3. 根据需求调整情感分类数量
4. 扩展可视化维度（地域、用户等级等）

## 📚 相关文档
- `README.md` - 项目说明
- `DATA_FLOW_ANALYSIS.md` - 数据流分析
- `CODE_STRUCTURE.md` - 本文档

## 🔍 代码质量

### 代码特点
- ✅ 模块化设计
- ✅ 清晰的函数注释
- ✅ 类型提示（部分）
- ✅ 错误处理
- ✅ 配置分离
- ✅ 路径自适应

### 改进空间
- 添加单元测试
- 添加类型注解完整性
- 添加日志系统
- 添加配置文件（YAML/JSON）
- 添加命令行工具（CLI）

---

**文档版本**: v1.0  
**最后更新**: 2024-12-07  
**维护者**: Bilibili Comment Analysis Team
