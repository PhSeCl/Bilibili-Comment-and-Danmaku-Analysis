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
    # 优先读取同目录下的 stopwords.txt
    current_dir = Path(__file__).resolve().parent
    stopwords_file = current_dir / "stopwords.txt"
    
    stop_words = set()
    
    if stopwords_file.exists():
        try:
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                stop_words = set([line.strip() for line in f if line.strip()])
            print(f"✅ 已加载自定义停用词表: {stopwords_file} (共 {len(stop_words)} 个词)")
        except Exception as e:
            print(f"⚠️ 读取停用词表失败: {e}")
    
    # 如果没有文件或文件为空，使用默认列表作为兜底
    if not stop_words:
        stop_words = set([
            '的', '了', '是', '我', '你', '他', '她', '它', '在', '就', '不', '也', '都', '吗', '啊', '吧', '呢', 
            '回复', 'Video', 'Note', '视频', '弹幕', '评论', '内容', 'up', 'UP', 'Up', 'uP', '主', 'up主', 'UP主',
            '我们', '你们', '他们', '这个', '那个', '就是', '还是', '只是', '但是', '而且', '因为', '所以', '如果', 
            '虽然', '觉得', '感觉', '时候', '什么', '怎么', '哪里', '为什么', '真的', '非常', '比较', '可以', '可能', 
            '应该', '必须', '一定', '开始', '结束', '现在', '后来', '之前', '之后', '已经', '曾经', '正在', '将要',
            '哈哈', '哈哈哈', '哈哈哈哈', '确实', '其实', '当然', '不过', '然后', '于是', '接着', '最后', '总之',
            '一般', '一样', '一直', '一些', '一点', '一切', '一下', '一次', '一种', '没有', '不是', '不要', '不能',
            '看到', '知道', '出来', '起来', '下去', '过来', '过去', '回来', '回去', '为了', '关于', '对于', '根据',
            '自己', '大家', '很多', '多少', '几个', '那些', '这些', '这样', '那样', '这么', '那么', '这种', '那种',
            '今天', '明天', '昨天', '今年', '明年', '去年', '最近', '以前', '以后', '目前', '当时', '忽然', '突然',
            'and', 'the', 'to', 'of', 'in', 'for', 'with', 'on', 'at', 'by', 'from', 'up', 'about', 'into', 
            'over', 'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 
            'does', 'did', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must'
        ])
    
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
