# ================= 核心配置 =================
# 这里填你的 Cookie (直接粘贴控制台里 document.cookie 的输出)
# 注意：Cookie 包含个人隐私，不要把这个文件 push 到公开仓库！
# 理论上是这样，但是因为这是私有仓库，用我小号的Cookie就行
COOKIE = "buvid3=11A053EB-4305-951B-A200-EA70F6F6776018698infoc; b_nut=1757409318; _uuid=72937DA3-810D4-C9B5-71C2-CD25F1043656820323infoc; buvid_fp=dc1135814a44246cf5fcf2b711aa947a; buvid4=46D2875C-54CC-993D-FEDB-F80B428681E442672-024081914-vdm7BfKErMTXKkZ8dFJ01g%3D%3D; theme-tip-show=SHOWED; rpdid=|(JJmYYk|~|m0J'u~l~RuJY|k; enable_web_push=DISABLE; PVID=2; CURRENT_QUALITY=80; CURRENT_FNVAL=4048; DedeUserID=3690981121591537; DedeUserID__ckMd5=3e56f2ac8bafead3; home_feed_column=5; bsource=search_bing; browser_resolution=1699-935; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjUzNjc0MTAsImlhdCI6MTc2NTEwODE1MCwicGx0IjotMX0.VFYmKOl0JCuY_fPQy5wyzBk23apC9jqhv3AmbznyhIk; bili_ticket_expires=1765367350; SESSDATA=4cd253a5%2C1780660211%2Cca1fd%2Ac1CjATc8Ew_eLVsUNXXuJ7-uuFBS30HYD09HJxTv9DznKX00QBBaolx-FGFvIlL6ie4WsSVk54VWFfUnIzd2NtcEpxdlVnMEh1N3V4c3paQ0JTeHRZc1RHdmw1cVhaNmpvTzBVSG5IR19NREpMVGYxZlVOMUZCbVgweUFQNGFJN0s0ZzJ4RjNhdmZ3IIEC; bili_jct=5edd1370f041d96d75ab92be4f81398c; sid=52v8ifqo; b_lsid=B43466E6_19AF9935337; theme_style=dark"

# ================= 爬虫目标 =================
# 视频 BV 号(这个是千恋*万花的OP)
BV_CODE = "BV1L4421S7Kr" 

# ================= 爬取参数 =================
# 评论爬取页数 (0 表示爬完为止，建议设置一个上限比如 50，防止封号)
MAX_COMMENT_PAGES = 5

# 弹幕爬取日期 (格式: 'YYYY-MM-DD')
# 注意：只有登录用户才能爬取历史弹幕，且通常只能爬最近几个月的
DANMAKU_DATE = '2025-01-20'

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
    "Cookie": COOKIE,
    "Referer": "https://www.bilibili.com/"
}