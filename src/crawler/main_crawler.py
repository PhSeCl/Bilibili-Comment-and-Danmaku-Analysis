import requests
import time
import csv
import random
import re
import os
import json
import config 

def get_video_info(bv):
    """通过BV号获取视频详细信息 (OID, CID, 标题, 作者, 时间, 标签)"""
    url = f"https://www.bilibili.com/video/{bv}"
    # 既然要抓详细信息，不如直接调 API，比正则爬网页更稳
    api_url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": bv}
    
    try:
        resp = requests.get(api_url, params=params, headers=config.HEADERS)
        data = resp.json()
        
        if data['code'] == 0:
            info = data['data']
            # 提取我们需要的所有信息
            return {
                "oid": info['aid'],
                "cid": info['cid'],
                "title": info['title'],
                "owner": info['owner']['name'],
                "pubdate": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['pubdate'])),
                "tags": [tag['tag_name'] for tag in info.get('tags', [])] if 'tags' in info else []
                # 注意：API v2 有时 tags 不在这里，如果不重要可以先忽略，或者调另一个 tag 接口
                # 这里简单处理，如果没有 tags 字段就留空
            }
        else:
            print(f"❌ 获取视频信息失败: {data['message']}")
            return None
    except Exception as e:
        print(f"❌ 网络请求错误: {e}")
        return None

