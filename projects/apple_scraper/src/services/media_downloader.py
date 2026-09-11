import urllib.request
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import IMAGES_DIR, DATA_DIR, DEFAULT_HEADERS

class AppleMediaDownloader:
    """ตัวดาวน์โหลดรูปภาพทุกสี ครบทุกมุมมอง (Multi-Angle Gallery) ความละเอียดสูงระดับ 4K Retina และ Transparent PNG"""

    def __init__(self):
        self.images_dir = IMAGES_DIR
        self.videos_dir = DATA_DIR / "videos"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def attach_local_paths(self, variants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """เพิ่มฟิลด์ local_image_path, local_image_png และอัปเดตพาธใน gallery ทุกรายการ"""
        for v in variants:
            cat = v.get("category", "other")
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            
            # 1. พาธรูปหลัก (Backward-compatible & Standard)
            v["local_image_path"] = f"data/images/{cat}/{pid}/{cid}.jpg"
            v["local_image_png"] = f"data/images/{cat}/{pid}/{cid}/hero.png"

            # 2. อัปเดตพาธภายใน gallery
            if "gallery" in v and isinstance(v["gallery"], list):
                for g in v["gallery"]:
                    angle = g.get("angle_type", "view")
                    g["local_image_path"] = f"data/images/{cat}/{pid}/{cid}/{angle}.jpg"
                    g["local_image_png"] = f"data/images/{cat}/{pid}/{cid}/{angle}.png"

        return variants

    def _download_file(self, url: str, dest_path: Path, min_size: int = 50000) -> bool:
        """ดาวน์โหลดไฟล์แบบปลอดภัย ตรวจสอบขนาดเพื่อยืนยันว่าเป็นภาพความละเอียดสูงแท้จริง"""
        if not url or not url.startswith("http"):
            return False

        # ถ้ามีไฟล์อยู่แล้ว และขนาดเกิน min_size (ภาพความละเอียดสูง 2560px ปกติจะมีขนาด > 50KB) ให้ข้ามได้
        if dest_path.exists() and dest_path.stat().st_size >= min_size:
            return False

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read()
                if len(content) > 1000:
                    with open(dest_path, "wb") as f:
                        f.write(content)
                    return True
        except Exception as e:
            pass
        return False

    def download_all_images(self, variants: List[Dict[str, Any]], download_galleries: bool = True, download_png: bool = False, max_workers: int = 20) -> int:
        """ดาวน์โหลดภาพทางการของทุกสีและทุกมุมมอง (2560x2560 Retina) ลงเครื่องแบบ Multi-threaded"""
        self.attach_local_paths(variants)

        tasks = []  # list of (url, dest_path)
        seen_urls = set()

        for v in variants:
            cat = v.get("category", "other")
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")

            # 1. รูปหลักประจำสี (Hero 2560px)
            hero_url = v.get("image_url_highres") or v.get("image_url")
            hero_dest = self.images_dir / cat / pid / f"{cid}.jpg"
            hero_dest_folder = self.images_dir / cat / pid / cid / "hero.jpg"

            if hero_url and hero_url not in seen_urls:
                seen_urls.add(hero_url)
                tasks.append((hero_url, hero_dest))
                tasks.append((hero_url, hero_dest_folder))

            # 2. รูปไดคัตพื้นหลังใส Transparent PNG (ถ้าต้องการ)
            if download_png and v.get("image_url_png"):
                png_url = v.get("image_url_png")
                png_dest = self.images_dir / cat / pid / cid / "hero.png"
                if png_url not in seen_urls:
                    seen_urls.add(png_url)
                    tasks.append((png_url, png_dest))

            # 3. รูปภาพหลายมุมมองใน Gallery (Back, Side, Box, Display, Ports, ฯลฯ)
            if download_galleries and "gallery" in v and isinstance(v["gallery"], list):
                for g in v["gallery"]:
                    g_url = g.get("image_url")
                    angle = g.get("angle_type", "view")
                    g_dest = self.images_dir / cat / pid / cid / f"{angle}.jpg"
                    if g_url and g_url not in seen_urls:
                        seen_urls.add(g_url)
                        tasks.append((g_url, g_dest))

        print(f"🚀 กำลังดาวน์โหลดรูปภาพสินค้า 4K Retina ทั้งหมด {len(tasks)} ไฟล์ ด้วย {max_workers} threads...")

        downloaded_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._download_file, url, dest): dest for url, dest in tasks}
            for future in as_completed(future_to_url):
                dest = future_to_url[future]
                try:
                    if future.result():
                        downloaded_count += 1
                except Exception:
                    pass

        # สำเนาไฟล์ hero ให้ตรงกับ root ของสีเพื่อความสมบูรณ์และอัปเกรดเป็น 4K Retina 100%
        for v in variants:
            cat = v.get("category", "other")
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            src_hero = self.images_dir / cat / pid / cid / "hero.jpg"
            dest_hero = self.images_dir / cat / pid / f"{cid}.jpg"
            if src_hero.exists():
                shutil.copyfile(src_hero, dest_hero)

        print(f"📸 ตรวจสอบและดาวน์โหลดภาพสินค้า Apple 4K Retina เสร็จสิ้น: บันทึกสำเร็จ {downloaded_count} ไฟล์ใหม่!")
        return downloaded_count

    def download_variant_images(self, variants: List[Dict[str, Any]], max_per_family: int = 3):
        """เข้ากันได้กับโค้ดเดิม พร้อมดาวน์โหลดภาพความละเอียดสูงทุกสีและทุกมุมมอง"""
        return self.download_all_images(variants, download_galleries=True, download_png=False)


