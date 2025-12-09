import requests
import time
import csv
import random
import re
import os
import json
# 导入配置文件
import config 

def check_cookie():
    """检查 Cookie 是否有效"""
    url = "https://api.bilibili.com/x/web-interface/nav"
    try:
        print("🍪 正在检查 Cookie 状态...")
        resp = requests.get(url, headers=config.HEADERS)
        data = resp.json()
        if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
            print(f"✅ Cookie 有效，当前用户: {data['data']['uname']}")
            return True
        else:
            print("⚠️ Cookie 已失效或未登录！")
            print("   (这可能会导致无法获取历史弹幕，或触发风控验证码)")
            return False
    except Exception as e:
        print(f"⚠️ 检查 Cookie 时发生网络异常: {e}")
        return False

def get_video_info(bv):
    """通过BV号获取 oid (aid) 和 cid"""
    url = f"https://www.bilibili.com/video/{bv}"
    try:
        resp = requests.get(url, headers=config.HEADERS)
        # 正则提取 aid (即 oid)
        aid_match = re.search(r'"aid":(\d+)', resp.text)
        # 正则提取 cid (弹幕要用到)
        cid_match = re.search(r'"cid":(\d+)', resp.text)
        
        if aid_match and cid_match:
            return {
                "oid": aid_match.group(1),
                "cid": cid_match.group(1)
            }
        else:
            print("❌ 找不到 oid 或 cid，请检查 BV 号或 Cookie。")
            return None
    except Exception as e:
        print(f"❌ 网络请求错误: {e}")
        return None

# ==================== 评论爬取部分 ====================
def fetch_comments(oid, page):
    """获取单页评论"""
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,
        "oid": oid,
        "sort": 2,
        "pn": page,
        "ps": 20
    }
    
    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=config.HEADERS, timeout=10) # 增加 timeout
            data = resp.json()
            if data['code'] == 0:
                return data['data']['replies']
            elif data['code'] == 12002: # 评论区已关闭或无权限
                print(f"⚠️ 评论区可能已关闭或需要权限 (Code: 12002)")
                return None
            else:
                print(f"⚠️ API 返回错误 (Code: {data['code']}): {data.get('message', 'Unknown error')}")
                return None
                
        except requests.exceptions.SSLError as e:
            print(f"⚠️ SSL 错误 (尝试 {attempt+1}/{max_retries}): {e}")
            time.sleep(2 * (attempt + 1)) # 遇到 SSL 错误多等一会儿
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ 连接错误 (尝试 {attempt+1}/{max_retries}): {e}")
            time.sleep(1 * (attempt + 1))
        except Exception as e:
            print(f"❌ 获取评论第 {page} 页失败: {e}")
            return None
            
    print(f"❌ 第 {page} 页重试 {max_retries} 次后仍失败，跳过。")
    return None

