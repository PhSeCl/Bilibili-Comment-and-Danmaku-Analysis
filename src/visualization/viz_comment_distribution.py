import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# 设置中文字体，防止乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def plot_distribution(file_path, title_prefix, output_filename):
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在。请先运行预测脚本。")
        return

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    if 'predicted_emotion' not in df.columns:
        print(f"错误: {file_path} 中缺少 'predicted_emotion' 列。")
        return

    # 统计情感分布
    emotion_counts = df['predicted_emotion'].value_counts()
    
    # 定义颜色映射 (根据情感极性调整颜色)
    # 假设情感标签包含：非常负面, 略微负面, 中立, 略微正面, 非常正面
    # 这是一个通用的颜色板，可以根据实际标签调整
    color_map = {
        '非常负面': '#ff4d4f', # 红色
        '略微负面': '#ffccc7', # 浅红
        '中立': '#d9d9d9',     # 灰色
        '略微正面': '#b7eb8f', # 浅绿
        '非常正面': '#52c41a'  # 绿色
    }
    
    # 如果有未定义的标签，使用默认颜色
    colors = [color_map.get(label, '#69c0ff') for label in emotion_counts.index]

    # 创建画布
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # 1. 饼图
    ax1.pie(emotion_counts, labels=emotion_counts.index, autopct='%1.1f%%', startangle=140, colors=colors)
    ax1.set_title(f'{title_prefix} - 情感占比 (饼图)')

    # 2. 柱状图
    sns.barplot(x=emotion_counts.index, y=emotion_counts.values, ax=ax2, palette=colors)
    ax2.set_title(f'{title_prefix} - 情感数量 (柱状图)')
    ax2.set_xlabel('情感类别')
    ax2.set_ylabel('数量')
    
    # 在柱状图上显示数值
    for i, v in enumerate(emotion_counts.values):
        ax2.text(i, v + max(emotion_counts.values)*0.01, str(v), ha='center')

    plt.tight_layout()
    
    # 保存图片
    output_dir = 'results/figures'
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, output_filename)
    plt.savefig(save_path)
    print(f"图表已保存至: {save_path}")
    plt.show()

if __name__ == "__main__":
    # 确保在项目根目录下运行，或者使用绝对路径
    # 这里假设脚本在 src/visualization 下，数据在 data/processed 下
    # 我们向上两级找到项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    data_path = os.path.join(project_root, 'data', 'processed', 'comments_predicted.csv')
    
    print("正在绘制评论情感分布...")
    plot_distribution(data_path, "评论", "comment_emotion_distribution.png")
