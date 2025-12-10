# ================= 核心配置 =================
# 默认 Cookie (仅供测试使用，建议用户在 GUI 中输入自己的 Cookie)
DEFAULT_COOKIE = "buvid3=11A053EB-4305-951B-A200-EA70F6F6776018698infoc; b_nut=1757409318; _uuid=72937DA3-810D4-C9B5-71C2-CD25F1043656820323infoc; buvid_fp=dc1135814a44246cf5fcf2b711aa947a; buvid4=46D2875C-54CC-993D-FEDB-F80B428681E442672-024081914-vdm7BfKErMTXKkZ8dFJ01g%3D%3D; theme-tip-show=SHOWED; rpdid=|(JJmYYk|~|m0J'u~l~RuJY|k; enable_web_push=DISABLE; PVID=2; CURRENT_QUALITY=80; CURRENT_FNVAL=4048; DedeUserID=3690981121591537; DedeUserID__ckMd5=3e56f2ac8bafead3; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjUzNjc0MTAsImlhdCI6MTc2NTEwODE1MCwicGx0IjotMX0.VFYmKOl0JCuY_fPQy5wyzBk23apC9jqhv3AmbznyhIk; bili_ticket_expires=1765367350; SESSDATA=4cd253a5%2C1780660211%2Cca1fd%2Ac1CjATc8Ew_eLVsUNXXuJ7-uuFBS30HYD09HJxTv9DznKX00QBBaolx-FGFvIlL6ie4WsSVk54VWFfUnIzd2NtcEpxdlVnMEh1N3V4c3paQ0JTeHRZc1RHdmw1cVhaNmpvTzBVSG5IR19NREpMVGYxZlVOMUZCbVgweUFQNGFJN0s0ZzJ4RjNhdmZ3IIEC; bili_jct=5edd1370f041d96d75ab92be4f81398c; b_lsid=675DD184_19AFE4C7898; bsource=search_bing; home_feed_column=4; browser_resolution=1106-935; theme_style=dark"

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