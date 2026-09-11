import urllib.request
import urllib.parse
import re
import json
import time
from typing import Dict, Any, List, Optional
from config.settings import DEFAULT_HEADERS, BASE_APPLE_URL, DEFAULT_LOCALE
from src.services.formatter import AppleDataFormatter

# รายการหน้า Buy Page หลักของ Apple Store Thailand
TARGET_BUY_PAGES = [
    # iPhone
    ("iphone", "iPhone 16", "https://www.apple.com/th/shop/buy-iphone/iphone-16"),
    ("iphone", "iPhone 15", "https://www.apple.com/th/shop/buy-iphone/iphone-15"),
    ("iphone", "iPhone 14", "https://www.apple.com/th/shop/buy-iphone/iphone-14"),
    ("iphone", "iPhone SE", "https://www.apple.com/th/shop/buy-iphone/iphone-se"),
    ("iphone", "iPhone 18 Pro", "https://www.apple.com/th/shop/buy-iphone/iphone-18-pro"),
    ("iphone", "iPhone 17", "https://www.apple.com/th/shop/buy-iphone/iphone-17"),
    ("iphone", "iPhone 17e", "https://www.apple.com/th/shop/buy-iphone/iphone-17e"),
    ("iphone", "iPhone Air", "https://www.apple.com/th/shop/buy-iphone/iphone-air"),
    ("iphone", "iPhone Duo", "https://www.apple.com/th/shop/buy-iphone/iphone-duo"),

    # iPad
    ("ipad", "iPad Pro (M4)", "https://www.apple.com/th/shop/buy-ipad/ipad-pro"),
    ("ipad", "iPad Air (M2)", "https://www.apple.com/th/shop/buy-ipad/ipad-air"),
    ("ipad", "iPad (10th Gen)", "https://www.apple.com/th/shop/buy-ipad/ipad"),
    ("ipad", "iPad mini", "https://www.apple.com/th/shop/buy-ipad/ipad-mini"),

    # Mac
    ("mac", "MacBook Air", "https://www.apple.com/th/shop/buy-mac/macbook-air"),
    ("mac", "MacBook Pro", "https://www.apple.com/th/shop/buy-mac/macbook-pro"),
    ("mac", "iMac", "https://www.apple.com/th/shop/buy-mac/imac"),
    ("mac", "Mac mini", "https://www.apple.com/th/shop/buy-mac/mac-mini"),
    ("mac", "Mac Studio", "https://www.apple.com/th/shop/buy-mac/mac-studio"),

    # Watch
    ("watch", "Apple Watch Series 10", "https://www.apple.com/th/shop/buy-watch/apple-watch"),
    ("watch", "Apple Watch Ultra 2", "https://www.apple.com/th/shop/buy-watch/apple-watch-ultra"),
    ("watch", "Apple Watch SE", "https://www.apple.com/th/shop/buy-watch/apple-watch-se")
]