def save_comments_to_csv(comments, filename):
    """保存评论"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)

    # 尝试打开目标文件；如果被占用（例如 Excel 已经打开该 CSV），回退到带时间戳的备用文件
    try:
        f = open(filename, mode='a', encoding='utf-8-sig', newline='')
        opened_filename = filename
    except PermissionError:
        # 生成备份文件名
        ts = time.strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(filename)
        alt_filename = f"{base}_{ts}{ext}"
        print(f"⚠️ 无法写入目标文件（可能被占用）。改写入备用文件: {alt_filename}")
        f = open(alt_filename, mode='a', encoding='utf-8-sig', newline='')
        opened_filename = alt_filename

    with f:
        writer = csv.writer(f)
        if not file_exists:
            # 表头
            writer.writerow(['content', 'username', 'time', 'ip_location', 'user_level', 'likes'])
        
        count = 0
        if not comments: return 0
        for c in comments:
            if not c: continue
            content = c['content']['message']
            username = c['member']['uname']
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['ctime']))
            location = c.get('reply_control', {}).get('location', '')
            if location:
                location = location.replace('IP属地：', '')
            user_level = c['member']['level_info']['current_level']
            likes = c['like']
            writer.writerow([content, username, ctime, location, user_level, likes])
            count += 1
        return count

# ==================== 弹幕爬取部分 ====================
def fetch_danmaku(cid, date):
    """获取指定日期的历史弹幕"""
    # B站历史弹幕接口 (返回JSON，比XML好处理)
    url = "https://api.bilibili.com/x/v2/dm/web/history/seg.so"
    params = {
        "type": 1,
        "oid": cid,
        "date": date
    }
    try:
        print(f"📡 正在请求 {date} 的弹幕...")
        resp = requests.get(url, params=params, headers=config.HEADERS)
        
        # 注意：如果 Cookie 失效或非会员，这个接口可能返回空或乱码
        # 历史弹幕接口返回的是二进制 protobuf 或者是特殊编码，简单处理可以用 web 接口
        # 这里尝试用更简单的 web 接口，如果不行则建议用 xml 接口
        # 备用方案：普通弹幕池 https://comment.bilibili.com/{cid}.xml (XML格式)
        # 但为了统一 CSV 格式，我们尝试解析 JSON 格式的历史接口（需要正确 Cookie）
        
        # 如果直接返回了 JSON 文本
        try:
            data = resp.json()
            if data.get('code') != 0:
                print(f"⚠️ 接口报错: {data.get('message')}")
                return None
            return data['data']['dm']
        except:
            print("⚠️ 响应不是标准JSON，尝试使用 XML 接口或检查 Cookie 权限")
            return None
            
    except Exception as e:
        print(f"❌ 获取弹幕失败: {e}")
        return None

def crawl_danmaku_xml(cid):
    """备用：爬取当前弹幕池 (XML接口，不需要特定日期，比较稳定)"""
    url = f"https://comment.bilibili.com/{cid}.xml"
    try:
        resp = requests.get(url, headers=config.HEADERS)
        resp.encoding = 'utf-8'
        # 简单的正则提取，不想引入 lxml 库增加复杂度
        # 格式: <d p="...25.87400,1,25,16777215,1670000000,0,0,0">弹幕内容</d>
        # p属性: 时间,模式,字体,颜色,时间戳,连接池,用户ID,行ID
        patterns = re.findall(r'<d p="([^"]+)">([^<]+)</d>', resp.text)
        
        results = []
        for p_attr, content in patterns:
            attrs = p_attr.split(',')
            video_time = float(attrs[0]) # 视频内时间
            date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(attrs[4])))
            uid = attrs[6] # 用户Hash
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

def save_danmaku_to_csv(danmaku_list, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 改为覆盖模式 'w'
    with open(filename, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # 总是写入表头
        writer.writerow(['video_time', 'real_time', 'content', 'user_hash'])
        
        count = 0
        for d in danmaku_list:
            # 这里兼容一下 fetch_danmaku 和 crawl_danmaku_xml 的返回格式
            # 如果是用 XML 爬的：
            writer.writerow([
                f"{d['time']:.2f}", 
                d['date'], 
                d['content'], 
                d['uid']
            ])
            count += 1
        return count

# ==================== 封装好的调用接口 ====================
def crawl_comments_by_bv(bv_code, max_pages=None, output_path=None):
    """
    根据 BV 号爬取评论的封装函数
    """
    if max_pages is None:
        max_pages = config.MAX_COMMENT_PAGES
    if output_path is None:
        output_path = config.COMMENT_SAVE_PATH
        
    print(f"🎯 [API] 开始爬取评论: {bv_code}, 页数: {max_pages}")
    
    # 1. 获取视频信息
    video_info = get_video_info(bv_code)
    if not video_info:
        return 0
    
    oid = video_info['oid']
    
    # 2. 循环爬取
    total_saved = 0
    for page in range(1, max_pages + 1):
        print(f"📄 第 {page} 页...")
        replies = fetch_comments(oid, page)
        if not replies:
            print("⚠️ 本页无数据或已爬完。")
            break
        saved_count = save_comments_to_csv(replies, filename=output_path)
        total_saved += saved_count
        time.sleep(random.uniform(1.5, 3.5))
        
    print(f"🎉 [API] 评论爬取结束！共 {total_saved} 条。")
    return total_saved

def crawl_danmaku_by_bv(bv_code, max_count=None, output_path=None):
    """
    根据 BV 号爬取弹幕的封装函数
    """
    if output_path is None:
        output_path = config.DANMAKU_SAVE_PATH
        
    print(f"🎯 [API] 开始爬取弹幕: {bv_code}")
    
    # 1. 获取视频信息
    video_info = get_video_info(bv_code)
    if not video_info:
        return 0
    
    cid = video_info['cid']
    
    # 2. 爬取 XML
    danmaku_list = crawl_danmaku_xml(cid)
    
    if danmaku_list:
        if max_count:
            danmaku_list = danmaku_list[:max_count]
        
        count = save_danmaku_to_csv(danmaku_list, filename=output_path)
        print(f"🎉 [API] 弹幕爬取结束！共 {count} 条。")
        return count
    else:
        print("⚠️ [API] 未爬取到弹幕。")
        return 0

# ==================== 主程序 ====================
if __name__ == "__main__":
    # 0. 检查 Cookie (新增功能)
    check_cookie()
    print("=======================================")

    # 运行时输入 BV 号（可选，默认使用 config 中的值）
    bv_code = input("请输入 BV 号（按Enter使用默认值: " + config.BV_CODE + "）：").strip()
    if not bv_code:
        bv_code = config.BV_CODE
    
    print(f"🎯 目标 BV 号: {bv_code}")
    print("=======================================")
    
    # 1. 获取基础信息
    video_info = get_video_info(bv_code)
    if not video_info:
        exit()
    
    oid = video_info['oid']
    cid = video_info['cid']
    print(f"✅ 视频信息获取成功 [OID: {oid} | CID: {cid}]")
    
    # 2. 用户选择
    print("\n请选择要爬取的内容：")
    print("1. 📝 评论 (Comments)")
    print("2. 🚀 弹幕 (Danmaku)")
    choice = input("👉 请输入数字 (1 或 2): ").strip()
    
    if choice == '1':
        # ----- 爬评论 -----
        max_pages = input(f"请输入爬取页数（按Enter使用默认值: {config.MAX_COMMENT_PAGES}）：").strip()
        if max_pages:
            try:
                max_pages = int(max_pages)
            except ValueError:
                print(f"⚠️ 输入无效，使用默认值 {config.MAX_COMMENT_PAGES}")
                max_pages = config.MAX_COMMENT_PAGES
        else:
            max_pages = config.MAX_COMMENT_PAGES
        
        # 在开始爬取前，尝试删除旧文件以实现覆盖
        if os.path.exists(config.COMMENT_SAVE_PATH):
            try:
                os.remove(config.COMMENT_SAVE_PATH)
                print(f"🗑️ 已删除旧文件: {config.COMMENT_SAVE_PATH}")
            except PermissionError:
                print(f"⚠️ 无法删除旧文件 (可能被占用): {config.COMMENT_SAVE_PATH}")
            except Exception as e:
                print(f"⚠️ 删除旧文件失败: {e}")

        print("\n--- 开始爬取评论 ---")
        total_saved = 0
        for page in range(1, max_pages + 1):
            print(f"📄 第 {page} 页...")
            replies = fetch_comments(oid, page)
            if not replies:
                print("⚠️ 本页无数据或已爬完。")
                break
            saved_count = save_comments_to_csv(replies, filename=config.COMMENT_SAVE_PATH)
            total_saved += saved_count
            time.sleep(random.uniform(1.5, 3.5))
        print(f"\n🎉 评论爬取结束！共 {total_saved} 条。")
        print(f"📂 保存路径: {config.COMMENT_SAVE_PATH}")

    elif choice == '2':
        # ----- 爬弹幕 -----
        print("\n--- 开始爬取弹幕 ---")
        # 这里使用 XML 接口，因为它最稳定，不需要太复杂的 Cookie 权限也能跑
        danmaku_list = crawl_danmaku_xml(cid)
        
        if danmaku_list:
            max_count = input(f"请输入爬取条数限制（上限 {len(danmaku_list)} 条，按Enter使用最大值）：").strip()
            if max_count:
                try:
                    max_count = int(max_count)
                    danmaku_list = danmaku_list[:max_count]
                except ValueError:
                    print(f"⚠️ 输入无效，使用上限 {len(danmaku_list)} 条")
            
            count = save_danmaku_to_csv(danmaku_list, filename=config.DANMAKU_SAVE_PATH)
            print(f"\n🎉 弹幕爬取结束！共 {count} 条。")
            print(f"📂 保存路径: {config.DANMAKU_SAVE_PATH}")
        else:
            print("⚠️ 未爬取到弹幕，可能是弹幕池为空或网络问题。")
            
            
    else:
        print("❌ 输入无效，程序退出。")