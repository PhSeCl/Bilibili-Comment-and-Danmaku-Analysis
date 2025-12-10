import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Map
import os

def plot_geo_heatmap(input_data, output_filename, mode='count'):
    """
    绘制地域热力图
    
    Args:
        input_data: 文件路径 (str) 或 DataFrame
        output_filename: 输出 HTML 文件路径
        mode: 'count' (评论数量) 或 'sentiment' (情感倾向)
    """
    if isinstance(input_data, str):
        if not os.path.exists(input_data):
            print(f"错误: 文件 {input_data} 不存在。")
            return None
        df = pd.read_csv(input_data)
    else:
        df = input_data.copy()
    
    if 'ip_location' not in df.columns:
        print("错误: 缺少 'ip_location' 列")
        return None

    # 清洗数据：去除空值、空字符串和"未知"
    # 1. 去除 NaN
    df = df.dropna(subset=['ip_location'])
    # 2. 去除空字符串
    df = df[df['ip_location'].str.strip() != '']
    # 3. 去除 "未知"
    df = df[df['ip_location'] != '未知']
    
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
    
    # 根据模式处理数据
    if mode == 'sentiment' and 'labels' in df.columns:
        # 映射情感分数 (8分类)
        # 0: Very Negative -> -3
        # 1: Negative -> -2
        # 2: Slightly Negative -> -1
        # 3: Neutral -> 0
        # 4: Slightly Positive -> 1
        # 5: Positive -> 2
        # 6: Very Positive -> 3
        # 7: Surprise -> 1 (视为略微正面)
        
        def map_sentiment(label):
            try:
                l = int(label)
                score_map = {
                    0: -3, 1: -2, 2: -1, 3: 0,
                    4: 1, 5: 2, 6: 3, 7: 1
                }
                return score_map.get(l, 0)
            except:
                return 0
            
        df['sentiment_score'] = df['labels'].apply(map_sentiment)
        
        # 按省份计算平均分
        # 先过滤掉样本数过少的省份，避免个别只有1条评论且极端的省份拉偏整体范围
        province_counts = df['normalized_location'].value_counts()
        valid_provinces = province_counts[province_counts >= 3].index # 至少有3条评论才参与统计
        
        df_filtered = df[df['normalized_location'].isin(valid_provinces)]
        
        if len(df_filtered) == 0:
             # 如果过滤完没数据了，就回退到不过滤
             df_filtered = df
             
        province_stats = df_filtered.groupby('normalized_location')['sentiment_score'].mean()
        
        # 动态计算范围，增强对比度
        if len(province_stats) > 0:
            # 使用分位数法 (Quantile) 代替最大值法
            # 计算所有省份得分绝对值的 90% 分位数
            abs_scores = province_stats.abs()
            limit = abs_scores.quantile(0.90)
            
            print(f"DEBUG: Quantile(0.9) Limit: {limit}")
            
            # 兜底逻辑：
            if limit < 0.1: limit = 0.1 # 稍微调高下限
            if limit > 2.0: limit = 2.0 # 调高上限，因为现在分数范围是 -3 到 3
            
        else:
            limit = 1.0
        
        # 确保 limit 是原生 float 类型，并保留3位小数
        limit = round(float(limit), 3)
        print(f"DEBUG: Final VisualMap Limit: +/- {limit}")

        data_pair = [list(z) for z in zip(province_stats.index, province_stats.values.round(3).tolist())]
        
        title = "各省份情感倾向热力图 (正值=正面, 负值=负面)"
        series_name = "平均情感指数"
        # 使用动态范围
        visual_map = opts.VisualMapOpts(
            max_=limit, 
            min_=-limit,
            is_piecewise=False,
            range_color=["#D94E5D", "#EAC736", "#50A3BA"] # 红(负) -> 黄(中) -> 蓝/绿(正)
        )
        
    else:
        # 默认模式：统计数量
        location_counts = df['normalized_location'].value_counts()
        data_pair = [list(z) for z in zip(location_counts.index, location_counts.values.tolist())]
        
        title = "评论用户地域分布热力图"
        series_name = "评论数量"
        visual_map = opts.VisualMapOpts(max_=int(location_counts.max()) if len(location_counts) > 0 else 100, is_piecewise=False)

    # 创建地图
    c = (
        Map()
        .add(series_name, data_pair, "china")
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            visualmap_opts=visual_map,
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}")
        )
    )

    if output_filename:
        output_dir = os.path.dirname(output_filename)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        c.render(output_filename)
        print(f"地图已保存至: {output_filename}")
        
    return c

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_path = os.path.join(project_root, 'data', 'processed', 'comments_predicted.csv')
    
    print("正在绘制地域热力图...")
    plot_geo_heatmap(data_path, "results/figures/comment_geo_heatmap.html")
