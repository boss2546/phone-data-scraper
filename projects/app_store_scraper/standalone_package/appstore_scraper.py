#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍎 Universal Apple App Store Media Scraper (AI-Ready & Zero-Dependency)
โมดูลดึงรูปภาพตัวอย่างหน้าจอ (Screenshots) ความละเอียดระดับ Retina 4K และข้อมูล Metadata จาก Apple App Store
- ไม่ต้องติดตั้งไลบรารีภายนอก (ใช้เฉพาะ Standard Library ของ Python 3.8+)
- ใช้งานได้ทั้งแบบ Command Line (CLI) และ Import ไปใช้ในโค้ด Python
- ดึงความละเอียดสูงสุด: iPhone (1290×2796), iPad Pro (2048×2732), App Icon (1024×1024)
"""

import os
import sys
import time
import json
import re
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}


class AppStoreScraper:
    def __init__(self, output_dir: str = "./appstore_output", country: str = "th", max_workers: int = 8):
        self.output_dir = Path(output_dir).resolve()
        self.country = country
        self.max_workers = max_workers
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def transform_highres_url(url: str, device: str = "iphone", fmt: str = "png") -> str:
        """แปลง URL จาก Storefront Thumbnail เป็น Retina 4K แท้"""
        if not url:
            return ""
        if device == "artwork":
            return re.sub(r'/\d+x\d+bb\.[a-zA-Z]+$', f'/1024x1024bb.{fmt}', url)
        
        target_dim = "1290x2796bb" if device == "iphone" else "2048x2732bb"
        if re.search(r'/\d+x\d+bb\.[a-zA-Z]+$', url):
            return re.sub(r'/\d+x\d+bb\.[a-zA-Z]+$', f'/{target_dim}.{fmt}', url)
        return f"{url}/{target_dim}.{fmt}"

    def fetch_metadata(self, identifier: str) -> dict:
        """
        ดึง Metadata ของแอป โดย identifier สามารถเป็น:
        - ชื่อแอป (Search term) e.g. "Netflix"
        - Apple Track ID (ตัวเลข) e.g. "363590051"
        - App Store URL e.g. "https://apps.apple.com/th/app/netflix/id363590051"
        - Bundle ID e.g. "bundle:com.netflix.Netflix"
        """
        identifier = str(identifier).strip()
        url = None

        # 1. ตรวจสอบว่าเป็น URL หรือไม่
        if "apps.apple.com" in identifier or "itunes.apple.com" in identifier:
            id_match = re.search(r'/id(\d+)', identifier)
            if id_match:
                track_id = id_match.group(1)
                url = f"https://itunes.apple.com/lookup?id={track_id}&country={self.country}"
        # 2. ตรวจสอบว่าเป็นตัวเลขล้วน (Track ID)
        elif identifier.isdigit():
            url = f"https://itunes.apple.com/lookup?id={identifier}&country={self.country}"
        # 3. ตรวจสอบว่าเป็น bundle ID
        elif identifier.startswith("bundle:"):
            bundle = identifier.replace("bundle:", "").strip()
            url = f"https://itunes.apple.com/lookup?bundleId={bundle}&country={self.country}"
        # 4. ค้นหาด้วยชื่อแอป
        else:
            term = urllib.parse.quote(identifier)
            url = f"https://itunes.apple.com/search?term={term}&country={self.country}&entity=software&limit=1"

        if not url:
            return None

        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                if results:
                    return results[0]
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจาก Apple API ({identifier}): {e}")
        return None

    def _download_file(self, target_url: str, fallback_url: str, dest_path: Path) -> bool:
        """ดาวน์โหลดไฟล์เดี่ยวพร้อม fallback"""
        if dest_path.exists() and dest_path.stat().st_size > 5000:
            return True

        for u in [target_url, fallback_url]:
            if not u:
                continue
            try:
                req = urllib.request.Request(u, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = resp.read()
                    if len(data) > 1000:
                        dest_path.write_bytes(data)
                        return True
            except Exception:
                continue
        return False

    def scrape_app(self, identifier: str, download_media: bool = True, devices: list = None) -> dict:
        """
        ฟังก์ชันหลัก: สกัดข้อมูลและดาวน์โหลดสื่อทั้งหมดของแอป
        - identifier: ชื่อแอป, Track ID, หรือ URL
        - download_media: ถ้าเป็น False จะคืนค่าเฉพาะ Metadata ไม่โหลดรูปภาพ
        - devices: รายการอุปกรณ์ที่ต้องการ เช่น ["iphone", "ipad"] (ค่าเริ่มต้น: ทั้งหมด)
        """
        if devices is None:
            devices = ["iphone", "ipad"]

        raw = self.fetch_metadata(identifier)
        if not raw:
            return {"status": "error", "message": f"ไม่พบข้อมูลแอป: {identifier}"}

        track_id = raw.get("trackId")
        track_name = raw.get("trackName")
        clean_name = re.sub(r'[^a-zA-Z0-9_\u0E00-\u0E7F]', '_', track_name).strip('_')
        app_folder = self.output_dir / f"{clean_name}_{track_id}"
        app_folder.mkdir(parents=True, exist_ok=True)

        # ข้อมูลพื้นฐาน
        file_size_bytes = int(raw.get("fileSizeBytes", 0))
        app_info = {
            "status": "success",
            "track_id": track_id,
            "track_name": track_name,
            "artist_name": raw.get("artistName"),
            "bundle_id": raw.get("bundleId"),
            "category": raw.get("primaryGenreName"),
            "genres": raw.get("genres", []),
            "version": raw.get("version"),
            "price": raw.get("formattedPrice", "Free"),
            "rating": raw.get("averageUserRating", 0.0),
            "rating_count": raw.get("userRatingCount", 0),
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2) if file_size_bytes else 0,
            "appstore_url": raw.get("trackViewUrl"),
            "description": raw.get("description", ""),
            "release_notes": raw.get("releaseNotes", ""),
            "logo_path": str(app_folder / "logo.png"),
            "iphone_screenshots": [],
            "ipad_screenshots": []
        }

        if not download_media:
            return app_info

        tasks = []

        # 1. โลโก้แอป 1024x1024
        raw_art = raw.get("artworkUrl512") or raw.get("artworkUrl100")
        if raw_art:
            highres_art = self.transform_highres_url(raw_art, device="artwork", fmt="png")
            tasks.append((highres_art, raw_art, app_folder / "logo.png"))

        # 2. ภาพหน้าจอ iPhone
        if "iphone" in devices:
            iphone_dir = app_folder / "iphone"
            iphone_dir.mkdir(parents=True, exist_ok=True)
            for idx, u in enumerate(raw.get("screenshotUrls", []), 1):
                p = iphone_dir / f"screenshot_{idx:02d}.png"
                high_u = self.transform_highres_url(u, device="iphone", fmt="png")
                fallback_u = self.transform_highres_url(u, device="iphone", fmt="jpg")
                tasks.append((high_u, fallback_u, p))
                app_info["iphone_screenshots"].append({
                    "index": idx,
                    "file_path": str(p),
                    "url": high_u
                })

        # 3. ภาพหน้าจอ iPad
        if "ipad" in devices:
            ipad_dir = app_folder / "ipad"
            ipad_dir.mkdir(parents=True, exist_ok=True)
            for idx, u in enumerate(raw.get("ipadScreenshotUrls", []), 1):
                p = ipad_dir / f"screenshot_{idx:02d}.png"
                high_u = self.transform_highres_url(u, device="ipad", fmt="png")
                fallback_u = self.transform_highres_url(u, device="ipad", fmt="jpg")
                tasks.append((high_u, fallback_u, p))
                app_info["ipad_screenshots"].append({
                    "index": idx,
                    "file_path": str(p),
                    "url": high_u
                })

        # ดาวน์โหลดแบบมัลติเธรด
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._download_file, t[0], t[1], t[2]) for t in tasks]
            for f in as_completed(futures):
                pass

        # บันทึก info.json ในโฟลเดอร์แอป
        (app_folder / "info.json").write_text(json.dumps(app_info, ensure_ascii=False, indent=2), encoding="utf-8")
        return app_info


def main():
    parser = argparse.ArgumentParser(description="🍎 Apple App Store Media & Screenshot Scraper (AI-Ready)")
    parser.add_argument("apps", nargs="+", help="ชื่อแอป, Track ID, หรือ ลิงก์ App Store URL")
    parser.add_argument("-o", "--output", default="./appstore_output", help="โฟลเดอร์สำหรับบันทึกไฟล์ (ค่าเริ่มต้น: ./appstore_output)")
    parser.add_argument("-c", "--country", default="th", help="รหัสประเทศ Storefront (ค่าเริ่มต้น: th)")
    parser.add_argument("--no-media", action="store_true", help="ดึงเฉพาะ Metadata JSON ไม่ดาวน์โหลดรูปภาพ")
    parser.add_argument("--devices", default="iphone,ipad", help="อุปกรณ์ที่ต้องการ: iphone, ipad, หรือ iphone,ipad")
    parser.add_argument("--json", action="store_true", help="แสดงผลลัพธ์สุดท้ายเป็น JSON ทาง stdout")

    args = parser.parse_args()
    devices = [d.strip().lower() for d in args.devices.split(",")]
    scraper = AppStoreScraper(output_dir=args.output, country=args.country)

    results = []
    for app_name in args.apps:
        if not args.json:
            print(f"📦 กำลังสกัดข้อมูล Apple App Store: {app_name} ...")
        res = scraper.scrape_app(app_name, download_media=not args.no_media, devices=devices)
        results.append(res)
        if not args.json:
            if res.get("status") == "success":
                shots = len(res.get("iphone_screenshots", [])) + len(res.get("ipad_screenshots", []))
                print(f"  ↳ ✅ สำเร็จ! {res.get('track_name')} ({res.get('artist_name')}) -> โหลด {shots} ภาพ บันทึกที่ {args.output}")
            else:
                print(f"  ↳ ❌ {res.get('message')}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
