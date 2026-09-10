import re
from typing import Dict, Any, Optional

class AppleDataFormatter:
    """จัดระเบียบ คลีน และแปลงโครงสร้างข้อมูลสเปก/ราคาของ Apple"""

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """ล้าง whitespace, อักขระพิเศษ และตัวเลขอ้างอิงเชิงอรรถ (footnotes)"""
        if not text:
            return ""
        # ลบเลข footnote เช่น "จอภาพ Super Retina XDR1" -> "จอภาพ Super Retina XDR"
        cleaned = re.sub(r'[\r\n\t]+', ' ', text)
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        return cleaned.strip()

    @staticmethod
    def parse_price(price_str: Optional[str]) -> Optional[int]:
        """แปลงข้อความราคา เช่น '฿43,900' หรือ '43,900 บาท' หรือ '$1,199' เป็น integer"""
        if not price_str:
            return None
        match = re.search(r'[\d,]+', str(price_str))
        if match:
            clean_digits = match.group(0).replace(',', '')
            if clean_digits.isdigit():
                return int(clean_digits)
        return None

    @staticmethod
    def extract_model_and_family(title_or_url: str) -> Dict[str, str]:
        """แยกตระกูลสินค้าและชื่อรุ่นจาก URL หรือ Title"""
        clean = title_or_url.lower()
        family = "other"
        if "iphone" in clean:
            family = "iphone"
        elif "ipad" in clean:
            family = "ipad"
        elif "mac" in clean or "macbook" in clean:
            family = "mac"
        elif "watch" in clean:
            family = "watch"
        elif "airpods" in clean:
            family = "audio"

        return {
            "family": family
        }
