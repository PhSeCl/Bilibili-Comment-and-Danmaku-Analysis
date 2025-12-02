import requests
import time
import csv
import random
import re
import os
# 导入刚才写的配置文件
import config 

def get_oid(bv):
    """通过BV号获取视频的数字ID(oid)"""
    url = f"https://www.bilibili.com/video/{bv}"
    try:
        # 直接使用 config.HEADERS
        resp = requests.get(url, headers=config.HEADERS)
        match = re.search(r'"aid":(\d+)', resp.text)
        if match:
            return match.group(1)
        else:
            print("❌ 找不到 oid，请检查 BV 号或 Cookie。")
            return None
    except Exception as e:
        print(f"❌ 网络请求错误: {e}")
        return None

def fetch_comments(oid, page):
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,
        "oid": oid,
        "sort": 2,
        "pn": page,
        "ps": 20
    }
    try:
        resp = requests.get(url, params=params, headers=config.HEADERS)
        data = resp.json()
        if data['code'] == 0:
            return data['data']['replies']
        else:
            # 有时候虽然code非0，但也可能只是没评论了
            return None
    except Exception as e:
        print(f"❌ 获取第 {page} 页失败: {e}")
        return None

def save_to_csv(comments, filename):
    # 自动创建目录
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['rpid', 'username', 'content', 'likes', 'date'])
        
        count = 0
        if not comments: return 0
        
        for c in comments:
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
    print("🕷️ 评论爬虫启动...")
    print(f"🎯 目标BV: {config.BV_CODE}")
    
    oid = get_oid(config.BV_CODE)
    if not oid: exit()
    
    total_saved = 0
    
    for page in range(1, config.MAX_COMMENT_PAGES + 1):
        print(f"📄 正在爬取第 {page} 页...")
        replies = fetch_comments(oid, page)
        
        if not replies:
            print("⚠️ 本页无数据或已爬完，停止。")
            break
            
        # 使用 config 里配置好的保存路径
        saved_count = save_to_csv(replies, filename=config.COMMENT_SAVE_PATH)
        total_saved += saved_count
        
        time.sleep(random.uniform(1.5, 3.5))
    
    print(f"\n🎉 结束！共保存 {total_saved} 条评论。")
    print(f"📂 文件路径: {config.COMMENT_SAVE_PATH}")