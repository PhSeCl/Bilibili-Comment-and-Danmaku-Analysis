import requests
import time
import csv
import random
import re
import os

# ================= 配置区域 =================
# 1. 把你的 Cookie 粘贴在下面引号里 (非常重要！)
COOKIE = "buvid3=11A053EB-4305-951B-A200-EA70F6F6776018698infoc; b_nut=1757409318; _uuid=72937DA3-810D4-C9B5-71C2-CD25F1043656820323infoc; buvid_fp=dc1135814a44246cf5fcf2b711aa947a; buvid4=46D2875C-54CC-993D-FEDB-F80B428681E442672-024081914-vdm7BfKErMTXKkZ8dFJ01g%3D%3D; theme-tip-show=SHOWED; rpdid=|(JJmYYk|~|m0J'u~l~RuJY|k; enable_web_push=DISABLE; PVID=2; CURRENT_QUALITY=80; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjQ3Njc5MDgsImlhdCI6MTc2NDUwODY0OCwicGx0IjotMX0.2S28OIF5cYR_bOXT1qyH4XXl60eawcweU41Fo_n14ZY; bili_ticket_expires=1764767848; CURRENT_FNVAL=4048; b_lsid=BBAF31097_19ADEF10203; bsource=search_bing; SESSDATA=5d603be8%2C1780229269%2C696db%2Ac2CjBkh2iXeVEluLEYCm11C6I5XwzKuBeRr6847DDMAFieeIEY4KXCi_8P9exRSIo389MSVnRvdjdpdm5TNm9PMmJ4MFN1dnJaQlpzOHJjSEt2anMzZlVqWkJUQzhuekdzYzBFYWZYb29XZktBTnJ1YnJfQVpfME1DcW9xTm03SV9pb3ZnWktqaDB3IIEC; bili_jct=7e5274f4573f703bfadf55000d87b3a9; DedeUserID=3690981121591537; DedeUserID__ckMd5=3e56f2ac8bafead3; sid=8c1aob6f; home_feed_column=4; browser_resolution=702-941; theme_style=dark"

# 2. 要爬取的视频 BV 号 (例如：千恋*万花 的OP)
BV_CODE = "BV1L4421S7Kr"  # 你可以随时改这个BV号

# 3. 想要爬取的页数 (每页约20条，建议先填5页测试)
MAX_PAGES = 5
# ===========================================

# 设置请求头，伪装成浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Cookie": COOKIE
}

def get_oid(bv):
    """通过BV号获取视频的数字ID(oid)"""
    url = f"https://www.bilibili.com/video/{bv}"
    try:
        resp = requests.get(url, headers=HEADERS)
        # 使用正则提取 oid (aid)
        match = re.search(r'"aid":(\d+)', resp.text)
        if match:
            return match.group(1)
        else:
            print("❌ 找不到 oid，请检查 BV 号是否正确或 Cookie 是否失效。")
            return None
    except Exception as e:
        print(f"❌ 网络请求错误: {e}")
        return None

def fetch_comments(oid, page):
    """获取单页评论"""
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,      # 1表示视频评论
        "oid": oid,     # 视频ID
        "sort": 2,      # 2表示按热度排序，0表示按时间
        "pn": page,     # 页码
        "ps": 20        # 每页条数
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS)
        data = resp.json()
        if data['code'] == 0:
            return data['data']['replies'] # 返回评论列表
        else:
            print(f"⚠️ 接口报错: {data['message']}")
            return None
    except Exception as e:
        print(f"❌ 获取第 {page} 页失败: {e}")
        return None

def save_to_csv(comments, filename="bili_comments.csv"):
    """保存数据到 CSV 文件"""
    # 自动判断是新建文件还是追加写入
    file_exists = os.path.isfile(filename)
    
    # 确保保存目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # 如果是新文件，先写入表头
        if not file_exists:
            writer.writerow(['rpid', 'username', 'content', 'likes', 'date'])
        
        count = 0
        for c in comments:
            # 有时候 API 会返回 None (比如被折叠的评论)
            if not c: continue
            
            rpid = c['rpid']
            uname = c['member']['uname']
            content = c['content']['message']
            likes = c['like']
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['ctime']))
            
            writer.writerow([rpid, uname, content, likes, ctime])
            count += 1
        return count

if __name__ == "__main__":
    print("🕷️ 爬虫启动...")
    
    # 1. 获取 OID
    oid = get_oid(BV_CODE)
    if not oid:
        exit()
    
    print(f"✅ 成功获取视频 OID: {oid}")
    
    # 2. 循环爬取
    total_saved = 0
    # 保存路径设置在 data/raw 目录下
    save_path = "../../data/raw/sample_comments.csv" 
    
    for page in range(1, MAX_PAGES + 1):
        print(f"📄 正在爬取第 {page} 页...")
        replies = fetch_comments(oid, page)
        
        if not replies:
            print("⚠️ 本页无数据或已爬完，停止。")
            break
            
        saved_count = save_to_csv(replies, filename=save_path)
        total_saved += saved_count
        
        # 随机等待 1~3 秒，防止被 B 站封号
        sleep_time = random.uniform(1, 3)
        time.sleep(sleep_time)
    
    print(f"\n🎉 爬取结束！共保存 {total_saved} 条评论。")
    print(f"📂 文件保存在: {os.path.abspath(save_path)}")