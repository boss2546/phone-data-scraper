#!/usr/bin/env python3
"""
App Logo Fetcher & Catalog Studio Builder
ดึงโลโก้ทางการความละเอียดสูง (512x512 / 1024x1024) ของทั้ง 35 แอปจาก ราคาสินค้า.xlsx
พร้อมสร้าง Metadata JSON และ Web Preview Studio
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "app_logos"
IMAGES_DIR = OUTPUT_DIR / "images"
METADATA_FILE = OUTPUT_DIR / "apps_catalog.json"
PREVIEW_HTML = BASE_DIR / "app_logos_preview.html"

# รายการแอป 35 ตัวพร้อมคำค้นหาที่แม่นยำที่สุดบน Apple Store
APPS_CONFIG = [
    {
        "id": "netflix",
        "name": "Netflix",
        "search_term": "Netflix",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
        "fallback_logo": "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg"
    },
    {
        "id": "iqiyi",
        "name": "iQIYI",
        "search_term": "iQIYI",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "monomax",
        "name": "Monomax",
        "search_term": "Monomax",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "prime_video",
        "name": "Prime Video",
        "search_term": "Amazon Prime Video",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "disney_plus",
        "name": "Disney+ Hotstar",
        "search_term": "Disney+",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "viu",
        "name": "Viu",
        "search_term": "Viu",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "wetv",
        "name": "WeTV",
        "search_term": "WeTV",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "hbo_max",
        "name": "HBO MAX",
        "search_term": "Max: Stream HBO, TV, & Movies",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "youku",
        "name": "Youku",
        "search_term": "YOUKU",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "bilibili",
        "name": "Bilibili",
        "search_term": "BiliBili",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "oned",
        "name": "One D",
        "search_term": "oneD",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "bugaboo",
        "name": "Bugaboo.TV",
        "search_term": "Bugaboo",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "true_id",
        "name": "True ID",
        "search_term": "TrueID",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "truevisions_now",
        "name": "TrueVision Now",
        "search_term": "TrueVisions NOW",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "ch3_plus",
        "name": "CH3 Plus",
        "search_term": "CH3 Plus",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "gagaoolala",
        "name": "GagaOOLala",
        "search_term": "GagaOOLala",
        "country": "th",
        "category": "สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)",
    },
    {
        "id": "shortmax",
        "name": "ShortMax",
        "search_term": "ShortMax",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "dramawave",
        "name": "DramaWave",
        "search_term": "DramaWave",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "dramabox",
        "name": "DramaBox",
        "search_term": "DramaBox",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "reelshort",
        "name": "ReelShort",
        "search_term": "ReelShort",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "shortwave",
        "name": "ShortWave",
        "search_term": "ShortsWave",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "goodshort",
        "name": "GoodShort",
        "search_term": "GoodShort",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "netshort",
        "name": "NetShort",
        "search_term": "NetShort",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "flickreels",
        "name": "FlickReels",
        "search_term": "FlickReels",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "idrama",
        "name": "iDrama",
        "search_term": "iDrama",
        "country": "th",
        "category": "แอปซีรีส์สั้น (Short Drama)",
    },
    {
        "id": "capcut",
        "name": "CapCut",
        "search_term": "CapCut",
        "country": "th",
        "category": "ตัดต่อ & แต่งภาพ & ดีไซน์",
    },
    {
        "id": "meitu",
        "name": "Meitu",
        "search_term": "Meitu",
        "country": "th",
        "category": "ตัดต่อ & แต่งภาพ & ดีไซน์",
    },
    {
        "id": "wink",
        "name": "Wink",
        "search_term": "Wink - Video Enhancer",
        "country": "th",
        "category": "ตัดต่อ & แต่งภาพ & ดีไซน์",
    },
    {
        "id": "beauticam",
        "name": "BeautiCam",
        "search_term": "BeautyCam",
        "country": "th",
        "category": "ตัดต่อ & แต่งภาพ & ดีไซน์",
    },
    {
        "id": "canva",
        "name": "Canva",
        "search_term": "Canva",
        "country": "th",
        "category": "ตัดต่อ & แต่งภาพ & ดีไซน์",
    },
    {
        "id": "youtube",
        "name": "YouTube",
        "search_term": "YouTube",
        "country": "th",
        "category": "สตรีมมิ่งเพลงและวิดีโอ",
    },
    {
        "id": "spotify",
        "name": "Spotify",
        "search_term": "Spotify",
        "country": "th",
        "category": "สตรีมมิ่งเพลงและวิดีโอ",
    },
    {
        "id": "chatgpt",
        "name": "ChatGPT",
        "search_term": "ChatGPT",
        "country": "th",
        "category": "ปัญญาประดิษฐ์ (AI Tools)",
    },
    {
        "id": "gemini",
        "name": "Gemini",
        "search_term": "Google Gemini",
        "country": "us",
        "category": "ปัญญาประดิษฐ์ (AI Tools)",
    },
    {
        "id": "microsoft_365",
        "name": "Microsoft 365",
        "search_term": "Microsoft 365 Copilot",
        "country": "us",
        "category": "ซอฟต์แวร์ทำงาน (Office)",
    }
]

def search_itunes_app(term: str, country: str = "th"):
    """ค้นหาข้อมูลแอปจาก iTunes Search API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    encoded_term = urllib.parse.quote(term)
    url = f"https://itunes.apple.com/search?term={encoded_term}&entity=software&country={country}&limit=3"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("resultCount", 0) > 0:
                return data["results"][0]
    except Exception as e:
        print(f"    ⚠️ Warning search failed for {term} ({country}): {e}")
    return None

