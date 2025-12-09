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

    # 清洗数据：去除空值
    df = df.dropna(subset=['ip_location'])
    
    # 定义省份名称标准化函数
    def normalize_province(name):
        if not isinstance(name, str): return name
        name = name.strip()
        
        # 处理 "中国香港" -> "香港" (后续再处理后缀)
        if name.startswith('中国') and len(name) > 2:
            name = name.replace('中国', '')
            
        # 直辖市
        if name in ['北京', '天津', '上海', '重庆']:
            return name + '市'
        # 自治区
        if name == '内蒙古': return '内蒙古自治区'
        if name == '新疆': return '新疆维吾尔自治区'
        if name == '西藏': return '西藏自治区'
        if name == '广西': return '广西壮族自治区'
        if name == '宁夏': return '宁夏回族自治区'
        # 特别行政区
        if name == '香港': return '香港特别行政区'
        if name == '澳门': return '澳门特别行政区'
        
        # 普通省份 (如果已经是全称则不变，否则加省)
        if len(name) <= 3 and name not in ['北京', '天津', '上海', '重庆', '香港', '澳门', '台湾']:
             if not name.endswith('省') and not name.endswith('市') and not name.endswith('区'):
                return name + '省'
        
        return name

    # 应用标准化
    df['normalized_location'] = df['ip_location'].apply(normalize_province)
    
    # 统计各省份评论数量
    location_counts = df['normalized_location'].value_counts()
    
    print("Top 10 地域 (标准化后):")
    print(location_counts.head(10))
    
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
