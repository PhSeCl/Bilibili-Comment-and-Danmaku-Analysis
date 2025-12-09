import matplotlib.pyplot as plt
import pandas as pd
import os
from pathlib import Path
import re

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def generate_wordcloud(df, output_path=None, max_words=200):
    """
    生成词云图
    """
    try:
        import jieba
        from wordcloud import WordCloud
    except ImportError:
        print("❌ 缺少依赖库: jieba 或 wordcloud。请运行 `pip install jieba wordcloud`")
        return None

    if 'content' not in df.columns:
        print("❌ 数据中缺少 'content' 列")
        return None

    # 1. 文本拼接
    text = " ".join(df['content'].astype(str).tolist())
    
    # 2. 清洗 (去除一些无意义的词)
    # 这里可以加载停用词表，暂时简单处理
    stop_words = set(['的', '了', '是', '我', '你', '他', '在', '就', '不', '也', '都', '吗', '啊', '吧', '呢', '回复', 'Video', 'Note'])
    
    # 3. 分词
    words = jieba.cut(text)
    filtered_words = [w for w in words if len(w) > 1 and w not in stop_words]
    
    if not filtered_words:
        print("⚠️ 没有足够的词生成词云")
        return None
        
    text_space_split = " ".join(filtered_words)
    
    # 4. 生成词云
    # 尝试找到一个中文字体路径
    font_path = "msyh.ttc" # Windows 默认
    if not os.path.exists("C:/Windows/Fonts/msyh.ttc"):
        # 尝试其他字体
        font_path = "simhei.ttf"
    
    wc = WordCloud(
        font_path=font_path,
        background_color='white',
        width=1000,
        height=600,
        max_words=max_words,
        max_font_size=100,
        random_state=42,
        collocations=False # 避免重复词
    )
    
    try:
        wc.generate(text_space_split)
    except Exception as e:
        print(f"❌ 词云生成失败 (可能是字体问题): {e}")
        return None
        
    # 5. 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wc.to_file(output_path)
        print(f"词云已保存至: {output_path}")
        
    return fig

def plot_sentiment_wordcloud(df):
    """
    分别生成正面和负面词云
    """
    # 假设 labels: 0-2 负面, 3 中立, 4-7 正面
    neg_df = df[df['labels'] <= 2]
    pos_df = df[df['labels'] >= 4]
    
    fig_neg = generate_wordcloud(neg_df)
    fig_pos = generate_wordcloud(pos_df)
    
    return fig_neg, fig_pos
