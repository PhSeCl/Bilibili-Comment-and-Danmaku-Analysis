# 中山大学人工智能学院数据分析实践大作业

本项目是中山大学人工智能学院数据分析实践课程的大作业，该项目的内容是爬取到数据集进行数据分析和可视化展示。 具体任务是对 B 站（Bilibili）的视频评论和弹幕数据进行情感分析，并通过多维度的可视化手段展示分析结果。项目采用 Streamlit 框架构建交互式 Web 界面，方便用户进行数据爬取、分析和结果展示。

## 📂 项目结构

```text
Bilibili-Comment-Analysis/ (根目录)
├── app.py                       # Streamlit Web 应用入口
├── assets/                      # 静态资源 (如加载动画图片)
├── data/                        # 存放数据文件
│   ├── raw/                     # 原始数据
│   │   ├── comments_BVxx.csv         # 爬取的评论数据
│   │   └── danmaku_BVxx.csv          # 爬取的弹幕数据
│   └── processed/               # 调用模型处理后的数据
│       ├── comment_BVxx_emotion.csv  # 评论情感分类结果
│       └── danmaku_BVxx_emotion.csv  # 弹幕情感分类结果
│
├── src/                         # 源代码 (Source Code)
│   ├── analysis/                # 核心分析与模型模块
│   │   ├── model.py             # 模型推理接口
│   │   ├── run_prediction.py    # 调用模型进行情感分类
│   ├── crawler/                 # 爬虫模块
│   │   ├── config.py            # 爬虫配置 (Cookie等)
│   │   └── main_crawler.py      # 爬虫主程序
│   ├── utils/                   # 通用工具库
│   │   ├── emotion_mapper.py    # 情感标签与颜色映射
│   │   └── time_series.py       # 时间序列计算与统计工具
│   └── visualization/           # 可视化模块
│       ├── distribution.py      # 情感分布可视化 (饼图/柱状图)
│       ├── timeline.py          # 时间序列可视化 (折线趋势图)
│       ├── viz_geo_heatmap.py   # 地域热力图 (Pyecharts)
│       ├── wordcloud_viz.py     # 词云图生成
│       └── stopwords.txt        # 词云停用词表
├── docs/                        # 文档与产出
│   └── images/                  # 存放生成的图表图片
├── README.md                    # 项目说明书
└── requirements.txt             # 依赖包列表
```

---

## 📊 功能特性

### 核心功能亮点

- **多维度情感分析**：支持时间、地域、用户等级等维度的情感分析。
- **交互式可视化**：通过 Streamlit 提供直观的交互界面。
- **自定义数据爬取**：支持用户自定义爬取 B 站评论和弹幕数据。

### 核心工作流

```text
原始评论/弹幕数据
  → 数据预处理 
  → 情感分类 
  → 多维度可视化
```

### 数据输出格式规范

#### 评论数据输出格式

```csv
content,username,time,ip_location,user_level,likes,labels
"评论内容","用户名","2024-11-20 21:56:54","广东",6,1244,2
```

#### 弹幕数据输出格式

```csv
video_time,real_time,content,user_hash,labels
123.45,"2024-11-20 21:56:54","弹幕内容","user_hash",3
```

---

## 使用说明

- 克隆项目到本地：

    ```bash
    git clone https://github.com/PhSeCl/Bilibili-Comment-and-Danmaku-Analysis.git
    cd Bilibili-Comment-and-Danmaku-Analysis
    ```

- 安装依赖包：

    ```bash
    pip install -r requirements.txt
    ```

- 配置爬虫参数：

    在 `src/crawler/config.py` 中设置 B 站 Cookie 。(Cookie 获取方法请参考网络教程)

- 运行 GUI 界面：

    ```bash
    streamlit run app.py
    ```

- 按照界面提示进行数据爬取、分析与可视化。

---

## 注意事项

- 如果Cookie失效，可能导致无法爬取数据，请及时更新。建议在配置文件 `src/crawler/config.py` 中将 DEFAULT_COOKIE 替换为自己的有效 Cookie。
- 请确保网络连接畅通，以便顺利爬取 B 站数据。
- 爬取数据时请遵守 B 站的使用条款，避免过于频繁的请求导致封禁。
- 分析过程中可能会消耗较多计算资源，请根据实际情况调整批处理大小等参数。
- 如有任何问题或建议，欢迎在项目的 GitHub 页面提交 issue 或 pull request，或联系 [xuhch28@mail2.sysu.edu.cn](mailto:xuhch28@mail2.sysu.edu.cn)。

## 贡献者

- @Anony-mous-210
- @ScarletShinku
- @PhSeCl
