import json
import csv
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import DATA_DIR, JSON_DIR, RAW_HTML_DIR, IMAGES_DIR, EXPORTS_DIR, DEFAULT_HEADERS

class AppleStorageService:
    """จัดการการบันทึกไฟล์ จัดการแคช และดาวน์โหลดภาพสำหรับ Apple Scraper"""

    @staticmethod
    def save_raw_html(html_content: str, filename: str) -> Path:
        """บันทึก Raw HTML สำหรับใช้ตรวจสอบหรือแคชออฟไลน์"""
        if not filename.endswith(".html"):
            filename += ".html"
        file_path = RAW_HTML_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return file_path

    @staticmethod
    def save_product_json(data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """บันทึกข้อมูลสินค้าในรูปแบบ JSON"""
        slug = data.get("slug") or "apple_product"
        if not filename:
            filename = f"{slug}.json"
        elif not filename.endswith(".json"):
            filename += ".json"

        file_path = JSON_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    @staticmethod
    def export_summary_csv(products: List[Dict[str, Any]], filename: str = "apple_products_summary.csv") -> Path:
        """ส่งออกตารางสรุปสินค้าเป็นไฟล์ CSV"""
        file_path = EXPORTS_DIR / filename
        headers = [
            "title", "family", "starting_price_thb", "colors_count", "capacities",
            "chip", "display_size", "camera_summary", "url", "image_url"
        ]

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for p in products:
                writer.writerow({
                    "title": p.get("title", "-"),
                    "family": p.get("family", "-"),
                    "starting_price_thb": p.get("starting_price_thb", "-"),
                    "colors_count": len(p.get("colors", [])),
                    "capacities": ", ".join(p.get("capacities", [])) if isinstance(p.get("capacities"), list) else "-",
                    "chip": p.get("specs", {}).get("chip", "-"),
                    "display_size": p.get("specs", {}).get("display", "-"),
                    "camera_summary": p.get("specs", {}).get("camera", "-"),
                    "url": p.get("url", "-"),
                    "image_url": p.get("images", [""])[0] if p.get("images") else "-"
                })
        return file_path

    @staticmethod
    def download_images(image_urls: List[str], folder_name: str, max_images: int = 8) -> List[str]:
        """ดาวน์โหลดรูปภาพทางการของ Apple ลงเครื่อง"""
        target_dir = IMAGES_DIR / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for idx, url in enumerate(image_urls[:max_images], start=1):
            if not url or not url.startswith("http"):
                continue
            ext = ".png" if ".png" in url.lower() else ".jpg"
            dest_file = target_dir / f"img_{idx}{ext}"

            try:
                req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=10) as res:
                    with open(dest_file, "wb") as f:
                        f.write(res.read())
                saved_files.append(str(dest_file.relative_to(DATA_DIR.parent)))
            except Exception:
                pass

        return saved_files
