"""
总体情感分布可视化模块
使用饼图 + 柱状图展示情感分布
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np
from pathlib import Path

# 设置中文字体
mpl.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False

from ..utils import (
    get_emotion_label,
    get_emotion_color,
    get_all_emotions,
    get_all_colors,
)

# 自动找到项目根目录
def get_project_root():
    """获取项目根目录"""
    current_dir = Path(__file__).resolve().parent
    # 从 src/visualization 往上找三级到达项目根目录
    return current_dir.parent.parent

PROJECT_ROOT = get_project_root()
OUTPUT_DIR = PROJECT_ROOT / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_emotion_distribution(df, emotion_col='labels', figsize=(14, 6), save_path=None, use_zh=True):
    """
    绘制饼图 + 柱状图展示情感分布
    
    Args:
        df: pd.DataFrame，包含情感数据的数据框
        emotion_col: str，情感列名（默认 'labels'）
        figsize: tuple，图片大小
        save_path: str，保存路径（可选）
        use_zh: bool，是否使用中文标签
        
    Returns:
        fig, axes：matplotlib 图表对象
    """
    
    # 计算情感分布
    emotion_counts = df[emotion_col].value_counts().sort_index()
    
    # 获取标签和颜色
    labels = [get_emotion_label(code, use_zh=use_zh) for code in emotion_counts.index]
    colors = [get_emotion_color(code) for code in emotion_counts.index]
    counts = emotion_counts.values
    percentages = (counts / counts.sum() * 100).round(2)
    
    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    fig.suptitle('评论情感分布分析', fontsize=16, fontweight='bold', y=1.00)
    
    # ========== 左侧：饼图 ==========
    ax_pie = axes[0]
    
    # 绘制饼图
    wedges, texts, autotexts = ax_pie.pie(
        counts,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10}
    )
    
    # 美化自动文本（百分比标签）
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    ax_pie.set_title('情感占比分布', fontsize=12, fontweight='bold', pad=20)
    
    # ========== 右侧：柱状图 ==========
    ax_bar = axes[1]
    
    # 绘制柱状图
    x_pos = np.arange(len(labels))
    bars = ax_bar.bar(x_pos, counts, color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
    
    # 在柱子顶部添加数值标签
    for i, (bar, count, pct) in enumerate(zip(bars, counts, percentages)):
        height = bar.get_height()
        ax_bar.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{int(count)}\n({pct}%)',
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )
    
    # 设置柱状图的坐标轴
    ax_bar.set_xlabel('情感类别', fontsize=11, fontweight='bold')
    ax_bar.set_ylabel('评论数量', fontsize=11, fontweight='bold')
    ax_bar.set_title('情感数量分布', fontsize=12, fontweight='bold', pad=20)
    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels(labels, rotation=45, ha='right')
    ax_bar.grid(axis='y', alpha=0.3, linestyle='--')
    ax_bar.set_axisbelow(True)
    
    # 优化布局
    plt.tight_layout()
    
    # 保存图表
    if save_path is None:
        save_path = OUTPUT_DIR / 'emotion_distribution_pie_bar.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 图表已保存到: {save_path}")
    
    return fig, axes

def print_emotion_statistics(df, emotion_col='labels', use_zh=True):
    """
    打印情感分布的统计信息
    
    Args:
        df: pd.DataFrame，包含情感数据的数据框
        emotion_col: str，情感列名（默认 'labels'）
        use_zh: bool，是否使用中文标签
    """
    
    emotion_counts = df[emotion_col].value_counts().sort_index()
    total = emotion_counts.sum()
    
    print("\n" + "="*60)
    print("📊 情感分布统计")
    print("="*60)
    print(f"总评论数: {total}")
    print("-"*60)
    
    for code in emotion_counts.index:
        count = emotion_counts[code]
        percentage = (count / total * 100)
        label = get_emotion_label(code, use_zh=use_zh)
        print(f"{label:12} | 数量: {count:3d} | 占比: {percentage:5.2f}%")
    
    print("="*60 + "\n")

def get_emotion_summary(df, emotion_col='labels'):
    """
    获取情感分布的摘要字典
    
    Args:
        df: pd.DataFrame，包含情感数据的数据框
        emotion_col: str，情感列名（默认 'labels'）
        
    Returns:
        dict，包含分布信息的字典
    """
    emotion_counts = df[emotion_col].value_counts().sort_index()
    total = emotion_counts.sum()
    
    summary = {
        'total_count': total,
        'distribution': {},
    }
    
    for code in emotion_counts.index:
        count = emotion_counts[code]
        summary['distribution'][code] = {
            'label': get_emotion_label(code, use_zh=True),
            'count': int(count),
            'percentage': float((count / total * 100).round(2)),
        }
    
    return summary
