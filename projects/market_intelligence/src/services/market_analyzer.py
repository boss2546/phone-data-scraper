import json
import csv
import sys
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import PROJECTS_DIR, EXPORTS_DIR, REPORTS_DIR

class MarketIntelligenceAnalyzer:
    """ระบบรวบรวมและวิเคราะห์ราคาสินค้า เปรียบเทียบราคาทางการ (Apple) กับราคามือสอง (CompAsia / Facebook)"""

    @staticmethod
    def load_apple_catalog() -> List[Dict[str, Any]]:
        apple_json = PROJECTS_DIR / "apple_scraper" / "data" / "exports" / "apple_full_catalog.json"
        if not apple_json.exists():
            return []
        try:
            with open(apple_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("products", []) or data.get("variants", [])
                elif isinstance(data, list):
                    return data
                return []
        except Exception:
            return []

    @staticmethod
    def load_compasia_catalog() -> List[Dict[str, Any]]:
        comp_json = PROJECTS_DIR / "compasia_scraper" / "data" / "compasia" / "compasia_all_products.json"
        if not comp_json.exists():
            legacy = PROJECTS_DIR.parent / "_archive_legacy" / "data" / "compasia" / "compasia_all_products.json"
            if legacy.exists():
                comp_json = legacy
        if not comp_json.exists():
            return []
        try:
            with open(comp_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def analyze_price_disparity() -> Dict[str, Any]:
        apple_data = MarketIntelligenceAnalyzer.load_apple_catalog()
        comp_data = MarketIntelligenceAnalyzer.load_compasia_catalog()

        report_rows = []
        for a_item in apple_data:
            model_name = a_item.get("name") or a_item.get("product_name")
            official_price = a_item.get("min_price_thb") or a_item.get("price_thb") or a_item.get("starting_price_thb")
            if not official_price:
                continue

            # ค้นหารุ่นที่ตรงกันใน CompAsia
            matched_secondhand = []
            if model_name:
                for c_item in comp_data:
                    c_title = c_item.get("title", "")
                    if model_name.lower() in c_title.lower():
                        matched_secondhand.append(c_item)

            report_rows.append({
                "model": model_name,
                "official_price": official_price,
                "secondhand_matches": len(matched_secondhand),
                "deal_status": "มีตัวเลือกมือสองเปรียบเทียบ" if matched_secondhand else "ราคามาตรฐานทางการ"
            })

        # บันทึกรายงาน
        out_csv = EXPORTS_DIR / "market_price_overview.csv"
        if report_rows:
            with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["model", "official_price", "secondhand_matches", "deal_status"])
                writer.writeheader()
                writer.writerows(report_rows)

        return {
            "apple_models_analyzed": len(apple_data),
            "compasia_products_available": len(comp_data),
            "report_file": str(out_csv),
            "rows": report_rows
        }
