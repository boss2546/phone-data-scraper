import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "apple_catalog.db"

class AppleDatabase:
    """Helper Class สำหรับเรียกใช้ฐานข้อมูล Apple ใน Backend (FastAPI, Flask, Django)"""

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
            cur.execute("""
                SELECT * FROM v_catalog_complete 
                WHERE model_name LIKE ? OR color_th LIKE ? OR color_en LIKE ? OR part_number LIKE ?
                ORDER BY price_thb ASC
            """, (pattern, pattern, pattern, pattern))
            return [dict(r) for r in cur.fetchall()]
