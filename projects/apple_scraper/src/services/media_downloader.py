import urllib.request
import os
from pathlib import Path
from typing import List, Dict, Any
from config.settings import IMAGES_DIR, DATA_DIR, DEFAULT_HEADERS

class AppleMediaDownloader:
    """ตัวดาวน์โหลดรูปภาพทุกสีและวิดีโอทางการจาก Apple"""

    def __init__(self):
        self.images_dir = IMAGES_DIR
        self.videos_dir = DATA_DIR / "videos"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def attach_local_paths(self, variants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """เพิ่มฟิลด์ local_image_path ให้กับทุก variant โดยอิงตามมาตรฐาน data/images/{cat}/{pid}/{color}.jpg"""
        for v in variants:
            cat = v.get("category", "other")
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            rel_path = f"data/images/{cat}/{pid}/{cid}.jpg"
            v["local_image_path"] = rel_path
        return variants

    def download_all_images(self, variants: List[Dict[str, Any]]) -> int:
        """ดาวน์โหลดภาพทางการของทุกสีและทุกรุ่นลงเครื่องเพื่อใช้แบบ Offline / Self-host"""
        downloaded = 0
        seen_targets = set()

        for v in variants:
            cat = v.get("category", "other")
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            img_url = v.get("image_url")

            target_key = (cat, pid, cid)
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)

            if not img_url or not img_url.startswith("http"):
                continue

            folder = self.images_dir / cat / pid
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / f"{cid}.jpg"

            if not dest.exists() or dest.stat().st_size < 1000:
                try:
                    req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
                    with urllib.request.urlopen(req, timeout=12) as res:
                        with open(dest, "wb") as f:
                            f.write(res.read())
                    downloaded += 1
                except Exception as e:
                    print(f"⚠️ ไม่สามารถดาวน์โหลดรูป {pid} ({cid}): {e}")

        print(f"📸 ตรวจสอบและดาวน์โหลดภาพสินค้า Apple ทางการ: บันทึกใหม่ {downloaded} รูป (รวมทั้งหมด {len(seen_targets)} สี)")
        return downloaded

    def download_variant_images(self, variants: List[Dict[str, Any]], max_per_family: int = 3):
        """เข้ากันได้กับโค้ดเดิม พร้อมอัปเดตดาวน์โหลดภาพทุกสีแบบครบวงจร"""
        self.attach_local_paths(variants)
        return self.download_all_images(variants)