def download_image(url: str, dest_path: Path):
    """ดาวน์โหลดรูปภาพและบันทึกลงไฟล์"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
        dest_path.write_bytes(content)

def main():
    print("=" * 72)
    print("🚀 เริ่มกระบวนการดึงโลโก้ทางการของทั้ง 35 แอปพลิเคชัน...")
    print(f"📁 บันทึกไฟล์ลงที่: {OUTPUT_DIR}")
    print("=" * 72)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    results = []
    success_count = 0
    
    for idx, cfg in enumerate(APPS_CONFIG, 1):
        app_name = cfg["name"]
        app_id = cfg["id"]
        category = cfg["category"]
        term = cfg["search_term"]
        country = cfg.get("country", "th")
        
        print(f"[{idx}/{len(APPS_CONFIG)}] 🔍 กำลังค้นหาโลโก้: {app_name} ({term})...")
        
        # 1. ค้นหาบน Store ตามประเทศที่ระบุ
        info = search_itunes_app(term, country)
        
        # 2. ถ้าไม่พบ ลองสลับเป็น US store
        if not info and country != "us":
            print(f"    ↳ ลองค้นหาซ้ำใน US Store...")
            info = search_itunes_app(term, "us")
            
        # 3. ถ้ายังไม่พบ ลองค้นด้วยชื่อสั้น
        if not info:
            print(f"    ↳ ลองค้นหาด้วยชื่อแอปสั้น: '{app_name}'...")
            info = search_itunes_app(app_name, "th")

        logo_url = None
        store_url = None
        seller_name = None
        version = None
        bundle_id = None
        track_name = app_name
        
        if info:
            # ดึงขนาด 512x512 หรือ 1024x1024
            logo_url = info.get("artworkUrl512") or info.get("artworkUrl100")
            store_url = info.get("trackViewUrl")
            seller_name = info.get("sellerName")
            version = info.get("version")
            bundle_id = info.get("bundleId")
            track_name = info.get("trackName", app_name)
        elif "fallback_logo" in cfg:
            logo_url = cfg["fallback_logo"]
            seller_name = "Official Brand"
            
        if logo_url:
            # กำหนดชื่อไฟล์รูปภาพ
            ext = ".png" if ".png" in logo_url.lower() else ".jpg"
            if ".svg" in logo_url.lower():
                ext = ".svg"
            img_filename = f"{app_id}{ext}"
            img_path = IMAGES_DIR / img_filename
            
            try:
                download_image(logo_url, img_path)
                print(f"    ✅ ดาวน์โหลดสำเร็จ -> {img_filename} ({img_path.stat().st_size // 1024} KB)")
                success_count += 1
                
                results.append({
                    "id": app_id,
                    "name": app_name,
                    "official_name": track_name,
                    "category": category,
                    "seller": seller_name,
                    "bundle_id": bundle_id,
                    "version": version,
                    "local_filename": img_filename,
                    "local_path": f"data/app_logos/images/{img_filename}",
                    "logo_url": logo_url,
                    "store_url": store_url
                })
            except Exception as e:
                print(f"    ❌ โหลดรูปล้มเหลว: {e}")
        else:
            print(f"    ❌ ไม่พบข้อมูลโลโก้")
            
        # หน่วงเวลา 0.6 วินาทีเพื่อป้องกัน Rate-Limit (429)
        time.sleep(0.6)

    # บันทึกไฟล์ JSON สรุปผล
    METADATA_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "=" * 72)
    print(f"🎉 สำเร็จ! ดาวน์โหลดโลโก้ได้ทั้งหมด {success_count}/{len(APPS_CONFIG)} แอป")
    print(f"📄 บันทึกดัชนีข้อมูลไว้ที่: {METADATA_FILE}")
    print("=" * 72)
    
    # สร้างหน้า HTML Preview Studio
    generate_preview_html(results)

def generate_preview_html(apps_list):
    """สร้างแดชบอร์ด Web Gallery Studio สไตล์ Obsidian Glassmorphism"""
    html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎨 Digital Apps Logo Studio — 35 แอพพลิเคชัน</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #0a0c10;
      --card-bg: rgba(22, 27, 34, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover-border: rgba(99, 102, 241, 0.5);
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.25);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      padding: 40px 24px;
      min-height: 100vh;
      background-image: 
        radial-gradient(circle at 10% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 90% 85%, rgba(236, 72, 153, 0.1) 0%, transparent 40%);
    }}
    .container {{
      max-width: 1380px;
      margin: 0 auto;
    }}
    header {{
      text-align: center;
      margin-bottom: 40px;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      color: #a5b4fc;
      margin-bottom: 12px;
      letter-spacing: 0.5px;
    }}
    h1 {{
      font-size: 36px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 10px;
      background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p.subtitle {{
      color: var(--text-muted);
      font-size: 16px;
      max-width: 650px;
      margin: 0 auto;
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
    }}
    .search-box {{
      position: relative;
      flex: 1;
      min-width: 280px;
    }}
    .search-box input {{
      width: 100%;
      padding: 12px 18px 12px 42px;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: white;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }}
    .search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}
    .filter-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
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
      color: white;
      border-color: var(--accent);
      box-shadow: 0 4px 12px var(--accent-glow);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 24px;
    }}
    .app-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      backdrop-filter: blur(16px);
      position: relative;
      overflow: hidden;
    }}
    .app-card:hover {{
      transform: translateY(-6px);
      border-color: var(--card-hover-border);
      box-shadow: 0 16px 32px -8px rgba(0, 0, 0, 0.6), 0 0 24px var(--accent-glow);
    }}
    .logo-wrapper {{
      width: 108px;
      height: 108px;
      border-radius: 24px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
      overflow: hidden;
      margin-bottom: 18px;
      background: #1e293b;
      position: relative;
      transition: transform 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .app-card:hover .logo-wrapper {{
      transform: scale(1.06);
    }}
    .logo-wrapper img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .app-category {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.12);
      padding: 4px 10px;
      border-radius: 6px;
      margin-bottom: 10px;
    }}
    .app-title {{
      font-size: 18px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 6px;
    }}
    .app-official {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: 16px;
      min-height: 34px;
    }}
    .card-footer {{
      width: 100%;
      margin-top: auto;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
    }}
    .seller-tag {{
      color: #64748b;
      max-width: 120px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: left;
    }}
    .download-link {{
      color: #38bdf8;
      text-decoration: none;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: color 0.2s;
    }}
    .download-link:hover {{
      color: #7dd3fc;
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">OFFICIAL RETINA LOGO ASSETS</div>
      <h1>🎨 Digital Subscriptions Logo Studio</h1>
      <p class="subtitle">คลังโลโก้ทางการความละเอียดสูง 512×512 HD ครบทั้ง 35 แอพพลิเคชัน จากตารางราคาสินค้า ดึงสดผ่าน Apple App Store CDN</p>
    </header>

    <div class="controls">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" placeholder="พิมพ์ชื่อแอพเพื่อค้นหา (เช่น Netflix, CapCut, ShortMax)..." oninput="filterApps()">
      </div>
      <div class="filter-pills" id="categoryFilters">
        <button class="filter-btn active" onclick="setCategory('ALL')">ทั้งหมด (35)</button>
        <button class="filter-btn" onclick="setCategory('สตรีมมิ่งดูหนัง/ซีรีส์ (OTT)')">🎬 สตรีมมิ่ง OTT</button>
        <button class="filter-btn" onclick="setCategory('แอปซีรีส์สั้น (Short Drama)')">📱 ซีรีส์สั้น</button>
        <button class="filter-btn" onclick="setCategory('ตัดต่อ & แต่งภาพ & ดีไซน์')">🎨 แต่งรูป/ตัดต่อ</button>
        <button class="filter-btn" onclick="setCategory('สตรีมมิ่งเพลงและวิดีโอ')">🎵 เพลง/วิดีโอ</button>
        <button class="filter-btn" onclick="setCategory('ปัญญาประดิษฐ์ (AI Tools)')">🤖 AI Tools</button>
        <button class="filter-btn" onclick="setCategory('ซอฟต์แวร์ทำงาน (Office)')">💼 Office</button>
      </div>
    </div>

    <div class="grid" id="appsGrid">
"""
    
    for a in apps_list:
        html_content += f"""      <div class="app-card" data-name="{a['name'].lower()}" data-official="{a['official_name'].lower()}" data-category="{a['category']}">
        <div class="logo-wrapper">
          <img src="{a['local_path']}" alt="{a['name']}" loading="lazy" onerror="this.src='{a['logo_url']}'">
        </div>
        <div class="app-category">{a['category'].split()[0]}</div>
        <h3 class="app-title">{a['name']}</h3>
        <p class="app-official">{a['official_name']}</p>
        <div class="card-footer">
          <span class="seller-tag" title="{a.get('seller') or ''}">🏢 {a.get('seller') or 'Official'}</span>
          <a href="{a['local_path']}" download class="download-link">💾 บันทึกรูป</a>
        </div>
      </div>
"""

    html_content += """    </div>
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
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      const cards = document.querySelectorAll('.app-card');

      cards.forEach(card => {
        const name = card.getAttribute('data-name');
        const official = card.getAttribute('data-official');
        const category = card.getAttribute('data-category');

        const matchesQuery = !query || name.includes(query) || official.includes(query);
        const matchesCategory = currentCategory === 'ALL' || category === currentCategory;

        if (matchesQuery && matchesCategory) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    }
  </script>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html_content, encoding="utf-8")
    print(f"🌐 สร้างหน้า Web Preview Studio สำเร็จ: {PREVIEW_HTML}")

if __name__ == "__main__":
    main()
