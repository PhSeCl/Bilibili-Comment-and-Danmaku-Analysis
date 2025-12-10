import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import time

# Page Config
st.set_page_config(
    page_title="Bilibili Comment Analysis",
    page_icon="📊",
    layout="wide"
)

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Title
st.title("📺 Bilibili 评论与弹幕情感分析系统")
st.markdown("项目开源地址: [GitHub](https://github.com/PhSeCl/Bilibili-Comments-and-Danmaku-Analysis)")
st.markdown("---")

# Sidebar: Configuration
st.sidebar.header("⚙️ 参数设置")

# Cookie 输入框
user_cookie = st.sidebar.text_area(
    "B站 Cookie (可选，用于爬取更多数据)", 
    value="",
    placeholder="在此可粘贴您的 Cookie，留空则使用默认测试 Cookie",
    help="登录 B 站后，按 F12 打开控制台，输入 document.cookie 并复制结果。"
)

# 更新 config 中的 Cookie
from src.crawler import config
if user_cookie.strip():
    config.COOKIE = user_cookie.strip()
    config.HEADERS["Cookie"] = config.COOKIE
else:
    # 如果用户未输入，使用默认 Cookie
    if hasattr(config, 'DEFAULT_COOKIE'):
        config.COOKIE = config.DEFAULT_COOKIE
        config.HEADERS["Cookie"] = config.COOKIE

bv_code = st.sidebar.text_input("BV 号 (例如 BV1xx411c7mD)", value="BV1xx411c7mD")
max_pages = st.sidebar.number_input("爬取页数 (每页20条)", min_value=1, max_value=100, value=5)
max_danmaku = st.sidebar.number_input("弹幕爬取条数 (0为不限制)", min_value=0, value=1000, step=100)

st.sidebar.markdown("---")
st.sidebar.info("提示：先爬取数据，再进行分析。")

# --- 启动加载动画 ---
loading_placeholder = st.empty()
with loading_placeholder.container():
    # 创建三列布局让内容居中
    l_col1, l_col2, l_col3 = st.columns([1, 2, 1])
    with l_col2:
        st.markdown("<br><br>", unsafe_allow_html=True) # 顶出一点距离
        st.markdown("<h2 style='text-align: center;'>少女折寿中... 🙏</h2>", unsafe_allow_html=True)
        
        # 尝试加载用户自定义图片
        image_path = PROJECT_ROOT / "assets" / "loading.png"
        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
        else:
            # 如果没有图片，显示一个提示或者 emoji
            st.markdown("<div style='text-align: center; font-size: 80px;'>🛐</div>", unsafe_allow_html=True)
            st.caption("（提示：您可以将Q版图片命名为 loading.png 并放入 assets 文件夹中）")

