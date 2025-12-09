"""
时间序列情感变化可视化模块
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.interpolate import make_interp_spline

# 设置中文字体
mpl.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False

from ..utils.time_series import (
    aggregate_by_time,
    aggregate_by_numeric,
    calculate_confidence_interval,
    get_sentiment_color,
    get_sentiment_label,
)

# 自动找到项目根目录
def get_project_root():
    """获取项目根目录"""
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent.parent

PROJECT_ROOT = get_project_root()
OUTPUT_DIR = PROJECT_ROOT / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_comment_timeline(
    df: pd.DataFrame,
    date_column: str = 'date',
    emotion_column: str = 'labels',
    freq: str = 'W',  # 'D'=日, 'W'=周, 'M'=月
    figsize: tuple = (14, 6),
    save_path=None,
    title: str = '评论情感时间序列分析'
):
    """
    绘制评论的时间序列情感变化图
    
    Args:
        df: pd.DataFrame，包含日期和情感列的数据框
        date_column: str，日期列名
        emotion_column: str，情感列名
        freq: str，时间频率 ('D'=日, 'W'=周, 'M'=月)
        figsize: tuple，图片大小
        save_path: str，保存路径（可选）
        title: str，图表标题
        
    Returns:
        fig, ax：matplotlib 图表对象
    """
    
    # 聚合数据
    timeline_df = aggregate_by_time(df, date_column, emotion_column, freq=freq)
    
    if len(timeline_df) == 0:
        print("❌ 没有有效的时间序列数据")
        return None, None
    
    # 提取数据
    times = timeline_df['time'].values
    sentiments = timeline_df['sentiment_index'].values
    counts = timeline_df['count'].values
    stds = timeline_df['std'].values
    
    # 计算置信区间
    confidences = [
        calculate_confidence_interval(sent, std, count)
        for sent, std, count in zip(sentiments, stds, counts)
    ]
    ci_lower = np.array([ci[0] for ci in confidences])
    ci_upper = np.array([ci[1] for ci in confidences])
    
    # 创建图表
    fig, ax = plt.subplots(figsize=figsize)
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # ========== 绘制背景区域 ==========
    # 负面区域（红色）
    ax.axhspan(-3, 0, alpha=0.1, color='red', label='负面区间')
    # 正面区域（绿色）
    ax.axhspan(0, 3, alpha=0.1, color='green', label='正面区间')
    # 中立线
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # ========== 绘制置信区间 ==========
    ax.fill_between(
        range(len(times)),
        ci_lower,
        ci_upper,
        alpha=0.25,
        color='steelblue',
        label='95% 置信区间'
    )
    
    # ========== 绘制平滑曲线 ==========
    if len(times) >= 3:
        # 生成光滑曲线（样条插值）
        x_numeric = np.arange(len(times))
        spl = make_interp_spline(x_numeric, sentiments, k=min(3, len(times)-1))
        x_smooth = np.linspace(0, len(times)-1, 300)
        y_smooth = spl(x_smooth)
        
        ax.plot(
            x_smooth,
            y_smooth,
            linewidth=2.5,
            color='darkblue',
            alpha=0.8,
            label='情感趋势（平滑）'
        )
    
    # ========== 绘制原始数据点 ==========
    colors = [get_sentiment_color(s) for s in sentiments]
    scatter = ax.scatter(
        range(len(times)),
        sentiments,
        s=100,
        c=colors,
        edgecolors='black',
        linewidth=1.5,
        alpha=0.7,
        zorder=3,
        label='实际数据点'
    )
    
    # ========== 添加数据标签 ==========
    for i, (time, sent, count) in enumerate(zip(times, sentiments, counts)):
        # 情感指数标签
        ax.text(
            i, sent + 0.15,
            f'{sent:.2f}',
            ha='center', va='bottom',
            fontsize=9,
            fontweight='bold'
        )
        # 样本数标签
        ax.text(
            i, -3.2,
            f'n={int(count)}',
            ha='center', va='top',
            fontsize=8,
            alpha=0.7
        )
    
    # ========== 设置坐标轴 ==========
    ax.set_xlabel('时间', fontsize=12, fontweight='bold')
    ax.set_ylabel('情感指数', fontsize=12, fontweight='bold')
    
    # 设置 Y 轴范围和刻度
    ax.set_ylim(-3.5, 3.5)
    ax.set_yticks([-3, -2, -1, 0, 1, 2, 3])
    ax.set_yticklabels(['非常负面', '负面', '略微负面', '中立', '略微正面', '正面', '非常正面'])
    
    # 设置 X 轴刻度（时间标签）
    ax.set_xticks(range(len(times)))
    
    # 格式化时间标签
    time_labels = []
    for t in times:
        if pd.isna(t):
            time_labels.append('N/A')
        else:
            # 根据频率选择合适的时间格式
            if freq == 'D':
                time_labels.append(pd.Timestamp(t).strftime('%Y-%m-%d'))
            elif freq == 'W':
                time_labels.append(pd.Timestamp(t).strftime('%Y-W%U'))
            elif freq == 'M':
                time_labels.append(pd.Timestamp(t).strftime('%Y-%m'))
            else:
                time_labels.append(str(t))
    
    ax.set_xticklabels(time_labels, rotation=45, ha='right')
    
    # 网格
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # 图例
    ax.legend(loc='upper left', fontsize=10)
    
    # 优化布局
    plt.tight_layout()
    
    # 保存图表
    if save_path is None:
        save_path = OUTPUT_DIR / 'comment_timeline_weekly.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 图表已保存到: {save_path}")
    
    return fig, ax

def print_timeline_statistics(timeline_df: pd.DataFrame):
    """
    打印时间序列的统计信息
    
    Args:
        timeline_df: pd.DataFrame，由 aggregate_by_time 返回的数据框
    """
    print("\n" + "="*80)
    print("📈 时间序列情感分析统计")
    print("="*80)
    
    print(f"{'时间':<20} | {'情感指数':<10} | {'置信区间':<20} | {'样本数':<6} | {'描述':<8}")
    print("-"*80)
    
    for _, row in timeline_df.iterrows():
        time_str = pd.Timestamp(row['time']).strftime('%Y-W%U') if pd.notna(row['time']) else 'N/A'
        sent_idx = row['sentiment_index']
        lower, upper = calculate_confidence_interval(
            sent_idx, row['std'], row['count']
        )
        count = int(row['count'])
        label = get_sentiment_label(sent_idx)
        
        print(
            f"{time_str:<20} | {sent_idx:>8.2f} | [{lower:>6.2f}, {upper:>6.2f}] | "
            f"{count:>4} | {label:<8}"
        )
    
    print("="*80 + "\n")

def plot_video_progress_trend(
    df: pd.DataFrame,
    time_column: str = 'video_time',
    emotion_column: str = 'labels',
    bin_size: float = 30.0,
    figsize: tuple = (14, 6),
    save_path=None,
    title: str = '弹幕情感随视频进度变化'
):
    """
    绘制弹幕随视频进度的情感变化图
    
    Args:
        df: pd.DataFrame
        time_column: str，视频时间列名 (秒)
        emotion_column: str，情感列名
        bin_size: float，分箱大小 (秒)
        figsize: tuple
        save_path: str
        title: str
    """
    # 聚合数据
    timeline_df = aggregate_by_numeric(df, time_column, emotion_column, bin_size=bin_size)
    
    if len(timeline_df) == 0:
        print("❌ 没有有效的视频进度数据")
        return None, None
    
    # 提取数据
    times = timeline_df['time'].values # 这里是 bin 的起始秒数
    sentiments = timeline_df['sentiment_index'].values
    counts = timeline_df['count'].values
    stds = timeline_df['std'].values
    
    # 计算置信区间
    confidences = [
        calculate_confidence_interval(sent, std, count)
        for sent, std, count in zip(sentiments, stds, counts)
    ]
    ci_lower = np.array([ci[0] for ci in confidences])
    ci_upper = np.array([ci[1] for ci in confidences])
    
    # 创建图表
    fig, ax = plt.subplots(figsize=figsize)
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # ========== 绘制背景区域 ==========
    ax.axhspan(-3, 0, alpha=0.1, color='red', label='负面区间')
    ax.axhspan(0, 3, alpha=0.1, color='green', label='正面区间')
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # ========== 绘制置信区间 ==========
    ax.fill_between(
        times / 60, # 转换为分钟
        ci_lower,
        ci_upper,
        alpha=0.25,
        color='steelblue',
        label='95% 置信区间'
    )
    
    # ========== 绘制平滑曲线 ==========
    # 如果点太少，就不平滑了
    if len(times) > 3:
        try:
            # 创建平滑曲线
            x_smooth = np.linspace(times.min(), times.max(), 300)
            spl = make_interp_spline(times, sentiments, k=3)
            y_smooth = spl(x_smooth)
            
            # 限制 y 范围
            y_smooth = np.clip(y_smooth, -3, 3)
            
            ax.plot(x_smooth / 60, y_smooth, color='steelblue', linewidth=2, label='情感指数趋势')
        except:
            # 平滑失败则画折线
            ax.plot(times / 60, sentiments, color='steelblue', linewidth=2, marker='o', label='情感指数趋势')
    else:
        ax.plot(times / 60, sentiments, color='steelblue', linewidth=2, marker='o', label='情感指数趋势')
        
    # ========== 绘制散点 ==========
    # 根据情感值给点上色
    colors = [get_sentiment_color(s) for s in sentiments]
    scatter = ax.scatter(times / 60, sentiments, c=colors, s=50, zorder=5, edgecolors='white')
    
    # ========== 设置坐标轴 ==========
    ax.set_ylim(-3.5, 3.5)
    ax.set_ylabel('情感指数\n(负面 < 0 < 正面)', fontsize=12)
    ax.set_xlabel('视频进度 (分钟)', fontsize=12)
    
    # 添加图例
    ax.legend(loc='upper right', frameon=True)
    
    # 添加网格
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 双轴显示评论数量
    ax2 = ax.twinx()
    ax2.bar(times / 60, counts, width=(bin_size/60)*0.8, alpha=0.15, color='gray', label='弹幕数量')
    ax2.set_ylabel('弹幕数量', fontsize=12, color='gray')
    ax2.tick_params(axis='y', labelcolor='gray')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存至: {save_path}")
        
    return fig, ax

# 导出函数
__all__ = [
    'plot_comment_timeline',
    'plot_video_progress_trend',
    'print_timeline_statistics',
]
