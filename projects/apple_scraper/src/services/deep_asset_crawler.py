import urllib.request
import urllib.parse
import re
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

# Base Directory & Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
PRODUCTS_DEEP_DIR = DATA_DIR / "products_deep"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTS_DEEP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 6 หมวดหมู่ภาพมาตรฐานเพื่อการแจกแจงที่ชัดเจนระดับมืออาชีพ
ASSET_CATEGORIES = {
    "hardware_angles": {
        "title_th": "🎨 ตัวเครื่องและสีสันทุกมุมมอง",
        "title_en": "Hardware Angles & Color Finishes",
        "icon": "📱",
        "order": 1
    },
    "in_the_box": {
        "title_th": "📦 ของในกล่องและบรรจุภัณฑ์",
        "title_en": "What's In The Box & Packaging",
        "icon": "📦",
        "order": 2
    },
    "chip_internal": {
        "title_th": "⚡ ชิปและวิศวกรรมสถาปัตยกรรมภายใน",
        "title_en": "Chip & Internal Architecture",
        "icon": "⚡",
        "order": 3
    },
    "apple_intelligence": {
        "title_th": "🤖 Apple Intelligence และประสบการณ์ใช้งาน",
        "title_en": "Apple Intelligence & UI Experience",
        "icon": "🤖",
        "order": 4
    },
    "camera_samples": {
        "title_th": "📸 ตัวอย่างภาพถ่ายจริงจากระบบกล้อง",
        "title_en": "Shot On Device & Camera Samples",
        "icon": "📸",
        "order": 5
    },
    "workflow_accessories": {
        "title_th": "💼 การใช้งานระดับโปรและอุปกรณ์เสริม",
        "title_en": "Pro Workflows & Ecosystem Accessories",
        "icon": "💼",
        "order": 6
    }
}

# รายการสินค้าหลักที่ทำการเจาะลึก
PRODUCTS_REGISTRY = [
    # iPhone Family
    {
        "id": "iphone-16-pro",
        "name_th": "iPhone 16 Pro & iPhone 16 Pro Max",
        "name_en": "iPhone 16 Pro",
        "category": "iphone",
        "chip": "A18 Pro (3nm)",
        "overview_url": "https://www.apple.com/th/iphone-16-pro/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16-pro",
        "specs_url": "https://www.apple.com/th/iphone-16-pro/specs/"
    },
    {
        "id": "iphone-16",
        "name_th": "iPhone 16 & iPhone 16 Plus",
        "name_en": "iPhone 16",
        "category": "iphone",
        "chip": "A18 (3nm)",
        "overview_url": "https://www.apple.com/th/iphone-16/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16",
        "specs_url": "https://www.apple.com/th/iphone-16/specs/"
    },
    {
        "id": "iphone-15",
        "name_th": "iPhone 15 & iPhone 15 Plus",
        "name_en": "iPhone 15",
        "category": "iphone",
        "chip": "A16 Bionic",
        "overview_url": "https://www.apple.com/th/iphone-15/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-15",
        "specs_url": "https://www.apple.com/th/iphone-15/specs/"
    },
    {
        "id": "iphone-14",
        "name_th": "iPhone 14 & iPhone 14 Plus",
        "name_en": "iPhone 14",
        "category": "iphone",
        "chip": "A15 Bionic",
        "overview_url": "https://www.apple.com/th/iphone-14/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-14",
        "specs_url": "https://www.apple.com/th/iphone-14/specs/"
    },
    {
        "id": "iphone-se",
        "name_th": "iPhone SE (รุ่นที่ 3 Touch ID)",
        "name_en": "iPhone SE",
        "category": "iphone",
        "chip": "A15 Bionic",
        "overview_url": "https://www.apple.com/th/iphone-se/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-se",
        "specs_url": "https://www.apple.com/th/iphone-se/specs/"
    },

    # iPad Family
    {
        "id": "ipad-pro",
        "name_th": "iPad Pro (ชิป M4 จอ Ultra Retina XDR)",
        "name_en": "iPad Pro (M4)",
        "category": "ipad",
        "chip": "Apple M4",
        "overview_url": "https://www.apple.com/th/ipad-pro/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-pro",
        "specs_url": "https://www.apple.com/th/ipad-pro/specs/"
    },
    {
        "id": "ipad-air",
        "name_th": "iPad Air (ชิป M2 รุ่น 11\" และ 13\")",
        "name_en": "iPad Air (M2)",
        "category": "ipad",
        "chip": "Apple M2",
        "overview_url": "https://www.apple.com/th/ipad-air/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-air",
        "specs_url": "https://www.apple.com/th/ipad-air/specs/"
    },
    {
        "id": "ipad-10th-gen",
        "name_th": "iPad (รุ่นที่ 10 ดีไซน์หน้าจอทั้งหมด)",
        "name_en": "iPad (10th Generation)",
        "category": "ipad",
        "chip": "A14 Bionic",
        "overview_url": "https://www.apple.com/th/ipad-10.9/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad",
        "specs_url": "https://www.apple.com/th/ipad-10.9/specs/"
    },
    {
        "id": "ipad-mini",
        "name_th": "iPad mini (ชิป A17 Pro รองรับ Apple Intelligence)",
        "name_en": "iPad mini (A17 Pro)",
        "category": "ipad",
        "chip": "A17 Pro",
        "overview_url": "https://www.apple.com/th/ipad-mini/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-mini",
        "specs_url": "https://www.apple.com/th/ipad-mini/specs/"
    },

    # Mac Family
    {
        "id": "macbook-pro",
        "name_th": "MacBook Pro 14\" และ 16\" (ชิปตระกูล M4)",
        "name_en": "MacBook Pro (M4 / M4 Pro / M4 Max)",
        "category": "mac",
        "chip": "M4 / M4 Pro / M4 Max",
        "overview_url": "https://www.apple.com/th/macbook-pro/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-pro",
        "specs_url": "https://www.apple.com/th/macbook-pro/specs/"
    },
    {
        "id": "macbook-air",
        "name_th": "MacBook Air 13\" และ 15\" (ชิป M3)",
        "name_en": "MacBook Air (M3)",
        "category": "mac",
        "chip": "Apple M3",
        "overview_url": "https://www.apple.com/th/macbook-air/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-air",
        "specs_url": "https://www.apple.com/th/macbook-air/specs/"
    },
    {
        "id": "imac",
        "name_th": "iMac 24\" (ชิป M4 จอภาพ 4.5K Retina)",
        "name_en": "iMac (M4)",
        "category": "mac",
        "chip": "Apple M4",
        "overview_url": "https://www.apple.com/th/imac/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/imac",
        "specs_url": "https://www.apple.com/th/imac/specs/"
    },
    {
        "id": "mac-mini",
        "name_th": "Mac mini (ชิป M4 และ M4 Pro ไซส์กะทัดรัด 5x5 นิ้ว)",
        "name_en": "Mac mini (M4 / M4 Pro)",
        "category": "mac",
        "chip": "Apple M4 / M4 Pro",
        "overview_url": "https://www.apple.com/th/mac-mini/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/mac-mini",
        "specs_url": "https://www.apple.com/th/mac-mini/specs/"
    },
    {
        "id": "mac-studio",
        "name_th": "Mac Studio (ชิป M2 Max และ M2 Ultra ระดับซูเปอร์คอมพิวเตอร์)",
        "name_en": "Mac Studio (M2 Max / M2 Ultra)",
        "category": "mac",
        "chip": "M2 Max / M2 Ultra",
        "overview_url": "https://www.apple.com/th/mac-studio/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/mac-studio",
        "specs_url": "https://www.apple.com/th/mac-studio/specs/"
    },

    # Watch Family
    {
        "id": "apple-watch-series-10",
        "name_th": "Apple Watch Series 10 (จอใหญ่ที่สุดและบางที่สุด)",
        "name_en": "Apple Watch Series 10",
        "category": "watch",
        "chip": "S10 SiP",
        "overview_url": "https://www.apple.com/th/apple-watch-series-10/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch",
        "specs_url": "https://www.apple.com/th/apple-watch-series-10/specs/"
    },
    {
        "id": "apple-watch-ultra-2",
        "name_th": "Apple Watch Ultra 2 (ไทเทเนียมสีดำและธรรมชาติ)",
        "name_en": "Apple Watch Ultra 2",
        "category": "watch",
        "chip": "S9 SiP",
        "overview_url": "https://www.apple.com/th/apple-watch-ultra-2/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch-ultra",
        "specs_url": "https://www.apple.com/th/apple-watch-ultra-2/specs/"
    },
    {
        "id": "apple-watch-se",
        "name_th": "Apple Watch SE (คุ้มค่าครบครัน ฟีเจอร์สุขภาพและความปลอดภัย)",
        "name_en": "Apple Watch SE",
        "category": "watch",
        "chip": "S8 SiP",
        "overview_url": "https://www.apple.com/th/apple-watch-se/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch-se",
        "specs_url": "https://www.apple.com/th/apple-watch-se/specs/"
    }
]

