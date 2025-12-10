import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Add project root to sys.path to allow importing src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.emotion_mapper import EMOTION_MAP

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def plot_timeline(file_path, output_filename):
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在。")
        return

    df = pd.read_csv(file_path)
    
    if 'time' not in df.columns or 'predicted_emotion' not in df.columns:
        print("错误: 缺少 'time' 或 'predicted_emotion' 列")
        return

    # 转换时间格式
    try:
        df['time'] = pd.to_datetime(df['time'])
    except Exception as e:
        print(f"时间格式转换失败: {e}")
        return

    # 按日期聚合 (也可以按小时，取决于数据跨度)
    # 这里我们按天统计每种情感的数量
    df['date'] = df['time'].dt.date
    timeline_data = df.groupby(['date', 'predicted_emotion']).size().unstack(fill_value=0)
    
    # 绘制堆叠面积图
    plt.figure(figsize=(14, 7))
    
    # 构建颜色映射表 (中文标签 -> 颜色)
    color_map = {info['zh_label']: info['color'] for code, info in EMOTION_MAP.items()}
    
    colors = [color_map.get(col, '#69c0ff') for col in timeline_data.columns]
    
    timeline_data.plot(kind='area', stacked=True, color=colors, alpha=0.8, figsize=(14, 7))
    
    plt.title('评论情感随时间变化趋势')
    plt.xlabel('日期')
    plt.ylabel('评论数量')
    plt.legend(title='情感类别', bbox_to_anchor=(1.05, 1), loc='upper left')
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
    data_path = os.path.join(project_root, 'data', 'processed', 'comments_predicted.csv')
    
    print("正在绘制评论时间轴趋势...")
    plot_timeline(data_path, "comment_emotion_timeline.png")
