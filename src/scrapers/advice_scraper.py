import urllib.request
import re
import json
from typing import Dict, Any, Optional
from config.settings import DEFAULT_HEADERS

class AdviceScraper:
    """Scraper สำหรับดึงข้อมูลสินค้าจาก Advice.co.th"""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or DEFAULT_HEADERS

    def fetch_product(self, url: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลสินค้าจาก Advice URL
        """
        req = urllib.request.Request(url, headers=self.headers)
        
        try:
            with urllib.request.urlopen(req, timeout=12) as res:
                html = res.read().decode("utf-8")
        except Exception as e:
            return {
                "status": "error",
                "message": f"ไม่สามารถเปิด URL ได้: {str(e)}",
                "url": url
            }

        # 1. ดึง Schema.org JSON-LD
        schema_data = {}
        schema_match = re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        if schema_match:
            try:
                schema_data = json.loads(schema_match.group(1))
            except Exception:
                pass

        sku = schema_data.get("sku", "")

        # 2. ดึงรูปสินค้าภาพคมชัดสูง (High-Resolution Gallery)
        images = []
        if sku:
            img_pattern = rf'https?://img\.advice\.co\.th/cdn-cgi/image/format=auto,width=700,quality=82,fit=contain/images_nas/pic_product4/{sku}/[^\s"\'<>\\]+\.jpg'
            images = list(dict.fromkeys(re.findall(img_pattern, html)))
        
        if not images and "image" in schema_data:
            images = [schema_data["image"]]

        # 3. ดึงสเปกย่อ / Key Specs Summary
        key_specs = ""
        summary_spec_match = re.search(r'([A-Z0-9]+\s*/\s*\d+GB\s*/[^\n"<>]+)', html)
        if summary_spec_match:
            key_specs = summary_spec_match.group(1).strip()

        # 4. ดึงคำอธิบายสินค้า
        description = ""
        p_matches = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
        for p in p_matches:
            clean_p = re.sub(r'<[^>]+>', ' ', p).strip()
            if len(clean_p) > 50:
                description = clean_p
                break

        offers = schema_data.get("offers", {})
        brand_info = schema_data.get("brand", {})
        brand_name = brand_info.get("name") if isinstance(brand_info, dict) else brand_info

        return {
            "status": "success",
            "data": {
                "name": schema_data.get("name"),
                "sku": sku,
                "brand": brand_name,
                "price": offers.get("price"),
                "currency": offers.get("priceCurrency", "THB"),
                "in_stock": "InStock" in str(offers.get("availability", "")),
                "availability": offers.get("availability"),
                "key_specs": key_specs or None,
                "images": images,
                "description": description or schema_data.get("description"),
                "url": url
            }
        }
