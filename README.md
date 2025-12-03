# 中山大学人工智能学院数据分析实践大作业

本项目是中山大学人工智能学院数据分析实践课程的大作业，该项目的内容是基于提供的数据集进行数据分析和可视化展示。

## 项目结构

Bilibili-Emotion-Analysis/  (根目录)
├── data/                   # 存放数据文件
│   ├── raw/                # 原始数据 (爬下来的CSV，未清洗)
│   ├── processed/          # 清洗后的数据 (去重、去空值后)
│   └── sample.csv          # 少量样本数据 (供队友测试代码用，不要传几百兆的大文件)
│
├── src/                    # 源代码 (Source Code)
│   ├── crawler/            # 爬虫模块
│   │   ├── main_crawler.py # 爬虫主程序
│   │   └── config.py       # 爬虫配置 (注意不要上传自己的Cookie!)
│   │
│   ├── analysis/           # 分析模块
│   │   ├── clean_data.py   # 数据清洗脚本
│   │   └── emotion_model.py# 情感分析逻辑 (调用API或模型)
│   │
│   └── visualization/      # 可视化模块
│       ├── plot_pie.py     # 画饼图的代码
│       └── word_cloud.py   # (可选) 画词云的代码
│
├── notebooks/              # Jupyter Notebook (草稿本)
│   ├── explorative_analysis.ipynb # 队友用于尝试性分析的笔记
│   └── demo_visualization.ipynb   # 画图的测试笔记
│
├── docs/                   # 文档与报告
│   ├── final_report.pdf    # 最终提交给老师的作业报告
│   ├── presentation.pptx   # 答辩PPT
│   └── images/             # 存放生成的图片 (用于插入README或报告)
│
├── .gitignore              # 忽略文件列表 (非常重要！)
├── README.md               # 项目说明书 (门面)
└── requirements.txt        # 依赖包列表 (环境配置)
