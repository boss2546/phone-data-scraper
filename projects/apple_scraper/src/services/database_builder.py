import json
import csv
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any
from config.settings import EXPORTS_DIR

CATEGORY_METADATA = [
    {"id": "iphone", "name_th": "iPhone", "name_en": "iPhone", "icon": "📱", "sort_order": 1},
    {"id": "ipad", "name_th": "iPad", "name_en": "iPad", "icon": "📱", "sort_order": 2},
    {"id": "mac", "name_th": "Mac", "name_en": "Mac", "icon": "💻", "sort_order": 3},
    {"id": "watch", "name_th": "Apple Watch", "name_en": "Apple Watch", "icon": "⌚", "sort_order": 4}
]

class AppleDatabaseBuilder:
    """ตัวสร้างฐานข้อมูลสินค้า Apple เชิงสัมพันธ์ (Relational) และโครงสร้าง JSON/CSV/SQL/JS ที่พร้อมใช้งานทันที"""

    def __init__(self, exports_dir: Path = EXPORTS_DIR):
        self.exports_dir = exports_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def extract_normalized_entities(self, variants: List[Dict[str, Any]]):
        """แยก Entity ให้เป็นไปตามมาตรฐานฐานข้อมูล Relational (Categories, Products, Colors, Variants)"""
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

        # 2. Products (Families)
        products_map = {}
        for v in variants:
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cat = v.get("category", "other")
            fam = v.get("family", "Unknown")
            price = v.get("price_thb", 0)

            if pid not in products_map:
                products_map[pid] = {
                    "id": pid,
                    "category_id": cat,
                    "name": fam,
                    "chip": v.get("specs_chip", "-"),
                    "screen_size": v.get("screen_size", "-"),
                    "min_price_thb": price,
                    "max_price_thb": price,
                    "hero_image_url": v.get("image_url", ""),
                    "product_url": v.get("product_url", "")
                }
            else:
                p = products_map[pid]
                if price > 0:
                    p["min_price_thb"] = min(p["min_price_thb"], price)
                    p["max_price_thb"] = max(p["max_price_thb"], price)

        return list(colors_map.values()), list(products_map.values())

    def build_sqlite_database(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.db") -> Path:
        """สร้างฐานข้อมูล SQLite เชิงสัมพันธ์แบบ Normalized (4 Tables + 2 Views + Indexes)"""
        file_path = self.exports_dir / filename
        if file_path.exists():
            file_path.unlink()

        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        # 1. ตาราง Categories
        cursor.execute("""
        CREATE TABLE categories (
            id TEXT PRIMARY KEY,
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            icon TEXT,
            sort_order INTEGER DEFAULT 0
        );
        """)

        # 2. ตาราง Products
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
            product_url TEXT
        );
        """)

        # 3. ตาราง Colors
        cursor.execute("""
        CREATE TABLE colors (
            id TEXT PRIMARY KEY,
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            color_hex TEXT NOT NULL
        );
        """)

        # 4. ตาราง Variants
        cursor.execute("""
        CREATE TABLE variants (
            id TEXT PRIMARY KEY,
            part_number TEXT NOT NULL,
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
            price_thb INTEGER NOT NULL,
            formatted_price TEXT NOT NULL,
            image_url TEXT,
            product_url TEXT
        );
        """)

        # สร้าง Indexes เพื่อการค้นหาประสิทธิภาพสูง
        cursor.execute("CREATE INDEX idx_var_category ON variants(category_id);")
        cursor.execute("CREATE INDEX idx_var_product ON variants(product_id);")
        cursor.execute("CREATE INDEX idx_var_price ON variants(price_thb);")
        cursor.execute("CREATE INDEX idx_var_color ON variants(color_id);")
        cursor.execute("CREATE INDEX idx_var_storage ON variants(storage);")

        # 5. สร้าง Views สำหรับ Query ได้ง่ายในคำสั่งเดียว
        cursor.execute("""
        CREATE VIEW v_catalog AS
        SELECT 
            v.id AS variant_id,
            v.part_number,
            c.id AS category_id,
            c.name_th AS category_name,
            p.id AS product_id,
            p.name AS product_name,
            v.model_name,
            v.color_th,
            v.color_en,
            v.color_hex,
            v.storage,
            v.screen_size,
            v.connectivity,
            v.specs_chip,
            v.price_thb,
            v.formatted_price,
            v.image_url,
            v.product_url
        FROM variants v
        LEFT JOIN products p ON v.product_id = p.id
        LEFT JOIN categories c ON v.category_id = c.id;
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
            COUNT(v.id) AS total_variants,
            GROUP_CONCAT(DISTINCT v.color_th) AS colors_available,
            GROUP_CONCAT(DISTINCT v.storage) AS storages_available,
            p.hero_image_url
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN variants v ON v.product_id = p.id
        GROUP BY p.id;
        """)

        # บันทึกข้อมูล
        cursor.executemany(
            "INSERT INTO categories (id, name_th, name_en, icon, sort_order) VALUES (?, ?, ?, ?, ?)",
            [(c["id"], c["name_th"], c["name_en"], c["icon"], c["sort_order"]) for c in CATEGORY_METADATA]
        )

        colors, products = self.extract_normalized_entities(variants)

        cursor.executemany(
            "INSERT INTO colors (id, name_th, name_en, color_hex) VALUES (?, ?, ?, ?)",
            [(c["id"], c["name_th"], c["name_en"], c["color_hex"]) for c in colors]
        )

        cursor.executemany(
            """INSERT INTO products (id, category_id, name, chip, screen_size, min_price_thb, max_price_thb, hero_image_url, product_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(p["id"], p["category_id"], p["name"], p["chip"], p["screen_size"], p["min_price_thb"], p["max_price_thb"], p["hero_image_url"], p["product_url"]) for p in products]
        )

        var_rows = [
            (
                v.get("id"),
                v.get("part_number") or v.get("id"),
                v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", ""),
                v.get("category", "other"),
                v.get("model_name"),
                v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-"),
                v.get("color_th"),
                v.get("color_en"),
                v.get("color_hex"),
                v.get("storage", "-"),
                v.get("screen_size", "-"),
                v.get("connectivity", "Standard"),
                v.get("specs_chip", "-"),
                int(v.get("price_thb", 0)),
                v.get("formatted_price", "฿0"),
                v.get("image_url", ""),
                v.get("product_url", "")
            )
            for v in variants
        ]

        cursor.executemany(
            """INSERT INTO variants (
                id, part_number, product_id, category_id, model_name,
                color_id, color_th, color_en, color_hex, storage,
                screen_size, connectivity, specs_chip, price_thb,
                formatted_price, image_url, product_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            var_rows
        )

        conn.commit()
        conn.close()

        print(f"🗄️ สร้าง SQLite Database (Normalized + Views): {file_path} ({len(variants)} variants)")
        return file_path

    def build_sql_dump(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.sql") -> Path:
        """สร้างไฟล์ SQL Dump มาตรฐาน (DDL + INSERT) พร้อมนำเข้า MySQL, PostgreSQL, Supabase หรือ SQLite ได้ทันที"""
        file_path = self.exports_dir / filename
        colors, products = self.extract_normalized_entities(variants)

        def esc(val: Any) -> str:
            if val is None:
                return "NULL"
            s = str(val).replace("'", "''")
            return f"'{s}'"

        lines = [
            "-- Apple Store Thailand Official Catalog SQL Dump",
            f"-- Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Total variants: {len(variants)}",
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
            "-- 2. Products Table",
            "CREATE TABLE IF NOT EXISTS products (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    category_id VARCHAR(32) NOT NULL,",
            "    name VARCHAR(128) NOT NULL,",
            "    chip VARCHAR(64),",
            "    screen_size VARCHAR(64),",
            "    min_price_thb INT,",
            "    max_price_thb INT,",
            "    hero_image_url TEXT,",
            "    product_url TEXT",
            ");",
            "",
            "-- 3. Colors Table",
            "CREATE TABLE IF NOT EXISTS colors (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    name_th VARCHAR(64) NOT NULL,",
            "    name_en VARCHAR(64) NOT NULL,",
            "    color_hex VARCHAR(16) NOT NULL",
            ");",
            "",
            "-- 4. Variants Table",
            "CREATE TABLE IF NOT EXISTS variants (",
            "    id VARCHAR(64) PRIMARY KEY,",
            "    part_number VARCHAR(64) NOT NULL,",
            "    product_id VARCHAR(64) NOT NULL,",
            "    category_id VARCHAR(32) NOT NULL,",
            "    model_name TEXT NOT NULL,",
            "    color_id VARCHAR(64),",
            "    color_th VARCHAR(64),",
            "    color_en VARCHAR(64),",
            "    color_hex VARCHAR(16),",
            "    storage VARCHAR(32),",
            "    screen_size VARCHAR(32),",
            "    connectivity VARCHAR(32),",
            "    specs_chip VARCHAR(64),",
            "    price_thb INT NOT NULL,",
            "    formatted_price VARCHAR(32) NOT NULL,",
            "    image_url TEXT,",
            "    product_url TEXT",
            ");",
            "",
            "-- Insert Categories"
        ]

        for c in CATEGORY_METADATA:
            lines.append(f"INSERT INTO categories VALUES ({esc(c['id'])}, {esc(c['name_th'])}, {esc(c['name_en'])}, {esc(c['icon'])}, {c['sort_order']});")

        lines.append("\n-- Insert Colors")
        for c in colors:
            lines.append(f"INSERT INTO colors VALUES ({esc(c['id'])}, {esc(c['name_th'])}, {esc(c['name_en'])}, {esc(c['color_hex'])});")

        lines.append("\n-- Insert Products")
        for p in products:
            lines.append(f"INSERT INTO products VALUES ({esc(p['id'])}, {esc(p['category_id'])}, {esc(p['name'])}, {esc(p['chip'])}, {esc(p['screen_size'])}, {p['min_price_thb']}, {p['max_price_thb']}, {esc(p['hero_image_url'])}, {esc(p['product_url'])});")

        lines.append("\n-- Insert Variants")
        for v in variants:
            pid = v.get("product_id") or v.get("family", "").lower().replace(" ", "-").replace("(", "").replace(")", "")
            cid = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
            lines.append(
                f"INSERT INTO variants VALUES ({esc(v['id'])}, {esc(v.get('part_number', v['id']))}, {esc(pid)}, {esc(v.get('category'))}, "
                f"{esc(v['model_name'])}, {esc(cid)}, {esc(v['color_th'])}, {esc(v['color_en'])}, {esc(v['color_hex'])}, {esc(v.get('storage', '-'))}, "
                f"{esc(v.get('screen_size', '-'))}, {esc(v.get('connectivity', 'Standard'))}, {esc(v.get('specs_chip', '-'))}, {int(v['price_thb'])}, "
                f"{esc(v['formatted_price'])}, {esc(v.get('image_url'))}, {esc(v.get('product_url'))});"
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"📜 สร้าง SQL Dump File: {file_path}")
        return file_path

    def build_json_database(self, variants: List[Dict[str, Any]], filename: str = "apple_full_catalog.json") -> Path:
        """สร้างฐานข้อมูล JSON เต็มรูปแบบพร้อม normalized tables และ hierarchical tree"""
        file_path = self.exports_dir / filename
        colors, products = self.extract_normalized_entities(variants)

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
                    "screen_size": v.get("screen_size", "-"),
                    "min_price": v["price_thb"],
                    "max_price": v["price_thb"],
                    "colors": [],
                    "variants": []
                }

            fam_obj = catalog_tree[cat]["families"][fam]
            fam_obj["min_price"] = min(fam_obj["min_price"], v["price_thb"])
            fam_obj["max_price"] = max(fam_obj["max_price"], v["price_thb"])
            
            c_info = {"color_id": v.get("color_id"), "th": v.get("color_th"), "en": v.get("color_en"), "hex": v.get("color_hex")}
            if c_info not in fam_obj["colors"]:
                fam_obj["colors"].append(c_info)

            fam_obj["variants"].append(v)
            catalog_tree[cat]["total_items"] += 1

        output_data = {
            "metadata": {
                "version": "2.0.0",
                "generated_at": int(time.time()),
                "total_variants": len(variants),
                "total_products": len(products),
                "total_colors": len(colors),
                "categories": [c["id"] for c in CATEGORY_METADATA],
                "currency": "THB"
            },
            "categories": CATEGORY_METADATA,
            "products": products,
            "colors": colors,
            "catalog_tree": catalog_tree,
            "variants": variants
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"📦 สร้าง JSON Database (Master): {file_path}")
        return file_path

    def build_catalog_tree_json(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog_tree.json") -> Path:
        """สร้าง JSON ลำดับชั้นสำหรับทำ UI Product Selector / Configurator"""
        file_path = self.exports_dir / filename
        colors, products = self.extract_normalized_entities(variants)
        
        tree = {}
        for c in CATEGORY_METADATA:
            tree[c["id"]] = {
                "info": c,
                "products": {}
            }

        for p in products:
            cat_id = p["category_id"]
            if cat_id in tree:
                p_variants = [v for v in variants if (v.get("product_id") == p["id"] or v.get("family") == p["name"])]
                
                # จัดกลุ่ม colors
                color_groups = {}
                for v in p_variants:
                    c_id = v.get("color_id") or v.get("color_en", "").lower().replace(" ", "-")
                    if c_id not in color_groups:
                        color_groups[c_id] = {
                            "color_id": c_id,
                            "name_th": v.get("color_th"),
                            "name_en": v.get("color_en"),
                            "color_hex": v.get("color_hex"),
                            "image_url": v.get("image_url"),
                            "options": []
                        }
                    color_groups[c_id]["options"].append({
                        "id": v.get("id"),
                        "storage": v.get("storage"),
                        "screen_size": v.get("screen_size"),
                        "connectivity": v.get("connectivity"),
                        "price_thb": v.get("price_thb"),
                        "formatted_price": v.get("formatted_price")
                    })

                tree[cat_id]["products"][p["id"]] = {
                    "product_info": p,
                    "colors": list(color_groups.values())
                }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)

        print(f"🌳 สร้าง E-Commerce Selector Tree JSON: {file_path}")
        return file_path

    def build_js_bundle(self, variants: List[Dict[str, Any]], filename: str = "apple_catalog.js") -> Path:
        """สร้าง JS Global Bundle นำเข้า <script> หน้าเว็บได้ทันที ไม่ติดปัญหา CORS"""
        file_path = self.exports_dir / filename
        colors, products = self.extract_normalized_entities(variants)

        payload = {
            "categories": CATEGORY_METADATA,
            "products": products,
            "colors": colors,
            "variants": variants
        }

        js_content = (
            "// Apple Official Catalog Web Data Bundle\n"
            f"window.APPLE_DATABASE = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
            "window.APPLE_VARIANTS = window.APPLE_DATABASE.variants;\n"
            "window.APPLE_PRODUCTS = window.APPLE_DATABASE.products;\n"
            "window.APPLE_CATEGORIES = window.APPLE_DATABASE.categories;\n"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)

        print(f"⚡ สร้าง JavaScript Web Bundle: {file_path}")
        return file_path

    def build_csv_database(self, variants: List[Dict[str, Any]], filename: str = "apple_all_variants.csv") -> Path:
        """สร้าง Master CSV ภาษาไทย UTF-8 BOM รองรับ Excel และ Google Sheets"""
        file_path = self.exports_dir / filename
        
        headers = [
            "id", "part_number", "product_id", "category", "family", "model_name",
            "color_id", "color_th", "color_en", "color_hex", "storage", "screen_size",
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

    def build_client_helpers(self) -> None:
        """สร้าง Helper Modules พร้อมใช้งานทั้งสำหรับ JavaScript (Frontend) และ Python (Backend)"""
        # 1. Frontend Helper (apple_db_helper.js)
        js_helper_path = self.exports_dir / "apple_db_helper.js"
        js_helper_code = """// Apple Catalog Frontend Helper SDK
// วิธีใช้: นำเข้า apple_catalog.js แล้วตามด้วยไฟล์นี้
const AppleCatalog = {
  // ดึงสินค้าทั้งหมด
  getAll: () => window.APPLE_VARIANTS || [],

  // ดึงหมวดหมู่ทั้งหมด
  getCategories: () => window.APPLE_CATEGORIES || [],

  // ดึงตระกูลสินค้าตามหมวดหมู่ ('iphone', 'ipad', 'mac', 'watch')
  getProductsByCategory: (catId) => {
    return (window.APPLE_PRODUCTS || []).filter(p => p.category_id === catId);
  },

  // ดึงตัวเลือกสินค้าทั้งหมดของรุ่นนั้นๆ (เช่น 'iphone-16')
  getVariantsByProduct: (productId) => {
    return (window.APPLE_VARIANTS || []).filter(v => v.product_id === productId);
  },

  // กรองสินค้าตามเงื่อนไข (หมวดหมู่, งบประมาณสูงสุด, สี, ขนาดความจุ)
  filter: ({ category, maxPrice, color, storage, query }) => {
    return (window.APPLE_VARIANTS || []).filter(item => {
      if (category && category !== 'all' && item.category !== category) return false;
      if (maxPrice && item.price_thb > maxPrice) return false;
      if (color && item.color_en.toLowerCase() !== color.toLowerCase() && item.color_th !== color) return false;
      if (storage && item.storage !== storage) return false;
      if (query) {
        const q = query.toLowerCase();
        const text = `${item.model_name} ${item.family} ${item.color_th} ${item.color_en} ${item.part_number}`.toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  },

  // ค้นหาตาม Part Number หรือ SKU
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

    def get_products(self, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if category_id:
                cur.execute("SELECT * FROM products WHERE category_id = ? ORDER BY min_price_thb ASC", (category_id,))
            else:
                cur.execute("SELECT * FROM products ORDER BY category_id, min_price_thb ASC")
            return [dict(r) for r in cur.fetchall()]

    def get_variants(self, product_id: Optional[str] = None, max_price: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM v_catalog WHERE 1=1"
            params = []
            if product_id:
                query += " AND product_id = ?"
                params.append(product_id)
            if max_price:
                query += " AND price_thb <= ?"
                params.append(max_price)
            query += " ORDER BY price_thb ASC"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            pattern = f"%{keyword}%"
            cur.execute(\"\"\"
                SELECT * FROM v_catalog 
                WHERE model_name LIKE ? OR color_th LIKE ? OR color_en LIKE ? OR part_number LIKE ?
                ORDER BY price_thb ASC
            \"\"\", (pattern, pattern, pattern, pattern))
            return [dict(r) for r in cur.fetchall()]
"""
        with open(py_helper_path, "w", encoding="utf-8") as f:
            f.write(py_helper_code)
        print(f"🛠️  สร้าง Backend Helper SDK (Python): {py_helper_path}")
