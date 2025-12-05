# 中山大学人工智能学院数据分析实践大作业

本项目是中山大学人工智能学院数据分析实践课程的大作业，该项目的内容是基于提供的数据集进行数据分析和可视化展示。

## 📂 项目结构

```text
Bilibili-Emotion-Analysis/ (根目录)
├── data/                      # 存放数据文件
│   ├── raw/                   # 原始数据 (爬下来的CSV，未清洗)
│   ├── processed/             # 清洗后的数据 (去重、去空值后)
│   └── sample.csv             # 少量样本数据 (供队友测试代码用)
│
├── src/                       # 源代码 (Source Code)
│   ├── crawler/               # 爬虫模块
│   │   ├── main_crawler.py    # 爬虫主程序
│   │   └── config.py          # 爬虫配置 (注意不要上传自己的Cookie!)
│   │
│   ├── analysis/              # 分析模块
│   │   ├── clean_data.py      # 数据清洗脚本
│   │   └── emotion_model.py   # 情感分析逻辑 (调用API或模型)
│   │
│   └── visualization/         # 可视化模块
│       ├── plot_pie.py        # 画饼图的代码
│       └── word_cloud.py      # (可选) 画词云的代码
│
├── notebooks/                 # Jupyter Notebook (草稿本)
│   ├── explorative_analysis.ipynb  # 队友用于尝试性分析的笔记
│   └── demo_visualization.ipynb    # 画图的测试笔记
│
├── docs/                      # 文档与报告
│   ├── final_report.pdf       # 最终提交给老师的作业报告
│   ├── presentation.pptx      # 答辩PPT
│   └── images/                # 存放生成的图片 (用于插入README或报告)
│
├── .gitignore                 # 忽略文件列表 (非常重要！)
├── README.md                  # 项目说明书 (门面)
└── requirements.txt           # 依赖包列表 (环境配置)
```

---

## 📊 功能与可视化架构

### 核心工作流

```
原始评论/弹幕数据 
  → 数据预处理 
  → 情感分类 
  → 多维度可视化
```

### 数据输出格式规范

#### 评论数据输出格式
```csv
rpid,username,level,content,likes,location,date,emotion_code,emotion_label
247633504176,拉普兰德不孤独,6,我是骑士吗？,1244,广东,2024-11-20 21:56:54,2,positive
```

| 字段 | 说明 | 数据类型 | 备注 |
|------|------|---------|------|
| `rpid` | 评论 ID | int | 原始数据 |
| `username` | 用户名 | str | 原始数据 |
| `level` | 用户等级 | int | 原始数据 |
| `content` | 评论内容 | str | 原始数据 |
| `likes` | 点赞数 | int | 原始数据 |
| `location` | 地域 IP | str | 原始数据 |
| `date` | 发布时间 | datetime | 原始数据 |
| `emotion_code` | 情感代码 | int | **新增** 0-7（8分类） |
| `emotion_label` | 情感标签 | str | **新增** positive/neutral/negative 等 |

#### 弹幕数据输出格式
```csv
danmaku_id,user_hash,content,real_time,video_time,emotion_code,emotion_label
1,user_abc123,弹幕内容,2024-11-20 21:56:54,01:23:45,3,neutral
```

| 字段 | 说明 | 数据类型 | 备注 |
|------|------|---------|------|
| `danmaku_id` | 弹幕 ID | int | 原始数据 |
| `user_hash` | 用户 Hash | str | 原始数据 |
| `content` | 弹幕内容 | str | 原始数据 |
| `real_time` | 发布现实时间 | datetime | 原始数据（可分析视频背景） |
| `video_time` | 视频播放时间 | str (HH:MM:SS) | 原始数据（可分析视频内容） |
| `emotion_code` | 情感代码 | int | **新增** 0-7（8分类） |
| `emotion_label` | 情感标签 | str | **新增** positive/neutral/negative 等 |

---

### 可视化模块设计

#### 模块1：总体情感分布

**方案 A：雷达图（Radar Chart）**
- 展示多个情感维度（正面/中立/负面/惊喜/失望等）
- 工具：`matplotlib` 或 `plotly`
- 优势：可展示多维度数据，综合性强

**方案 B：饼图 + 柱状图组合**
- 左侧：饼图展示占比
- 右侧：柱状图展示绝对数量
- 工具：`matplotlib`、`plotly`
- 优势：直观易理解

**方案 C：词云图（Word Cloud）**
- 正面评论用绿色、大字体
- 中立评论用灰色、中等字体
- 负面评论用红色、小字体
- 工具：`wordcloud` 库
- 优势：视觉冲击强，适合报告展示

---

#### 模块2：时间序列情感变化

**评论的实时时间维度**
```
Y轴：评论数量
X轴：发布日期
颜色：不同情感

可视化方案：堆积面积图 / 堆积柱状图 / 折线图
时间粒度：日级 / 周级 / 月级
```

**弹幕的双时间维度**

维度A：现实时间（实时背景分析）
- 分析视频发布后不同时间段的舆论变化
- 例如：热点事件突发 → 评论/弹幕情感变化

维度B：视频时间（内容相关性分析）
- 分析视频不同内容段落的观众情感反应
- 例如：高潮部分 → 正面情感增多

可视化方案：
- 上图：随现实时间推移的情感变化（刻画外部事件影响）
- 下图：随视频进度推移的情感变化（刻画内容影响）
- 对比视图：两个时间维度并排展示

---

#### 模块3：地域情感特征分布

**方案 A：热力图（Heatmap）**
- 创建地域-情感的热力图
- 直观展示地域差异
- 适用：10-30 个地域

**方案 B：地图可视化（Geo Map）**
- 使用 folium 绘制中国地图
- 不同省份用不同颜色表示主要情感
- 圆形大小表示评论数量
- 优势：地理直观，交互性强

**方案 C：分组柱状图**
- 按地域分组展示情感分布
- 可筛选 Top 10 地域
- 简洁清晰

---

### 优先级与实现计划

**第一阶段（核心功能）**
- [ ] 完成情感分类输出（emotion_code + emotion_label）
- [ ] 实现总体情感分布（饼图 + 柱状图）
- [ ] 实现时间序列可视化（堆积面积图）
- [ ] 实现地域热力图

**第二阶段（增强功能）**
- [ ] 地理位置地图可视化
- [ ] 交互式 Dashboard（使用 Streamlit 或 Dash）
- [ ] 词云图和高频词分析
- [ ] 用户等级/点赞数与情感的关系分析

**第三阶段（高级功能）**
- [ ] 深度学习模型优化
- [ ] 实时数据更新
- [ ] 机器学习模型解释性分析
- [ ] 异常检测（异常评论识别）
