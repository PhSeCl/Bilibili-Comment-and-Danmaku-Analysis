# ================= 核心配置 =================
# 默认 Cookie (仅供测试使用，建议用户在 GUI 中输入自己的 Cookie)
DEFAULT_COOKIE = "buvid3=11A053EB-4305-951B-A200-EA70F6F6776018698infoc; b_nut=1757409318; _uuid=72937DA3-810D4-C9B5-71C2-CD25F1043656820323infoc; buvid_fp=dc1135814a44246cf5fcf2b711aa947a; buvid4=46D2875C-54CC-993D-FEDB-F80B428681E442672-024081914-vdm7BfKErMTXKkZ8dFJ01g%3D%3D; theme-tip-show=SHOWED; rpdid=|(JJmYYk|~|m0J'u~l~RuJY|k; enable_web_push=DISABLE; PVID=2; CURRENT_QUALITY=80; CURRENT_FNVAL=4048; DedeUserID=3690981121591537; DedeUserID__ckMd5=3e56f2ac8bafead3; b_lsid=891EB87E_19B0B4AB798; bsource=search_bing; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjU2ODAyMDYsImlhdCI6MTc2NTQyMDk0NiwicGx0IjotMX0.CEJ0Mh5miRrG2KIHq4EWeoeTaczMN205yvvZsZGbMw4; bili_ticket_expires=1765680146; SESSDATA=7fec23da%2C1780973007%2C7202b%2Ac1CjACKb3yN6PGGtYV2ZIUCMob6YyEAISppbXKxyFwM88CN_xotRsDakIh9hxWd5_elpcSVjdXWWRjY1JDTWEzX2M2NmRGRVRSTTNzZEUyVmhhMElTbWczRE5FWG1jV1plNGx5OGVmclZ2bXJHRExaM0dXYnU1dUJncktNWld4UjlxY2ZscGdETGtnIIEC; bili_jct=f8cf931bc3f3920e3d4b059a6e98bcd9; sid=dnbbvvbd; home_feed_column=4; browser_resolution=841-935; theme_style=dark"

# 当前使用的 Cookie (将在运行时被覆盖)
COOKIE = DEFAULT_COOKIE

# ================= 文件保存路径 =================
import os
# 获取当前脚本所在目录的上一级再上一级 (即项目根目录)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

# 输出文件路径
COMMENT_SAVE_PATH = os.path.join(DATA_RAW_DIR, "comments.csv")
DANMAKU_SAVE_PATH = os.path.join(DATA_RAW_DIR, "danmaku.csv")

# ================= 请求头 =================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}