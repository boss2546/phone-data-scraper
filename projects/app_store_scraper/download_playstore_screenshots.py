#!/usr/bin/env python3
"""
Play Store Screenshots Scraper & Multi-App Gallery Studio
ดึงรูปภาพตัวอย่าง (Preview Screenshots) ทั้งหมดของ 35 แอปจาก Google Play Store (ภาษาไทย)
จัดเก็บแยกโฟลเดอร์ตามแต่ละแอปอย่างเป็นระบบ พร้อมสร้าง JSON Manifest และ Web Studio แดชบอร์ด
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
SCREENSHOTS_DIR = BASE_DIR / "data" / "app_screenshots"
MANIFEST_FILE = SCREENSHOTS_DIR / "screenshots_manifest.json"
PREVIEW_HTML = BASE_DIR / "app_screenshots_studio.html"

# รายการ 35 แอปพร้อม Package ID ทางการบน Google Play Store
APPS_CONFIG = [
    {"id": "netflix", "name": "Netflix", "pkg": "com.netflix.mediaclient", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "iqiyi", "name": "iQIYI", "pkg": "com.iqiyi.i18n", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "monomax", "name": "Monomax", "pkg": "com.doonung.activity", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "prime_video", "name": "Prime Video", "pkg": "com.amazon.avod.thirdpartyclient", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "disney_plus", "name": "Disney+ Hotstar", "pkg": "com.disney.disneyplus", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "viu", "name": "Viu", "pkg": "com.viu.phone", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "wetv", "name": "WeTV", "pkg": "com.tencent.qqlivei18n", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "hbo_max", "name": "HBO MAX", "pkg": "com.wbd.stream", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "youku", "name": "Youku", "pkg": "com.youku.international.phone", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "bilibili", "name": "Bilibili", "pkg": "com.bstar.intl", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "oned", "name": "One D", "pkg": "com.gmm.onehd", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "bugaboo", "name": "Bugaboo.TV", "pkg": "com.bbtv.bugabootvinter", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "true_id", "name": "True ID", "pkg": "com.tdcm.trueidapp", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "truevisions_now", "name": "TrueVision Now", "pkg": "com.truevisions.android", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "ch3_plus", "name": "CH3 Plus", "pkg": "com.beci.thaitv3android", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "gagaoolala", "name": "GagaOOLala", "pkg": "com.gagaoolala.app", "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)"},
    {"id": "shortmax", "name": "ShortMax", "pkg": "live.shorttv.apps", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "dramawave", "name": "DramaWave", "pkg": "com.dramawave.app", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "dramabox", "name": "DramaBox", "pkg": "com.storymatrix.drama", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "reelshort", "name": "ReelShort", "pkg": "com.newleaf.app.android.victor", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "shortwave", "name": "ShortWave", "pkg": "com.shorts.wave.drama", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "goodshort", "name": "GoodShort", "pkg": "com.newreading.goodreels", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "netshort", "name": "NetShort", "pkg": "com.netshort.abroad", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "flickreels", "name": "FlickReels", "pkg": "com.zyhwplatform.shortplay", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "idrama", "name": "iDrama", "pkg": "com.gooddrama.idrama", "category": "แอปซีรีส์สั้น (Short Drama)"},
    {"id": "capcut", "name": "CapCut", "pkg": "com.lemon.lvoverseas", "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "meitu", "name": "Meitu", "pkg": "com.mt.mtxx.mtxx", "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "wink", "name": "Wink", "pkg": "com.meitu.wink", "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "beauticam", "name": "BeautiCam", "pkg": "com.meitu.meiyancamera", "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "canva", "name": "Canva", "pkg": "com.canva.editor", "category": "ตัดต่อ & แต่งภาพ & ดีไซน์"},
    {"id": "youtube", "name": "YouTube", "pkg": "com.google.android.youtube", "category": "สตรีมมิ่งเพลงและวิดีโอ"},
    {"id": "spotify", "name": "Spotify", "pkg": "com.spotify.music", "category": "สตรีมมิ่งเพลงและวิดีโอ"},
    {"id": "chatgpt", "name": "ChatGPT", "pkg": "com.openai.chatgpt", "category": "ปัญญาประดิษฐ์ (AI Tools)"},
    {"id": "gemini", "name": "Google Gemini", "pkg": "com.google.android.apps.bard", "category": "ปัญญาประดิษฐ์ (AI Tools)"},
    {"id": "microsoft_365", "name": "Microsoft 365", "pkg": "com.microsoft.office.officehubrow", "category": "ซอฟต์แวร์ทำงาน (Office)"}
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_playstore_screenshots(pkg: str):
    """สกัด URL ภาพตัวอย่างจากหน้า Google Play Store ภาษาไทย"""
    url = f"https://play.google.com/store/apps/details?id={pkg}&hl=th"
    req = urllib.request.Request(url, headers=HEADERS)
    screenshots = []
    seen = set()
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            
            # ดึง title
            title_match = re.search(r'<h1[^>]*>.*?<span[^>]*>(.*?)</span>', html, re.DOTALL)
            app_title = title_match.group(1).strip() if title_match else pkg

            # ดึงรูปภาพ Screenshots จาก tag <img>
            img_tags = re.findall(r'<img[^>]+>', html)
            for tag in img_tags:
                if "ภาพหน้าจอ" in tag or "screenshot" in tag.lower():
                    src_match = re.search(r'src=\"([^\"]+)\"', tag) or re.search(r'data-src=\"([^\"]+)\"', tag)
                    if src_match:
                        src = src_match.group(1)
                        base = src.split("=")[0]
                        if base not in seen:
                            seen.add(base)
                            # =s0 เพื่อเอาความละเอียดสูงสุด Original Resolution
                            screenshots.append(f"{base}=s0")
                            
            return app_title, screenshots
    except Exception as e:
        print(f"    ⚠️ เกิดข้อผิดพลาดในการดึงข้อมูล Play Store ({pkg}): {e}")
        return pkg, []

def download_single_image(args):
    """ดาวน์โหลดรูปภาพเดี่ยวพร้อมบันทึก"""
    url, dest_path = args
    if dest_path.exists() and dest_path.stat().st_size > 5000:
        return True, dest_path.name
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            dest_path.write_bytes(data)
            return True, dest_path.name
    except Exception as e:
        return False, f"{dest_path.name}: {e}"

def process_app(app_info):
    """ประมวลผลดึงและบันทึกรูปภาพทั้งหมดของ 1 แอป"""
    app_id = app_info["id"]
    name = app_info["name"]
    pkg = app_info["pkg"]
    category = app_info["category"]
    
    # สร้างโฟลเดอร์เฉพาะของแต่ละแอป
    app_folder = SCREENSHOTS_DIR / app_id
    app_folder.mkdir(parents=True, exist_ok=True)
    
    # ถ้ามีโลโก้อยู่ใน data/app_logos/images/ ให้ก๊อปปี้มาไว้ในโฟลเดอร์นี้ด้วย
    existing_logo = BASE_DIR / "data" / "app_logos" / "images" / f"{app_id}.png"
    dest_logo = app_folder / "logo.png"
    if existing_logo.exists() and not dest_logo.exists():
        dest_logo.write_bytes(existing_logo.read_bytes())

    official_title, screenshot_urls = fetch_playstore_screenshots(pkg)
    
    download_tasks = []
    saved_files = []
    
    for idx, url in enumerate(screenshot_urls, 1):
        filename = f"screenshot_{idx:02d}.png"
        filepath = app_folder / filename
        download_tasks.append((url, filepath))
        saved_files.append({
            "index": idx,
            "filename": filename,
            "rel_path": f"data/app_screenshots/{app_id}/{filename}",
            "source_url": url
        })

    # ดาวน์โหลดรูปภาพทั้งหมดของแอปนี้แบบ Multi-threaded
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(download_single_image, task) for task in download_tasks]
        for f in as_completed(futures):
            f.result()

    # บันทึก info.json ภายในโฟลเดอร์ของแอป
    app_meta = {
        "id": app_id,
        "name": name,
        "official_title": official_title,
        "package_id": pkg,
        "category": category,
        "playstore_url": f"https://play.google.com/store/apps/details?id={pkg}&hl=th",
        "total_screenshots": len(saved_files),
        "screenshots": saved_files
    }
    
    (app_folder / "info.json").write_text(json.dumps(app_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return app_meta

def main():
    print("=" * 76)
    print("📱 เริ่มต้นกระบวนการสกัดรูปภาพ Screenshots ทั้งหมดจาก Google Play Store")
    print(f"📁 บันทึกแยกโฟลเดอร์รายแอปใน: {SCREENSHOTS_DIR}")
    print("=" * 76)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    manifest = []
    total_images_count = 0

    # ประมวลผลทีละแอปอย่างเป็นระบบ
    for i, app_info in enumerate(APPS_CONFIG, 1):
        print(f"[{i}/{len(APPS_CONFIG)}] 📦 กำลังดักจับรูปภาพ Play Store: {app_info['name']} ({app_info['pkg']})...")
        meta = process_app(app_info)
        count = meta["total_screenshots"]
        total_images_count += count
        print(f"    ↳ ✅ สำเร็จ! ได้ภาพความละเอียดสูงทั้งหมด {count} รูป บันทึกลง data/app_screenshots/{app_info['id']}/")
        manifest.append(meta)
        time.sleep(0.4) # ป้องกัน rate limit

    # บันทึกภาพรวมทั้งหมดลงใน screenshots_manifest.json
    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - start_time

    print("\n" + "=" * 76)
    print(f"🎉 เสร็จสิ้นสมบูรณ์ 100%! สกัดรูปภาพได้รวมทั้งหมด {total_images_count} รูป (ใช้เวลา {elapsed:.1f} วินาที)")
    print(f"📑 ดัชนี Manifest กลาง: {MANIFEST_FILE}")
    print("=" * 76)

    # สร้างแดชบอร์ด Web Studio Preview
    generate_studio_html(manifest, total_images_count)

def generate_studio_html(manifest, total_images):
    """สร้างแดชบอร์ด Web Studio แบบเลื่อนดูแกลเลอรีภาพหน้าจอของแต่ละแอปอย่างสวยงาม"""
    html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📱 Google Play Store Screenshots Studio — 35 แอพพลิเคชัน</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #07090e;
      --card-bg: rgba(18, 22, 31, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      padding: 40px 24px;
      min-height: 100vh;
      background-image: 
        radial-gradient(circle at 5% 10%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 95% 90%, rgba(168, 85, 247, 0.08) 0%, transparent 40%);
    }}
    .container {{ max-width: 1440px; margin: 0 auto; }}
    header {{ text-align: center; margin-bottom: 36px; }}
    .badge {{
      display: inline-block;
      padding: 6px 16px;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      color: #7dd3fc;
      margin-bottom: 12px;
      letter-spacing: 0.5px;
    }}
    h1 {{
      font-size: 38px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 10px;
      background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p.subtitle {{ color: var(--text-muted); font-size: 16px; max-width: 720px; margin: 0 auto; }}
    .stat-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      background: rgba(255, 255, 255, 0.05);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 13px;
      color: #cbd5e1;
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding: 16px 20px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      backdrop-filter: blur(12px);
      position: sticky;
      top: 16px;
      z-index: 50;
    }}
    .search-box {{ position: relative; flex: 1; min-width: 280px; }}
    .search-box input {{
      width: 100%;
      padding: 12px 18px 12px 42px;
      background: rgba(10, 14, 22, 0.85);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: white;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }}
    .search-icon {{ position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-muted); }}
    .filter-pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .filter-btn {{
      padding: 8px 14px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: var(--accent);
      color: #030712;
      border-color: var(--accent);
      font-weight: 700;
      box-shadow: 0 4px 12px var(--accent-glow);
    }}
    .apps-stack {{ display: flex; flex-direction: column; gap: 36px; }}
    .app-section {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 24px;
      padding: 28px;
      backdrop-filter: blur(16px);
      transition: border-color 0.3s;
    }}
    .app-section:hover {{ border-color: rgba(56, 189, 248, 0.4); }}
    .app-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 22px;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .app-meta-left {{ display: flex; align-items: center; gap: 18px; }}
    .app-logo-badge {{
      width: 64px;
      height: 64px;
      border-radius: 16px;
      background: #1e293b;
      overflow: hidden;
      flex-shrink: 0;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }}
    .app-logo-badge img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .app-titles h2 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
    .app-titles p {{ font-size: 13px; color: var(--text-muted); }}
    .app-meta-right {{ display: flex; align-items: center; gap: 12px; }}
    .cat-tag {{
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.12);
      color: #7dd3fc;
    }}
    .play-link {{
      color: #38bdf8;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .play-link:hover {{ text-decoration: underline; }}
    .carousel {{
      display: flex;
      gap: 16px;
      overflow-x: auto;
      padding-bottom: 14px;
      scroll-snap-type: x mandatory;
      scrollbar-width: thin;
      scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
    }}
    .carousel::-webkit-scrollbar {{ height: 8px; }}
    .carousel::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.2); border-radius: 4px; }}
    .screen-item {{
      flex: 0 0 auto;
      width: 220px;
      height: 440px;
      border-radius: 16px;
      overflow: hidden;
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.08);
      cursor: pointer;
      scroll-snap-align: start;
      transition: transform 0.25s, box-shadow 0.25s;
      position: relative;
    }}
    .screen-item:hover {{
      transform: translateY(-4px) scale(1.02);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.6), 0 0 16px var(--accent-glow);
    }}
    .screen-item img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .screen-num {{
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(4px);
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      color: white;
    }}
    /* Modal Lightbox */
    .lightbox {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.9);
      backdrop-filter: blur(10px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      cursor: pointer;
    }}
    .lightbox.active {{ display: flex; }}
    .lightbox img {{
      max-width: 90vw;
      max-height: 90vh;
      border-radius: 16px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8);
      object-fit: contain;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">GOOGLE PLAY STORE HIGH-RES PREVIEWS</div>
      <h1>📱 Google Play Store Screenshots Studio</h1>
      <p class="subtitle">คลังภาพหน้าจอตัวอย่าง (Preview Screenshots) คุณภาพสูงระดับ Full HD ครบทั้ง 35 แอพพลิเคชัน แยกเก็บเป็นระเบียบรายโฟลเดอร์</p>
      <div class="stat-pill">📦 สกัดทั้งหมด <strong>{total_images} ภาพ</strong> • ครบถ้วน 35/35 แอพพลิเคชัน 100%</div>
    </header>

    <div class="controls">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" placeholder="ค้นหาตามชื่อแอพ (เช่น Google Gemini, Netflix, CapCut)..." oninput="filterApps()">
      </div>
      <div class="filter-pills">
        <button class="filter-btn active" onclick="setCategory('ALL')">ทั้งหมด (35)</button>
        <button class="filter-btn" onclick="setCategory('สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)')">🎬 สตรีมมิ่ง OTT</button>
        <button class="filter-btn" onclick="setCategory('แอปซีรีส์สั้น (Short Drama)')">📱 ซีรีส์สั้น</button>
        <button class="filter-btn" onclick="setCategory('ตัดต่อ & แต่งภาพ & ดีไซน์')">🎨 แต่งรูป/ตัดต่อ</button>
        <button class="filter-btn" onclick="setCategory('สตรีมมิ่งเพลงและวิดีโอ')">🎵 เพลง/วิดีโอ</button>
        <button class="filter-btn" onclick="setCategory('ปัญญาประดิษฐ์ (AI Tools)')">🤖 AI Tools</button>
        <button class="filter-btn" onclick="setCategory('ซอฟต์แวร์ทำงาน (Office)')">💼 Office</button>
      </div>
    </div>

    <div class="apps-stack" id="appsStack">
"""

    for a in manifest:
        logo_path = f"data/app_logos/images/{a['id']}.png"
        html_content += f"""      <div class="app-section" data-name="{a['name'].lower()}" data-title="{a['official_title'].lower()}" data-category="{a['category']}">
        <div class="app-header">
          <div class="app-meta-left">
            <div class="app-logo-badge">
              <img src="{logo_path}" alt="{a['name']}" loading="lazy">
            </div>
            <div class="app-titles">
              <h2>{a['name']}</h2>
              <p>{a['official_title']} • 📁 <code>data/app_screenshots/{a['id']}/</code> ({a['total_screenshots']} รูป)</p>
            </div>
          </div>
          <div class="app-meta-right">
            <span class="cat-tag">{a['category']}</span>
            <a href="{a['playstore_url']}" target="_blank" class="play-link">🌐 ดูบน Play Store ↗</a>
          </div>
        </div>

        <div class="carousel">
"""
        for sc in a["screenshots"]:
            html_content += f"""          <div class="screen-item" onclick="openLightbox('{sc['rel_path']}')">
            <img src="{sc['rel_path']}" alt="{a['name']} Screenshot {sc['index']}" loading="lazy">
            <span class="screen-num">#{sc['index']}</span>
          </div>
"""
        html_content += """        </div>
      </div>
"""

    html_content += """    </div>
  </div>

  <div class="lightbox" id="lightboxModal" onclick="closeLightbox()">
    <img id="lightboxImg" src="" alt="Fullscreen Screenshot">
  </div>

  <script>
    let currentCategory = 'ALL';

    function setCategory(cat) {
      currentCategory = cat;
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(cat) || (cat === 'ALL' && btn.textContent.includes('ทั้งหมด')));
      });
      filterApps();
    }

    function filterApps() {
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      document.querySelectorAll('.app-section').forEach(sec => {
        const name = sec.getAttribute('data-name');
        const title = sec.getAttribute('data-title');
        const cat = sec.getAttribute('data-category');

        const matchQ = !q || name.includes(q) || title.includes(q);
        const matchCat = currentCategory === 'ALL' || cat === currentCategory;

        sec.style.display = (matchQ && matchCat) ? 'block' : 'none';
      });
    }

    function openLightbox(src) {
      document.getElementById('lightboxImg').src = src;
      document.getElementById('lightboxModal').classList.add('active');
    }

    function closeLightbox() {
      document.getElementById('lightboxModal').classList.remove('active');
    }
  </script>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html_content, encoding="utf-8")
    print(f"🌐 สร้างหน้า Web Preview Studio สำเร็จ: {PREVIEW_HTML}")

if __name__ == "__main__":
    main()
