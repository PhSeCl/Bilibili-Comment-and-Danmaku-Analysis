"""
时间序列情感分析演示脚本
包含生成假设数据表的步骤
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import add_emotion_labels, calculate_sentiment_index
from src.visualization import plot_comment_timeline, print_timeline_statistics
from src.utils.time_series import aggregate_by_time

def generate_sample_data_with_dates():
    """
    生成带有日期的样本数据
    
    由于原始数据中的日期跨度较小（都在 2024-11 附近），
    我们生成一个更完整的时间序列样本数据用于演示
    
    Returns:
        pd.DataFrame，包含日期和情感标签的样本数据
    """
    print("📊 生成样本时间序列数据...\n")
    
    # 生成日期范围：从 2024-11-20 到 2024-12-31（共约 6 周）
    dates = pd.date_range(start='2024-11-20', end='2024-12-31', freq='D')
    
    # 为每天生成随机数量的评论（5-15 条）
    data = []
    for date in dates:
        # 每天的评论数量（随机）
        num_comments = np.random.randint(5, 16)
        
        # 为了让数据更有趣，我们设置不同周期的情感偏好
        # 这模拟了不同时间点的真实舆论变化
        week_of_year = date.isocalendar()[1]
        
        for _ in range(num_comments):
            # 基于周数和随机性生成情感标签
            if week_of_year <= 47:
                # 第一周：略微倾向负面（如刚开始时的吐槽）
                emotion_code = np.random.choice(
                    [0, 1, 2, 3, 4, 5],
                    p=[0.15, 0.15, 0.2, 0.25, 0.15, 0.1]
                )
            elif week_of_year <= 49:
                # 第二周：倾向中立到正面（如内容发展）
                emotion_code = np.random.choice(
                    [1, 2, 3, 4, 5, 6],
                    p=[0.1, 0.15, 0.2, 0.25, 0.2, 0.1]
                )
            elif week_of_year <= 51:
                # 第三周：倾向正面（如高潮）
                emotion_code = np.random.choice(
                    [3, 4, 5, 6, 7],
                    p=[0.1, 0.15, 0.25, 0.35, 0.15]
                )
            else:
                # 最后一周：回归中立
                emotion_code = np.random.choice(
                    [2, 3, 4, 5, 6],
                    p=[0.1, 0.3, 0.3, 0.2, 0.1]
                )
            
            data.append({
                'date': date,
                'emotion_code': emotion_code,
            })
    
    df = pd.DataFrame(data)
    print(f"✅ 生成了 {len(df)} 条样本数据")
    print(f"📅 日期范围：{df['date'].min()} 到 {df['date'].max()}")
    print(f"📊 数据统计：")
    print(f"   - 每天平均评论数：{len(df) / len(df['date'].unique()):.1f}")
    print(f"   - 情感代码分布：{df['emotion_code'].value_counts().sort_index().to_dict()}\n")
    
    return df

def main():
    print("🚀 开始时间序列情感分析演示...\n")
    
    # ========== 第一步：生成样本数据 ==========
    df = generate_sample_data_with_dates()
    
    # ========== 第二步：添加情感标签 ==========
    print("🏷️  添加情感标签...\n")
    
    # 将 emotion_code 重命名为 labels（供可视化函数使用）
    df.rename(columns={'emotion_code': 'labels'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    
    # 添加情感文字标签
    from src.utils.emotion_mapper import get_emotion_label
    emotion_mapping = {i: get_emotion_label(i, use_zh=True) for i in range(8)}
    df['emotion_label'] = df['labels'].map(emotion_mapping)
    
    print("✅ 标签添加完成\n")
    
    # ========== 第三步：聚合时间序列数据 ==========
    print("📊 聚合时间序列数据（按周）...\n")
    timeline_df = aggregate_by_time(df, 'date', 'labels', freq='W')
    
    # 打印统计信息
    print_timeline_statistics(timeline_df)
    
    # ========== 第四步：绘制时间序列图表 ==========
    print("🎨 绘制时间序列可视化图表...\n")
    fig, ax = plot_comment_timeline(
        df,
        date_column='date',
        emotion_column='labels',
        freq='W',
        figsize=(14, 7),
        title='评论情感时间序列分析（按周）'
    )
    
    if fig is not None:
        print("\n✅ 演示完成！")
        print("\n📊 时间序列分析总结：")
        print("="*60)
        
        # 计算一些有用的统计指标
        sentiments = timeline_df['sentiment_index'].values
        print(f"整体情感指数：{sentiments.mean():.2f}")
        print(f"最高情感指数：{sentiments.max():.2f} (第 {sentiments.argmax() + 1} 周)")
        print(f"最低情感指数：{sentiments.min():.2f} (第 {sentiments.argmin() + 1} 周)")
        print(f"情感变化范围：{sentiments.max() - sentiments.min():.2f}")
        print(f"总评论数：{len(df)}")
        print(f"周数：{len(timeline_df)}")
        print("="*60)

if __name__ == "__main__":
    main()