# Import project modules
try:
    from src.crawler.main_crawler import crawl_comments_by_bv, crawl_danmaku_by_bv, get_video_info
    from src.analysis.run_prediction import run_prediction_pipeline
    from src.visualization.distribution import plot_emotion_distribution
    from src.visualization.timeline import plot_comment_timeline, plot_video_progress_trend
    from src.visualization.viz_geo_heatmap import plot_geo_heatmap
    from src.visualization.wordcloud_viz import generate_wordcloud
    
    # 模拟一点延迟，让用户能看清动画 (可选，如果加载太快的话)
    # time.sleep(1) 
    
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# --- 缓存模型加载 ---
@st.cache_resource
def load_sentiment_model():
    """
    加载情感分析模型并缓存，避免重复加载
    """
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    
    LOCAL_MODEL_DIR = PROJECT_ROOT / "trained_models"
    HF_MODEL_ID = "ScarletShinku/bilibili-sentiment-bert"
    
    model_path = LOCAL_MODEL_DIR if LOCAL_MODEL_DIR.exists() else HF_MODEL_ID
    
    print(f"🚀 [Cache] Loading model from: {model_path}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        return model, tokenizer
    except Exception as e:
        st.error(f"模型加载失败: {e}")
        return None, None

# 清除加载动画
loading_placeholder.empty()

# Main Content
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 数据采集")
    
    # Tabs for Comments and Danmaku
    crawl_tab1, crawl_tab2 = st.tabs(["📝 评论", "🚀 弹幕"])
    
    with crawl_tab1:
        if st.button("🕷️ 开始爬取评论", use_container_width=True):
            if not bv_code:
                st.warning("请输入有效的 BV 号")
            else:
                with st.spinner(f"正在获取视频信息: {bv_code}..."):
                    video_info = get_video_info(bv_code)
                    
                if not video_info:
                    st.error("无法获取视频信息，请检查 BV 号或网络。")
                else:
                    st.success(f"找到视频 (OID: {video_info['oid']})")
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Define a custom output path for this session
                    raw_data_path = PROJECT_ROOT / "data" / "raw" / f"comments_{bv_code}.csv"
                    
                    # Callback function for progress
                    def progress_callback(current, total, msg):
                        status_text.text(msg)
                        if total > 0:
                            progress_bar.progress(min(current / total, 1.0))
                    
                    # Run crawler
                    try:
                        count = crawl_comments_by_bv(bv_code, max_pages, str(raw_data_path), callback=progress_callback)
                        progress_bar.progress(100)
                        if count > 0:
                            st.success(f"✅ 爬取完成！共获取 {count} 条评论。")
                            st.session_state['current_raw_data'] = str(raw_data_path)
                            st.session_state['current_bv'] = bv_code
                        else:
                            st.warning("⚠️ 未爬取到任何评论。")
                    except Exception as e:
                        st.error(f"爬取失败: {e}")

    with crawl_tab2:
        if st.button("🚀 开始爬取弹幕", use_container_width=True):
            if not bv_code:
                st.warning("请输入有效的 BV 号")
            else:
                with st.spinner(f"正在爬取弹幕: {bv_code}..."):
                    danmaku_path = PROJECT_ROOT / "data" / "raw" / f"danmaku_{bv_code}.csv"
                    limit = max_danmaku if max_danmaku > 0 else None
                    try:
                        count = crawl_danmaku_by_bv(bv_code, limit, str(danmaku_path))
                        if count > 0:
                            st.success(f"✅ 弹幕爬取完成！共 {count} 条。")
                            st.info(f"保存路径: {danmaku_path.name}")
                        else:
                            st.warning("⚠️ 未爬取到弹幕。")
                    except Exception as e:
                        st.error(f"弹幕爬取失败: {e}")

with col2:
    st.subheader("2. 情感分析")
    
    # File Selection Logic
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    if raw_data_dir.exists():
        csv_files = list(raw_data_dir.glob("*.csv"))
        # Sort by modification time (newest first)
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        file_options = {f.name: str(f) for f in csv_files}
    else:
        file_options = {}

    selected_file_name = st.selectbox(
        "选择要分析的数据文件:",
        options=list(file_options.keys()),
        index=0 if file_options else None,
        help="从 data/raw 目录中选择已爬取的 CSV 文件"
    )
    
    current_raw_data = file_options.get(selected_file_name) if selected_file_name else None

    if st.button("🧠 开始分析", disabled=not current_raw_data, use_container_width=True):
        with st.spinner("正在加载模型并分析情感 (可能需要几秒钟)..."):
            try:
                # 预加载模型
                model, tokenizer = load_sentiment_model()
                if model is None:
                    st.error("无法加载模型，分析终止。")
                else:
                    output_csv = PROJECT_ROOT / "data" / "processed" / f"predictions_{Path(current_raw_data).stem}.csv"
                    # 传入预加载的模型
                    df = run_prediction_pipeline(
                        input_path=current_raw_data, 
                        output_path=output_csv,
                        model=model,
                        tokenizer=tokenizer
                    )
                    
                    if df is not None:
                        st.session_state['analysis_result'] = df
                        st.success("✅ 分析完成！")
                    else:
                        st.error("分析失败，请检查日志。")
            except Exception as e:
                st.error(f"运行出错: {e}")

st.markdown("---")

# Visualization Section
if 'analysis_result' in st.session_state:
    df = st.session_state['analysis_result']
    
    st.header("📊 分析结果可视化")
    
    # 动态生成标签页
    tab_names = ["情感分布", "时间趋势", "词云图"]
    has_location = 'ip_location' in df.columns
    if has_location:
        tab_names.append("地域热力图")
    tab_names.append("原始数据")
    
    tabs = st.tabs(tab_names)
    
    tab1 = tabs[0]
    tab2 = tabs[1]
    tab_wc = tabs[2]
    
    if has_location:
        tab3 = tabs[3]
        tab4 = tabs[4]
    else:
        tab3 = None
        tab4 = tabs[3]
    
    with tab1:
        st.subheader("总体情感分布")
        try:
            fig, _ = plot_emotion_distribution(df, save_path=None)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"绘图失败: {e}")
            
    with tab2:
        st.subheader("情感随时间变化")
        
        # 判断是否为弹幕数据 (含有 video_time 列)
        is_danmaku = 'video_time' in df.columns
        
        if is_danmaku:
            timeline_mode = st.radio("时间维度:", ["现实时间 (发布日期)", "视频进度 (播放时间)"], horizontal=True)
        else:
            timeline_mode = "现实时间 (发布日期)"
            
        if timeline_mode == "视频进度 (播放时间)":
             try:
                # 分箱大小滑块
                bin_size = st.slider("时间分箱大小 (秒)", min_value=10, max_value=300, value=30, step=10)
                fig_timeline, _ = plot_video_progress_trend(df, time_column='video_time', bin_size=bin_size)
                if fig_timeline:
                    st.pyplot(fig_timeline)
                else:
                    st.info("数据不足以生成视频进度图。")
             except Exception as e:
                st.error(f"视频进度绘图失败: {e}")
        
        else:
            # 尝试查找时间列
            date_col = None
            if 'time' in df.columns:
                date_col = 'time'
            elif 'date' in df.columns:
                date_col = 'date'
            elif 'real_time' in df.columns:
                date_col = 'real_time'
                
            if date_col:
                try:
                    # Convert to datetime if needed
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    
                    # 时间频率选择
                    freq_map = {
                        "按小时": "H", 
                        "按天": "D", 
                        "每3天": "3D", 
                        "按周": "W", 
                        "每半月": "15D", 
                        "按月": "M"
                    }
                    freq_label = st.select_slider(
                        "时间聚合粒度:", 
                        options=list(freq_map.keys()), 
                        value="按天"
                    )
                    freq = freq_map[freq_label]
                    
                    fig_timeline, _ = plot_comment_timeline(df, date_column=date_col, freq=freq)
                    if fig_timeline:
                        st.pyplot(fig_timeline)
                    else:
                        st.info("数据不足以生成时间序列图。")
                except Exception as e:
                    st.error(f"时间序列绘图失败: {e}")
            else:
                st.warning("数据中缺少时间列 (time/date/real_time)，无法绘制趋势图。")
    
    with tab_wc:
        st.subheader("评论词云图")
        st.info("词云图展示了评论中出现频率最高的词汇。")
        try:
            fig_wc = generate_wordcloud(df)
            
            if fig_wc:
                st.pyplot(fig_wc)
            else:
                st.warning("无法生成词云（可能评论太少或缺少依赖）")
                    
        except Exception as e:
            st.error(f"词云生成失败: {e}")
            st.warning("提示: 请确保已安装 jieba 和 wordcloud 库。")
            
    if tab3:
        with tab3:
            st.subheader("评论用户地域分布")
            
            # 统计并展示无地域信息的评论
            total_count = len(df)
            # 筛选出无效的地理位置 (NaN, 空字符串, 或 "未知")
            unknown_mask = (
                df['ip_location'].isna() | 
                (df['ip_location'].astype(str).str.strip() == '') | 
                (df['ip_location'] == '未知')
            )
            unknown_count = unknown_mask.sum()
            
            # 计算缺失率
            unknown_ratio = unknown_count / total_count if total_count > 0 else 0
            
            # 如果缺失率过高 (例如超过 90%)，则拒绝生成
            if unknown_ratio > 0.9:
                st.error(f"⚠️ 无法生成热力图：数据中 {unknown_ratio:.1%} 的评论缺少IP属地信息（评论时间过于古老），有效样本过少。")
            else:
                if unknown_count > 0:
                    st.info(f"ℹ️ 数据说明：共有 {total_count} 条评论，其中 {unknown_count} 条 ({unknown_ratio:.1%}) 未显示IP属地，已在地图中排除。")
            
                heatmap_mode = st.radio("显示模式:", ["评论数量", "情感倾向"], horizontal=True)
                mode_key = 'sentiment' if heatmap_mode == "情感倾向" else 'count'
                
                try:
                    # Use a temporary file for the HTML output
                    temp_html = PROJECT_ROOT / "docs" / "temp_heatmap.html"
                    # Pass the DataFrame directly instead of path, and pass the mode
                    c = plot_geo_heatmap(df, str(temp_html), mode=mode_key)
                    if c:
                        # Render HTML in Streamlit
                        import streamlit.components.v1 as components
                        with open(temp_html, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        components.html(html_content, height=600)
                    else:
                        st.warning("无法生成热力图。")
                except Exception as e:
                    st.error(f"热力图生成失败: {e}")

    with tab4:
        st.subheader("评论数据预览")
        st.dataframe(df[['content', 'labels', 'time']].head(100) if 'time' in df.columns else df[['content', 'labels']].head(100))
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下载完整分析结果 (CSV)",
            data=csv,
            file_name=f"sentiment_analysis_{st.session_state.get('current_bv', 'result')}.csv",
            mime='text/csv',
        )
