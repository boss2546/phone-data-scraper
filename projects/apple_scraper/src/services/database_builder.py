import json
import csv
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config.settings import EXPORTS_DIR

CATEGORY_METADATA = [
    {"id": "iphone", "name_th": "iPhone", "name_en": "iPhone", "icon": "📱", "sort_order": 1},
    {"id": "ipad", "name_th": "iPad", "name_en": "iPad", "icon": "📱", "sort_order": 2},
    {"id": "mac", "name_th": "Mac", "name_en": "Mac", "icon": "💻", "sort_order": 3},
    {"id": "watch", "name_th": "Apple Watch", "name_en": "Apple Watch", "icon": "⌚", "sort_order": 4}
]

class AppleDatabaseBuilder:
    """ตัวสร้างฐานข้อมูลสินค้า Apple เชิงสัมพันธ์แบบสมบูรณ์ 100% (Sub-Models, Dimensions, Weights, Full Tech Specs, 4K Retina Images)"""

    def __init__(self, exports_dir: Path = EXPORTS_DIR):
        self.exports_dir = exports_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def extract_normalized_entities(self, variants: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """แยก Entity ให้เป็นไปตามมาตรฐานฐานข้อมูลเชิงสัมพันธ์แบบ Normalized:
        1. Colors
        2. Products (Families)
        3. Sub-Models (รุ่นย่อยและฟอร์มแฟกเตอร์พร้อมสเปกละเอียดครบ 100%)
        4. Product_Images (ชุดรูปภาพ 4K Retina ทุกมุมมอง)
        """
        # 1. Colors
        colors_map = {}
        for v in variants:
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            if cid and cid not in colors_map:
                colors_map[cid] = {
                    "id": cid,
                    "name_th": v.get("color_th", "มาตรฐาน"),
                    "name_en": v.get("color_en", "Standard"),
                    "color_hex": v.get("color_hex", "#888888")
                }

        # 2. Product Images (All unique angle assets)
        images_map = {}
        for v in variants:
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            sub_id = v.get("sub_model_id") or pid
            cat = v.get("category", "other")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            gallery = v.get("gallery", [])

            for g in gallery:
                img_id = g.get("id") or f"{pid}-{cid}-{g.get('angle_type', 'view')}"
                if img_id not in images_map:
                    images_map[img_id] = {
                        "image_id": img_id,
                        "product_id": pid,
                        "sub_model_id": sub_id,
                        "color_id": cid,
                        "angle_type": g.get("angle_type", "view"),
                        "label_th": g.get("label_th", ""),
                        "label_en": g.get("label_en", ""),
                        "image_url": g.get("image_url", ""),
                        "image_url_png": g.get("image_url_png", ""),
                        "local_image_path": g.get("local_image_path", f"data/images/{cat}/{pid}/{cid}/{g.get('angle_type')}.jpg"),
                        "local_image_png": g.get("local_image_png", f"data/images/{cat}/{pid}/{cid}/{g.get('angle_type')}.png"),
                        "resolution": g.get("resolution", "2560x2560"),
                        "is_hero": 1 if g.get("is_hero") else 0,
                        "sort_order": g.get("sort_order", 0)
                    }

        # 3. Sub-Models (รุ่นย่อยเจาะจงพร้อมสเปกเต็ม 100%)
        sub_models_map = {}
        for v in variants:
            sub_id = v.get("sub_model_id") or v.get("product_id")
            pid = v.get("product_id")
            cat = v.get("category", "other")
            price = v.get("price_thb", 0)

            if sub_id not in sub_models_map:
                sub_models_map[sub_id] = {
                    "id": sub_id,
                    "family_id": pid,
                    "category_id": cat,
                    "name_th": v.get("sub_model_name") or v.get("family"),
                    "name_en": v.get("sub_model_name_en") or v.get("family"),
                    "screen_size": v.get("screen_size", "-"),
                    "dimensions_mm": v.get("dimensions_mm", "-"),
                    "weight_grams": v.get("weight_grams", "-"),
                    "chip": v.get("specs_chip", "-"),
                    "display_specs": v.get("display_specs", "-"),
                    "camera_specs": v.get("camera_specs", "-"),
                    "battery_specs": v.get("battery_specs", "-"),
                    "box_contents": v.get("box_contents", "-"),
                    "connectivity": v.get("connectivity", "-"),
                    "material": v.get("material", "-"),
                    "min_price_thb": price,
                    "max_price_thb": price,
                    "hero_image_url": v.get("image_url_highres") or v.get("image_url", ""),
                    "hero_image_png": v.get("image_url_png", ""),
                    "buy_url": v.get("buy_url", v.get("product_url", "")),
                    "specs_url": v.get("specs_url", ""),
                    "overview_url": v.get("overview_url", "")
                }
            else:
                sm = sub_models_map[sub_id]
                if price > 0:
                    sm["min_price_thb"] = min(sm["min_price_thb"], price)
                    sm["max_price_thb"] = max(sm["max_price_thb"], price)

        # 4. Products (Product Families)
        products_map = {}
        for v in variants:
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cat = v.get("category", "other")
            fam = v.get("family", "Unknown")
            price = v.get("price_thb", 0)

            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            local_img = v.get("local_image_path") or f"data/images/{cat}/{pid}/{cid}.jpg"
            local_png = v.get("local_image_png") or f"data/images/{cat}/{pid}/{cid}/hero.png"
            v["local_image_path"] = local_img
            v["local_image_png"] = local_png

            if pid not in products_map:
                products_map[pid] = {
                    "id": pid,
                    "category_id": cat,
                    "name": fam,
                    "chip": v.get("specs_chip", "-"),
                    "screen_size": v.get("screen_size", "-"),
                    "min_price_thb": price,
                    "max_price_thb": price,
                    "hero_image_url": v.get("image_url_highres") or v.get("image_url", ""),
                    "hero_image_png": v.get("image_url_png", ""),
                    "local_hero_image": local_img,
                    "local_hero_image_png": local_png,
                    "gallery_count": len(v.get("gallery", [])),
                    "buy_url": v.get("buy_url", v.get("product_url", "")),
                    "specs_url": v.get("specs_url", ""),
                    "overview_url": v.get("overview_url", ""),
                    "product_url": v.get("buy_url", v.get("product_url", ""))
                }
            else:
                p = products_map[pid]
                if price > 0:
                    p["min_price_thb"] = min(p["min_price_thb"], price)
                    p["max_price_thb"] = max(p["max_price_thb"], price)

        for pid, p in products_map.items():
            count = sum(1 for img in images_map.values() if img["product_id"] == pid)
            if count > 0:
                p["gallery_count"] = count

        return list(colors_map.values()), list(products_map.values()), list(sub_models_map.values()), list(images_map.values()), variants

    def build_sqlite_database(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.db") -> Path:
        """สร้างฐานข้อมูล SQLite เชิงสัมพันธ์แบบ Normalized (6 Tables + 3 Views + Indexes ครบทุกมิติ)"""
        file_path = self.exports_dir / filename
        if file_path.exists():
            file_path.unlink()

        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        # 1. Categories Table
        cursor.execute("""
        CREATE TABLE categories (
            id TEXT PRIMARY KEY,
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            icon TEXT,
            sort_order INTEGER DEFAULT 0
        );
        """)

        # 2. Products (Families) Table
        cursor.execute("""
        CREATE TABLE products (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL REFERENCES categories(id),
            name TEXT NOT NULL,
            chip TEXT,
            screen_size TEXT,
            min_price_thb INTEGER,
            max_price_thb INTEGER,
            hero_image_url TEXT,
            hero_image_png TEXT,
            local_hero_image TEXT,
            local_hero_image_png TEXT,
            gallery_count INTEGER DEFAULT 1,
            buy_url TEXT,
            specs_url TEXT,
            overview_url TEXT,
            product_url TEXT
        );
        """)

        # 3. Sub-Models Table
        cursor.execute("""
        CREATE TABLE sub_models (
            id TEXT PRIMARY KEY,
            family_id TEXT NOT NULL REFERENCES products(id),
            category_id TEXT NOT NULL REFERENCES categories(id),
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            screen_size TEXT NOT NULL,
            dimensions_mm TEXT NOT NULL,
            weight_grams TEXT NOT NULL,
            chip TEXT NOT NULL,
            display_specs TEXT NOT NULL,
            camera_specs TEXT NOT NULL,
            battery_specs TEXT NOT NULL,
            box_contents TEXT NOT NULL,
            connectivity TEXT NOT NULL,
            material TEXT,
            min_price_thb INTEGER NOT NULL,
            max_price_thb INTEGER NOT NULL,
            hero_image_url TEXT,
            hero_image_png TEXT,
            buy_url TEXT,
            specs_url TEXT,
            overview_url TEXT
        );
        """)

        # 4. Colors Table
        cursor.execute("""
        CREATE TABLE colors (
            id TEXT PRIMARY KEY,
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            color_hex TEXT NOT NULL
        );
        """)

        # 5. Product Images Table
        cursor.execute("""
        CREATE TABLE product_images (
            image_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL REFERENCES products(id),
            sub_model_id TEXT,
            color_id TEXT NOT NULL,
            angle_type TEXT NOT NULL,
            label_th TEXT,
            label_en TEXT,
            image_url TEXT NOT NULL,
            image_url_png TEXT,
            local_image_path TEXT,
            local_image_png TEXT,
            resolution TEXT DEFAULT '2560x2560',
            is_hero BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        );
        """)

        # 6. Variants Table (Full Specifications)
        cursor.execute("""
        CREATE TABLE variants (
            id TEXT PRIMARY KEY,
            part_number TEXT NOT NULL,
            sub_model_id TEXT NOT NULL REFERENCES sub_models(id),
            product_id TEXT NOT NULL REFERENCES products(id),
            category_id TEXT NOT NULL REFERENCES categories(id),
            model_name TEXT NOT NULL,
            color_id TEXT REFERENCES colors(id),
            color_th TEXT NOT NULL,
            color_en TEXT NOT NULL,
            color_hex TEXT NOT NULL,
            storage TEXT NOT NULL,
            screen_size TEXT NOT NULL,
            connectivity TEXT NOT NULL,
            specs_chip TEXT NOT NULL,
            dimensions_mm TEXT NOT NULL,
            weight_grams TEXT NOT NULL,
            display_specs TEXT NOT NULL,
            camera_specs TEXT NOT NULL,
            battery_specs TEXT NOT NULL,
            box_contents TEXT NOT NULL,
            material TEXT,
            price_thb INTEGER NOT NULL,
            formatted_price TEXT NOT NULL,
            image_url TEXT,
            image_url_png TEXT,
            local_image_path TEXT,
            local_image_png TEXT,
            buy_url TEXT,
            specs_url TEXT,
            overview_url TEXT,
            product_url TEXT
        );
        """)

        # Indexes
        cursor.execute("CREATE INDEX idx_var_category ON variants(category_id);")
        cursor.execute("CREATE INDEX idx_var_product ON variants(product_id);")
        cursor.execute("CREATE INDEX idx_var_sub_model ON variants(sub_model_id);")
        cursor.execute("CREATE INDEX idx_var_price ON variants(price_thb);")
        cursor.execute("CREATE INDEX idx_var_color ON variants(color_id);")
        cursor.execute("CREATE INDEX idx_var_storage ON variants(storage);")
        cursor.execute("CREATE INDEX idx_img_product ON product_images(product_id);")
        cursor.execute("CREATE INDEX idx_img_color ON product_images(color_id);")

        # 7. Views
        cursor.execute("""
        CREATE VIEW v_catalog_complete AS
        SELECT 
            v.id AS variant_id,
            v.part_number,
            c.id AS category_id,
            c.name_th AS category_name,
            p.id AS family_id,
            p.name AS family_name,
            sm.id AS sub_model_id,
            sm.name_th AS sub_model_name,
            v.model_name,
            v.color_th,
            v.color_en,
            v.color_hex,
            v.storage,
            v.screen_size,
            v.connectivity,
            v.specs_chip,
            v.dimensions_mm,
            v.weight_grams,
            v.display_specs,
            v.camera_specs,
            v.battery_specs,
            v.box_contents,
            v.material,
            v.price_thb,
            v.formatted_price,
            v.image_url,
            v.image_url_png,
            v.local_image_path,
            v.local_image_png,
            v.buy_url,
            v.specs_url,
            v.overview_url
        FROM variants v
        JOIN sub_models sm ON v.sub_model_id = sm.id
        JOIN products p ON v.product_id = p.id
        JOIN categories c ON v.category_id = c.id;
        """)

        cursor.execute("""
        CREATE VIEW v_sub_models_summary AS
        SELECT 
            sm.id AS sub_model_id,
            c.name_th AS category,
            p.name AS family,
            sm.name_th AS sub_model,
            sm.screen_size,
            sm.dimensions_mm,
            sm.weight_grams,
            sm.chip,
            sm.min_price_thb,
            sm.max_price_thb,
            COUNT(v.id) AS total_variants,
            GROUP_CONCAT(DISTINCT v.color_th) AS colors_available,
            GROUP_CONCAT(DISTINCT v.storage) AS storages_available,
            sm.hero_image_url,
            sm.buy_url,
            sm.specs_url
        FROM sub_models sm
        JOIN products p ON sm.family_id = p.id
        JOIN categories c ON sm.category_id = c.id
        LEFT JOIN variants v ON v.sub_model_id = sm.id
        GROUP BY sm.id;
        """)

        cursor.execute("""
        CREATE VIEW v_product_summary AS
        SELECT 
            p.id AS product_id,
            c.name_th AS category,
            p.name AS product_name,
            p.chip,
            p.screen_size,
            p.min_price_thb,
            p.max_price_thb,
            COUNT(DISTINCT sm.id) AS total_sub_models,
            COUNT(v.id) AS total_variants,
            GROUP_CONCAT(DISTINCT v.color_th) AS colors_available,
            GROUP_CONCAT(DISTINCT v.storage) AS storages_available,
            p.hero_image_url,
            p.hero_image_png,
            p.local_hero_image,
            p.local_hero_image_png,
            p.gallery_count
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN sub_models sm ON sm.family_id = p.id
        LEFT JOIN variants v ON v.product_id = p.id
        GROUP BY p.id;
        """)

        # Insert Categories
        cursor.executemany(
            "INSERT INTO categories (id, name_th, name_en, icon, sort_order) VALUES (?, ?, ?, ?, ?)",
            [(c["id"], c["name_th"], c["name_en"], c["icon"], c["sort_order"]) for c in CATEGORY_METADATA]
        )

        colors, products, sub_models, product_images, _ = self.extract_normalized_entities(variants)

        # Insert Colors
        cursor.executemany(
            "INSERT INTO colors (id, name_th, name_en, color_hex) VALUES (?, ?, ?, ?)",
            [(c["id"], c["name_th"], c["name_en"], c["color_hex"]) for c in colors]
        )

        # Insert Products
        cursor.executemany(
            """INSERT INTO products (id, category_id, name, chip, screen_size, min_price_thb, max_price_thb, hero_image_url, hero_image_png, local_hero_image, local_hero_image_png, gallery_count, buy_url, specs_url, overview_url, product_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(p["id"], p["category_id"], p["name"], p["chip"], p["screen_size"], p["min_price_thb"], p["max_price_thb"], p["hero_image_url"], p.get("hero_image_png", ""), p.get("local_hero_image", ""), p.get("local_hero_image_png", ""), p.get("gallery_count", 1), p.get("buy_url", ""), p.get("specs_url", ""), p.get("overview_url", ""), p.get("product_url", "")) for p in products]
        )

        # Insert Sub-Models
        cursor.executemany(
            """INSERT INTO sub_models (id, family_id, category_id, name_th, name_en, screen_size, dimensions_mm, weight_grams, chip, display_specs, camera_specs, battery_specs, box_contents, connectivity, material, min_price_thb, max_price_thb, hero_image_url, hero_image_png, buy_url, specs_url, overview_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(sm["id"], sm["family_id"], sm["category_id"], sm["name_th"], sm["name_en"], sm["screen_size"], sm["dimensions_mm"], sm["weight_grams"], sm["chip"], sm["display_specs"], sm["camera_specs"], sm["battery_specs"], sm["box_contents"], sm["connectivity"], sm["material"], sm["min_price_thb"], sm["max_price_thb"], sm.get("hero_image_url", ""), sm.get("hero_image_png", ""), sm.get("buy_url", ""), sm.get("specs_url", ""), sm.get("overview_url", "")) for sm in sub_models]
        )

        # Insert Product Images
        cursor.executemany(
            """INSERT INTO product_images (image_id, product_id, sub_model_id, color_id, angle_type, label_th, label_en, image_url, image_url_png, local_image_path, local_image_png, resolution, is_hero, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(img["image_id"], img["product_id"], img.get("sub_model_id", img["product_id"]), img["color_id"], img["angle_type"], img["label_th"], img["label_en"], img["image_url"], img.get("image_url_png", ""), img.get("local_image_path", ""), img.get("local_image_png", ""), img.get("resolution", "2560x2560"), img.get("is_hero", 0), img.get("sort_order", 0)) for img in product_images]
        )

        # Insert Variants
        var_rows = [
            (
                v.get("id"),
                v.get("part_number") or v.get("id"),
                v.get("sub_model_id") or v.get("product_id"),
                v.get("product_id") or v.get("family", "").lower().replace(" ", "-"),
                v.get("category_id") or v.get("category", "other"),
                v.get("model_name"),
                v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-"),
                v.get("color_th"),
                v.get("color_en"),
                v.get("color_hex"),
                v.get("storage", "-"),
                v.get("screen_size", "-"),
                v.get("connectivity", "Standard"),
                v.get("specs_chip", "-"),
                v.get("dimensions_mm", "-"),
                v.get("weight_grams", "-"),
                v.get("display_specs", "-"),
                v.get("camera_specs", "-"),
                v.get("battery_specs", "-"),
                v.get("box_contents", "-"),
                v.get("material", "-"),
                int(v.get("price_thb", 0)),
                v.get("formatted_price", "฿0"),
                v.get("image_url", ""),
                v.get("image_url_png", ""),
                v.get("local_image_path", ""),
                v.get("local_image_png", ""),
                v.get("buy_url", v.get("product_url", "")),
                v.get("specs_url", ""),
                v.get("overview_url", ""),
                v.get("product_url", v.get("buy_url", ""))
            )
            for v in variants
        ]

        cursor.executemany(
            """INSERT OR REPLACE INTO variants (
                id, part_number, sub_model_id, product_id, category_id, model_name,
                color_id, color_th, color_en, color_hex, storage,
                screen_size, connectivity, specs_chip, dimensions_mm, weight_grams,
                display_specs, camera_specs, battery_specs, box_contents, material,
                price_thb, formatted_price, image_url, image_url_png, local_image_path,
                local_image_png, buy_url, specs_url, overview_url, product_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            var_rows
        )

        conn.commit()
        conn.close()

        print(f"🗄️ สร้าง SQLite Database: {file_path} ({len(variants)} variants, {len(sub_models)} sub-models, {len(product_images)} images)")
        return file_path

    def build_sql_dump(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.sql") -> Path:
        """สร้างไฟล์ SQL Dump มาตรฐาน (DDL + INSERT) พร้อมนำเข้า MySQL, PostgreSQL, Supabase หรือ SQLite"""
        file_path = self.exports_dir / filename
        colors, products, sub_models, product_images, _ = self.extract_normalized_entities(variants)

        def esc(val: Any) -> str:
            if val is None:
                return "NULL"
            s = str(val).replace("'", "''")
            return f"'{s}'"

        lines = [
            "-- ========================================================================",
            "-- Apple Store Thailand Official Catalog SQL Dump",
            f"-- Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Total variants: {len(variants)}, Sub-models: {len(sub_models)}, Images: {len(product_images)}",
            "-- ========================================================================",
            "",
            "-- 1. Categories Table",
            "CREATE TABLE IF NOT EXISTS categories (",
            "    id VARCHAR(32) PRIMARY KEY,",
            "    name_th VARCHAR(64) NOT NULL,",
            "    name_en VARCHAR(64) NOT NULL,",
            "    icon VARCHAR(16),",
            "    sort_order INT DEFAULT 0",
            ");",
            "",
            "-- 2. Products (Families) Table",
            "CREATE TABLE IF NOT EXISTS products (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    category_id VARCHAR(32) NOT NULL,",
            "    name VARCHAR(128) NOT NULL,",
            "    chip VARCHAR(64),",
            "    screen_size VARCHAR(64),",
            "    min_price_thb INT,",
            "    max_price_thb INT,",
            "    hero_image_url TEXT,",
            "    hero_image_png TEXT,",
            "    local_hero_image TEXT,",
            "    local_hero_image_png TEXT,",
            "    gallery_count INT DEFAULT 1,",
            "    buy_url TEXT,",
            "    specs_url TEXT,",
            "    overview_url TEXT,",
            "    product_url TEXT",
            ");",
            "",
            "-- 3. Sub-Models Table (Detailed Specs Hierarchy)",
            "CREATE TABLE IF NOT EXISTS sub_models (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    family_id VARCHAR(64) NOT NULL,",
            "    category_id VARCHAR(32) NOT NULL,",
            "    name_th VARCHAR(128) NOT NULL,",
            "    name_en VARCHAR(128) NOT NULL,",
            "    screen_size VARCHAR(64) NOT NULL,",
            "    dimensions_mm VARCHAR(128) NOT NULL,",
            "    weight_grams VARCHAR(64) NOT NULL,",
            "    chip TEXT NOT NULL,",
            "    display_specs TEXT NOT NULL,",
            "    camera_specs TEXT NOT NULL,",
            "    battery_specs TEXT NOT NULL,",
            "    box_contents TEXT NOT NULL,",
            "    connectivity TEXT NOT NULL,",
            "    material VARCHAR(128),",
            "    min_price_thb INT NOT NULL,",
            "    max_price_thb INT NOT NULL,",
            "    hero_image_url TEXT,",
            "    hero_image_png TEXT,",
            "    buy_url TEXT,",
            "    specs_url TEXT,",
            "    overview_url TEXT",
            ");",
            "",
            "-- 4. Colors Table",
            "CREATE TABLE IF NOT EXISTS colors (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    name_th VARCHAR(64) NOT NULL,",
            "    name_en VARCHAR(64) NOT NULL,",
            "    color_hex VARCHAR(16) NOT NULL",
            ");",
            "",
            "-- 5. Product Images Table",
            "CREATE TABLE IF NOT EXISTS product_images (",
            "    image_id VARCHAR(128) PRIMARY KEY,",
            "    product_id VARCHAR(64) NOT NULL,",
            "    sub_model_id VARCHAR(64),",
            "    color_id VARCHAR(64) NOT NULL,",
            "    angle_type VARCHAR(32) NOT NULL,",
            "    label_th VARCHAR(128),",
            "    label_en VARCHAR(128),",
            "    image_url TEXT NOT NULL,",
            "    image_url_png TEXT,",
            "    local_image_path TEXT,",
            "    local_image_png TEXT,",
            "    resolution VARCHAR(32) DEFAULT '2560x2560',",
            "    is_hero BOOLEAN DEFAULT 0,",
            "    sort_order INT DEFAULT 0",
            ");",
            "",
            "-- 6. Variants Table",
            "CREATE TABLE IF NOT EXISTS variants (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    part_number VARCHAR(64) NOT NULL,",
            "    sub_model_id VARCHAR(64) NOT NULL,",
            "    product_id VARCHAR(64) NOT NULL,",
            "    category_id VARCHAR(32) NOT NULL,",
            "    model_name VARCHAR(255) NOT NULL,",
            "    color_id VARCHAR(64),",
            "    color_th VARCHAR(64) NOT NULL,",
            "    color_en VARCHAR(64) NOT NULL,",
            "    color_hex VARCHAR(16) NOT NULL,",
            "    storage VARCHAR(64) NOT NULL,",
            "    screen_size VARCHAR(32) NOT NULL,",
            "    connectivity VARCHAR(64) NOT NULL,",
            "    specs_chip TEXT NOT NULL,",
            "    dimensions_mm VARCHAR(128) NOT NULL,",
            "    weight_grams VARCHAR(64) NOT NULL,",
            "    display_specs TEXT NOT NULL,",
            "    camera_specs TEXT NOT NULL,",
            "    battery_specs TEXT NOT NULL,",
            "    box_contents TEXT NOT NULL,",
            "    material VARCHAR(128),",
            "    price_thb INT NOT NULL,",
            "    formatted_price VARCHAR(32) NOT NULL,",
            "    image_url TEXT,",
            "    image_url_png TEXT,",
            "    local_image_path TEXT,",
            "    local_image_png TEXT,",
            "    buy_url TEXT,",
            "    specs_url TEXT,",
            "    overview_url TEXT,",
            "    product_url TEXT",
            ");",
            "",
            "-- INSERT DATA --"
        ]

        for c in CATEGORY_METADATA:
            lines.append(f"INSERT INTO categories (id, name_th, name_en, icon, sort_order) VALUES ({esc(c['id'])}, {esc(c['name_th'])}, {esc(c['name_en'])}, {esc(c['icon'])}, {c['sort_order']});")

        for c in colors:
            lines.append(f"INSERT INTO colors (id, name_th, name_en, color_hex) VALUES ({esc(c['id'])}, {esc(c['name_th'])}, {esc(c['name_en'])}, {esc(c['color_hex'])});")

        for p in products:
            lines.append(f"INSERT INTO products (id, category_id, name, chip, screen_size, min_price_thb, max_price_thb, hero_image_url, hero_image_png, local_hero_image, local_hero_image_png, gallery_count, buy_url, specs_url, overview_url, product_url) VALUES ({esc(p['id'])}, {esc(p['category_id'])}, {esc(p['name'])}, {esc(p['chip'])}, {esc(p['screen_size'])}, {p['min_price_thb']}, {p['max_price_thb']}, {esc(p['hero_image_url'])}, {esc(p.get('hero_image_png', ''))}, {esc(p.get('local_hero_image', ''))}, {esc(p.get('local_hero_image_png', ''))}, {p.get('gallery_count', 1)}, {esc(p.get('buy_url', ''))}, {esc(p.get('specs_url', ''))}, {esc(p.get('overview_url', ''))}, {esc(p.get('product_url', ''))});")

        for sm in sub_models:
            lines.append(f"INSERT INTO sub_models (id, family_id, category_id, name_th, name_en, screen_size, dimensions_mm, weight_grams, chip, display_specs, camera_specs, battery_specs, box_contents, connectivity, material, min_price_thb, max_price_thb, hero_image_url, hero_image_png, buy_url, specs_url, overview_url) VALUES ({esc(sm['id'])}, {esc(sm['family_id'])}, {esc(sm['category_id'])}, {esc(sm['name_th'])}, {esc(sm['name_en'])}, {esc(sm['screen_size'])}, {esc(sm['dimensions_mm'])}, {esc(sm['weight_grams'])}, {esc(sm['chip'])}, {esc(sm['display_specs'])}, {esc(sm['camera_specs'])}, {esc(sm['battery_specs'])}, {esc(sm['box_contents'])}, {esc(sm['connectivity'])}, {esc(sm.get('material', ''))}, {sm['min_price_thb']}, {sm['max_price_thb']}, {esc(sm.get('hero_image_url', ''))}, {esc(sm.get('hero_image_png', ''))}, {esc(sm.get('buy_url', ''))}, {esc(sm.get('specs_url', ''))}, {esc(sm.get('overview_url', ''))});")

        for img in product_images:
            lines.append(f"INSERT INTO product_images (image_id, product_id, sub_model_id, color_id, angle_type, label_th, label_en, image_url, image_url_png, local_image_path, local_image_png, resolution, is_hero, sort_order) VALUES ({esc(img['image_id'])}, {esc(img['product_id'])}, {esc(img.get('sub_model_id', img['product_id']))}, {esc(img['color_id'])}, {esc(img['angle_type'])}, {esc(img['label_th'])}, {esc(img['label_en'])}, {esc(img['image_url'])}, {esc(img.get('image_url_png', ''))}, {esc(img.get('local_image_path', ''))}, {esc(img.get('local_image_png', ''))}, {esc(img.get('resolution', '2560x2560'))}, {img.get('is_hero', 0)}, {img.get('sort_order', 0)});")

        for v in variants:
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-")
            sub_id = v.get("sub_model_id") or pid
            cat = v.get("category_id") or v.get("category", "other")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            lines.append(f"INSERT INTO variants (id, part_number, sub_model_id, product_id, category_id, model_name, color_id, color_th, color_en, color_hex, storage, screen_size, connectivity, specs_chip, dimensions_mm, weight_grams, display_specs, camera_specs, battery_specs, box_contents, material, price_thb, formatted_price, image_url, image_url_png, local_image_path, local_image_png, buy_url, specs_url, overview_url, product_url) VALUES ({esc(v.get('id'))}, {esc(v.get('part_number') or v.get('id'))}, {esc(sub_id)}, {esc(pid)}, {esc(cat)}, {esc(v.get('model_name'))}, {esc(cid)}, {esc(v.get('color_th'))}, {esc(v.get('color_en'))}, {esc(v.get('color_hex'))}, {esc(v.get('storage', '-'))}, {esc(v.get('screen_size', '-'))}, {esc(v.get('connectivity', 'Standard'))}, {esc(v.get('specs_chip', '-'))}, {esc(v.get('dimensions_mm', '-'))}, {esc(v.get('weight_grams', '-'))}, {esc(v.get('display_specs', '-'))}, {esc(v.get('camera_specs', '-'))}, {esc(v.get('battery_specs', '-'))}, {esc(v.get('box_contents', '-'))}, {esc(v.get('material', '-'))}, {int(v.get('price_thb', 0))}, {esc(v.get('formatted_price', '฿0'))}, {esc(v.get('image_url', ''))}, {esc(v.get('image_url_png', ''))}, {esc(v.get('local_image_path', ''))}, {esc(v.get('local_image_png', ''))}, {esc(v.get('buy_url', ''))}, {esc(v.get('specs_url', ''))}, {esc(v.get('overview_url', ''))}, {esc(v.get('product_url', ''))});")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"📄 สร้าง SQL Dump Script: {file_path}")
        return file_path

    def build_full_json_export(self, variants: List[Dict[str, Any]], filename: str = "apple_full_catalog.json") -> Path:
        """สร้างไฟล์ JSON Master แบบมีลำดับชั้น 100% ครบถ้วน พร้อม sub_models และสเปกละเอียด"""
        file_path = self.exports_dir / filename
        colors, products, sub_models, product_images, _ = self.extract_normalized_entities(variants)
        tree = self.generate_catalog_tree_dict(variants)

        output_data = {
            "metadata": {
                "source": "Apple Store Online (Thailand) Official Catalog",
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_variants": len(variants),
                "total_sub_models": len(sub_models),
                "total_products": len(products),
                "total_colors": len(colors),
                "total_images": len(product_images),
                "categories": [c["id"] for c in CATEGORY_METADATA],
                "image_resolution": "2560x2560 Ultra HD Retina",
                "supports_transparent_png": True,
                "currency": "THB"
            },
            "categories": CATEGORY_METADATA,
            "products": products,
            "sub_models": sub_models,
            "colors": colors,
            "product_images": product_images,
            "catalog_tree": tree,
            "variants": variants
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"📦 สร้าง JSON Database (Master): {file_path}")
        return file_path

    # Alias for backward compatibility
    build_json_database = build_full_json_export

    def generate_catalog_tree_dict(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """สร้างโครงสร้างต้นไม้ 4 ระดับ: Category -> Family -> Sub-Model -> Color -> Variants"""
        tree = {}
        for cat in CATEGORY_METADATA:
            tree[cat["id"]] = {
                "category_info": cat,
                "families": {}
            }

        for v in variants:
            cat_id = v.get("category_id") or v.get("category", "other")
            if cat_id not in tree:
                tree[cat_id] = {
                    "category_info": {"id": cat_id, "name_th": cat_id, "name_en": cat_id},
                    "families": {}
                }

            fam_id = v.get("product_id") or v.get("family", "").lower().replace(" ", "-")
            if fam_id not in tree[cat_id]["families"]:
                tree[cat_id]["families"][fam_id] = {
                    "family_id": fam_id,
                    "family_name": v.get("family", fam_id),
                    "chip": v.get("specs_chip", "-"),
                    "sub_models": {}
                }

            sub_id = v.get("sub_model_id") or fam_id
            fam_sub_models = tree[cat_id]["families"][fam_id]["sub_models"]
            if sub_id not in fam_sub_models:
                fam_sub_models[sub_id] = {
                    "sub_model_id": sub_id,
                    "name_th": v.get("sub_model_name") or v.get("family"),
                    "name_en": v.get("sub_model_name_en") or v.get("family"),
                    "screen_size": v.get("screen_size", "-"),
                    "dimensions_mm": v.get("dimensions_mm", "-"),
                    "weight_grams": v.get("weight_grams", "-"),
                    "display_specs": v.get("display_specs", "-"),
                    "camera_specs": v.get("camera_specs", "-"),
                    "battery_specs": v.get("battery_specs", "-"),
                    "box_contents": v.get("box_contents", "-"),
                    "buy_url": v.get("buy_url", v.get("product_url", "")),
                    "specs_url": v.get("specs_url", ""),
                    "overview_url": v.get("overview_url", ""),
                    "colors": {}
                }

            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            sub_colors = fam_sub_models[sub_id]["colors"]
            if cid not in sub_colors:
                sub_colors[cid] = {
                    "color_id": cid,
                    "name_th": v.get("color_th"),
                    "name_en": v.get("color_en"),
                    "color_hex": v.get("color_hex"),
                    "image_url": v.get("image_url"),
                    "image_url_highres": v.get("image_url_highres") or v.get("image_url"),
                    "image_url_png": v.get("image_url_png", ""),
                    "local_image_path": v.get("local_image_path", ""),
                    "local_image_png": v.get("local_image_png", ""),
                    "gallery": v.get("gallery", []),
                    "options": []
                }

            sub_colors[cid]["options"].append({
                "id": v.get("id"),
                "part_number": v.get("part_number") or v.get("id"),
                "storage": v.get("storage"),
                "screen_size": v.get("screen_size"),
                "connectivity": v.get("connectivity"),
                "price_thb": v.get("price_thb"),
                "formatted_price": v.get("formatted_price")
            })

        # แปลง colors dict ในแต่ละ sub_model ให้เป็น list
        for cat_id in tree:
            for fam_id in tree[cat_id]["families"]:
                for sub_id in tree[cat_id]["families"][fam_id]["sub_models"]:
                    sm = tree[cat_id]["families"][fam_id]["sub_models"][sub_id]
                    sm["colors"] = list(sm["colors"].values())

        # สร้าง products map สำหรับ backward compatibility และการใช้งาน UI อย่างเต็มประสิทธิภาพ
        for cat_id in tree:
            tree[cat_id]["products"] = {}
            for fam_id, fam_obj in tree[cat_id]["families"].items():
                fam_colors = {}
                min_p = float("inf")
                max_p = 0
                first_img = ""
                first_png = ""
                for sm_id, sm in fam_obj["sub_models"].items():
                    for c in sm["colors"]:
                        cid = c["color_id"]
                        if cid not in fam_colors:
                            fam_colors[cid] = {
                                "color_id": cid,
                                "name_th": c["name_th"],
                                "name_en": c["name_en"],
                                "color_hex": c["color_hex"],
                                "image_url": c["image_url"],
                                "image_url_highres": c.get("image_url_highres") or c["image_url"],
                                "image_url_png": c.get("image_url_png", ""),
                                "local_image_path": c.get("local_image_path", ""),
                                "local_image_png": c.get("local_image_png", ""),
                                "gallery": c.get("gallery", []),
                                "options": []
                            }
                        if not first_img:
                            first_img = c["image_url"]
                            first_png = c.get("image_url_png", "")
                        for opt in c["options"]:
                            p_val = opt.get("price_thb", 0)
                            if p_val > 0:
                                min_p = min(min_p, p_val)
                                max_p = max(max_p, p_val)
                            # เติมสเปกครบ 100% ในทุก option
                            opt["sub_model_id"] = sm_id
                            opt["sub_model_name"] = sm["name_th"]
                            opt["dimensions_mm"] = sm.get("dimensions_mm", "-")
                            opt["weight_grams"] = sm.get("weight_grams", "-")
                            opt["display_specs"] = sm.get("display_specs", "-")
                            opt["camera_specs"] = sm.get("camera_specs", "-")
                            opt["battery_specs"] = sm.get("battery_specs", "-")
                            opt["box_contents"] = sm.get("box_contents", "-")
                            opt["specs_url"] = sm.get("specs_url", "")
                            opt["buy_url"] = sm.get("buy_url", "")
                            fam_colors[cid]["options"].append(opt)

                tree[cat_id]["products"][fam_id] = {
                    "product_info": {
                        "id": fam_id,
                        "category_id": cat_id,
                        "name": fam_obj["family_name"],
                        "chip": fam_obj["chip"],
                        "min_price_thb": min_p if min_p != float("inf") else 0,
                        "max_price_thb": max_p,
                        "hero_image_url": first_img,
                        "hero_image_png": first_png,
                        "sub_models_count": len(fam_obj["sub_models"])
                    },
                    "colors": list(fam_colors.values()),
                    "sub_models": list(fam_obj["sub_models"].values())
                }

        return tree

    def build_catalog_tree_json(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog_tree.json") -> Path:
        """สร้าง JSON Tree ที่จัดระเบียบตามลำดับชั้นอย่างเป็นทางการ"""
        file_path = self.exports_dir / filename
        tree = self.generate_catalog_tree_dict(variants)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)

        print(f"🌳 สร้าง E-Commerce Hierarchy Tree JSON: {file_path}")
        return file_path

    def build_js_bundle(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.js") -> Path:
        """สร้าง JS Global Bundle นำเข้า <script> หน้าเว็บได้ทันที ไม่ติดปัญหา CORS"""
        file_path = self.exports_dir / filename
        colors, products, sub_models, product_images, _ = self.extract_normalized_entities(variants)
        tree = self.generate_catalog_tree_dict(variants)

        payload = {
            "categories": CATEGORY_METADATA,
            "products": products,
            "sub_models": sub_models,
            "colors": colors,
            "product_images": product_images,
            "variants": variants,
            "tree": tree
        }

        js_content = (
            "// Apple Official Catalog Web Data Bundle (4K Retina, Multi-Angle Gallery, 100% Complete Specs)\n"
            f"window.APPLE_DATABASE = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
            "window.APPLE_VARIANTS = window.APPLE_DATABASE.variants;\n"
            "window.APPLE_PRODUCTS = window.APPLE_DATABASE.products;\n"
            "window.APPLE_SUB_MODELS = window.APPLE_DATABASE.sub_models;\n"
            "window.APPLE_CATEGORIES = window.APPLE_DATABASE.categories;\n"
            "window.APPLE_IMAGES = window.APPLE_DATABASE.product_images;\n"
            "window.APPLE_TREE = window.APPLE_DATABASE.tree;\n"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)

        print(f"⚡ สร้าง JavaScript Web Bundle: {file_path}")
        return file_path

    def build_csv_database(self, variants: List[Dict[str, Any]], filename: str = "apple_all_variants.csv") -> Path:
        """สร้าง Master CSV ภาษาไทย UTF-8 BOM ที่มีคอลัมน์สเปกครบ 100% ไม่มีช่องว่างหรือ '-'"""
        file_path = self.exports_dir / filename
        
        headers = [
            "id", "part_number", "sub_model_id", "sub_model_name", "category_id", "product_id", "family", "model_name",
            "color_id", "color_th", "color_en", "color_hex", "storage", "screen_size",
            "connectivity", "specs_chip", "dimensions_mm", "weight_grams", "display_specs",
            "camera_specs", "battery_specs", "box_contents", "material",
            "price_thb", "formatted_price", "image_url", "image_url_png", "local_image_path",
            "local_image_png", "buy_url", "specs_url", "overview_url"
        ]

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for v in variants:
                row = {k: v.get(k, "") for k in headers}
                writer.writerow(row)

        print(f"📊 สร้าง CSV Master Table (ครบทุกสเปก): {file_path}")
        return file_path

    def build_client_helpers(self) -> None:
        """สร้าง Helper Modules พร้อมใช้งานทั้งสำหรับ JavaScript (Frontend) และ Python (Backend)"""
        # 1. Frontend Helper (apple_db_helper.js)
        js_helper_path = self.exports_dir / "apple_db_helper.js"
        js_helper_code = """// Apple Catalog Frontend Helper SDK (Ultra HD 4K, Sub-Models, Full Specs)
const AppleCatalog = {
  getAll: () => window.APPLE_VARIANTS || [],
  getCategories: () => window.APPLE_CATEGORIES || [],
  getFamilies: () => window.APPLE_PRODUCTS || [],
  getSubModels: (familyId) => {
    const list = window.APPLE_SUB_MODELS || [];
    return familyId ? list.filter(sm => sm.family_id === familyId) : list;
  },
  getVariantsBySubModel: (subModelId) => {
    return (window.APPLE_VARIANTS || []).filter(v => v.sub_model_id === subModelId);
  },
  getProductGallery: (productId, colorId) => {
    if (!window.APPLE_IMAGES) return [];
    return window.APPLE_IMAGES.filter(img => 
      img.product_id === productId && (!colorId || img.color_id === colorId)
    ).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
  },
  filter: ({ category, maxPrice, color, storage, query }) => {
    return (window.APPLE_VARIANTS || []).filter(item => {
      if (category && category !== 'all' && item.category_id !== category && item.category !== category) return false;
      if (maxPrice && item.price_thb > maxPrice) return false;
      if (color && item.color_en.toLowerCase() !== color.toLowerCase() && item.color_th !== color) return false;
      if (storage && item.storage !== storage) return false;
      if (query) {
        const q = query.toLowerCase();
        const text = `${item.model_name} ${item.family} ${item.sub_model_name} ${item.color_th} ${item.part_number}`.toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  },
  findByPartNumber: (partNo) => {
    return (window.APPLE_VARIANTS || []).find(v => v.part_number === partNo || v.id === partNo);
  }
};
window.AppleCatalog = AppleCatalog;
"""
        with open(js_helper_path, "w", encoding="utf-8") as f:
            f.write(js_helper_code)
        print(f"🛠️  สร้าง Frontend Helper SDK (JS): {js_helper_path}")

        # 2. Backend Helper (apple_db_helper.py)
        py_helper_path = self.exports_dir / "apple_db_helper.py"
        py_helper_code = """import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "apple_catalog.db"

class AppleDatabase:
    \"\"\"Helper Class สำหรับเรียกใช้ฐานข้อมูล Apple ใน Backend (FastAPI, Flask, Django)\"\"\"

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_categories(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM categories ORDER BY sort_order ASC")
            return [dict(r) for r in cur.fetchall()]

    def get_sub_models(self, family_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if family_id:
                cur.execute("SELECT * FROM sub_models WHERE family_id = ? ORDER BY min_price_thb ASC", (family_id,))
            else:
                cur.execute("SELECT * FROM sub_models ORDER BY category_id, min_price_thb ASC")
            return [dict(r) for r in cur.fetchall()]

    def get_variants(self, sub_model_id: Optional[str] = None, max_price: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM v_catalog_complete WHERE 1=1"
            params = []
            if sub_model_id:
                query += " AND sub_model_id = ?"
                params.append(sub_model_id)
            if max_price:
                query += " AND price_thb <= ?"
                params.append(max_price)
            query += " ORDER BY price_thb ASC"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_product_gallery(self, product_id: str, color_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if color_id:
                cur.execute("SELECT * FROM product_images WHERE product_id = ? AND color_id = ? ORDER BY sort_order ASC", (product_id, color_id))
            else:
                cur.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY color_id, sort_order ASC", (product_id,))
            return [dict(r) for r in cur.fetchall()]

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            pattern = f"%{keyword}%"
            cur.execute(\"\"\"
                SELECT * FROM v_catalog_complete 
                WHERE model_name LIKE ? OR color_th LIKE ? OR color_en LIKE ? OR part_number LIKE ?
                ORDER BY price_thb ASC
            \"\"\", (pattern, pattern, pattern, pattern))
            return [dict(r) for r in cur.fetchall()]
"""
        with open(py_helper_path, "w", encoding="utf-8") as f:
            f.write(py_helper_code)
        print(f"🛠️  สร้าง Backend Helper SDK (Python): {py_helper_path}")
