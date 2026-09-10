import urllib.request
import os
from pathlib import Path
from typing import List, Dict, Any
from config.settings import IMAGES_DIR, DATA_DIR, DEFAULT_HEADERS

class AppleMediaDownloader:
    """ตัวดาวน์โหลดรูปภาพทุกสีและวิดีโอทางการจาก Apple"""

    def __init__(self):
        self.videos_dir = DATA_DIR / "videos"
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def download_variant_images(self, variants: List[Dict[str, Any]], max_per_family: int = 3):
        """ดาวน์โหลดรูปภาพสินค้าแยกตามแต่ละสีและตระกูลสินค้า"""
        downloaded = 0
        family_counts = {}

        for v in variants:
            fam = v.get("family", "product").lower().replace(" ", "-")
            color = v.get("color_en", "standard").lower().replace(" ", "-")
            img_url = v.get("image_url")
            
            if not img_url or not img_url.startswith("http"):
                continue

            current_count = family_counts.get(fam, 0)
            if current_count >= max_per_family:
                continue

            folder = IMAGES_DIR / fam / color
            folder.mkdir(parents=True, exist_ok=True)
            
            ext = ".png" if ".png" in img_url.lower() else ".jpg"
            dest = folder / f"hero{ext}"

            if not dest.exists():
                try:
                    req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
                    with urllib.request.urlopen(req, timeout=10) as res:
                        with open(dest, "wb") as f:
                            f.write(res.read())
                    downloaded += 1
                    family_counts[fam] = current_count + 1
                except Exception:
                    pass

        print(f"📸 ดาวน์โหลดภาพสินค้าตัวอย่างเก็บลงเครื่องเรียบร้อย: {downloaded} รูป")
