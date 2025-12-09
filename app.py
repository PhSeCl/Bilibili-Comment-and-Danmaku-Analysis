import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import time

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Import project modules
try:
    from src.crawler.main_crawler import crawl_comments_by_bv, crawl_danmaku_by_bv, get_video_info
    from run_prediction import run_prediction_pipeline
    from src.visualization.distribution import plot_emotion_distribution
    from src.visualization.timeline import plot_comment_timeline
    from src.visualization.viz_geo_heatmap import plot_geo_heatmap
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# Page Config
st.set_page_config(
    page_title="Bilibili Comment Analysis",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📺 Bilibili 评论情感分析系统")
st.markdown("---")

# Sidebar: Configuration
st.sidebar.header("⚙️ 参数设置")

bv_code = st.sidebar.text_input("BV 号 (例如 BV1xx411c7mD)", value="BV1xx411c7mD")
max_pages = st.sidebar.number_input("爬取页数 (每页20条)", min_value=1, max_value=100, value=5)
max_danmaku = st.sidebar.number_input("弹幕爬取条数 (0为不限制)", min_value=0, value=1000, step=100)

st.sidebar.markdown("---")
st.sidebar.info("提示：先爬取数据，再进行分析。")

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
                output_csv = PROJECT_ROOT / "data" / "processed" / f"predictions_{Path(current_raw_data).stem}.csv"
                df = run_prediction_pipeline(input_path=current_raw_data, output_path=output_csv)
                
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["情感分布", "时间趋势", "地域热力图", "原始数据"])
    
    with tab1:
        st.subheader("总体情感分布")
        try:
            fig, _ = plot_emotion_distribution(df, save_path=None)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"绘图失败: {e}")
            
    with tab2:
        st.subheader("情感随时间变化")
        if 'date' in df.columns or 'time' in df.columns:
            # Ensure date column exists
            date_col = 'time' if 'time' in df.columns else 'date'
            try:
                # Convert to datetime if needed
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                fig_timeline, _ = plot_comment_timeline(df, date_column=date_col, freq='D')
                if fig_timeline:
                    st.pyplot(fig_timeline)
                else:
                    st.info("数据不足以生成时间序列图。")
            except Exception as e:
                st.error(f"时间序列绘图失败: {e}")
        else:
            st.warning("数据中缺少时间列，无法绘制趋势图。")
            
    with tab3:
        st.subheader("评论用户地域分布")
        if 'ip_location' in df.columns:
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
        else:
            st.warning("数据中缺少 'ip_location' 列，无法生成地域热力图。")

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