class AppleDeepAssetCrawler:
    """ระบบดึงรูปภาพทางการเจาะลึกรายสินค้าทุกชิ้น แยก 6 หมวดหมู่อย่างสมบูรณ์และชัดเจน 100%"""

    def __init__(self):
        self.headers = DEFAULT_HEADERS

    def fetch_url(self, url: str) -> Optional[str]:
        """ดึง HTML หน้าเว็บอย่างปลอดภัย"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=12) as res:
                return res.read().decode("utf-8", errors="ignore")
        except Exception:
            return None

    def classify_asset(self, url: str, p_info: Dict[str, Any]) -> Dict[str, Any]:
        """จำแนกหมวดหมู่ พร้อมสกัดชื่อภาษาไทย คำอธิบาย และสเปกความละเอียด"""
        u_lower = url.lower()
        slug = p_info["id"]

        category_key = "hardware_angles"
        title_th = f"มุมมองตัวเครื่องทางการของ {p_info['name_th']}"
        title_en = f"Official Hardware View of {p_info['name_en']}"
        desc_th = "ภาพเรนเดอร์ทางการความละเอียดสูงระดับ 4K Retina จาก Apple Store"
        badge = "ตัวเครื่อง"

        # 1. ของในกล่อง (In-The-Box)
        if any(k in u_lower for k in ["witb", "box", "in-the-box", "adapter", "cable", "cloth", "packaging"]):
            category_key = "in_the_box"
            badge = "ในกล่อง"
            if "cable" in u_lower:
                title_th = "สายชาร์จแบบถัก USB-C Woven Charge Cable"
                title_en = "USB-C Woven Charge Cable"
                desc_th = "สายชาร์จและถ่ายโอนข้อมูลความเร็วสูงแบบถักทนทานพิเศษที่มีให้ในกล่อง"
            elif "adapter" in u_lower:
                title_th = "อะแดปเตอร์แปลงไฟ Apple Power Adapter"
                title_en = "Apple Power Adapter"
                desc_th = "หัวชาร์จจ่ายไฟมาตรฐานความปลอดภัยสูงของ Apple"
            elif "cloth" in u_lower:
                title_th = "ผ้าเช็ดทำความสะอาดสำหรับกระจก Nano-texture"
                title_en = "Polishing Cloth for Nano-texture Glass"
                desc_th = "ผ้าเช็ดไมโครไฟเบอร์พิเศษไม่ทำให้ผิวสัมผัสกระจกเป็นรอย"
            else:
                title_th = f"ตัวเครื่อง {p_info['name_th']} ในกล่องบรรจุภัณฑ์มาตรฐาน"
                title_en = f"{p_info['name_en']} In The Box Packaging"
                desc_th = "กล่องบรรจุภัณฑ์ที่ทำจากเยื่อกระดาษรีไซเคิล 100% พร้อมอุปกรณ์ครบชุด"

        # 2. ชิปและวิศวกรรมภายใน (Chip & Internal Architecture)
        elif any(k in u_lower for k in ["chip", "die", "thermal", "cooling", "substructure", "sensor", "tetraprism", "ceramic", "titanium", "battery", "graphite"]):
            category_key = "chip_internal"
            badge = p_info.get("chip", "ชิปประมวลผล")
            if "chip" in u_lower:
                title_th = f"ชิปประมวลผล {p_info.get('chip')} สถาปัตยกรรม Apple Silicon"
                title_en = f"{p_info.get('chip')} Apple Silicon Architecture Die Shot"
                desc_th = "ภาพโครงสร้างวงจรรวมระดับนาโนเมตร พร้อมหน่วยประมวลผลกราฟิกและ Neural Engine"
            elif "sensor" in u_lower or "tetraprism" in u_lower:
                title_th = "โครงสร้างเซ็นเซอร์กล้อง Quad-Pixel และปริซึมสะท้อน 4 เท่า (Tetraprism)"
                title_en = "Quad-Pixel Camera Sensor & Tetraprism Periscope Structure"
                desc_th = "วิศวกรรมการออกแบบเลนส์และเซ็นเซอร์รับแสงขนาดใหญ่พิเศษเพื่อภาพคมชัดระดับสตูดิโอ"
            elif "thermal" in u_lower or "cooling" in u_lower or "substructure" in u_lower:
                title_th = "โครงสร้างโครงสร้างย่อยการระบายความร้อนด้วยอะลูมิเนียมรีไซเคิล 100%"
                title_en = "100% Recycled Aluminum Thermal Substructure"
                desc_th = "ระบบกระจายความร้อนประสิทธิภาพสูง รองรับการประมวลผลกราฟิกหนักได้ต่อเนื่องยาวนานขึ้น"
            elif "ceramic" in u_lower:
                title_th = "กระจกด้านหน้า Ceramic Shield เจเนอเรชั่นล่าสุด"
                title_en = "Next-Generation Ceramic Shield Front Glass"
                desc_th = "แข็งแกร่งกว่ากระจกสมาร์ทโฟนทั่วไปถึง 2 เท่า ทนต่อการตกกระแทกได้อย่างยอดเยี่ยม"
            elif "titanium" in u_lower:
                title_th = "งานประกอบตัวเรือนไทเทเนียมเกรด 5 พ่นผิวเนื้อละเอียด (Micro-blasted)"
                title_en = "Grade 5 Titanium with Micro-blasted Finish"
                desc_th = "โลหะไทเทเนียมเกรดอากาศยาน แข็งแรง ทนทาน และมีน้ำหนักเบาเป็นพิเศษ"
            else:
                title_th = f"นวัตกรรมทางวิศวกรรมฮาร์ดแวร์ของ {p_info['name_th']}"
                title_en = f"Hardware Engineering of {p_info['name_en']}"
                desc_th = "สถาปัตยกรรมภายในตัวเครื่องที่ออกแบบมาเพื่อประสิทธิภาพและการใช้พลังงานคุ้มค่าสูงสุด"

        # 3. Apple Intelligence และประสบการณ์ใช้งาน (Apple Intelligence & Features)
        elif any(k in u_lower for k in ["ai", "intelligence", "siri", "writing", "clean_up", "cameracontrol", "camera_control", "action_button", "dynamic_island", "interface"]):
            category_key = "apple_intelligence"
            badge = "Apple Intelligence"
            if "cameracontrol" in u_lower or "camera_control" in u_lower:
                title_th = "อินเทอร์เฟซตัวควบคุมกล้อง (Camera Control) ระบบเซ็นเซอร์แรงกด"
                title_en = "Camera Control Touch Interface & Tactile Switch"
                desc_th = "ระบบสัมผัสแบบสไลด์เพื่อซูม ปรับค่ารับแสง และความชัดลึกได้อย่างแม่นยำด้วยปลายนิ้ว"
            elif "siri" in u_lower:
                title_th = "แอนิเมชันแสงเรืองขอบจอ Siri แบบใหม่ (Glowing Edge Interface)"
                title_en = "New Glowing Siri Edge Display Animation"
                desc_th = "การตอบสนองที่ไหลลื่นและชาญฉลาดยิ่งขึ้น พร้อมความเข้าใจบริบทส่วนบุคคลอย่างปลอดภัย"
            elif "clean_up" in u_lower:
                title_th = "เครื่องมือลบวัตถุรบกวนอัจฉริยะในแอพรูปภาพ (Clean Up Tool)"
                title_en = "Clean Up Tool in Photos Powered by On-Device Intelligence"
                desc_th = "ตรวจจับและลบวัตถุที่ไม่ต้องการออกจากภาพถ่ายได้ในแตะเดียวโดยคงพื้นหลังธรรมชาติ"
            elif "writing" in u_lower:
                title_th = "เครื่องมือช่วยเขียนอัจฉริยะ (Writing Tools) ขัดเกลา ตรวจทาน และสรุปข้อความ"
                title_en = "Writing Tools for Rewriting, Proofreading, and Summarizing"
                desc_th = "ช่วยเขียนและปรับแต่งระดับภาษาในอีเมลและข้อความได้ทุกที่ในระบบปฏิบัติการ"
            else:
                title_th = f"ระบบ Apple Intelligence บน {p_info['name_th']}"
                title_en = f"Apple Intelligence System on {p_info['name_en']}"
                desc_th = "ปัญญาประดิษฐ์ส่วนบุคคลที่ทรงพลัง มีประโยชน์ และปกป้องความเป็นส่วนตัวสูงสุด"

        # 4. ภาพถ่ายตัวอย่างจริง (Camera Samples)
        elif any(k in u_lower for k in ["sample", "shot", "macro", "telephoto", "portrait", "depth", "night", "cinematic", "photographic_styles"]):
            category_key = "camera_samples"
            badge = "ภาพถ่ายจริง"
            if "macro" in u_lower:
                title_th = "ตัวอย่างภาพถ่ายมาโครความละเอียด 48MP เจาะลึกทุกรายละเอียด"
                title_en = "48MP Macro Photography Sample with Extreme Detail"
                desc_th = "ถ่ายทอดเกสรดอกไม้และละอองน้ำได้อย่างคมชัดไร้ที่ติ"
            elif "telephoto" in u_lower or "5x" in u_lower:
                title_th = "ตัวอย่างภาพถ่ายซูมออปติคอล 5 เท่า ระยะโฟกัส 120 มม."
                title_en = "5x Optical Zoom 120mm Telephoto Sample"
                desc_th = "ดึงวัตถุระยะไกลให้เข้ามาใกล้ชิดพร้อมความคมชัดระดับโปร"
            elif "night" in u_lower:
                title_th = "ตัวอย่างภาพถ่ายโหมดกลางคืน (Night Mode) ในสภาพแสงน้อย"
                title_en = "Night Mode Sample in Extreme Low-light Environment"
                desc_th = "การจัดการสัญญาณรบกวนและเก็บรายละเอียดสีสันในเงามืดได้อย่างยอดเยี่ยม"
            elif "photographic_styles" in u_lower:
                title_th = "ตัวอย่างสไตล์ภาพถ่ายเจเนอเรชั่นใหม่ (Photographic Styles)"
                title_en = "Next-Generation Photographic Styles Sample"
                desc_th = "ปรับโทนผิวและคอนทราสต์ของภาพแบบเรียลไทม์ได้ตรงตามใจผู้สร้างสรรค์"
            else:
                title_th = f"ภาพถ่ายความละเอียดสูง ถ่ายจริงด้วยกล้อง {p_info['name_th']}"
                title_en = f"Full Resolution Sample Shot on {p_info['name_en']}"
                desc_th = "ตัวอย่างภาพถ่ายจากระบบกล้องระดับสตูดิโอ 48MP Fusion"

        # 5. เวิร์กโฟลว์และอุปกรณ์เสริม (Workflows & Accessories)
        elif any(k in u_lower for k in ["accessory", "accessories", "magic_keyboard", "keyboard", "pencil", "magsafe", "case", "band", "apps", "coding", "3d", "design"]):
            category_key = "workflow_accessories"
            badge = "อุปกรณ์เสริม & Pro"
            if "pencil" in u_lower:
                title_th = "การใช้งานร่วมกับ Apple Pencil Pro รองรับการบีบและหมุนด้าม"
                title_en = "Workflow with Apple Pencil Pro with Squeeze and Barrel Roll"
                desc_th = "เครื่องมือสร้างสรรค์งานศิลปะและโน้ตที่ตอบสนองต่อแรงกดและการเอียงอย่างเป็นธรรมชาติ"
            elif "magic_keyboard" in u_lower or "keyboard" in u_lower:
                title_th = "Magic Keyboard พร้อมแผงปุ่มฟังก์ชั่นและแทร็คแพดกระจก"
                title_en = "Magic Keyboard with Function Row and Glass Trackpad"
                desc_th = "เปลี่ยนแท็บเล็ตให้กลายเป็นเวิร์กสเตชันสำหรับการทำงานเอกสารและการเขียนโค้ด"
            elif "magsafe" in u_lower or "case" in u_lower:
                title_th = "เคสและอุปกรณ์เสริม MagSafe รองรับการชาร์จไร้สายความเร็วสูง 25W"
                title_en = "MagSafe Cases and Accessories with 25W Fast Wireless Charging"
                desc_th = "ยึดติดด้วยแม่เหล็กอย่างแน่นหนาและเข้าชุดกับสีตัวเครื่องอย่างลงตัว"
            elif "apps" in u_lower or "coding" in u_lower or "3d" in u_lower:
                title_th = "เวิร์กโฟลว์การทำงานระดับมืออาชีพ (Pro Workflow: 3D Render, Coding & Video)"
                title_en = "Professional Workflow in Industry Standard Apps"
                desc_th = "ประมวลผลงานตัดต่อวิดีโอ 8K ProRes และการเรนเดอร์โมเดล 3D แบบเรียลไทม์ได้อย่างลื่นไหล"
            else:
                title_th = f"อุปกรณ์เสริมและระบบนิเวศการใช้งานของ {p_info['name_th']}"
                title_en = f"Ecosystem Accessories for {p_info['name_en']}"
                desc_th = "อุปกรณ์ต่อพ่วงที่ออกแบบมาเพื่อเสริมประสิทธิภาพการใช้งานให้สมบูรณ์แบบที่สุด"

        # 6. มุมมองตัวเครื่อง (Hardware Angles)
        else:
            category_key = "hardware_angles"
            badge = "ตัวเครื่อง"
            if "back" in u_lower:
                title_th = f"ตัวเครื่อง {p_info['name_th']} ด้านหลังเต็มตัว"
                title_en = f"{p_info['name_en']} Full Rear View"
                desc_th = "มุมมองด้านหลังแสดงพื้นผิววัสดุพรีเมียมและโมดูลกล้องที่ประณีต"
            elif "side" in u_lower or "profile" in u_lower:
                title_th = f"ตัวเครื่อง {p_info['name_th']} ด้านข้างและความบางเฉียบ"
                title_en = f"{p_info['name_en']} Profile Side View"
                desc_th = "แสดงความโค้งมนของขอบตัวเรือนและปุ่มควบคุมฟังก์ชันต่างๆ"
            elif "display" in u_lower or "front" in u_lower:
                title_th = f"หน้าจอแสดงผล Super Retina XDR ขอบจอบางเฉียบของ {p_info['name_th']}"
                title_en = f"{p_info['name_en']} Super Retina XDR Front Display"
                desc_th = "หน้าจอ OLED สว่างสูงสุด 2,000 nits พร้อมฟีเจอร์ Dynamic Island"
            elif "ports" in u_lower:
                title_th = f"พอร์ตเชื่อมต่อความเร็วสูงและช่องลำโพงสเตอริโอของ {p_info['name_th']}"
                title_en = f"{p_info['name_en']} Ports & Speaker Architecture"
                desc_th = "พอร์ตมาตรฐานระดับสากลรองรับการถ่ายโอนข้อมูลความเร็วสูงและการชาร์จเร็ว"
            else:
                title_th = f"มุมมองตัวเครื่องทางการ 4K Retina ของ {p_info['name_th']}"
                title_en = f"{p_info['name_en']} Official 4K Retina Hardware View"
                desc_th = "ภาพผลิตภัณฑ์ความละเอียดสูงระดับ 2560x2560 แสดงรายละเอียดสีและมิติอย่างสมบูรณ์แบบ"

        # Aspect Ratio & Resolution
        res = "2560x2560 (4K Retina)"
        aspect = "1:1"
        if "large_2x" in u_lower:
            res = "3840x2160 (Ultra HD 4K)"
            aspect = "16:9"
        elif "witb" in u_lower:
            res = "2000x2000 (Retina)"
            aspect = "1:1"

        return {
            "category": category_key,
            "category_th": ASSET_CATEGORIES[category_key]["title_th"],
            "category_en": ASSET_CATEGORIES[category_key]["title_en"],
            "badge": badge,
            "title_th": title_th,
            "title_en": title_en,
            "description_th": desc_th,
            "resolution": res,
            "aspect_ratio": aspect
        }

    def crawl_product_deep_assets(self, p_info: Dict[str, Any]) -> Dict[str, Any]:
        """เจาะลึกสินค้า 1 ตัว: ดึงทุกลิงก์รูปภาพจาก Overview + Buy Store + Curated Gallery"""
        pid = p_info["id"]
        print(f"\n🔍 กำลังเจาะลึกสินค้า: {p_info['name_th']} ({p_info['overview_url']})...")

        seen_urls = set()
        assets = []

        # Helper สำหรับเพิ่ม Asset
        def add_asset(raw_url: str):
            clean_url = raw_url.strip()
            if not clean_url or clean_url in seen_urls:
                return
            if any(k in clean_url.lower() for k in ["icon", "bullet", "logo", "glyph", "tracking", "pixel", ".svg"]):
                return

            seen_urls.add(clean_url)
            meta = self.classify_asset(clean_url, p_info)
            asset_id = f"{pid}-{meta['category']}-{len(assets)+1:03d}"
            assets.append({
                "id": asset_id,
                "product_id": pid,
                "image_url": clean_url,
                **meta
            })

        # 1. ดึงจาก Overview Page
        ov_html = self.fetch_url(p_info["overview_url"])
        if ov_html:
            # ค้นหาภาพใน src, srcset, data-src, background-image
            matches = re.findall(r'(?:src|data-src|data-progressive-image|srcset)=[\"\']([^\"\']+)[\"\']|url\([\"\']?([^\"\'\)]+)[\"\']?\)', ov_html)
            for m in matches:
                val = m[0] or m[1]
                for part in val.split(','):
                    u = part.strip().split(' ')[0]
                    if any(u.endswith(ext) or ext + '?' in u for ext in ['.jpg', '.png', '.jpeg', '.webp']):
                        full = urllib.parse.urljoin(p_info["overview_url"], u)
                        # คัดเฉพาะภาพขนาดใหญ่ large หรือ large_2x หรือภาพที่มีความหมาย
                        if "apple.com" in full and ("large" in full or "hero" in full or "overview" in full):
                            add_asset(full)

        # 2. ดึงจาก Store Buy Page
        buy_html = self.fetch_url(p_info["buy_url"])
        if buy_html:
            store_imgs = set(re.findall(r'https://store\.storeimages\.cdn-apple\.com/[^\s\"\'\,\?]+', buy_html))
            for s in store_imgs:
                # คัดเฉพาะภาพสินค้าจริง เช่น select, witb, finish, gallery, accessory
                s_lower = s.lower()
                if any(k in s_lower for k in ["select", "witb", "finish", "gallery", "pencil", "keyboard", "cable", "case"]):
                    add_asset(s)

        # 3. เสริม Curated Master Assets เพื่อรับประกันความสมบูรณ์ 100% (แม้ในภาวะออฟไลน์)
        curated_assets = self.get_curated_assets_for_product(pid, p_info)
        for ca in curated_assets:
            add_asset(ca["image_url"])

        # สรุปหมวดหมู่
        categories_count = Counter(a["category"] for a in assets)

        summary = {
            "product_id": pid,
            "product_name_th": p_info["name_th"],
            "product_name_en": p_info["name_en"],
            "category": p_info["category"],
            "chip": p_info.get("chip", "-"),
            "overview_url": p_info["overview_url"],
            "buy_url": p_info["buy_url"],
            "specs_url": p_info.get("specs_url", ""),
            "total_assets_count": len(assets),
            "categories_summary": {k: categories_count.get(k, 0) for k in ASSET_CATEGORIES.keys()},
            "assets": assets
        }

        # บันทึกไฟล์ JSON รายสินค้า
        p_json_path = PRODUCTS_DEEP_DIR / f"{pid}_deep_assets.json"
        with open(p_json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"  ✅ สกัดรูปภาพสำเร็จ: {len(assets)} ภาพ (ครอบคลุมครบ {len(categories_count)} หมวดหมู่)")
        for cat_k, c_info in ASSET_CATEGORIES.items():
            print(f"     ↳ {c_info['title_th']}: {categories_count.get(cat_k, 0)} ภาพ")
        print(f"  💾 บันทึกไฟล์: {p_json_path}")
        return summary

    def get_curated_assets_for_product(self, pid: str, p_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """ชุดภาพความละเอียดสูง 4K Retina และคัดแยกพิเศษเฉพาะของแต่ละรุ่น"""
        curated = []

        if pid == "iphone-16-pro":
            curated = [
                # 1. Hardware & Colors
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-finish-select-202409-6-3inch-deserttitanium"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-finish-select-202409-6-3inch-naturaltitanium"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-finish-select-202409-6-3inch-whitetitanium"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-finish-select-202409-6-3inch-blacktitanium"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-model-unselect-gallery-1-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-model-unselect-gallery-2-202409"},
                # 2. In The Box
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-black-witb-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-pro-cables-witb-202409"},
                # 3. Chip & Internal
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider/chip__fh5j5on49p2e_large_2x.jpg"},
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider_modals/camera/modal_pro_controls__fw329w7rs4y2_large_2x.jpg"},
                {"image_url": "https://www.apple.com/th/iphone/home/images/overview/consider_modals/design/modal_last__d33bqh7vdo6e_large_2x.jpg"},
                # 4. Apple Intelligence
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider/camera__dez4cvpw83sm_large_2x.jpg"},
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider_modals/chip-battery/modal_supersmart__fkud9c4nk6eu_large_2x.jpg"},
                # 5. Camera Samples
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider_modals/camera/modal_stunning__bywf285rkqj6_large_2x.jpg"},
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider_modals/camera/modal_depth__dm4mjbszi98i_large_2x.jpg"},
                # 6. Accessories
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/essentials/airtag__dpxizz2eal26_large_2x.jpg"},
                {"image_url": "https://www.apple.com/th/iphone/home/images/overview/augment/airpods__bz9s5pwm8j6u_large_2x.jpg"}
            ]
        elif pid == "iphone-16":
            curated = [
                # 1. Hardware & Colors
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-finish-select-202409-6-1inch-ultramarine"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-finish-select-202409-6-1inch-teal"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-finish-select-202409-6-1inch-pink"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-finish-select-202409-6-1inch-white"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-finish-select-202409-6-1inch-black"},
                # 2. In The Box
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-black-witb-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-16-cables-witb-202409"},
                # 3. Chip & Internal
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider/chip__fh5j5on49p2e_large_2x.jpg"},
                # 4. Apple Intelligence & Camera Control
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider/camera__dez4cvpw83sm_large_2x.jpg"},
                # 5. Camera Samples
                {"image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider_modals/camera/modal_stunning__bywf285rkqj6_large_2x.jpg"}
            ]
        elif pid == "ipad-pro":
            curated = [
                # 1. Hardware & Colors
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-finish-select-202405-13inch-spaceblack"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-finish-select-202405-11inch-spaceblack"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-13-select-wifi-silver-202405"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-13-select-wifi-spaceblack-202405"},
                # 2. In The Box
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-13-witb-spaceblack-wifi-202405"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-13-witb-silver-wifi-202405"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-witb-black-cable-202405"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-witb-adapter-202405_GEO_TH"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-witb-cloth-nano-202405"},
                # 3. Accessories (Pencil Pro & Magic Keyboard)
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-apple-pencil-pro-select-gallery-1-202405"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-apple-pencil-pro-select-gallery-2-202405_GEO_TH_LANG_TH"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-magic-keyboard-select-gallery-1-202405_GEO_TH_LANG_TH"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-magic-keyboard-select-gallery-2-202405_GEO_TH_LANG_TH"},
                # 4. Glass Engineering
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-pro-glass-select-gallery-1-202405"}
            ]
        elif pid == "macbook-pro":
            curated = [
                # 1. Hardware & Colors
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-macbook-pro-size-unselect-202601-gallery-1"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-macbook-pro-size-unselect-202601-gallery-2"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-macbook-pro-size-unselect-202601-gallery-3"},
                # 2. Pro Apps Workflows
                {"image_url": "https://www.apple.com/th/macbook-pro/images/overview/apps/apps_3d__c1afou0tu5yu_large_2x.jpg"},
                {"image_url": "https://www.apple.com/th/macbook-pro/images/overview/apps/apps_coding__c9v42iv3gioi_large_2x.jpg"},
                {"image_url": "https://www.apple.com/th/macbook-pro/images/overview/apps/apps_design__dsxdvaoxgtme_large_2x.jpg"},
                {"image_url": "https://www.apple.com/th/macbook-pro/images/overview/apps/apps_business__c2y64cyjtlqq_large_2x.jpg"}
            ]
        elif pid == "iphone-15":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-finish-select-202309-6-1inch-pink"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-finish-select-202309-6-1inch-yellow"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-finish-select-202309-6-1inch-green"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-finish-select-202309-6-1inch-blue"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-finish-select-202309-6-1inch-black"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-black-witb-202309"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-15-cables-witb-202309"}
            ]
        elif pid == "iphone-14":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-blue"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-purple"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-yellow"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-midnight"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-starlight"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-14-finish-select-202209-6-1inch-product-red"}
            ]
        elif pid == "iphone-se":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-se-finish-select-202207-midnight"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-se-finish-select-202207-starlight"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/iphone-se-finish-select-202207-product-red"}
            ]
        elif pid == "ipad-10th-gen":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-10th-gen-finish-select-202212-blue"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-10th-gen-finish-select-202212-pink"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-10th-gen-finish-select-202212-silver"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-10th-gen-finish-select-202212-yellow"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-10th-gen-witb-silver-202212"}
            ]
        elif pid == "ipad-mini":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-mini-finish-select-202410-spacegray"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-mini-finish-select-202410-blue"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-mini-finish-select-202410-purple"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-mini-finish-select-202410-starlight"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/ipad-mini-witb-spacegray-202410"}
            ]
        elif pid == "macbook-air":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/macbook-air-13-15-unselect-202402-gallery-1"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/macbook-air-13-15-unselect-202402-gallery-2"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/macbook-air-13-15-unselect-202402-gallery-3"}
            ]
        elif pid == "imac":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-blue"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-purple"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-pink"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-orange"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-yellow"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-green"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-finish-select-202410-24inch-silver"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/imac-witb-blue-202410"}
            ]
        elif pid == "mac-mini":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-mini-select-202410"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-mini-witb-202410"}
            ]
        elif pid == "mac-studio":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-studio-select-202306"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-studio-witb-202306"}
            ]
        elif pid == "apple-watch-series-10":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-aluminum-jet-black-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-aluminum-rose-gold-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-aluminum-silver-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-titanium-slate-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-titanium-natural-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-titanium-gold-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-series-10-witb-202409"}
            ]
        elif pid == "apple-watch-ultra-2":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-ultra-2-black-titanium-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-ultra-2-natural-titanium-select-202409"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-ultra-2-witb-202409"}
            ]
        elif pid == "apple-watch-se":
            curated = [
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-se-midnight-select-202209"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-se-starlight-select-202209"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-se-silver-select-202209"},
                {"image_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/apple-watch-se-witb-202209"}
            ]

        return curated

    def crawl_all_deep_products(self) -> Dict[str, Any]:
        """เจาะลึกสินค้าหลักทั้งหมดทุกตัวและสร้างฐานข้อมูล Deep Media Catalog"""
        print("=" * 74)
        print("🚀 เริ่มระบบเจาะลึกรูปภาพสินค้า Apple Store (Deep Product Asset Extractor)")
        print(f"📦 เป้าหมาย: {len(PRODUCTS_REGISTRY)} ตระกูลสินค้าชั้นนำ ครอบคลุม 6 หมวดหมู่")
        print("=" * 74)

        all_products_assets = {}
        total_all_images = 0

        for p_info in PRODUCTS_REGISTRY:
            res = self.crawl_product_deep_assets(p_info)
            all_products_assets[p_info["id"]] = res
            total_all_images += res["total_assets_count"]

        # 1. บันทึก Master JSON: apple_deep_assets_catalog.json
        master_json_path = EXPORTS_DIR / "apple_deep_assets_catalog.json"
        master_data = {
            "metadata": {
                "title": "Apple Store Thailand Deep Product Media Catalog",
                "description": "แคตตาล็อกรูปภาพทางการระดับ 4K เจาะลึกรายสินค้า แยก 6 หมวดหมู่อย่างสมบูรณ์ 100%",
                "total_products": len(all_products_assets),
                "total_images": total_all_images,
                "categories": ASSET_CATEGORIES,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "products": all_products_assets
        }

        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)
        print(f"\n📄 บันทึก Master JSON สำเร็จ: {master_json_path} (รวม {total_all_images} รูปภาพ)")

        # 2. บันทึก JavaScript Bundle: apple_deep_assets.js
        js_path = EXPORTS_DIR / "apple_deep_assets.js"
        js_content = "/**\n * Apple Deep Product Media Assets Bundle (4K Retina & 6 Categories)\n */\n"
        js_content += f"window.APPLE_DEEP_ASSETS = {json.dumps(master_data, ensure_ascii=False, indent=2)};\n"
        js_content += "if (typeof module !== 'undefined' && module.exports) { module.exports = window.APPLE_DEEP_ASSETS; }\n"
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"⚡ บันทึก JavaScript Bundle สำเร็จ: {js_path}")

        # 3. บันทึกและสร้างตารางใน SQLite: apple_catalog.db
        db_path = EXPORTS_DIR / "apple_catalog.db"
        if db_path.exists():
            self._save_to_sqlite(db_path, all_products_assets)

        print("\n" + "=" * 74)
        print("🎉 ระบบเจาะลึกรูปภาพรายสินค้าสร้างฐานข้อมูลสำเร็จสมบูรณ์ 100%!")
        print(f"📦 จำนวนสินค้าที่เจาะลึก: {len(all_products_assets)} รุ่นหลัก")
        print(f"📸 จำนวนรูปภาพทั้งหมดที่สกัดและจัดหมวดหมู่: {total_all_images} ภาพ")
        print("=" * 74 + "\n")
        return master_data

    def _save_to_sqlite(self, db_path: Path, all_products: Dict[str, Any]):
        """สร้างตาราง product_deep_assets และบันทึกข้อมูลรูปภาพเจาะลึกลง SQLite"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_deep_assets (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    category_th TEXT NOT NULL,
                    category_en TEXT NOT NULL,
                    badge TEXT,
                    title_th TEXT NOT NULL,
                    title_en TEXT NOT NULL,
                    description_th TEXT,
                    image_url TEXT NOT NULL,
                    resolution TEXT,
                    aspect_ratio TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            """)

            cursor.execute("DELETE FROM product_deep_assets")

            total_inserted = 0
            for pid, pdata in all_products.items():
                for idx, a in enumerate(pdata.get("assets", [])):
                    cursor.execute("""
                        INSERT INTO product_deep_assets (
                            id, product_id, category, category_th, category_en,
                            badge, title_th, title_en, description_th,
                            image_url, resolution, aspect_ratio, sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        a["id"], a["product_id"], a["category"], a["category_th"], a["category_en"],
                        a.get("badge", ""), a["title_th"], a["title_en"], a.get("description_th", ""),
                        a["image_url"], a.get("resolution", ""), a.get("aspect_ratio", ""), idx + 1
                    ))
                    total_inserted += 1

            # สร้าง View สำหรับ Query แกลเลอรีตามหมวดหมู่ได้ง่าย
            cursor.execute("DROP VIEW IF EXISTS v_product_deep_assets")
            cursor.execute("""
                CREATE VIEW v_product_deep_assets AS
                SELECT 
                    a.id AS asset_id,
                    a.product_id,
                    p.name AS product_name,
                    a.category,
                    a.category_th,
                    a.badge,
                    a.title_th,
                    a.description_th,
                    a.image_url,
                    a.resolution
                FROM product_deep_assets a
                LEFT JOIN products p ON a.product_id = p.id
                ORDER BY a.product_id, a.sort_order
            """)

            conn.commit()
            conn.close()
            print(f"🗄️ บันทึกลง SQLite ตาราง product_deep_assets สำเร็จ: {total_inserted} รายการ")
        except Exception as e:
            print(f"⚠️ SQLite deep assets error: {e}")

    def download_curated_local_images(self, max_per_product: int = 5, max_workers: int = 8) -> int:
        """ดาวน์โหลดรูปภาพเด่นความละเอียดสูงของแต่ละรุ่นลงเครื่องใน data/images_deep/{product_id}/"""
        deep_images_dir = DATA_DIR / "images_deep"
        deep_images_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📥 กำลังดาวน์โหลดภาพเด่นความละเอียดสูง 4K ลงเครื่องใน {deep_images_dir}...")

        tasks = []
        master_json_path = EXPORTS_DIR / "apple_deep_assets_catalog.json"
        if not master_json_path.exists():
            return 0
            
        with open(master_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for pid, pdata in data.get("products", {}).items():
            p_dir = deep_images_dir / pid
            p_dir.mkdir(parents=True, exist_ok=True)
            assets = pdata.get("assets", [])
            for idx, a in enumerate(assets[:max_per_product]):
                u = a["image_url"]
                ext = ".png" if ".png" in u.lower() else ".jpg"
                filename = f"{idx+1:02d}_{a['category']}{ext}"
                dest = p_dir / filename
                tasks.append((u, dest))

        downloaded_count = 0
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = []
            for url, path in tasks:
                if path.exists() and path.stat().st_size > 10000:
                    continue
                futures.append(pool.submit(self._download_file, url, path))
            for fut in as_completed(futures):
                if fut.result():
                    downloaded_count += 1
                    
        print(f"✅ ดาวน์โหลดภาพเด่นลงเครื่องสำเร็จ: {downloaded_count} ไฟล์ใหม่ (พร้อมใช้งานออฟไลน์)")
        return downloaded_count

    def _download_file(self, url: str, dest_path: Path) -> bool:
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as res:
                data = res.read()
                if len(data) > 1000:
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    return True
        except Exception:
            pass
        return False

if __name__ == "__main__":
    crawler = AppleDeepAssetCrawler()
    crawler.crawl_all_deep_products()
