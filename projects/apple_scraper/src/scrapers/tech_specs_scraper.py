import urllib.request
import re
from typing import Dict, Any, List, Optional
from config.settings import DEFAULT_HEADERS, BASE_APPLE_URL, DEFAULT_LOCALE
from src.services.formatter import AppleDataFormatter

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class TechSpecsScraper:
    """Scraper สำหรับดึงตารางสเปกทางเทคนิคอย่างละเอียด (Tech Specs) จาก Apple.com"""

    def __init__(self, locale: str = DEFAULT_LOCALE, headers: Optional[Dict[str, str]] = None):
        self.locale = locale.strip("/")
        self.base_url = f"{BASE_APPLE_URL}/{self.locale}" if self.locale else BASE_APPLE_URL
        self.headers = headers or DEFAULT_HEADERS

    def fetch_specs_html(self, specs_url: str) -> Optional[str]:
        """ดาวน์โหลดหน้า Tech Specs"""
        target = specs_url.strip()
        if not target.startswith("http"):
            target = f"{self.base_url.rstrip('/')}/{target.lstrip('/')}"
        
        req = urllib.request.Request(target, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                return res.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"❌ [TechSpecsScraper] ไม่สามารถดาวน์โหลด {target}: {e}")
            return None

    def parse_tech_specs(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """แยกสกัดตารางสเปกทางเทคนิคตามหมวดหมู่หลัก"""
        title = ""
        capacities = []
        colors = []
        chip = "-"
        display = "-"
        camera = "-"
        battery = "-"
        dimensions = "-"
        raw_sections = {}

        # 1. Product Title
        title_m = re.search(r'<title>(.*?)</title>', html_content, re.I | re.S)
        if title_m:
            title = title_m.group(1).strip()
            title = re.sub(r'(\s*-\s*ข้อมูลทางเทคนิค|\s*-\s*Tech Specs|\s*-\s*Apple\s*\([^\)]+\))', '', title).strip()

        # 2. ดึงความจุ (Capacities / Storage)
        storage_match = re.findall(r'\b(64GB|128GB|256GB|512GB|1TB|2TB)\b', html_content, re.IGNORECASE)
        if storage_match:
            unique_storage = []
            for s in storage_match:
                su = s.upper()
                if su not in unique_storage:
                    unique_storage.append(su)
            capacities = unique_storage

        # 3. ดึงชิปประมวลผล (Chip)
        chip_m = re.search(r'(?:ชิป|chip)\s*(A\d+\s*Pro|A\d+|M\d+\s*Pro|M\d+\s*Max|M\d+)', html_content, re.I)
        if chip_m:
            chip = f"ชิป {chip_m.group(1).strip()}"

        # 4. ดึงหน้าจอ (Display)
        disp_m = re.search(r'(จอภาพ\s*Super Retina XDR[^\.<>\n]{0,80}|Super Retina XDR display[^\.<>\n]{0,80})', html_content, re.I)
        if disp_m:
            display = AppleDataFormatter.clean_text(disp_m.group(1))

        # 5. ดึงกล้อง (Camera)
        cam_m = re.search(r'(ระบบกล้องโปร[^\.<>\n]{0,80}|กล้องหลัก\s*48MP[^\.<>\n]{0,80}|48MP Main[^\.<>\n]{0,80})', html_content, re.I)
        if cam_m:
            camera = AppleDataFormatter.clean_text(cam_m.group(1))

        # 6. ดึงแบตเตอรี่ (Battery)
        bat_m = re.search(r'(การเล่นวิดีโอสูงสุด\s*\d+\s*ชั่วโมง|Up to \d+ hours video playback)', html_content, re.I)
        if bat_m:
            battery = AppleDataFormatter.clean_text(bat_m.group(1))

        # 7. สกัดสี (Colors / Finishes)
        color_candidates = ["ไทเทเนียมทะเลทราย", "ไทเทเนียมธรรมชาติ", "ไทเทเนียมขาว", "ไทเทเนียมดำ", "ดำ", "ขาว", "ทอง", "เงิน", "ฟ้า", "ชมพู", "เขียว", "สเปซแบล็ค", "สตาร์ไลท์", "มิดไนท์"]
        for c in color_candidates:
            if c in html_content and c not in colors:
                colors.append(c)

        # หากมี BeautifulSoup ให้สกัดลึกเพิ่ม
        if HAS_BS4:
            soup = BeautifulSoup(html_content, "html.parser")
            section_headers = soup.find_all(['h2', 'h3', 'th'], class_=re.compile(r'header|title|label', re.I))
            for h in section_headers:
                header_text = AppleDataFormatter.clean_text(h.text)
                if not header_text or len(header_text) > 40:
                    continue
                parent_container = h.find_parent(['div', 'section', 'tr'])
                if parent_container:
                    content_text = AppleDataFormatter.clean_text(parent_container.text)
                    content_text = content_text.replace(header_text, '').strip()
                    if content_text and len(content_text) > 10:
                        raw_sections[header_text] = content_text

        return {
            "status": "success",
            "title": title,
            "url": source_url,
            "capacities": capacities,
            "colors": colors[:8],
            "specs": {
                "chip": chip,
                "display": display,
                "camera": camera,
                "battery": battery,
                "dimensions": dimensions,
                "storage_options": ", ".join(capacities) if capacities else "-"
            },
            "detailed_sections": raw_sections
        }

    def scrape_specs(self, specs_url: str) -> Dict[str, Any]:
        """เรียกทำงานดึงสเปกสินค้าจากหน้า /specs/"""
        html = self.fetch_specs_html(specs_url)
        if not html:
            return {
                "status": "error",
                "message": f"ไม่สามารถเปิดอ่านข้อมูล Tech Specs จาก {specs_url}",
                "url": specs_url
            }
        return self.parse_tech_specs(html, specs_url)
