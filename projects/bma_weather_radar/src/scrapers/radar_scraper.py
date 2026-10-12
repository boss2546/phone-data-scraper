import sys
import re
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import WEATHER_DIR, DEFAULT_HEADERS, BMA_NONGKHAM_URL, BMA_NONGCHOK_URL

class BMAWeatherRadarScraper:
    """Scraper สำหรับดึงภาพเรดาร์และรายงานสภาพฝน กทม. จากสำนักการระบายน้ำ"""

    @staticmethod
    def fetch_latest_radar() -> Dict[str, Any]:
        """ดึงข้อมูลสภาพฝนและดาวน์โหลดภาพเรดาร์ล่าสุด"""
        bulletin_text = "ไม่พบรายงานสด"
        try:
            req = urllib.request.Request(BMA_NONGKHAM_URL, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=12) as res:
                html = res.read().decode("utf-8", errors="ignore")
                
            m = re.search(r'id=["\']ctl00_ContentPlaceHolder1_lblBulletin["\'][^>]*>(.*?)</span>', html, re.DOTALL)
            if m:
                bulletin_text = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
        except Exception as e:
            bulletin_text = f"ดึงข้อมูลจากเว็บไซต์ไม่สำเร็จ ({e})"

        # Static radar URLs
        nk_img_url = "https://weather.bangkok.go.th/Radar/RadarAnimation/radar_nk_latest.gif"
        nc_img_url = "https://weather.bangkok.go.th/Radar/RadarAnimation/radar_nc_latest.gif"

        # Download latest images if reachable
        nk_local = WEATHER_DIR / "radar_nongkam_latest.gif"
        nc_local = WEATHER_DIR / "radar_nongchok_latest.gif"

        for url, path in [(nk_img_url, nk_local), (nc_img_url, nc_local)]:
            try:
                r = urllib.request.Request(url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(r, timeout=10) as resp:
                    with open(path, "wb") as f:
                        f.write(resp.read())
            except Exception:
                pass

        data = {
            "timestamp": int(time.time()),
            "last_updated_iso": datetime.now().isoformat(),
            "bulletin_raw": bulletin_text,
            "status": "clear" if "ไม่พบกลุ่มฝน" in bulletin_text else "rain_detected",
            "images": {
                "nongkam": {
                    "station_name": "สถานีเรดาร์หนองแขม (NK)",
                    "coverage": "ฝั่งธนบุรี / ภาคตะวันตก / ภาคใต้ตอนบน",
                    "file": str(nk_local.name) if nk_local.exists() else None
                },
                "nongchok": {
                    "station_name": "สถานีเรดาร์หนองจอก (NC)",
                    "coverage": "ฝั่งพระนคร / ภาคตะวันออก / ภาคกลางตอนบน",
                    "file": str(nc_local.name) if nc_local.exists() else None
                }
            },
            "source_url": BMA_NONGKHAM_URL
        }

        save_path = WEATHER_DIR / "bma_radar_latest.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data
