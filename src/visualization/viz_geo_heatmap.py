import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Map
import os

def plot_geo_heatmap(file_path, output_filename):
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在。")
        return

    df = pd.read_csv(file_path)
    
    if 'ip_location' not in df.columns:
        print("错误: 缺少 'ip_location' 列")
        return

    # 统计各省份评论数量
    # 注意：B站IP属地通常是省份名称，如 "广东", "北京" 等
    # pyecharts 地图需要省份全称或简称匹配，通常 "广东" 即可匹配 "广东省"
    location_counts = df['ip_location'].value_counts()
    
    # 准备数据格式 [(省份, 数量), ...]
    data_pair = [list(z) for z in zip(location_counts.index, location_counts.values.tolist())]

    # 创建地图
    c = (
        Map()
        .add("评论数量", data_pair, "china")
        .set_global_opts(
            title_opts=opts.TitleOpts(title="评论用户地域分布热力图"),
            visualmap_opts=opts.VisualMapOpts(max_=int(location_counts.max()), is_piecewise=False),
        )
    )

    output_dir = 'results/figures'
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, output_filename)
    
    # 渲染为 HTML
    c.render(save_path)
    print(f"地图已保存至: {save_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_path = os.path.join(project_root, 'data', 'processed', 'comments_predicted.csv')
    
    print("正在绘制地域热力图...")
    plot_geo_heatmap(data_path, "comment_geo_heatmap.html")