def write_metadata(filename, video_info):
    """在CSV文件开头写入视频元数据"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 为了不破坏 CSV 结构，我们把元数据写成注释形式 (# 开头)
    # 或者直接写在前几行，后续读取时跳过
    with open(filename, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["# 视频标题", video_info['title']])
        writer.writerow(["# BV号", config.BV_CODE]) # 这里也可以用参数传进来的 bv
        writer.writerow(["# 作者", video_info['owner']])
        writer.writerow(["# 发布时间", video_info['pubdate']])
        # 标签可能含有逗号，为了防止 CSV 错位，拼接成一个字符串
        tags_str = "|".join(video_info['tags']) if video_info['tags'] else "无标签"
        writer.writerow(["# 标签", tags_str])
        writer.writerow([]) # 空一行，美观
        # 这里不写表头，表头留给后面的函数写

# ==================== 评论爬取部分 ====================
def fetch_comments(oid, page):
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,
        "oid": oid,
        "sort": 2, # 如果要爬全部，建议还是用 2 (按时间)；如果失效了再改 0
        "pn": page,
        "ps": 20
    }
    try:
        resp = requests.get(url, params=params, headers=config.HEADERS)
        data = resp.json()
        if data['code'] == 0:
            return data['data']['replies']
        return None
    except Exception as e:
        print(f"❌ 获取评论第 {page} 页失败: {e}")
        return None

def save_comments_to_csv(comments, filename, is_first_write=False):
    """保存评论"""
    # 定义 CSV 表头
    headers = ['rpid', 'username', 'level', 'content', 'likes', 'location', 'date']
    
    with open(filename, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # 只有在第一次写入数据时，才写表头
        if is_first_write:
            writer.writerow(headers)
        
        count = 0
        if not comments: return 0
        
        for c in comments:
            if not c: continue
            try:
                rpid = c['rpid']
                uname = c['member']['uname']
                content = c['content']['message']
                likes = c['like']
                ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['ctime']))
                level = c['member']['level_info']['current_level']
                raw_location = c.get('reply_control', {}).get('location', '')
                location = raw_location.replace("IP属地：", "") if raw_location else "未知"
                
                writer.writerow([rpid, uname, level, content, likes, location, ctime])
                count += 1
            except Exception as e:
                print(f"⚠️ 解析失败: {e} | 数据片段: {str(c)[:50]}...") 
                continue
        return count

# ==================== 弹幕爬取部分 ====================
def crawl_danmaku_xml(cid):
    url = f"https://comment.bilibili.com/{cid}.xml"
    try:
        resp = requests.get(url, headers=config.HEADERS)
        resp.encoding = 'utf-8'
        patterns = re.findall(r'<d p="([^"]+)">([^<]+)</d>', resp.text)
        
        results = []
        for p_attr, content in patterns:
            attrs = p_attr.split(',')
            video_time = float(attrs[0])
            date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(attrs[4])))
            uid = attrs[6]
            results.append({
                'time': video_time,
                'date': date_time,
                'uid': uid,
                'content': content
            })
        return results
    except Exception as e:
        print(f"❌ XML 解析失败: {e}")
        return []

def save_danmaku_to_csv(danmaku_list, filename, is_first_write=False):
    headers = ['video_time', 'real_time', 'content', 'user_hash']
    
    with open(filename, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if is_first_write:
            writer.writerow(headers)
        
        count = 0
        for d in danmaku_list:
            writer.writerow([
                f"{d['time']:.2f}", 
                d['date'], 
                d['content'], 
                d['uid']
            ])
            count += 1
        return count

# ==================== 主程序 ====================
if __name__ == "__main__":
    print("=======================================")
    print("     B站评论/弹幕 交互式爬虫 v2.1     ")
    print("=======================================")
    
    input_bv = input("📺 请输入视频 BV 号 (例如 BV1xx...): ").strip()
    if not input_bv:
        print("⚠️ 未输入 BV 号，将使用配置文件中的默认值...")
        input_bv = config.BV_CODE
    
    print(f"🔍 正在获取视频信息: {input_bv} ...")
    video_info = get_video_info(input_bv)
    
    if not video_info:
        exit()
    
    print(f"✅ 获取成功: {video_info['title']}")
    print(f"   UP主: {video_info['owner']} | 发布于: {video_info['pubdate']}")
    
    oid = video_info['oid']
    cid = video_info['cid']
    
    # 2. 用户选择
    print("\n请选择要爬取的内容：")
    print("1. 📝 评论 (含 IP、等级、点赞等)")
    print("2. 🚀 弹幕 (当前弹幕池)")
    choice = input("👉 请输入数字 (1 或 2): ").strip()
    
    if choice == '1':
        page_input = input("\n📄 请输入要爬取的页数 (输入 -1 爬取全部): ").strip()
        try:
            max_pages = int(page_input)
        except ValueError:
            max_pages = 5 
            print("⚠️ 输入非法，默认爬取 5 页")

        # 1. 写入元数据 (这会覆盖旧文件)
        write_metadata(config.COMMENT_SAVE_PATH, video_info)
        print(f"📝 已写入视频信息到: {config.COMMENT_SAVE_PATH}")

        print("\n--- 开始爬取评论 ---")
        total_saved = 0
        page = 1
        is_first_data = True # 标记是否是第一批数据(用于写表头)
        
        while True:
            if max_pages != -1 and page > max_pages:
                print("✅ 达到指定页数，停止。")
                break
            
            print(f"📡 正在请求第 {page} 页...", end="")
            replies = fetch_comments(oid, page)
            
            if not replies:
                print("\n⚠️ 本页无数据 (可能已爬完)，停止。")
                break
                
            saved_count = save_comments_to_csv(
                replies, 
                filename=config.COMMENT_SAVE_PATH, 
                is_first_write=is_first_data
            )
            
            # 写完一次后，后面就都不是“第一次”了
            if saved_count > 0:
                is_first_data = False
                
            total_saved += saved_count
            print(f" -> 保存 {saved_count} 条")
            
            time.sleep(random.uniform(1.0, 2.5))
            page += 1
            
        print(f"\n🎉 评论爬取结束！共 {total_saved} 条。")

    elif choice == '2':
        # 1. 写入元数据
        write_metadata(config.DANMAKU_SAVE_PATH, video_info)
        print(f"📝 已写入视频信息到: {config.DANMAKU_SAVE_PATH}")
        
        print("\n--- 开始爬取弹幕 ---")
        danmaku_list = crawl_danmaku_xml(cid)
        
        if danmaku_list:
            count = save_danmaku_to_csv(
                danmaku_list, 
                filename=config.DANMAKU_SAVE_PATH, 
                is_first_write=True
            )
            print(f"\n🎉 弹幕爬取结束！共 {count} 条。")
        else:
            print("⚠️ 未爬取到弹幕。")
            
    else:
        print("❌ 输入无效，程序退出。")