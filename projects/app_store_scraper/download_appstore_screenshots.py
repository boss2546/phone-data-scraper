#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍎 Apple App Store Screenshots Scraper & Multi-App Gallery Studio
ระบบดึงรูปภาพตัวอย่างหน้าจอ (Screenshots) ความละเอียดสูงสุดระดับ Retina/4K ของแอปพลิเคชันจาก Apple App Store (TH Store)
รองรับทั้งภาพ iPhone (สูงสุด 1290×2796), iPad (สูงสุด 2048×2732) และโลโก้ 1024×1024
พร้อมจัดเก็บแยกโฟลเดอร์รายแอป สร้าง JSON Manifest และ Web Studio แดชบอร์ดสุดหรูสไตล์ Pastel Mint
"""

import os
import sys
import time
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOTS_DIR = BASE_DIR / "data" / "appstore_screenshots"
MANIFEST_FILE = SCREENSHOTS_DIR / "screenshots_manifest.json"
PREVIEW_HTML = BASE_DIR / "appstore_screenshots_studio.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
}

# รายการ 35 แอปยอดนิยมพร้อม Apple App Store Track ID ทางการ (TH Storefront)
APPS_CONFIG = [
    {"id": "netflix", "name": "Netflix", "track_id": 363590051, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "iqiyi", "name": "iQIYI", "track_id": 1461999674, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "monomax", "name": "Monomax", "track_id": 869291017, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "prime_video", "name": "Prime Video", "track_id": 545519333, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "disney_plus", "name": "Disney+ Hotstar", "track_id": 1446075923, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "viu", "name": "Viu", "track_id": 1036095179, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "wetv", "name": "WeTV", "track_id": 1441531611, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "hbo_max", "name": "HBO Max", "track_id": 1666653815, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "youku", "name": "Youku", "track_id": 1619761040, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "bilibili", "name": "Bilibili", "track_id": 1548857482, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "oned", "name": "oneD", "track_id": 922370524, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "bugaboo", "name": "Bugaboo.TV", "track_id": 1319756939, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "true_id", "name": "TrueID", "track_id": 1013814221, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "truevisions_now", "name": "TrueVisions NOW", "track_id": 6479410006, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "ch3_plus", "name": "CH3 Plus", "track_id": 475642354, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "gagaoolala", "name": "GagaOOLala", "track_id": 1196141528, "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "shortmax", "name": "ShortMax", "track_id": 6464002625, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "dramawave", "name": "DramaWave", "track_id": 6670430706, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "dramabox", "name": "DramaBox", "track_id": 6445905219, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "reelshort", "name": "ReelShort", "track_id": 1636235979, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "shortwave", "name": "ShortsWave", "track_id": 6478104173, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "goodshort", "name": "GoodShort", "track_id": 6448176203, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "netshort", "name": "NetShort", "track_id": 6504849169, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "flickreels", "name": "FlickReels", "track_id": 6514312894, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "idrama", "name": "iDrama", "track_id": 6741501595, "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "capcut", "name": "CapCut", "track_id": 1500855883, "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "meitu", "name": "Meitu", "track_id": 416048305, "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "wink", "name": "Wink", "track_id": 1594288016, "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "beauticam", "name": "BeautyCam", "track_id": 592331499, "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "canva", "name": "Canva", "track_id": 897446215, "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "youtube", "name": "YouTube", "track_id": 544007664, "category": "สตรีมมิ่งเพลงและวิดีโอ"},
    {"id": "spotify", "name": "Spotify", "track_id": 324684580, "category": "สตรีมมิ่งเพลงและวิดีโอ"},
    {"id": "chatgpt", "name": "ChatGPT", "track_id": 6448311069, "category": "ปัญญาประดิษฐ์ (AI Tools)"},
    {"id": "gemini", "name": "Google", "track_id": 284815942, "category": "ปัญญาประดิษฐ์ (AI Tools)"},
    {"id": "microsoft_365", "name": "Microsoft Copilot", "track_id": 541164041, "category": "ซอฟต์แวร์ทำงาน (Office)"}
]


def transform_highres_url(url: str, device: str = "iphone", fmt: str = "png") -> str:
    """
    แปลง URL ของ Apple mzstatic ให้เป็นขนาดความละเอียดสูงสุด (Retina/4K)
    - iPhone: 1290x2796bb.{fmt}
    - iPad: 2048x2732bb.{fmt}
    - Artwork/Logo: 1024x1024bb.png
    """
    if not url:
        return ""
    if device == "artwork":
        return re.sub(r'/\d+x\d+bb\.[a-zA-Z]+$', f'/1024x1024bb.{fmt}', url)
    
    target_dim = "1290x2796bb" if device == "iphone" else "2048x2732bb"
    # ตัดขนาดเดิมออก เช่น /392x696bb.jpg แล้วแทนที่ด้วยความละเอียดสูง
    if re.search(r'/\d+x\d+bb\.[a-zA-Z]+$', url):
        return re.sub(r'/\d+x\d+bb\.[a-zA-Z]+$', f'/{target_dim}.{fmt}', url)
    return f"{url}/{target_dim}.{fmt}"


def fetch_app_metadata(track_id: int = None, search_term: str = None, country: str = "th"):
    """
    ดึงข้อมูล Metadata และ URL ภาพหน้าจอทั้งหมดของแอปผ่าน Official iTunes Storefront API
    """
    if track_id:
        url = f"https://itunes.apple.com/lookup?id={track_id}&country={country}"
    elif search_term:
        term = urllib.parse.quote(search_term)
        url = f"https://itunes.apple.com/search?term={term}&country={country}&entity=software&limit=1"
    else:
        return None

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception as e:
        print(f"    ⚠️ ข้อผิดพลาดในการเรียก iTunes API ({track_id or search_term}): {e}")
    return None


def download_single_image(args):
    """ดาวน์โหลดรูปภาพเดี่ยวพร้อมบันทึก (มี fallback หากความละเอียดสูงมากๆ ตอบสนอง error)"""
    url_highres, url_fallback, dest_path = args
    if dest_path.exists() and dest_path.stat().st_size > 5000:
        return True, dest_path.name

    # ลองดาวน์โหลดแบบ High-Res ก่อน
    for target_url in [url_highres, url_fallback]:
        if not target_url:
            continue
        try:
            req = urllib.request.Request(target_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                if len(data) > 1000:
                    dest_path.write_bytes(data)
                    return True, dest_path.name
        except Exception:
            continue

    return False, f"Failed: {dest_path.name}"


def process_app(app_info: dict, country: str = "th") -> dict:
    """ประมวลผลดึงและบันทึกรูปภาพทั้งหมดของ 1 แอป (แยก iPhone, iPad, Logo)"""
    app_id = app_info.get("id") or str(app_info.get("track_id"))
    name = app_info.get("name")
    track_id = app_info.get("track_id")
    category = app_info.get("category", "General")

    # ดึง Metadata จาก Apple
    raw_meta = fetch_app_metadata(track_id=track_id, search_term=name if not track_id else None, country=country)
    if not raw_meta:
        print(f"    ❌ ไม่พบข้อมูลสำหรับ: {name} (ID: {track_id})")
        return None

    resolved_track_id = raw_meta.get("trackId")
    track_name = raw_meta.get("trackName")
    artist_name = raw_meta.get("artistName")
    bundle_id = raw_meta.get("bundleId")
    appstore_url = raw_meta.get("trackViewUrl")
    version = raw_meta.get("version")
    rating = raw_meta.get("averageUserRating", 0.0)
    rating_count = raw_meta.get("userRatingCount", 0)
    price = raw_meta.get("formattedPrice", "Free")
    primary_genre = raw_meta.get("primaryGenreName", category)
    genres = raw_meta.get("genres", [primary_genre])
    description = raw_meta.get("description", "")
    release_notes = raw_meta.get("releaseNotes", "")
    file_size_bytes = int(raw_meta.get("fileSizeBytes", 0))
    file_size_mb = round(file_size_bytes / (1024 * 1024), 1) if file_size_bytes else 0

    # จัดเตรียมโฟลเดอร์สำหรับแอปนี้
    app_folder = SCREENSHOTS_DIR / app_id
    iphone_folder = app_folder / "iphone"
    ipad_folder = app_folder / "ipad"
    app_folder.mkdir(parents=True, exist_ok=True)
    iphone_folder.mkdir(parents=True, exist_ok=True)
    ipad_folder.mkdir(parents=True, exist_ok=True)

    download_tasks = []
    iphone_saved = []
    ipad_saved = []

    # 1. โลโก้แอปความละเอียดสูง (1024x1024)
    artwork_url = raw_meta.get("artworkUrl512") or raw_meta.get("artworkUrl100")
    logo_path = app_folder / "logo.png"
    if artwork_url:
        highres_art = transform_highres_url(artwork_url, device="artwork", fmt="png")
        download_tasks.append((highres_art, artwork_url, logo_path))

    # 2. ภาพหน้าจอ iPhone Screenshots
    iphone_shots = raw_meta.get("screenshotUrls", [])
    for idx, raw_url in enumerate(iphone_shots, 1):
        filename = f"screenshot_{idx:02d}.png"
        filepath = iphone_folder / filename
        highres_url = transform_highres_url(raw_url, device="iphone", fmt="png")
        fallback_url = transform_highres_url(raw_url, device="iphone", fmt="jpg")
        download_tasks.append((highres_url, fallback_url, filepath))
        iphone_saved.append({
            "index": idx,
            "filename": filename,
            "rel_path": f"data/appstore_screenshots/{app_id}/iphone/{filename}",
            "device": "iPhone",
            "source_url": highres_url
        })

    # 3. ภาพหน้าจอ iPad Screenshots
    ipad_shots = raw_meta.get("ipadScreenshotUrls", [])
    for idx, raw_url in enumerate(ipad_shots, 1):
        filename = f"screenshot_{idx:02d}.png"
        filepath = ipad_folder / filename
        highres_url = transform_highres_url(raw_url, device="ipad", fmt="png")
        fallback_url = transform_highres_url(raw_url, device="ipad", fmt="jpg")
        download_tasks.append((highres_url, fallback_url, filepath))
        ipad_saved.append({
            "index": idx,
            "filename": filename,
            "rel_path": f"data/appstore_screenshots/{app_id}/ipad/{filename}",
            "device": "iPad",
            "source_url": highres_url
        })

    # ดาวน์โหลดภาพทั้งหมดของแอปนี้ด้วย Multi-threading
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(download_single_image, task) for task in download_tasks]
        for f in as_completed(futures):
            f.result()

    # ประกอบ Metadata บันทึก info.json
    app_meta = {
        "id": app_id,
        "name": name or track_name,
        "track_name": track_name,
        "artist_name": artist_name,
        "track_id": resolved_track_id,
        "bundle_id": bundle_id,
        "category": category,
        "primary_genre": primary_genre,
        "genres": genres,
        "version": version,
        "price": price,
        "rating": rating,
        "rating_count": rating_count,
        "file_size_mb": file_size_mb,
        "appstore_url": appstore_url,
        "logo_rel_path": f"data/appstore_screenshots/{app_id}/logo.png",
        "description": description[:1000] + ("..." if len(description) > 1000 else ""),
        "release_notes": release_notes[:500] if release_notes else "",
        "total_iphone_screenshots": len(iphone_saved),
        "total_ipad_screenshots": len(ipad_saved),
        "total_screenshots": len(iphone_saved) + len(ipad_saved),
        "iphone_screenshots": iphone_saved,
        "ipad_screenshots": ipad_saved
    }

    (app_folder / "info.json").write_text(json.dumps(app_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return app_meta


def generate_studio_html(manifest: list, total_images: int):
    """สร้างแดชบอร์ด Web Studio สุดหรูแบบฉบับ Ultra-Luxury Pastel Mint & Emerald Glassmorphism"""
    manifest_json = json.dumps(manifest, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🍎 Apple App Store Screenshots Studio — Retina 4K Gallery</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #070d0b;
      --card-bg: rgba(14, 26, 21, 0.75);
      --card-border: rgba(52, 211, 153, 0.18);
      --card-hover-border: rgba(52, 211, 153, 0.45);
      --mint-primary: #34d399;
      --mint-glow: rgba(52, 211, 153, 0.3);
      --mint-soft: #a7f3d0;
      --emerald-dark: #064e3b;
      --text-main: #f0fdf4;
      --text-muted: #94a3b8;
      --gold: #fbbf24;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      padding: 40px 24px;
      min-height: 100vh;
      background-image: 
        radial-gradient(circle at 10% 10%, rgba(52, 211, 153, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 90% 90%, rgba(16, 185, 129, 0.10) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(6, 78, 59, 0.25) 0%, transparent 60%);
      background-attachment: fixed;
    }}
    .container {{ max-width: 1440px; margin: 0 auto; }}
    
    /* Header */
    header {{ text-align: center; margin-bottom: 40px; position: relative; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 18px;
      background: rgba(52, 211, 153, 0.14);
      border: 1px solid rgba(52, 211, 153, 0.35);
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      color: var(--mint-soft);
      margin-bottom: 14px;
      letter-spacing: 0.5px;
      box-shadow: 0 0 20px rgba(52, 211, 153, 0.2);
    }}
    h1 {{
      font-size: 40px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 12px;
      background: linear-gradient(135deg, #ffffff 0%, var(--mint-soft) 50%, var(--mint-primary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p.subtitle {{ color: var(--text-muted); font-size: 16px; max-width: 760px; margin: 0 auto 16px; line-height: 1.6; }}
    
    .stats-row {{
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 10px;
    }}
    .stat-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 8px 16px;
      border-radius: 12px;
      font-size: 13px;
      color: #e2e8f0;
      backdrop-filter: blur(8px);
    }}
    .stat-pill strong {{ color: var(--mint-primary); }}

    /* Controls Bar */
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 36px;
      padding: 18px 24px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      position: sticky;
      top: 16px;
      z-index: 50;
    }}
    .search-box {{ position: relative; flex: 1; min-width: 280px; }}
    .search-box input {{
      width: 100%;
      padding: 12px 18px 12px 44px;
      background: rgba(7, 13, 11, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      color: white;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box input:focus {{
      border-color: var(--mint-primary);
      box-shadow: 0 0 0 3px var(--mint-glow);
    }}
    .search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--mint-soft);
      font-size: 16px;
    }}
    .filter-pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .filter-btn {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .filter-btn:hover {{
      background: rgba(52, 211, 153, 0.15);
      color: var(--mint-soft);
      border-color: var(--mint-primary);
    }}
    .filter-btn.active {{
      background: linear-gradient(135deg, var(--mint-primary), #059669);
      color: #064e3b;
      font-weight: 700;
      border-color: transparent;
      box-shadow: 0 4px 14px var(--mint-glow);
    }}

    /* App Card */
    .app-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 24px;
      padding: 24px;
      margin-bottom: 32px;
      backdrop-filter: blur(14px);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }}
    .app-card:hover {{
      border-color: var(--card-hover-border);
      box-shadow: 0 12px 36px rgba(52, 211, 153, 0.12);
      transform: translateY(-2px);
    }}
    .app-header {{
      display: flex;
      align-items: center;
      gap: 20px;
      margin-bottom: 20px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-wrap: wrap;
    }}
    .app-logo {{
      width: 72px;
      height: 72px;
      border-radius: 16px;
      object-fit: cover;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.15);
      background: #111;
      flex-shrink: 0;
    }}
    .app-title-group {{ flex: 1; min-width: 240px; }}
    .app-title {{ font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }}
    .app-artist {{ font-size: 13px; color: var(--text-muted); }}
    .app-meta-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }}
    .tag {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(255, 255, 255, 0.06);
      color: #cbd5e1;
    }}
    .tag.genre {{ background: rgba(52, 211, 153, 0.12); color: var(--mint-soft); border: 1px solid rgba(52, 211, 153, 0.25); }}
    .tag.rating {{ background: rgba(251, 191, 36, 0.12); color: var(--gold); border: 1px solid rgba(251, 191, 36, 0.25); }}
    .tag.price {{ background: rgba(56, 189, 248, 0.12); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.25); }}
    
    .app-actions {{ display: flex; gap: 10px; }}
    .btn-action {{
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      border: none;
    }}
    .btn-store {{ background: rgba(255, 255, 255, 0.1); color: white; }}
    .btn-store:hover {{ background: rgba(255, 255, 255, 0.2); }}
    .btn-copy-ai {{
      background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(16, 185, 129, 0.3));
      color: var(--mint-soft);
      border: 1px solid rgba(52, 211, 153, 0.4);
    }}
    .btn-copy-ai:hover {{
      background: var(--mint-primary);
      color: #064e3b;
      box-shadow: 0 0 12px var(--mint-glow);
    }}

    /* Device Switcher Tabs */
    .device-tabs {{
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }}
    .device-tab {{
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      background: rgba(255, 255, 255, 0.04);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.08);
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .device-tab.active {{
      background: rgba(52, 211, 153, 0.18);
      color: var(--mint-soft);
      border-color: var(--mint-primary);
    }}

    /* Gallery Carousel */
    .gallery-container {{
      position: relative;
    }}
    .gallery-track {{
      display: flex;
      gap: 16px;
      overflow-x: auto;
      padding: 8px 4px 16px;
      scroll-behavior: smooth;
      scrollbar-width: thin;
      scrollbar-color: var(--mint-primary) rgba(255, 255, 255, 0.05);
    }}
    .gallery-track::-webkit-scrollbar {{ height: 6px; }}
    .gallery-track::-webkit-scrollbar-thumb {{ background: var(--mint-primary); border-radius: 999px; }}
    
    .screenshot-item {{
      flex: 0 0 auto;
      width: 200px;
      border-radius: 16px;
      overflow: hidden;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.1);
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }}
    .screenshot-item.ipad {{ width: 260px; }}
    .screenshot-item:hover {{
      transform: translateY(-4px) scale(1.02);
      border-color: var(--mint-primary);
      box-shadow: 0 12px 28px rgba(52, 211, 153, 0.25);
    }}
    .screenshot-img {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 15px;
      transition: opacity 0.3s;
    }}
    .screenshot-index {{
      position: absolute;
      top: 8px;
      left: 8px;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      color: var(--mint-soft);
    }}

    /* Lightbox Modal */
    .lightbox-modal {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.92);
      backdrop-filter: blur(20px);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }}
    .lightbox-modal.active {{ display: flex; }}
    .lightbox-content {{
      position: relative;
      max-width: 90vw;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .lightbox-img {{
      max-width: 100%;
      max-height: 82vh;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.15);
      object-fit: contain;
    }}
    .lightbox-nav {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 48px;
      height: 48px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      color: white;
      font-size: 20px;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .lightbox-nav:hover {{ background: var(--mint-primary); color: #064e3b; }}
    .lightbox-prev {{ left: -60px; }}
    .lightbox-next {{ right: -60px; }}
    .lightbox-close {{
      position: absolute;
      top: -44px;
      right: 0;
      color: #94a3b8;
      font-size: 28px;
      cursor: pointer;
      transition: color 0.2s;
    }}
    .lightbox-close:hover {{ color: white; }}
    .lightbox-caption {{
      margin-top: 14px;
      font-size: 14px;
      color: var(--mint-soft);
      font-weight: 600;
      text-align: center;
    }}

    /* Toast Notification */
    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: linear-gradient(135deg, #064e3b, #047857);
      color: #f0fdf4;
      padding: 12px 20px;
      border-radius: 12px;
      border: 1px solid var(--mint-primary);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      font-size: 14px;
      font-weight: 600;
      display: none;
      z-index: 2000;
      animation: slideUp 0.3s ease;
    }}
    @keyframes slideUp {{
      from {{ transform: translateY(20px); opacity: 0; }}
      to {{ transform: translateY(0); opacity: 1; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">🍎 Apple App Store Media Suite • Ultra High-Res</div>
      <h1>App Store Screenshots Studio</h1>
      <p class="subtitle">คลังภาพตัวอย่างหน้าจอแอปพลิเคชันทางการจาก Apple App Store (TH Store) ความละเอียดสูงสุดระดับ Retina/4K แยกหมวดหมู่อุปกรณ์ทั้ง iPhone และ iPad อย่างสมบูรณ์</p>
      
      <div class="stats-row">
        <div class="stat-pill">📱 ทั้งหมด <strong>{len(manifest)}</strong> แอพพลิเคชัน</div>
        <div class="stat-pill">🖼️ ภาพหน้าจอ Retina รวม <strong>{total_images}</strong> ภาพ</div>
        <div class="stat-pill">🌟 Storefront: <strong>Apple TH (ภาษาไทย)</strong></div>
        <div class="stat-pill">⚡ อัปเดตล่าสุด: <strong>วันนี้</strong></div>
      </div>
    </header>

    <div class="controls">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" placeholder="ค้นหาชื่อแอป, หมวดหมู่, หรือนักพัฒนา..." oninput="filterApps()">
      </div>
      <div class="filter-pills" id="categoryFilters">
        <button class="filter-btn active" onclick="setCategory('all')">ทั้งหมด ({len(manifest)})</button>
      </div>
    </div>

    <div id="appsList">
      <!-- App Cards Will Render Here -->
    </div>
  </div>

  <!-- Lightbox Modal -->
  <div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
    <div class="lightbox-content" onclick="event.stopPropagation()">
      <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
      <button class="lightbox-nav lightbox-prev" onclick="prevImage()">❮</button>
      <img id="lightboxImg" class="lightbox-img" src="" alt="Zoomed Screenshot">
      <button class="lightbox-nav lightbox-next" onclick="nextImage()">❯</button>
      <div class="lightbox-caption" id="lightboxCaption"></div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div class="toast" id="toast"></div>

  <script>
    const appsData = {manifest_json};
    let currentCategory = 'all';
    let currentLightboxList = [];
    let currentLightboxIndex = 0;

    // รวบรวมหมวดหมู่ทั้งหมด
    function setupCategories() {{
      const categories = new Set();
      appsData.forEach(app => categories.add(app.category));
      const container = document.getElementById('categoryFilters');
      categories.forEach(cat => {{
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.innerText = cat;
        btn.onclick = () => setCategory(cat);
        container.appendChild(btn);
      }});
    }}

    function setCategory(cat) {{
      currentCategory = cat;
      document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.innerText.includes(cat) || (cat === 'all' && btn.innerText.includes('ทั้งหมด')));
      }});
      renderApps();
    }}

    function filterApps() {{
      renderApps();
    }}

    function renderApps() {{
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      const container = document.getElementById('appsList');
      container.innerHTML = '';

      const filtered = appsData.filter(app => {{
        const matchCat = (currentCategory === 'all' || app.category === currentCategory);
        const matchQuery = !query || 
          app.name.toLowerCase().includes(query) || 
          app.track_name.toLowerCase().includes(query) || 
          app.artist_name.toLowerCase().includes(query) ||
          app.category.toLowerCase().includes(query);
        return matchCat && matchQuery;
      }});

      if (filtered.length === 0) {{
        container.innerHTML = `<div style="text-align:center; padding: 60px 20px; color: var(--text-muted);">
          <h2>❌ ไม่พบแอพที่ตรงกับเงื่อนไขการค้นหา</h2>
        </div>`;
        return;
      }}

      filtered.forEach(app => {{
        const card = document.createElement('div');
        card.className = 'app-card';
        card.id = 'app-' + app.id;

        const ratingStars = '★'.repeat(Math.round(app.rating)) + '☆'.repeat(5 - Math.round(app.rating));

        card.innerHTML = `
          <div class="app-header">
            <img class="app-logo" src="${{app.logo_rel_path}}" onerror="this.src='${{app.iphone_screenshots[0]?.rel_path || ''}}'" alt="${{app.name}} Logo">
            <div class="app-title-group">
              <div class="app-title">
                ${{app.name}}
                <span style="font-size:12px; font-weight:normal; color:var(--text-muted); font-family:monospace;">ID: ${{app.track_id}}</span>
              </div>
              <div class="app-artist">🏢 พัฒนาโดย: <strong>${{app.artist_name}}</strong> • เวอร์ชัน: ${{app.version}} • ${{app.file_size_mb}} MB</div>
              <div class="app-meta-tags">
                <span class="tag genre">🏷️ ${{app.category}}</span>
                <span class="tag rating">⭐ ${{app.rating.toFixed(1)}} (${{app.rating_count.toLocaleString()}} รีวิว)</span>
                <span class="tag price">💳 ${{app.price}}</span>
                <span class="tag">📱 iPhone: ${{app.total_iphone_screenshots}} รูป</span>
                ${{app.total_ipad_screenshots ? `<span class="tag">📟 iPad: ${{app.total_ipad_screenshots}} รูป</span>` : ''}}
              </div>
            </div>
            <div class="app-actions">
              <a href="${{app.appstore_url}}" target="_blank" class="btn-action btn-store">🍎 App Store</a>
              <button class="btn-action btn-copy-ai" onclick="copyAiPrompt('${{app.id}}')">🤖 คัดลอก Prompt AI</button>
            </div>
          </div>

          <div class="device-tabs">
            <button class="device-tab active" onclick="switchDevice(this, '${{app.id}}', 'iphone')">📱 iPhone (${{app.total_iphone_screenshots}})</button>
            ${{app.total_ipad_screenshots ? `<button class="device-tab" onclick="switchDevice(this, '${{app.id}}', 'ipad')">📟 iPad Pro (${{app.total_ipad_screenshots}})</button>` : ''}}
          </div>

          <div class="gallery-container">
            <div class="gallery-track" id="gallery-${{app.id}}">
              ${{renderGalleryItems(app, 'iphone')}}
            </div>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function renderGalleryItems(app, device) {{
      const list = device === 'iphone' ? app.iphone_screenshots : app.ipad_screenshots;
      if (!list || list.length === 0) return '<p style="color:var(--text-muted); padding:20px;">ไม่มีภาพหน้าจอสำหรับอุปกรณ์นี้</p>';

      return list.map((item, idx) => `
        <div class="screenshot-item ${{device === 'ipad' ? 'ipad' : ''}}" onclick="openLightbox('${{app.id}}', '${{device}}', ${{idx}})">
          <span class="screenshot-index">#${{idx + 1}}</span>
          <img class="screenshot-img" src="${{item.rel_path}}" alt="${{app.name}} screenshot ${{idx + 1}}" loading="lazy">
        </div>
      `).join('');
    }}

    function switchDevice(btn, appId, device) {{
      const card = document.getElementById('app-' + appId);
      card.querySelectorAll('.device-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const app = appsData.find(a => a.id === appId);
      const gallery = document.getElementById('gallery-' + appId);
      gallery.innerHTML = renderGalleryItems(app, device);
    }}

    // Lightbox Controls
    function openLightbox(appId, device, index) {{
      const app = appsData.find(a => a.id === appId);
      currentLightboxList = device === 'iphone' ? app.iphone_screenshots : app.ipad_screenshots;
      currentLightboxIndex = index;
      updateLightboxContent(app.name, device);
      document.getElementById('lightboxModal').classList.add('active');
    }}

    function updateLightboxContent(appName, device) {{
      const item = currentLightboxList[currentLightboxIndex];
      const img = document.getElementById('lightboxImg');
      const caption = document.getElementById('lightboxCaption');
      img.src = item.rel_path;
      caption.innerHTML = `${{appName}} • ${{device.toUpperCase()}} ภาพที่ ${{currentLightboxIndex + 1}} จาก ${{currentLightboxList.length}} (${{item.filename}})`;
    }}

    function closeLightbox(e) {{
      document.getElementById('lightboxModal').classList.remove('active');
    }}

    function prevImage() {{
      if (currentLightboxIndex > 0) {{
        currentLightboxIndex--;
        updateLightboxContent('', '');
      }}
    }}

    function nextImage() {{
      if (currentLightboxIndex < currentLightboxList.length - 1) {{
        currentLightboxIndex++;
        updateLightboxContent('', '');
      }}
    }}

    document.addEventListener('keydown', (e) => {{
      const modal = document.getElementById('lightboxModal');
      if (!modal.classList.contains('active')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') prevImage();
      if (e.key === 'ArrowRight') nextImage();
    }});

    function showToast(text) {{
      const toast = document.getElementById('toast');
      toast.innerText = text;
      toast.style.display = 'block';
      setTimeout(() => {{ toast.style.display = 'none'; }}, 2800);
    }}

    function copyAiPrompt(appId) {{
      const app = appsData.find(a => a.id === appId);
      const prompt = `# 🤖 [AI Automation Request] ข้อมูลแอพ Apple App Store: ${{app.name}}

บริบทของแอพพลิเคชันที่ดึงมาจาก Apple App Store (TH Store):
- ชื่อแอพทางการ: ${{app.track_name}}
- Apple Track ID: ${{app.track_id}}
- Bundle ID: ${{app.bundle_id}}
- หมวดหมู่: ${{app.category}} (${{app.primary_genre}})
- นักพัฒนา: ${{app.artist_name}}
- เรตติ้ง: ${{app.rating.toFixed(1)}} ดาว (${{app.rating_count}} ผู้รีวิว)
- ราคา: ${{app.price}}
- ลิงก์ทางการ: ${{app.appstore_url}}
- ภาพหน้าจอ Retina: iPhone ${{app.total_iphone_screenshots}} รูป, iPad ${{app.total_ipad_screenshots}} รูป

กรุณานำข้อมูลและภาพหน้าจอความละเอียดสูงในคลังนี้ไปใช้วิเคราะห์ UI/UX หรือเขียนสคริปต์อัตโนมัติตามต้องการ`;

      navigator.clipboard.writeText(prompt).then(() => {{
        showToast(`📋 คัดลอก Prompt AI ของ ${{app.name}} เรียบร้อยแล้ว!`);
      }});
    }}

    // เริ่มต้นทำงาน
    setupCategories();
    renderApps();
  </script>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html_content, encoding="utf-8")
    print(f"✨ สร้างหน้าแดชบอร์ด Web Studio สุดหรูเรียบร้อย: {PREVIEW_HTML.name}")


def main():
    print("=" * 76)
    print("🍎 เริ่มต้นกระบวนการสกัดรูปภาพ Screenshots ความละเอียดสูงจาก Apple App Store")
    print(f"📁 บันทึกแยกโฟลเดอร์รายแอปใน: {SCREENSHOTS_DIR}")
    print("=" * 76)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ตรวจสอบว่าส่ง argument ค้นหาหรือไม่
    target_apps = APPS_CONFIG
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["search", "find"] and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            print(f"🔍 โหมดค้นหาเฉพาะ: '{query}'")
            target_apps = [{"id": re.sub(r'[^a-zA-Z0-9_]', '_', query.lower()), "name": query, "category": "ค้นหาเฉพาะ"}]
        elif cmd in ["id", "track"] and len(sys.argv) > 2:
            tid = int(sys.argv[2])
            print(f"🎯 โหมดดึงผ่าน Track ID: {tid}")
            target_apps = [{"id": f"app_{tid}", "track_id": tid, "category": "ระบุ ID เฉพาะ"}]
        elif cmd == "--limit" and len(sys.argv) > 2:
            limit = int(sys.argv[2])
            target_apps = APPS_CONFIG[:limit]
            print(f"⚡ โหมดจำกัดจำนวน: {limit} แอปแรก")

    start_time = time.time()
    manifest = []
    total_images_count = 0

    for i, app_info in enumerate(target_apps, 1):
        app_name = app_info.get("name", str(app_info.get("track_id")))
        print(f"[{i}/{len(target_apps)}] 📦 กำลังสกัดภาพ App Store: {app_name}...")
        meta = process_app(app_info, country="th")
        if meta:
            count = meta["total_screenshots"]
            total_images_count += count
            print(f"    ↳ ✅ สำเร็จ! ได้ภาพ Retina ทั้งหมด {count} ภาพ (iPhone: {meta['total_iphone_screenshots']}, iPad: {meta['total_ipad_screenshots']})")
            manifest.append(meta)
        time.sleep(0.3)  # Polite delay

    # บันทึกภาพรวมทั้งหมดลงใน screenshots_manifest.json (รวมกับของเดิมถ้ามี)
    combined_manifest_map = {}
    if MANIFEST_FILE.exists():
        try:
            existing = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
            for item in existing:
                combined_manifest_map[item.get("id")] = item
        except Exception:
            pass

    for item in manifest:
        combined_manifest_map[item.get("id")] = item

    final_manifest = list(combined_manifest_map.values())
    MANIFEST_FILE.write_text(json.dumps(final_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    
    total_stored_images = sum(app.get("total_screenshots", 0) for app in final_manifest)
    elapsed = time.time() - start_time

    print("\n" + "=" * 76)
    print(f"🎉 เสร็จสิ้นสมบูรณ์ 100%! สกัดภาพรอบนี้ได้ {total_images_count} ภาพ (ภาพรวมในคลังทั้งหมด {total_stored_images} ภาพ ใน {len(final_manifest)} แอป) (ใช้เวลา {elapsed:.1f} วินาที)")
    print(f"📑 ดัชนี Manifest กลาง: {MANIFEST_FILE}")
    print("=" * 76)

    # สร้างแดชบอร์ด Web Studio Preview
    generate_studio_html(final_manifest, total_stored_images)


if __name__ == "__main__":
    main()
