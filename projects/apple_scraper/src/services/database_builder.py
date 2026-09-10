import json
import csv
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any
from config.settings import EXPORTS_DIR

class AppleDatabaseBuilder:
    """ตัวสร้างฐานข้อมูลสินค้า Apple ทั้งรูปแบบ JSON, CSV, JS Bundle และ SQLite Database"""

    def __init__(self, exports_dir: Path = EXPORTS_DIR):
        self.exports_dir = exports_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def build_json_database(self, variants: List[Dict[str, Any]], filename: str = "apple_full_catalog.json") -> Path:
        """สร้างฐานข้อมูล JSON แบบลำดับชั้น (Hierarchical Catalog) เหมาะสำหรับ Frontend API"""
        file_path = self.exports_dir / filename

        # จัดกลุ่มตาม Category และ Family
        catalog_tree = {}
        for v in variants:
            cat = v.get("category", "other")
            fam = v.get("family", "Unknown")

            if cat not in catalog_tree:
                catalog_tree[cat] = {
                    "category": cat,
                    "total_items": 0,
                    "families": {}
                }

            if fam not in catalog_tree[cat]["families"]:
                catalog_tree[cat]["families"][fam] = {
                    "family_name": fam,
                    "chip": v.get("specs_chip", "-"),
                    "min_price": v["price_thb"],
                    "max_price": v["price_thb"],
                    "variants": []
                }

            fam_obj = catalog_tree[cat]["families"][fam]
            fam_obj["min_price"] = min(fam_obj["min_price"], v["price_thb"])
            fam_obj["max_price"] = max(fam_obj["max_price"], v["price_thb"])
            fam_obj["variants"].append(v)
            catalog_tree[cat]["total_items"] += 1

        output_data = {
            "metadata": {
                "generated_at": int(time.time()),
                "total_variants": len(variants),
                "categories": list(catalog_tree.keys()),
                "currency": "THB"
            },
            "catalog": catalog_tree
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"📦 สร้าง JSON Database: {file_path}")
        return file_path

    def build_js_bundle(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.js") -> Path:
        """สร้างไฟล์ JS Global variable เพื่อให้ Web Preview เปิดแบบ file:// ได้โดยตรงแบบไม่ติด CORS"""
        file_path = self.exports_dir / filename
        js_content = f"// Apple Official Catalog Data Bundle\nwindow.APPLE_VARIANTS = {json.dumps(variants, ensure_ascii=False, indent=2)};\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"⚡ สร้าง JavaScript Data Bundle: {file_path}")
        return file_path

    def build_csv_database(self, variants: List[Dict[str, Any]], filename: str = "apple_all_variants.csv") -> Path:
        """สร้างตารางข้อมูล Master CSV (UTF-8 with BOM) รองรับ Excel และ Google Sheets"""
        file_path = self.exports_dir / filename
        
        headers = [
            "id", "part_number", "category", "family", "model_name",
            "color_th", "color_en", "color_hex", "storage", "screen_size",
            "connectivity", "price_thb", "formatted_price", "specs_chip",
            "image_url", "product_url"
        ]

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for v in variants:
                row = {k: v.get(k, "-") for k in headers}
                writer.writerow(row)

        print(f"📊 สร้าง CSV Master Table: {file_path}")
        return file_path

    def build_sqlite_database(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.db") -> Path:
        """สร้างฐานข้อมูล SQLite เชิงสัมพันธ์พร้อมตารางและ Index สำหรับค้นหาได้อย่างรวดเร็ว"""
        file_path = self.exports_dir / filename
        
        # ลบไฟล์เก่าหากมีอยู่เพื่อสร้างใหม่
        if file_path.exists():
            file_path.unlink()

        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        # สร้างตาราง variants
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS variants (
            id TEXT PRIMARY KEY,
            part_number TEXT,
            category TEXT,
            family TEXT,
            model_name TEXT,
            color_th TEXT,
            color_en TEXT,
            color_hex TEXT,
            storage TEXT,
            screen_size TEXT,
            connectivity TEXT,
            price_thb INTEGER,
            formatted_price TEXT,
            specs_chip TEXT,
            image_url TEXT,
            product_url TEXT
        )
        """)

        # สร้าง Indexes เพื่อการค้นหาความเร็วสูง
        cursor.execute("CREATE INDEX idx_category ON variants(category)")
        cursor.execute("CREATE INDEX idx_family ON variants(family)")
        cursor.execute("CREATE INDEX idx_price ON variants(price_thb)")
        cursor.execute("CREATE INDEX idx_color ON variants(color_en)")

        # บันทึกข้อมูล
        insert_sql = """
        INSERT OR REPLACE INTO variants (
            id, part_number, category, family, model_name,
            color_th, color_en, color_hex, storage, screen_size,
            connectivity, price_thb, formatted_price, specs_chip,
            image_url, product_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        rows = [
            (
                v.get("id"), v.get("part_number"), v.get("category"), v.get("family"), v.get("model_name"),
                v.get("color_th"), v.get("color_en"), v.get("color_hex"), v.get("storage"), v.get("screen_size"),
                v.get("connectivity"), v.get("price_thb"), v.get("formatted_price"), v.get("specs_chip"),
                v.get("image_url"), v.get("product_url")
            )
            for v in variants
        ]

        cursor.executemany(insert_sql, rows)
        conn.commit()
        conn.close()

        print(f"🗄️ สร้าง SQLite Database: {file_path} (รวม {len(variants)} แถวข้อมูล)")
        return file_path

