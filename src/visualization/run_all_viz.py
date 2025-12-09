import os
import subprocess
import sys

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    print(f"--- 正在运行 {script_name} ---")
    try:
        subprocess.check_call([sys.executable, script_path])
        print(f"--- {script_name} 完成 ---\n")
    except subprocess.CalledProcessError as e:
        print(f"--- {script_name} 运行失败: {e} ---\n")

if __name__ == "__main__":
    scripts = [
        "viz_comment_distribution.py",
        "viz_danmaku_distribution.py",
        "viz_comment_timeline.py",
        "viz_danmaku_progress.py",
        "viz_geo_heatmap.py"
    ]
    
    print("开始批量生成可视化图表...\n")
    for script in scripts:
        run_script(script)
    print("所有可视化任务已完成。请查看 results/figures 目录。")
