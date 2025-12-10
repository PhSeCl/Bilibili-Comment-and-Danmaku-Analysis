import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import numpy as np

# Add project root to sys.path to allow importing src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.emotion_mapper import EMOTION_MAP

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def plot_video_progress(file_path, output_filename, bin_size_seconds=30):
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在。")
        return

    df = pd.read_csv(file_path)
    
    if 'video_time' not in df.columns or 'predicted_emotion' not in df.columns:
        print("错误: 缺少 'video_time' 或 'predicted_emotion' 列")
        return

    # 将视频时间分箱 (例如每30秒一个区间)
    df['time_bin'] = (df['video_time'] // bin_size_seconds) * bin_size_seconds
    
    # 统计每个时间段的情感分布
    progress_data = df.groupby(['time_bin', 'predicted_emotion']).size().unstack(fill_value=0)
    
    # 补全中间缺失的时间段 (可选，为了图表连续性)
    if not progress_data.empty:
        full_index = np.arange(0, progress_data.index.max() + bin_size_seconds, bin_size_seconds)
        progress_data = progress_data.reindex(full_index, fill_value=0)

    # 绘制折线图
    plt.figure(figsize=(14, 7))
    
    # 构建颜色映射表 (中文标签 -> 颜色)
    color_map = {info['zh_label']: info['color'] for code, info in EMOTION_MAP.items()}
    
    # 绘制每种情感的曲线
    for emotion in progress_data.columns:
        plt.plot(progress_data.index / 60, progress_data[emotion], # x轴转换为分钟
                 label=emotion, 
                 color=color_map.get(emotion, '#69c0ff'),
                 linewidth=2)
        
    plt.title(f'弹幕情感随视频进度变化 (每{bin_size_seconds}秒统计)')
    plt.xlabel('视频进度 (分钟)')
    plt.ylabel('弹幕数量')
    plt.legend(title='情感类别')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_dir = 'results/figures'
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, output_filename)
    plt.savefig(save_path)
    print(f"图表已保存至: {save_path}")
    plt.show()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_path = os.path.join(project_root, 'data', 'processed', 'danmaku_predicted.csv')
    
    print("正在绘制弹幕视频进度趋势...")
    plot_video_progress(data_path, "danmaku_emotion_progress.png")