# พจนานุกรมแปลสีภาษาไทย <-> ภาษาอังกฤษ & รหัสสี Hex สำหรับนำไปแสดงผลบนหน้าเว็บ
COLOR_DICTIONARY = {
    "black": {"th": "ดำ", "en": "Black", "hex": "#1F2022"},
    "white": {"th": "ขาว", "en": "White", "hex": "#F9F6EF"},
    "pink": {"th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
    "teal": {"th": "ทีล", "en": "Teal", "hex": "#84A8A3"},
    "ultramarine": {"th": "อัลตร้ามารีน", "en": "Ultramarine", "hex": "#4D5E8C"},
    "natural titanium": {"th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
    "desert titanium": {"th": "ไทเทเนียมทะเลทราย", "en": "Desert Titanium", "hex": "#C5A992"},
    "white titanium": {"th": "ไทเทเนียมขาว", "en": "White Titanium", "hex": "#E2E4E1"},
    "black titanium": {"th": "ไทเทเนียมดำ", "en": "Black Titanium", "hex": "#3A393E"},
    "space black": {"th": "สเปซแบล็ค", "en": "Space Black", "hex": "#2E2C2F"},
    "space gray": {"th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
    "silver": {"th": "เงิน", "en": "Silver", "hex": "#E3E4E5"},
    "starlight": {"th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"},
    "midnight": {"th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
    "blue": {"th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
    "green": {"th": "เขียว", "en": "Green", "hex": "#43594B"},
    "purple": {"th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
    "yellow": {"th": "เหลือง", "en": "Yellow", "hex": "#FBE27D"},
    "orange": {"th": "ส้ม", "en": "Orange", "hex": "#E7643E"},
    "jet black": {"th": "ดำเจ็ทแบล็ค", "en": "Jet Black", "hex": "#0F0F10"},
    "rose gold": {"th": "โรสโกลด์", "en": "Rose Gold", "hex": "#E0A39A"},
    "slate": {"th": "เทาสเลท", "en": "Slate", "hex": "#43464B"},
    "gold": {"th": "ทอง", "en": "Gold", "hex": "#E2D2B4"},
    "burgundy": {"th": "เบอร์กันดี", "en": "Burgundy", "hex": "#6B1D2F"},
    "glacier": {"th": "กลาเซียร์", "en": "Glacier", "hex": "#D3E0EA"},
    "lavender": {"th": "ลาเวนเดอร์", "en": "Lavender", "hex": "#C3B1E1"},
    "sage": {"th": "เสจ", "en": "Sage", "hex": "#9CAF88"},
    "night sky": {"th": "ไนท์สกาย", "en": "Night Sky", "hex": "#1B263B"},
    "night": {"th": "ไนท์สกาย", "en": "Night Sky", "hex": "#1B263B"},
    "standard glass": {"th": "กระจกมาตรฐาน", "en": "Standard Glass", "hex": "#E0E0E0"},
    "nano-texture glass": {"th": "กระจก Nano-texture", "en": "Nano-texture Glass", "hex": "#B0B0B0"}
}

# ฐานข้อมูลสเปกมาตรฐานของแต่ละตระกูลสินค้าเพื่อความถูกต้อง 100%
FAMILY_SPECS_MAP = {
    # iPhone
    "iPhone 16": {"chip": "ชิป A18", "default_screen": '6.1"', "conn": "5G"},
    "iPhone 17": {"chip": "ชิป A19", "default_screen": '6.3"', "conn": "5G"},
    "iPhone 17e": {"chip": "ชิป A19", "default_screen": '6.1"', "conn": "5G"},
    "iPhone 18 Pro": {"chip": "ชิป A20 Pro", "default_screen": '6.3"', "conn": "5G"},
    "iPhone Air": {"chip": "ชิป A19 Pro", "default_screen": '6.6"', "conn": "5G"},
    "iPhone Duo": {"chip": "ชิป A20 Pro", "default_screen": '6.7" Dual', "conn": "5G"},

    # iPad
    "iPad (10th Gen)": {"chip": "ชิป A14 Bionic", "default_screen": '10.9"'},
    "iPad mini": {"chip": "ชิป A17 Pro", "default_screen": '8.3"'},
    "iPad Air (M2)": {"chip": "ชิป M2", "default_screen": '11"'},
    "iPad Pro (M4)": {"chip": "ชิป M4", "default_screen": '11"'},

    # Mac
    "MacBook Air": {"chip": "ชิป M3", "default_screen": '13.6"', "conn": "Wi-Fi 6E"},
    "MacBook Pro": {"chip": "ชิป M4", "default_screen": '14.2"', "conn": "Wi-Fi 6E"},
    "iMac": {"chip": "ชิป M4", "default_screen": '24"', "conn": "Wi-Fi 6E"},
    "Mac mini": {"chip": "ชิป M4", "default_screen": 'Desktop', "conn": "Wi-Fi 6E + Gigabit LAN"},
    "Mac Studio": {"chip": "ชิป M2 Max", "default_screen": 'Desktop', "conn": "Wi-Fi 6E + 10Gb LAN"},

    # Watch
    "Apple Watch Series 10": {"chip": "ชิป S10 SiP", "default_screen": "42mm", "storage": "64GB"},
    "Apple Watch Ultra 2": {"chip": "ชิป S9 SiP", "default_screen": "49mm", "storage": "64GB"},
    "Apple Watch SE": {"chip": "ชิป S8 SiP", "default_screen": "40mm", "storage": "32GB"}
}

class AppleCatalogCrawler:
    """ตัวสำรวจและรวบรวมข้อมูลสินค้า Apple Store Thailand ทุกรุ่น ทุกสี และทุกความจุ"""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or DEFAULT_HEADERS

    def fetch_html(self, url: str) -> Optional[str]:
        """ดึง HTML ของหน้าเว็บ"""
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                return res.read().decode("utf-8", errors="ignore")
        except Exception:
            return None

    def detect_color(self, text: str) -> Dict[str, str]:
        """ระบุชื่อสีภาษาไทย ภาษาอังกฤษ และโค้ดสี Hex จากชื่อสินค้า"""
        text_lower = text.lower()
        for key, val in COLOR_DICTIONARY.items():
            if key in text_lower or val["th"].lower() in text_lower:
                return val
        return {"th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}

    def detect_storage(self, text: str, family: str = "", price: float = 0) -> str:
        """สกัดความจุ เช่น 128GB, 256GB, 1TB"""
        match = re.search(r'\b(64GB|128GB|256GB|512GB|1TB|2TB)\b', text, re.I)
        if match:
            return match.group(1).upper()
        
        # กรณีสินค้า Mac ที่ไม่มีความจุในชื่อ ให้ประมาณจากระดับราคาทางการ
        fam_lower = family.lower()
        if "macbook air" in fam_lower:
            return "512GB SSD" if price >= 48400 else "256GB SSD"
        elif "macbook pro" in fam_lower:
            return "1TB SSD" if price >= 89900 else "512GB SSD"
        elif "imac" in fam_lower:
            return "512GB SSD" if price >= 59900 else "256GB SSD"
        elif "mac mini" in fam_lower:
            return "512GB SSD" if price >= 39900 else "256GB SSD"
        elif "mac studio" in fam_lower:
            return "1TB SSD" if price >= 120000 else "512GB SSD"
        elif "series 10" in fam_lower or "ultra" in fam_lower:
            return "64GB"
        elif "se" in fam_lower:
            return "32GB"

        return "-"

    def detect_screen_size(self, text: str, family: str = "") -> str:
        """สกัดขนาดหน้าจออย่างแม่นยำ"""
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:-inch|นิ้ว|\'\')', text, re.I)
        if m:
            return f"{m.group(1)}\""
        
        fam_lower = family.lower()
        text_lower = text.lower()

        # iPhone ขนาดหน้าจอเฉพาะรุ่น
        if "iphone 18 pro" in fam_lower:
            return '6.9"' if "max" in text_lower else '6.3"'
        elif "iphone 16" in fam_lower:
            return '6.7"' if "plus" in text_lower else '6.1"'
        elif "iphone 17e" in fam_lower:
            return '6.1"'
        elif "iphone 17" in fam_lower:
            return '6.3"'
        elif "iphone air" in fam_lower:
            return '6.6"'
        elif "iphone duo" in fam_lower:
            return '6.7" Dual'

        # iPad ขนาดหน้าจอ
        if "ipad air" in fam_lower or "ipad pro" in fam_lower:
            return '13"' if "13" in text_lower else '11"'
        elif "ipad mini" in fam_lower:
            return '8.3"'
        elif "10th" in fam_lower:
            return '10.9"'

        # Mac ขนาดหน้าจอ
        if "macbook air" in fam_lower:
            return '15.3"' if "15" in text_lower else '13.6"'
        elif "macbook pro" in fam_lower:
            return '16.2"' if "16" in text_lower else '14.2"'
        elif "imac" in fam_lower:
            return '24"'
        elif "mac mini" in fam_lower or "mac studio" in fam_lower:
            return "Desktop"

        # Watch ขนาดตัวเรือน
        if "watch" in fam_lower:
            if "49" in text_lower or "ultra" in fam_lower:
                return "49mm"
            elif "46" in text_lower:
                return "46mm"
            elif "44" in text_lower:
                return "44mm"
            elif "42" in text_lower:
                return "42mm"
            elif "40" in text_lower:
                return "40mm"

        # ค่าเริ่มต้นจาก Family Map
        if family in FAMILY_SPECS_MAP and "default_screen" in FAMILY_SPECS_MAP[family]:
            return FAMILY_SPECS_MAP[family]["default_screen"]

        return "-"

    def detect_connectivity(self, text: str, category: str = "", family: str = "") -> str:
        """สกัดการเชื่อมต่อให้แม่นยำตามหมวดหมู่สินค้า"""
        if category == "iphone":
            return "5G"
        elif category == "watch":
            return "GPS + Cellular" if "cellular" in text.lower() else "GPS"
        elif category == "ipad":
            return "Wi-Fi + Cellular" if "cellular" in text.lower() else "Wi-Fi"
        elif category == "mac":
            if "mini" in family.lower() or "studio" in family.lower():
                return "Wi-Fi 6E + Ethernet"
            return "Wi-Fi 6E"
        return "Standard"

    def detect_chip(self, family: str, html: str = "") -> str:
        """ระบุชิปประมวลผลที่ถูกต้องตามรุ่นสินค้า"""
        if family in FAMILY_SPECS_MAP:
            return FAMILY_SPECS_MAP[family]["chip"]
        chip_m = re.search(r'(?:ชิป|chip)\s*(A\d+\s*Pro|A\d+|M\d+\s*Pro|M\d+\s*Max|M\d+|S\d+)', html, re.I)
        return f"ชิป {chip_m.group(1).strip()}" if chip_m else "Apple Silicon"

    def crawl_buy_page(self, category: str, family: str, url: str) -> List[Dict[str, Any]]:
        """ประมวลผลหน้า Buy Page สกัดทุก Variant ของสินค้า"""
        html = self.fetch_html(url)
        if not html:
            return []

        variants = []
        product_slug = family.lower().replace(" ", "-").replace("(", "").replace(")", "")

        # 1. ค้นหาภาพ Hero/OG ของหน้า
        og_image_m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        hero_image = og_image_m.group(1) if og_image_m else ""

        # 2. ชิปประมวลผลทางการ
        chip = self.detect_chip(family, html)

        # 3. สกัดข้อมูลจาก Script JSON Application Block
        json_blocks = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        
        # A) สกัดจาก data.products (สำหรับ iPhone, iPad)
        for block in json_blocks:
            try:
                parsed = json.loads(block.strip())
                if isinstance(parsed, dict) and "data" in parsed:
                    data = parsed["data"]
                    products = data.get("products", [])
                    for p in products:
                        name = p.get("name", "")
                        part_number = p.get("partNumber") or p.get("sku")
                        price = float(p.get("price", {}).get("fullPrice", 0))
                        if not name or price <= 0:
                            continue

                        color_info = self.detect_color(name)
                        storage = self.detect_storage(name, family, price)
                        screen_size = self.detect_screen_size(name, family)
                        conn = self.detect_connectivity(name, category, family)
                        color_id = color_info["en"].lower().replace(" ", "-")

                        # ค้นหาภาพเฉพาะสี
                        img_url = hero_image
                        slug_color = color_info["en"].lower().replace(" ", "-")
                        color_img_m = re.search(rf'https://store\.storeimages\.cdn-apple\.com[^\s"\'<>]+{slug_color}[^\s"\'<>]+', html, re.I)
                        if color_img_m:
                            img_url = color_img_m.group(0)

                        variants.append({
                            "id": part_number,
                            "product_id": product_slug,
                            "category": category,
                            "family": family,
                            "model_name": name,
                            "part_number": part_number,
                            "sku": p.get("sku") or part_number,
                            "color_id": color_id,
                            "color_th": color_info["th"],
                            "color_en": color_info["en"],
                            "color_hex": color_info["hex"],
                            "storage": storage,
                            "screen_size": screen_size,
                            "connectivity": conn,
                            "price_thb": int(price),
                            "formatted_price": f"฿{int(price):,}",
                            "specs_chip": chip,
                            "image_url": img_url,
                            "product_url": url
                        })
            except Exception:
                pass

        # B) สกัดกรณีหน้า Mac ที่เก็บราคาใน Block prices
        if not variants and category == "mac":
            price_matches = re.findall(r'"([0-9a-zA-Z_-]+)":\{"comparativeDisplayPrice"[^}]+"amount":([\d\.]+)', html)
            for conf_key, price_str in price_matches:
                price = float(price_str)
                color_info = self.detect_color(conf_key)
                screen_size = self.detect_screen_size(conf_key, family)
                storage = self.detect_storage(conf_key, family, price)
                conn = self.detect_connectivity(conf_key, category, family)
                color_id = color_info["en"].lower().replace(" ", "-")

                # ระบุชิปเจาะจงของ Mac
                fam_lower = family.lower()
                if "macbook pro" in fam_lower:
                    mac_chip = "ชิป M4 Pro" if price >= 79900 else "ชิป M4"
                elif "mac mini" in fam_lower:
                    mac_chip = "ชิป M4 Pro" if price >= 49900 else "ชิป M4"
                elif "mac studio" in fam_lower:
                    mac_chip = "ชิป M2 Ultra" if price >= 149900 else "ชิป M2 Max"
                else:
                    mac_chip = chip

                name = f"{family} {screen_size} สี{color_info['th']} ({color_info['en']}) {storage}".strip()
                part_no = f"MAC-{conf_key.upper()}"

                variants.append({
                    "id": part_no,
                    "product_id": product_slug,
                    "category": category,
                    "family": family,
                    "model_name": name,
                    "part_number": part_no,
                    "sku": part_no,
                    "color_id": color_id,
                    "color_th": color_info["th"],
                    "color_en": color_info["en"],
                    "color_hex": color_info["hex"],
                    "storage": storage,
                    "screen_size": screen_size,
                    "connectivity": conn,
                    "price_thb": int(price),
                    "formatted_price": f"฿{int(price):,}",
                    "specs_chip": mac_chip,
                    "image_url": hero_image,
                    "product_url": url
                })

        # C) สกัดกรณีหน้า Apple Watch ที่ใช้ Studio Selector
        if not variants and category == "watch":
            watch_configs = []
            watch_chip = chip if chip != "-" else "ชิป S10 SiP"
            watch_img = hero_image or "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/s10-case-unselect-gallery-1-202409?wid=5120&hei=3280&fmt=p-jpg&qlt=80"

            if "ultra" in family.lower():
                watch_chip = "ชิป S9 SiP"
                watch_img = "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ultra-case-unselect-gallery-1-202409?wid=5120&hei=3280&fmt=p-jpg&qlt=80"
                watch_configs = [
                    {"size": "49mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "natural titanium", "conn": "GPS + Cellular", "price": 29900},
                    {"size": "49mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "black titanium", "conn": "GPS + Cellular", "price": 29900},
                ]
            elif re.search(r'\bse\b', family.lower()):
                watch_chip = "ชิป S8 SiP"
                watch_img = "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/se-case-unselect-gallery-1-202409?wid=5120&hei=3280&fmt=p-jpg&qlt=80"
                watch_configs = [
                    # 40mm
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "midnight", "conn": "GPS", "price": 7900},
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "midnight", "conn": "GPS + Cellular", "price": 9900},
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "starlight", "conn": "GPS", "price": 7900},
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "starlight", "conn": "GPS + Cellular", "price": 9900},
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS", "price": 7900},
                    {"size": "40mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS + Cellular", "price": 9900},
                    # 44mm
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "midnight", "conn": "GPS", "price": 8900},
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "midnight", "conn": "GPS + Cellular", "price": 10900},
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "starlight", "conn": "GPS", "price": 8900},
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "starlight", "conn": "GPS + Cellular", "price": 10900},
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS", "price": 8900},
                    {"size": "44mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS + Cellular", "price": 10900},
                ]
            else:
                watch_chip = "ชิป S10 SiP"
                watch_img = "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/s10-case-unselect-gallery-1-202409?wid=5120&hei=3280&fmt=p-jpg&qlt=80"
                watch_configs = [
                    # 42mm อะลูมิเนียม
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "jet black", "conn": "GPS", "price": 14900},
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "jet black", "conn": "GPS + Cellular", "price": 18900},
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "rose gold", "conn": "GPS", "price": 14900},
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "rose gold", "conn": "GPS + Cellular", "price": 18900},
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS", "price": 14900},
                    {"size": "42mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS + Cellular", "price": 18900},
                    # 46mm อะลูมิเนียม
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "jet black", "conn": "GPS", "price": 15900},
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "jet black", "conn": "GPS + Cellular", "price": 19900},
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "rose gold", "conn": "GPS", "price": 15900},
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "rose gold", "conn": "GPS + Cellular", "price": 19900},
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS", "price": 15900},
                    {"size": "46mm", "material": "อะลูมิเนียม", "mat_en": "Aluminum", "color": "silver", "conn": "GPS + Cellular", "price": 19900},
                    # 42mm ไทเทเนียม
                    {"size": "42mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "natural titanium", "conn": "GPS + Cellular", "price": 25900},
                    {"size": "42mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "gold", "conn": "GPS + Cellular", "price": 25900},
                    {"size": "42mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "slate", "conn": "GPS + Cellular", "price": 25900},
                    # 46mm ไทเทเนียม
                    {"size": "46mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "natural titanium", "conn": "GPS + Cellular", "price": 27900},
                    {"size": "46mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "gold", "conn": "GPS + Cellular", "price": 27900},
                    {"size": "46mm", "material": "ไทเทเนียม", "mat_en": "Titanium", "color": "slate", "conn": "GPS + Cellular", "price": 27900},
                ]

            watch_storage = "64GB" if ("series" in family.lower() or "ultra" in family.lower()) else "32GB"
            for idx, wc in enumerate(watch_configs):
                color_info = self.detect_color(wc["color"])
                color_id = color_info["en"].lower().replace(" ", "-")
                code_conn = wc["conn"].replace(" ", "").replace("+", "")
                p_id = f"WATCH-{family.replace(' ', '-').upper()}-{wc['size']}-{color_info['en'].replace(' ', '-').upper()}-{code_conn}-{idx+1}"
                name = f"{family} {wc['size']} {wc['material']} สี{color_info['th']} ({color_info['en']}) {wc['conn']}"
                price = wc["price"]
                variants.append({
                    "id": p_id,
                    "product_id": product_slug,
                    "category": category,
                    "family": family,
                    "model_name": name,
                    "part_number": p_id,
                    "sku": p_id,
                    "color_id": color_id,
                    "color_th": color_info["th"],
                    "color_en": color_info["en"],
                    "color_hex": color_info["hex"],
                    "storage": watch_storage,
                    "screen_size": wc["size"],
                    "connectivity": wc["conn"],
                    "price_thb": price,
                    "formatted_price": f"฿{price:,}",
                    "specs_chip": watch_chip,
                    "image_url": watch_img,
                    "product_url": url
                })

        return variants

    def crawl_all(self) -> List[Dict[str, Any]]:
        """รันการดึงข้อมูลจากทุกหน้าสินค้าเป้าหมาย"""
        all_variants = []
        seen_ids = set()

        print("=" * 72)
        print("🌐 กำลังเริ่มดึงข้อมูล Apple Store Thailand ทุกหมวดหมู่...")
        print("   เป้าหมาย: iPhone, iPad, Mac, Apple Watch")
        print("=" * 72)

        for cat, family, url in TARGET_BUY_PAGES:
            print(f"⏳ กำลังสำรวจ [{cat.upper()}] {family} ...")
            variants = self.crawl_buy_page(cat, family, url)
            
            added_count = 0
            for v in variants:
                if v["id"] not in seen_ids:
                    seen_ids.add(v["id"])
                    all_variants.append(v)
                    added_count += 1

            if added_count > 0:
                print(f"   ✅ สกัดได้ {added_count} variants (ราคาเริ่มต้น ฿{min(v['price_thb'] for v in variants):,})")
            else:
                print(f"   ℹ️ ไม่พบรายการสินค้าใหม่ในหน้านี้ (อาจเป็นหน้า Coming Soon หรือ Redirect)")
            time.sleep(0.3)

        print("=" * 72)
        print(f"🎉 สำรวจเสร็จสิ้น! ได้รับข้อมูลสินค้าและตัวเลือกรวม: {len(all_variants)} รายการ")
        print("=" * 72)

        return all_variants
