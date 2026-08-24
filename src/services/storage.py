import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from config.settings import JSON_DIR, EXPORTS_DIR

class StorageService:
    """จัดการบันทึกและส่งออกข้อมูลสินค้า"""

    @staticmethod
    def save_product_json(product_data: Dict[str, Any], filename: str = None) -> Path:
        """บันทึกข้อมูลสินค้าแต่ละชิ้นลงโฟลเดอร์ data/json/{sku}.json"""
        sku = product_data.get("sku") or "unknown"
        if not filename:
            filename = f"{sku}.json"
        
        file_path = JSON_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        
        return file_path

    @staticmethod
    def update_catalog(product_data: Dict[str, Any]) -> Path:
        """อัปเดตหรือเพิ่มสินค้าลงในแคตตาล็อกรวม data/catalog.json"""
        catalog_path = JSON_DIR / "catalog.json"
        catalog: List[Dict[str, Any]] = []

        if catalog_path.exists():
            try:
                with open(catalog_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
            except Exception:
                catalog = []

        # อัปเดตถ้ามีอยู่แล้ว หรือเพิ่มถ้าเป็นชิ้นใหม่
        sku = product_data.get("sku")
        found = False
        for i, item in enumerate(catalog):
            if item.get("sku") == sku and sku:
                catalog[i] = product_data
                found = True
                break
        
        if not found:
            catalog.append(product_data)

        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        return catalog_path

    @staticmethod
    def export_to_csv(filename: str = "products.csv") -> Path:
        """ส่งออกแคตตาล็อกทั้งหมดเป็นไฟล์ CSV ใน data/exports/"""
        catalog_path = JSON_DIR / "catalog.json"
        if not catalog_path.exists():
            return None

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        csv_path = EXPORTS_DIR / filename
        fieldnames = ["sku", "name", "brand", "price", "currency", "in_stock", "key_specs", "url"]

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for item in catalog:
                writer.writerow(item)

        return csv_path

    @staticmethod
    def download_product_images(product_data: Dict[str, Any]) -> List[Path]:
        """ดาวน์โหลดรูปภาพทั้งหมดของสินค้ามาเก็บไว้ใน data/images/{sku}/"""
        import urllib.request
        from config.settings import IMAGES_DIR, DEFAULT_HEADERS

        sku = product_data.get("sku") or "unknown"
        sku_img_dir = IMAGES_DIR / sku
        sku_img_dir.mkdir(parents=True, exist_ok=True)

        images = product_data.get("images", [])
        saved_paths: List[Path] = []

        for i, img_url in enumerate(images, start=1):
            # หา extension ของไฟล์ เช่น .jpg, .png
            ext = ".jpg"
            if ".png" in img_url.lower():
                ext = ".png"
            elif ".webp" in img_url.lower():
                ext = ".webp"

            file_path = sku_img_dir / f"{sku}_{i}{ext}"
            try:
                req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=10) as res:
                    with open(file_path, "wb") as f:
                        f.write(res.read())
                saved_paths.append(file_path)
            except Exception as e:
                print(f"⚠️ ไม่สามารถโหลดรูป {img_url}: {e}")

        return saved_paths
