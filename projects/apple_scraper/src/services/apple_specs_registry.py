"""
Apple Official Technical Specifications Master Registry (Apple Store Thailand)
ฐานข้อมูลสเปกทางเทคนิคทางการของ Apple ครบถ้วน 100% ทุกรุ่นย่อย ทุกมิติขนาด น้ำหนัก จอภาพ กล้อง แบตเตอรี่ และอุปกรณ์ในกล่อง
"""

from typing import Dict, Any, List

OFFICIAL_SUB_MODELS_REGISTRY: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # iPhone 16 Family
    # =========================================================================
    "iphone-16": {
        "family_id": "iphone-16",
        "category_id": "iphone",
        "family_name": "iPhone 16",
        "sub_model_id": "iphone-16-standard",
        "name_th": "iPhone 16",
        "name_en": "iPhone 16",
        "screen_size": '6.1"',
        "dimensions_mm": "147.6 x 71.6 x 7.80 มม.",
        "weight_grams": "170 กรัม",
        "chip_specs": "ชิป A18 พร้อม CPU แบบ 6-core (2 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 5-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.1 นิ้ว (แนวทแยง), ความละเอียด 2556 x 1179 พิกเซลที่ 460 ppi, ความสว่างสูงสุด 2,000 นิต (กลางแจ้ง), Dynamic Island, คอนทราสต์เรโช 2,000,000:1",
        "camera_specs": "ระบบกล้องคู่ขั้นสูง: กล้อง Fusion 48MP (26 มม., ƒ/1.6, ระบบ OIS แบบเลื่อนเซ็นเซอร์) + กล้อง Ultra Wide 12MP (13 มม., ƒ/2.2, มุมมอง 120°), ภาพถ่ายความละเอียดสูงพิเศษ (24MP และ 48MP), ปุ่มควบคุมกล้อง (Camera Control)",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 22 ชั่วโมง, การเล่นเสียงนานสูงสุด 80 ชั่วโมง, รองรับการชาร์จเร็วสูงสุด 50% ใน 30 นาที ด้วยอะแดปเตอร์ 20W หรือสูงกว่า",
        "box_contents": "iPhone 16 พร้อม iOS 18, สายชาร์จ USB-C (1 ม., รองรับ 60W), เอกสารประกอบ",
        "connectivity": "5G (sub-6 GHz), Wi-Fi 7 (802.11be), Bluetooth 5.3, ชิป Ultra Wideband รุ่นที่ 2, พอร์ต USB-C รองรับ USB 2",
        "material": "กระจกแต่งสีด้านหลังและกรอบอะลูมิเนียมเกรดเดียวกับที่ใช้ในอุตสาหกรรมอวกาศ, ด้านหน้าแบบ Ceramic Shield รุ่นล่าสุด",
        "starting_price_thb": 29900,
        "capacities_prices": {
            "128GB": 29900,
            "256GB": 33900,
            "512GB": 41900
        },
        "colors": [
            {"id": "ultramarine", "th": "น้ำเงินอัลตร้ามารีน", "en": "Ultramarine", "hex": "#4D5E8C"},
            {"id": "teal", "th": "เขียวอมฟ้า", "en": "Teal", "hex": "#84A8A3"},
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "white", "th": "ขาว", "en": "White", "hex": "#F9F6EF"},
            {"id": "black", "th": "ดำ", "en": "Black", "hex": "#1F2022"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-16/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16",
        "overview_url": "https://www.apple.com/th/iphone-16/"
    },
    "iphone-16-plus": {
        "family_id": "iphone-16",
        "category_id": "iphone",
        "family_name": "iPhone 16",
        "sub_model_id": "iphone-16-plus",
        "name_th": "iPhone 16 Plus",
        "name_en": "iPhone 16 Plus",
        "screen_size": '6.7"',
        "dimensions_mm": "160.9 x 77.8 x 7.80 มม.",
        "weight_grams": "199 กรัม",
        "chip_specs": "ชิป A18 พร้อม CPU แบบ 6-core (2 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 5-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.7 นิ้ว (แนวทแยง), ความละเอียด 2796 x 1290 พิกเซลที่ 460 ppi, ความสว่างสูงสุด 2,000 นิต (กลางแจ้ง), Dynamic Island, คอนทราสต์เรโช 2,000,000:1",
        "camera_specs": "ระบบกล้องคู่ขั้นสูง: กล้อง Fusion 48MP (26 มม., ƒ/1.6) + กล้อง Ultra Wide 12MP (13 มม., ƒ/2.2), รองรับภาพถ่ายมาโคร, ปุ่มควบคุมกล้อง (Camera Control)",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 27 ชั่วโมง, การเล่นเสียงนานสูงสุด 100 ชั่วโมง, รองรับการชาร์จเร็วสูงสุด 50% ใน 30 นาที",
        "box_contents": "iPhone 16 Plus พร้อม iOS 18, สายชาร์จ USB-C (1 ม.), เอกสารประกอบ",
        "connectivity": "5G (sub-6 GHz), Wi-Fi 7, Bluetooth 5.3, ชิป Ultra Wideband รุ่นที่ 2, พอร์ต USB-C",
        "material": "กระจกแต่งสีด้านหลังและกรอบอะลูมิเนียมเกรดเดียวกับที่ใช้ในอุตสาหกรรมอวกาศ, ด้านหน้าแบบ Ceramic Shield รุ่นล่าสุด",
        "starting_price_thb": 34900,
        "capacities_prices": {
            "128GB": 34900,
            "256GB": 38900,
            "512GB": 46900
        },
        "colors": [
            {"id": "ultramarine", "th": "น้ำเงินอัลตร้ามารีน", "en": "Ultramarine", "hex": "#4D5E8C"},
            {"id": "teal", "th": "เขียวอมฟ้า", "en": "Teal", "hex": "#84A8A3"},
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "white", "th": "ขาว", "en": "White", "hex": "#F9F6EF"},
            {"id": "black", "th": "ดำ", "en": "Black", "hex": "#1F2022"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-16/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16",
        "overview_url": "https://www.apple.com/th/iphone-16/"
    },

    # =========================================================================
    # iPhone 16 Pro Family
    # =========================================================================
    "iphone-16-pro": {
        "family_id": "iphone-16-pro",
        "category_id": "iphone",
        "family_name": "iPhone 16 Pro",
        "sub_model_id": "iphone-16-pro",
        "name_th": "iPhone 16 Pro",
        "name_en": "iPhone 16 Pro",
        "screen_size": '6.3"',
        "dimensions_mm": "149.6 x 71.5 x 8.25 มม.",
        "weight_grams": "199 กรัม",
        "chip_specs": "ชิป A18 Pro พร้อม CPU แบบ 6-core (2 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 6-core ระดับโปร และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.3 นิ้ว, เทคโนโลยี ProMotion อัตรารีเฟรชสูงสุด 120Hz, ความละเอียด 2622 x 1206 พิกเซลที่ 460 ppi, จอภาพติดตลอด (Always-On)",
        "camera_specs": "ระบบกล้องระดับโปร: กล้อง Fusion 48MP (24 มม., ƒ/1.78) + กล้อง Ultra Wide 48MP (13 มม., ƒ/2.2) + กล้อง Telephoto 5x 12MP (120 มม., ƒ/2.8), สแกนเนอร์ LiDAR, บันทึกวิดีโอ 4K Dolby Vision 120 fps, ปุ่มควบคุมกล้อง (Camera Control)",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 27 ชั่วโมง, การเล่นสตรีมวิดีโอนานสูงสุด 22 ชั่วโมง, ชาร์จเร็ว 50% ใน 30 นาที",
        "box_contents": "iPhone 16 Pro พร้อม iOS 18, สายชาร์จ USB-C (1 ม., รองรับ USB 3), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 7, Bluetooth 5.3, Ultra Wideband 2, Thread, พอร์ต USB-C รองรับ USB 3 (สูงสุด 10Gb/s)",
        "material": "ดีไซน์ไทเทเนียมเกรด 5 ผิวขัดเงาละเอียด ด้านหลังกระจกผิวด้านแบบมีสีในตัว ด้านหน้า Ceramic Shield รุ่นล่าสุด",
        "starting_price_thb": 39900,
        "capacities_prices": {
            "128GB": 39900,
            "256GB": 43900,
            "512GB": 51900,
            "1TB": 59900
        },
        "colors": [
            {"id": "desert-titanium", "th": "ไทเทเนียมทะเลทราย", "en": "Desert Titanium", "hex": "#C5A992"},
            {"id": "natural-titanium", "th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
            {"id": "white-titanium", "th": "ไทเทเนียมขาว", "en": "White Titanium", "hex": "#E2E4E1"},
            {"id": "black-titanium", "th": "ไทเทเนียมดำ", "en": "Black Titanium", "hex": "#3A393E"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-16-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16-pro",
        "overview_url": "https://www.apple.com/th/iphone-16-pro/"
    },
    "iphone-16-pro-max": {
        "family_id": "iphone-16-pro",
        "category_id": "iphone",
        "family_name": "iPhone 16 Pro",
        "sub_model_id": "iphone-16-pro-max",
        "name_th": "iPhone 16 Pro Max",
        "name_en": "iPhone 16 Pro Max",
        "screen_size": '6.9"',
        "dimensions_mm": "163.0 x 77.6 x 8.25 มม.",
        "weight_grams": "227 กรัม",
        "chip_specs": "ชิป A18 Pro พร้อม CPU แบบ 6-core (2 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 6-core ระดับโปร และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.9 นิ้ว, เทคโนโลยี ProMotion อัตรารีเฟรช 1-120Hz, ความละเอียด 2868 x 1320 พิกเซลที่ 460 ppi, จอภาพติดตลอด (Always-On)",
        "camera_specs": "ระบบกล้องระดับโปร: กล้อง Fusion 48MP + กล้อง Ultra Wide 48MP + กล้อง Telephoto 5x 12MP (120 มม., ดีไซน์เตตร้าปริซึม), ซูมแบบออปติคัล 5 เท่า, สแกนเนอร์ LiDAR, ปุ่มควบคุมกล้อง (Camera Control)",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 33 ชั่วโมง (แบตเตอรี่อึดที่สุดในประวัติศาสตร์ iPhone), การเล่นเสียงนานสูงสุด 105 ชั่วโมง",
        "box_contents": "iPhone 16 Pro Max พร้อม iOS 18, สายชาร์จ USB-C (1 ม., รองรับ USB 3), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 7, Bluetooth 5.3, Ultra Wideband 2, Thread, พอร์ต USB-C รองรับ USB 3 (สูงสุด 10Gb/s)",
        "material": "ดีไซน์ไทเทเนียมเกรด 5 ผิวขัดเงา ด้านหลังกระจกผิวด้านแบบมีสีในตัว ด้านหน้า Ceramic Shield",
        "starting_price_thb": 48900,
        "capacities_prices": {
            "256GB": 48900,
            "512GB": 56900,
            "1TB": 64900
        },
        "colors": [
            {"id": "desert-titanium", "th": "ไทเทเนียมทะเลทราย", "en": "Desert Titanium", "hex": "#C5A992"},
            {"id": "natural-titanium", "th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
            {"id": "white-titanium", "th": "ไทเทเนียมขาว", "en": "White Titanium", "hex": "#E2E4E1"},
            {"id": "black-titanium", "th": "ไทเทเนียมดำ", "en": "Black Titanium", "hex": "#3A393E"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-16-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-16-pro",
        "overview_url": "https://www.apple.com/th/iphone-16-pro/"
    },

    # =========================================================================
    # iPhone 15 & 14 Series
    # =========================================================================
    "iphone-15": {
        "family_id": "iphone-15",
        "category_id": "iphone",
        "family_name": "iPhone 15",
        "sub_model_id": "iphone-15",
        "name_th": "iPhone 15",
        "name_en": "iPhone 15",
        "screen_size": '6.1"',
        "dimensions_mm": "147.6 x 71.6 x 7.80 มม.",
        "weight_grams": "171 กรัม",
        "chip_specs": "ชิป A16 Bionic พร้อม CPU แบบ 6-core (2 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 5-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.1 นิ้ว, ความละเอียด 2556 x 1179 พิกเซลที่ 460 ppi, Dynamic Island, ความสว่างสูงสุด 2,000 นิต (กลางแจ้ง)",
        "camera_specs": "ระบบกล้องคู่ขั้นสูง: กล้องหลัก 48MP (26 มม., ƒ/1.6) + กล้อง Ultra Wide 12MP (13 มม., ƒ/2.4), ถ่ายภาพบุคคลรุ่นถัดไปพร้อมการควบคุมโฟกัสและความชัดลึก",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 20 ชั่วโมง, การเล่นเสียงนานสูงสุด 80 ชั่วโมง, ชาร์จเร็ว 50% ใน 30 นาที",
        "box_contents": "iPhone 15 พร้อม iOS, สายชาร์จ USB-C (1 ม.), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 6, Bluetooth 5.3, ชิป Ultra Wideband รุ่นที่ 2, พอร์ต USB-C",
        "material": "ด้านหลังแบบกระจกแต่งสี และดีไซน์อะลูมิเนียม ด้านหน้า Ceramic Shield",
        "starting_price_thb": 26900,
        "capacities_prices": {
            "128GB": 26900,
            "256GB": 30900,
            "512GB": 38900
        },
        "colors": [
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "yellow", "th": "เหลือง", "en": "Yellow", "hex": "#FBE27D"},
            {"id": "green", "th": "เขียว", "en": "Green", "hex": "#43594B"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "black", "th": "ดำ", "en": "Black", "hex": "#1F2022"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-15/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-15",
        "overview_url": "https://www.apple.com/th/iphone-15/"
    },
    "iphone-15-plus": {
        "family_id": "iphone-15",
        "category_id": "iphone",
        "family_name": "iPhone 15",
        "sub_model_id": "iphone-15-plus",
        "name_th": "iPhone 15 Plus",
        "name_en": "iPhone 15 Plus",
        "screen_size": '6.7"',
        "dimensions_mm": "160.9 x 77.8 x 7.80 มม.",
        "weight_grams": "201 กรัม",
        "chip_specs": "ชิป A16 Bionic พร้อม CPU แบบ 6-core, GPU แบบ 5-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.7 นิ้ว, ความละเอียด 2796 x 1290 พิกเซลที่ 460 ppi, Dynamic Island",
        "camera_specs": "ระบบกล้องคู่: กล้องหลัก 48MP + กล้อง Ultra Wide 12MP, ซูมแบบออปติคัล 2 เท่า",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 26 ชั่วโมง, การเล่นเสียงนานสูงสุด 100 ชั่วโมง",
        "box_contents": "iPhone 15 Plus พร้อม iOS, สายชาร์จ USB-C (1 ม.), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 6, Bluetooth 5.3, Ultra Wideband 2, USB-C",
        "material": "กระจกแต่งสีด้านหลังและกรอบอะลูมิเนียม",
        "starting_price_thb": 29900,
        "capacities_prices": {
            "128GB": 29900,
            "256GB": 33900,
            "512GB": 41900
        },
        "colors": [
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "yellow", "th": "เหลือง", "en": "Yellow", "hex": "#FBE27D"},
            {"id": "green", "th": "เขียว", "en": "Green", "hex": "#43594B"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "black", "th": "ดำ", "en": "Black", "hex": "#1F2022"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-15/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-15",
        "overview_url": "https://www.apple.com/th/iphone-15/"
    },
    "iphone-14": {
        "family_id": "iphone-14",
        "category_id": "iphone",
        "family_name": "iPhone 14",
        "sub_model_id": "iphone-14",
        "name_th": "iPhone 14",
        "name_en": "iPhone 14",
        "screen_size": '6.1"',
        "dimensions_mm": "146.7 x 71.5 x 7.80 มม.",
        "weight_grams": "172 กรัม",
        "chip_specs": "ชิป A15 Bionic พร้อม CPU แบบ 6-core, GPU แบบ 5-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Super Retina XDR OLED ขนาด 6.1 นิ้ว, ความละเอียด 2532 x 1170 พิกเซลที่ 460 ppi",
        "camera_specs": "ระบบกล้องคู่: กล้องหลัก 12MP (26 มม., ƒ/1.5) + กล้อง Ultra Wide 12MP (13 มม., ƒ/2.4), โหมดแอ็คชั่นและโหมดภาพยนตร์",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 20 ชั่วโมง, ชาร์จเร็ว 50% ใน 30 นาที",
        "box_contents": "iPhone 14 พร้อม iOS, สาย USB-C เป็น Lightning (1 ม.), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 6, Bluetooth 5.3, พอร์ต Lightning",
        "material": "ด้านหน้าแบบ Ceramic Shield, ด้านหลังแบบกระจก และอะลูมิเนียม",
        "starting_price_thb": 22900,
        "capacities_prices": {
            "128GB": 22900,
            "256GB": 26900
        },
        "colors": [
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "purple", "th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
            {"id": "midnight", "th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-14/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-14",
        "overview_url": "https://www.apple.com/th/iphone-14/"
    },
    "iphone-se": {
        "family_id": "iphone-se",
        "category_id": "iphone",
        "family_name": "iPhone SE",
        "sub_model_id": "iphone-se-3",
        "name_th": "iPhone SE (รุ่นที่ 3)",
        "name_en": "iPhone SE (3rd Gen)",
        "screen_size": '4.7"',
        "dimensions_mm": "138.4 x 67.3 x 7.3 มม.",
        "weight_grams": "144 กรัม",
        "chip_specs": "ชิป A15 Bionic พร้อม CPU แบบ 6-core, GPU แบบ 4-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Retina HD LCD ขนาด 4.7 นิ้ว, ความละเอียด 1334 x 750 พิกเซลที่ 326 ppi, ปุ่มโฮมพร้อม Touch ID",
        "camera_specs": "กล้องไวด์ 12MP (ƒ/1.8), HDR อัจฉริยะ 4, วิดีโอ 4K สูงสุด 60 fps",
        "battery_specs": "การเล่นวิดีโอนานสูงสุด 15 ชั่วโมง, ชาร์จเร็ว 50% ใน 30 นาที",
        "box_contents": "iPhone SE พร้อม iOS, สาย USB-C เป็น Lightning (1 ม.), เอกสารประกอบ",
        "connectivity": "5G, Wi-Fi 6, Bluetooth 5.0, พอร์ต Lightning",
        "material": "ดีไซน์กระจกและอะลูมิเนียม",
        "starting_price_thb": 17900,
        "capacities_prices": {
            "64GB": 17900,
            "128GB": 19900,
            "256GB": 23900
        },
        "colors": [
            {"id": "midnight", "th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"},
            {"id": "red", "th": "แดง", "en": "Red", "hex": "#E11C2A"}
        ],
        "specs_url": "https://www.apple.com/th/iphone-se/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-iphone/iphone-se",
        "overview_url": "https://www.apple.com/th/iphone-se/"
    },

    # =========================================================================
    # iPad Pro Family (M4)
    # =========================================================================
    "ipad-pro-11": {
        "family_id": "ipad-pro",
        "category_id": "ipad",
        "family_name": "iPad Pro (M4)",
        "sub_model_id": "ipad-pro-11-m4",
        "name_th": "iPad Pro รุ่น 11 นิ้ว (M4)",
        "name_en": "iPad Pro 11-inch (M4)",
        "screen_size": '11"',
        "dimensions_mm": "249.7 x 177.5 x 5.3 มม.",
        "weight_grams": "444 กรัม (Wi-Fi) / 446 กรัม (Cellular)",
        "chip_specs": "ชิป M4 พร้อม CPU สูงสุดแบบ 10-core, GPU แบบ 10-core รองรับ Ray Tracing ด้วยฮาร์ดแวร์ และ Neural Engine แบบ 16-core (38 ล้านล้านคำสั่งต่อวินาที)",
        "display_specs": "จอภาพ Ultra Retina XDR เทคโนโลยี Tandem OLED สองชั้น, ความละเอียด 2420 x 1668 พิกเซลที่ 264 ppi, ProMotion 10-120Hz, ความสว่างเต็มหน้าจอ 1,000 นิต (XDR สูงสุด 1,600 นิต), ตัวเลือกกระจก Nano-texture สำหรับรุ่น 1TB/2TB",
        "camera_specs": "กล้องไวด์ 12MP (ƒ/1.8), ซูมดิจิทัล 5x, แฟลช True Tone แบบปรับตามสภาวะ, สแกนเนอร์ LiDAR, กล้องหน้าแนวนอน Ultra Wide 12MP พร้อมคุณสมบัติจัดให้อยู่ตรงกลาง (Center Stage)",
        "battery_specs": "ท่องเว็บผ่าน Wi-Fi หรือดูวิดีโอนานสูงสุด 10 ชั่วโมง, ชาร์จผ่านอะแดปเตอร์แปลงไฟหรือ USB-C เข้ากับระบบคอมพิวเตอร์",
        "box_contents": "iPad Pro 11 นิ้ว, สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C ขนาด 20W, ผ้าเช็ดหน้าจอ (เฉพาะรุ่นกระจก Nano-texture)",
        "connectivity": "Thunderbolt / USB 4 (สูงสุด 40Gb/s), Wi-Fi 6E (802.11ax), Bluetooth 5.3, ตัวเลือก 5G (eSIM)",
        "material": "ตัวเครื่องอะลูมิเนียมรีไซเคิล 100% ดีไซน์บางเฉียบที่สุดเท่าที่ Apple เคยสร้างมาเพียง 5.3 มม.",
        "starting_price_thb": 39900,
        "capacities_prices": {
            "256GB (Wi-Fi)": 39900,
            "512GB (Wi-Fi)": 47900,
            "1TB (Wi-Fi)": 63900,
            "2TB (Wi-Fi)": 79900,
            "256GB (Cellular)": 47900,
            "512GB (Cellular)": 55900,
            "1TB (Cellular)": 71900,
            "2TB (Cellular)": 87900
        },
        "colors": [
            {"id": "space-black", "th": "ดำสเปซแบล็ค", "en": "Space Black", "hex": "#2E2C2F"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-pro",
        "overview_url": "https://www.apple.com/th/ipad-pro/"
    },
    "ipad-pro-13": {
        "family_id": "ipad-pro",
        "category_id": "ipad",
        "family_name": "iPad Pro (M4)",
        "sub_model_id": "ipad-pro-13-m4",
        "name_th": "iPad Pro รุ่น 13 นิ้ว (M4)",
        "name_en": "iPad Pro 13-inch (M4)",
        "screen_size": '13"',
        "dimensions_mm": "281.6 x 215.5 x 5.1 มม.",
        "weight_grams": "579 กรัม (Wi-Fi) / 582 กรัม (Cellular)",
        "chip_specs": "ชิป M4 พร้อม CPU สูงสุดแบบ 10-core, GPU แบบ 10-core รองรับ Ray Tracing และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Ultra Retina XDR Tandem OLED ขนาด 13 นิ้ว, ความละเอียด 2752 x 2064 พิกเซลที่ 264 ppi, ProMotion 10-120Hz, ความสว่าง XDR สูงสุด 1,600 นิต, บางเฉียบที่สุดในประวัติศาสตร์ Apple เพียง 5.1 มม.",
        "camera_specs": "กล้องไวด์ 12MP + LiDAR + กล้องหน้า Ultra Wide แนวนอน 12MP รองรับ Center Stage",
        "battery_specs": "ท่องเว็บผ่าน Wi-Fi หรือดูวิดีโอนานสูงสุด 10 ชั่วโมง",
        "box_contents": "iPad Pro 13 นิ้ว, สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C 20W, ผ้าเช็ดหน้าจอ (สำหรับกระจก Nano-texture)",
        "connectivity": "Thunderbolt / USB 4, Wi-Fi 6E, Bluetooth 5.3, ตัวเลือก 5G (eSIM)",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100% บางที่สุดเพียง 5.1 มม.",
        "starting_price_thb": 52900,
        "capacities_prices": {
            "256GB (Wi-Fi)": 52900,
            "512GB (Wi-Fi)": 60900,
            "1TB (Wi-Fi)": 76900,
            "2TB (Wi-Fi)": 92900,
            "256GB (Cellular)": 60900,
            "512GB (Cellular)": 68900,
            "1TB (Cellular)": 84900,
            "2TB (Cellular)": 100900
        },
        "colors": [
            {"id": "space-black", "th": "ดำสเปซแบล็ค", "en": "Space Black", "hex": "#2E2C2F"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-pro",
        "overview_url": "https://www.apple.com/th/ipad-pro/"
    },

    # =========================================================================
    # iPad Air Family (M2) & iPad 10th & mini
    # =========================================================================
    "ipad-air-11": {
        "family_id": "ipad-air",
        "category_id": "ipad",
        "family_name": "iPad Air (M2)",
        "sub_model_id": "ipad-air-11-m2",
        "name_th": "iPad Air รุ่น 11 นิ้ว (M2)",
        "name_en": "iPad Air 11-inch (M2)",
        "screen_size": '11"',
        "dimensions_mm": "247.6 x 178.5 x 6.1 มม.",
        "weight_grams": "462 กรัม (Wi-Fi) / 464 กรัม (Cellular)",
        "chip_specs": "ชิป M2 พร้อม CPU แบบ 8-core (4 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU แบบ 9-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Liquid Retina LED ขนาด 11 นิ้ว, ความละเอียด 2360 x 1640 พิกเซลที่ 264 ppi, แสดงผลแบบ True Tone, ขอบเขตสีกว้าง P3, ความสว่าง 500 นิต",
        "camera_specs": "กล้องหลังไวด์ 12MP (ƒ/1.8) + กล้องหน้าแนวนอน Ultra Wide 12MP รองรับ Center Stage",
        "battery_specs": "ท่องเว็บผ่าน Wi-Fi หรือดูวิดีโอนานสูงสุด 10 ชั่วโมง",
        "box_contents": "iPad Air 11 นิ้ว, สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C 20W",
        "connectivity": "พอร์ต USB-C รองรับ USB 3 (สูงสุด 10Gb/s), Wi-Fi 6E, Bluetooth 5.3, ตัวเลือก 5G",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100%",
        "starting_price_thb": 23900,
        "capacities_prices": {
            "128GB": 23900,
            "256GB": 27900,
            "512GB": 35900,
            "1TB": 43900
        },
        "colors": [
            {"id": "space-gray", "th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "purple", "th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-air/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-air",
        "overview_url": "https://www.apple.com/th/ipad-air/"
    },
    "ipad-air-13": {
        "family_id": "ipad-air",
        "category_id": "ipad",
        "family_name": "iPad Air (M2)",
        "sub_model_id": "ipad-air-13-m2",
        "name_th": "iPad Air รุ่น 13 นิ้ว (M2)",
        "name_en": "iPad Air 13-inch (M2)",
        "screen_size": '13"',
        "dimensions_mm": "280.6 x 214.9 x 6.1 มม.",
        "weight_grams": "617 กรัม (Wi-Fi) / 618 กรัม (Cellular)",
        "chip_specs": "ชิป M2 พร้อม CPU แบบ 8-core, GPU แบบ 9-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Liquid Retina LED ขนาด 13 นิ้ว, ความละเอียด 2732 x 2048 พิกเซลที่ 264 ppi, ความสว่าง 600 นิต",
        "camera_specs": "กล้องหลังไวด์ 12MP + กล้องหน้าแนวนอน Ultra Wide 12MP",
        "battery_specs": "ท่องเว็บหรือดูวิดีโอนานสูงสุด 10 ชั่วโมง",
        "box_contents": "iPad Air 13 นิ้ว, สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C 20W",
        "connectivity": "USB-C (USB 3), Wi-Fi 6E, Bluetooth 5.3, ตัวเลือก 5G",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100%",
        "starting_price_thb": 29900,
        "capacities_prices": {
            "128GB": 29900,
            "256GB": 33900,
            "512GB": 41900,
            "1TB": 49900
        },
        "colors": [
            {"id": "space-gray", "th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "purple", "th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-air/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-air",
        "overview_url": "https://www.apple.com/th/ipad-air/"
    },
    "ipad-10th-gen": {
        "family_id": "ipad-10th-gen",
        "category_id": "ipad",
        "family_name": "iPad (รุ่นที่ 10)",
        "sub_model_id": "ipad-10th-gen",
        "name_th": "iPad (รุ่นที่ 10)",
        "name_en": "iPad (10th Gen)",
        "screen_size": '10.9"',
        "dimensions_mm": "248.6 x 179.5 x 7.0 มม.",
        "weight_grams": "477 กรัม (Wi-Fi) / 481 กรัม (Cellular)",
        "chip_specs": "ชิป A14 Bionic พร้อม CPU แบบ 6-core, GPU แบบ 4-core และ Neural Engine แบบ 16-core",
        "display_specs": "จอภาพ Liquid Retina ขนาด 10.9 นิ้ว, ความละเอียด 2360 x 1640 พิกเซลที่ 264 ppi, ความสว่าง 500 นิต, True Tone",
        "camera_specs": "กล้องไวด์ 12MP (ƒ/1.8) + กล้องหน้าแนวนอน Ultra Wide 12MP พร้อม Center Stage",
        "battery_specs": "ดูวิดีโอนานสูงสุด 10 ชั่วโมง",
        "box_contents": "iPad (รุ่นที่ 10), สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C 20W",
        "connectivity": "USB-C, Wi-Fi 6, Bluetooth 5.2, ตัวเลือก 5G",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100%",
        "starting_price_thb": 12900,
        "capacities_prices": {
            "64GB (Wi-Fi)": 12900,
            "256GB (Wi-Fi)": 17900,
            "64GB (Cellular)": 18900,
            "256GB (Cellular)": 23900
        },
        "colors": [
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "yellow", "th": "เหลือง", "en": "Yellow", "hex": "#FBE27D"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-10.9/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad",
        "overview_url": "https://www.apple.com/th/ipad-10.9/"
    },
    "ipad-mini": {
        "family_id": "ipad-mini",
        "category_id": "ipad",
        "family_name": "iPad mini",
        "sub_model_id": "ipad-mini-a17",
        "name_th": "iPad mini (A17 Pro)",
        "name_en": "iPad mini (A17 Pro)",
        "screen_size": '8.3"',
        "dimensions_mm": "195.4 x 134.8 x 6.3 มม.",
        "weight_grams": "293 กรัม (Wi-Fi) / 297 กรัม (Cellular)",
        "chip_specs": "ชิป A17 Pro พร้อม CPU แบบ 6-core, GPU แบบ 5-core รองรับ Ray Tracing และ Neural Engine แบบ 16-core ออกแบบมาเพื่อ Apple Intelligence",
        "display_specs": "จอภาพ Liquid Retina ขนาด 8.3 นิ้ว, ความละเอียด 2266 x 1488 พิกเซลที่ 326 ppi, ความสว่าง 500 นิต, รองรับ Apple Pencil Pro",
        "camera_specs": "กล้องหลังไวด์ 12MP (ƒ/1.8) + กล้องหน้า Ultra Wide 12MP",
        "battery_specs": "ดูวิดีโอนานสูงสุด 10 ชั่วโมง",
        "box_contents": "iPad mini, สายชาร์จ USB-C (1 ม.), อะแดปเตอร์แปลงไฟ USB-C 20W",
        "connectivity": "USB-C (USB 3 สูงสุด 10Gb/s), Wi-Fi 6E, Bluetooth 5.3, ตัวเลือก 5G (eSIM)",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100%",
        "starting_price_thb": 17900,
        "capacities_prices": {
            "128GB (Wi-Fi)": 17900,
            "256GB (Wi-Fi)": 21900,
            "512GB (Wi-Fi)": 29900,
            "128GB (Cellular)": 23900,
            "256GB (Cellular)": 27900,
            "512GB (Cellular)": 35900
        },
        "colors": [
            {"id": "space-gray", "th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "purple", "th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"}
        ],
        "specs_url": "https://www.apple.com/th/ipad-mini/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-ipad/ipad-mini",
        "overview_url": "https://www.apple.com/th/ipad-mini/"
    },

    # =========================================================================
    # Mac Family (MacBook Pro, MacBook Air, iMac, Mac mini, Mac Studio)
    # =========================================================================
    "macbook-pro-14": {
        "family_id": "macbook-pro",
        "category_id": "mac",
        "family_name": "MacBook Pro",
        "sub_model_id": "macbook-pro-14",
        "name_th": "MacBook Pro 14 นิ้ว (M4 / M4 Pro / M4 Max)",
        "name_en": "MacBook Pro 14-inch (M4 / M4 Pro / M4 Max)",
        "screen_size": '14.2"',
        "dimensions_mm": "312.6 x 221.2 x 15.5 มม.",
        "weight_grams": "1,550 กรัม (M4) / 1,600 กรัม (M4 Pro/Max)",
        "chip_specs": "ชิป M4 (CPU 10-core, GPU 10-core) หรือ M4 Pro (CPU สูงสุด 14-core, GPU สูงสุด 20-core) หรือ M4 Max (CPU สูงสุด 16-core, GPU สูงสุด 40-core)",
        "display_specs": "จอภาพ Liquid Retina XDR ขนาด 14.2 นิ้ว, ความละเอียด 3024 x 1964 พิกเซลที่ 254 ppi, ProMotion 120Hz, ความสว่าง SDR สูงสุด 1,000 นิต, XDR สูงสุด 1,600 นิต, ตัวเลือกกระจก Nano-texture",
        "camera_specs": "กล้อง 12MP Center Stage รองรับ Desk View และวิดีโอ 1080p HD, ระบบเสียง 6 ลำโพงพร้อมวูฟเฟอร์ตัดแรงสั่นสะเทือน",
        "battery_specs": "เล่นวิดีโอนานสูงสุด 24 ชั่วโมง (M4) / สูงสุด 22 ชั่วโมง (M4 Pro/Max), ท่องเว็บแบบไร้สายสูงสุด 16 ชั่วโมง, ชาร์จเร็วผ่านอะแดปเตอร์ 70W หรือ 96W",
        "box_contents": "MacBook Pro 14 นิ้ว, สาย USB-C เป็น MagSafe 3 (2 ม.), อะแดปเตอร์แปลงไฟ USB-C ขนาด 70W (สำหรับ M4) หรือ 96W (สำหรับ M4 Pro)",
        "connectivity": "พอร์ต Thunderbolt 4 (M4) หรือ Thunderbolt 5 สูงสุด 120Gb/s (M4 Pro/Max) จำนวน 3 พอร์ต, ช่องเสียบการ์ด SDXC, พอร์ต HDMI รองรับ 8K, ช่องต่อหูฟัง 3.5 มม., พอร์ต MagSafe 3, Wi-Fi 6E, Bluetooth 5.3",
        "material": "ตัวเครื่องอะลูมิเนียมชิ้นเดียว (Unibody) รีไซเคิล 100% พร้อมระบบระบายความร้อนอันล้ำสมัย",
        "starting_price_thb": 54900,
        "capacities_prices": {
            "M4 (16GB / 512GB)": 54900,
            "M4 (16GB / 1TB)": 61900,
            "M4 (24GB / 1TB)": 68900,
            "M4 Pro (24GB / 512GB)": 69900,
            "M4 Pro (24GB / 1TB)": 76900,
            "M4 Max (36GB / 1TB)": 112900
        },
        "colors": [
            {"id": "space-black", "th": "ดำสเปซแบล็ค", "en": "Space Black", "hex": "#2E2C2F"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/macbook-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-pro",
        "overview_url": "https://www.apple.com/th/macbook-pro/"
    },
    "macbook-pro-16": {
        "family_id": "macbook-pro",
        "category_id": "mac",
        "family_name": "MacBook Pro",
        "sub_model_id": "macbook-pro-16",
        "name_th": "MacBook Pro 16 นิ้ว (M4 Pro / M4 Max)",
        "name_en": "MacBook Pro 16-inch (M4 Pro / M4 Max)",
        "screen_size": '16.2"',
        "dimensions_mm": "355.7 x 248.1 x 16.8 มม.",
        "weight_grams": "2,140 กรัม (M4 Pro) / 2,150 กรัม (M4 Max)",
        "chip_specs": "ชิป M4 Pro หรือ M4 Max ระดับสุดยอดโปร สำหรับเวิร์กโฟลว์ระดับภาพยนตร์และ AI ขั้นสูง",
        "display_specs": "จอภาพ Liquid Retina XDR ขนาด 16.2 นิ้ว, ความละเอียด 3456 x 2234 พิกเซลที่ 254 ppi, ProMotion 120Hz, ความสว่าง XDR 1,600 นิต, ตัวเลือกกระจก Nano-texture",
        "camera_specs": "กล้อง 12MP Center Stage พร้อม Desk View, ระบบเสียง 6 ลำโพงความเที่ยงตรงสูงระดับสตูดิโอ",
        "battery_specs": "เล่นวิดีโอนานสูงสุด 24 ชั่วโมง (แบตเตอรี่ที่ยาวนานที่สุดใน Mac ทุกรุ่น), รองรับอะแดปเตอร์แปลงไฟ USB-C 140W",
        "box_contents": "MacBook Pro 16 นิ้ว, สาย USB-C เป็น MagSafe 3 (2 ม.), อะแดปเตอร์แปลงไฟ USB-C 140W",
        "connectivity": "Thunderbolt 5 (สูงสุด 120Gb/s) x 3, ช่องเสียบการ์ด SDXC, พอร์ต HDMI 8K, MagSafe 3, Wi-Fi 6E",
        "material": "ตัวเรือนอะลูมิเนียม Unibody พร้อมชั้นอะโนไดซ์ลดรอยนิ้วมือ",
        "starting_price_thb": 89900,
        "capacities_prices": {
            "M4 Pro (24GB / 512GB)": 89900,
            "M4 Pro (48GB / 512GB)": 103900,
            "M4 Max (36GB / 1TB)": 124900,
            "M4 Max (48GB / 1TB)": 138900
        },
        "colors": [
            {"id": "space-black", "th": "ดำสเปซแบล็ค", "en": "Space Black", "hex": "#2E2C2F"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/macbook-pro/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-pro",
        "overview_url": "https://www.apple.com/th/macbook-pro/"
    },
    "macbook-air-13": {
        "family_id": "macbook-air",
        "category_id": "mac",
        "family_name": "MacBook Air",
        "sub_model_id": "macbook-air-13",
        "name_th": "MacBook Air 13 นิ้ว (M3)",
        "name_en": "MacBook Air 13-inch (M3)",
        "screen_size": '13.6"',
        "dimensions_mm": "304.1 x 215.0 x 11.3 มม.",
        "weight_grams": "1,240 กรัม",
        "chip_specs": "ชิป M3 พร้อม CPU แบบ 8-core (4 ประสิทธิภาพ + 4 ประหยัดพลังงาน), GPU สูงสุด 10-core รองรับ Ray Tracing และ Neural Engine แบบ 16-core, หน่วยความจำเริ่มต้นมาตรฐาน 16GB",
        "display_specs": "จอภาพ Liquid Retina ขนาด 13.6 นิ้ว, ความละเอียด 2560 x 1664 พิกเซลที่ 224 ppi, ความสว่าง 500 นิต, ขอบเขตสีกว้าง P3, รองรับจอภาพภายนอกสูงสุด 2 จอ (เมื่อปิดฝาพับ)",
        "camera_specs": "กล้อง FaceTime HD 1080p, ระบบเสียง 4 ลำโพงพร้อมระบบเสียงตามตำแหน่ง Spatial Audio",
        "battery_specs": "เล่นวิดีโอนานสูงสุด 18 ชั่วโมง, ท่องเว็บไร้สายนานสูงสุด 15 ชั่วโมง",
        "box_contents": "MacBook Air 13 นิ้ว, สาย USB-C เป็น MagSafe 3 (2 ม.), อะแดปเตอร์แปลงไฟ USB-C ขนาด 30W หรือพอร์ตคู่ 35W",
        "connectivity": "พอร์ต MagSafe 3, พอร์ต Thunderbolt / USB 4 จำนวน 2 พอร์ต, ช่องต่อหูฟัง 3.5 มม., Wi-Fi 6E, Bluetooth 5.3",
        "material": "ตัวเรือนอะลูมิเนียมแบบไร้พัดลม เงียบสนิท 100% พร้อมการเคลือบผิวอะโนไดซ์ลดรอยนิ้วมือสำหรับสีมิดไนท์",
        "starting_price_thb": 39900,
        "capacities_prices": {
            "16GB / 256GB SSD": 39900,
            "16GB / 512GB SSD": 46900,
            "24GB / 512GB SSD": 53900
        },
        "colors": [
            {"id": "midnight", "th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"},
            {"id": "space-gray", "th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/macbook-air/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-air",
        "overview_url": "https://www.apple.com/th/macbook-air/"
    },
    "macbook-air-15": {
        "family_id": "macbook-air",
        "category_id": "mac",
        "family_name": "MacBook Air",
        "sub_model_id": "macbook-air-15",
        "name_th": "MacBook Air 15 นิ้ว (M3)",
        "name_en": "MacBook Air 15-inch (M3)",
        "screen_size": '15.3"',
        "dimensions_mm": "340.4 x 237.6 x 11.5 มม.",
        "weight_grams": "1,510 กรัม",
        "chip_specs": "ชิป M3 พร้อม CPU แบบ 8-core, GPU แบบ 10-core และ Neural Engine แบบ 16-core, หน่วยความจำเริ่มต้นมาตรฐาน 16GB",
        "display_specs": "จอภาพ Liquid Retina ขนาด 15.3 นิ้ว, ความละเอียด 2880 x 1864 พิกเซลที่ 224 ppi, ความสว่าง 500 นิต",
        "camera_specs": "กล้อง FaceTime HD 1080p, ระบบเสียง 6 ลำโพงพร้อมวูฟเฟอร์ตัดแรงสั่นสะเทือน",
        "battery_specs": "เล่นวิดีโอนานสูงสุด 18 ชั่วโมง",
        "box_contents": "MacBook Air 15 นิ้ว, สาย USB-C เป็น MagSafe 3 (2 ม.), อะแดปเตอร์แปลงไฟ USB-C ขนาดกะทัดรัดแบบพอร์ตคู่ 35W",
        "connectivity": "MagSafe 3, Thunderbolt / USB 4 x 2, ช่องต่อหูฟัง 3.5 มม., Wi-Fi 6E",
        "material": "ตัวเรือนอะลูมิเนียมบางเฉียบเพียง 11.5 มม. ทำงานเงียบสนิทไร้พัดลม",
        "starting_price_thb": 47900,
        "capacities_prices": {
            "16GB / 256GB SSD": 47900,
            "16GB / 512GB SSD": 54900,
            "24GB / 512GB SSD": 61900
        },
        "colors": [
            {"id": "midnight", "th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"},
            {"id": "space-gray", "th": "สเปซเกรย์", "en": "Space Gray", "hex": "#68696E"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/macbook-air/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/macbook-air",
        "overview_url": "https://www.apple.com/th/macbook-air/"
    },
    "imac": {
        "family_id": "imac",
        "category_id": "mac",
        "family_name": "iMac",
        "sub_model_id": "imac-24-m4",
        "name_th": "iMac 24 นิ้ว (M4)",
        "name_en": "iMac 24-inch (M4)",
        "screen_size": '24"',
        "dimensions_mm": "547 x 461 x 147 มม.",
        "weight_grams": "4,420 กรัม (รุ่น 2 พอร์ต) / 4,440 กรัม (รุ่น 4 พอร์ต)",
        "chip_specs": "ชิป M4 พร้อม CPU แบบ 8-core หรือ 10-core, GPU แบบ 8-core หรือ 10-core และ Neural Engine แบบ 16-core, หน่วยความจำเริ่มต้น 16GB",
        "display_specs": "จอภาพ 4.5K Retina ขนาด 24 นิ้ว, ความละเอียด 4480 x 2520 พิกเซลที่ 218 ppi, ความสว่าง 500 นิต, แสดงผลได้กว่า 1 พันล้านสี, มีตัวเลือกกระจก Nano-texture",
        "camera_specs": "กล้อง 12MP Center Stage รองรับ Desk View และวิดีโอ 1080p HD, ระบบเสียง 6 ลำโพงพร้อมระบบตัดเสียงสะท้อนระดับสตูดิโอ",
        "battery_specs": "ใช้ไฟกระแสสลับ 100-240V AC ผ่านอะแดปเตอร์แปลงไฟ 143W พร้อมพอร์ต Gigabit Ethernet",
        "box_contents": "iMac 24 นิ้ว, Magic Keyboard พร้อม Touch ID (ตามรุ่น), Magic Mouse, อะแดปเตอร์แปลงไฟ 143W, สายไฟ (2 ม.), สาย USB-C เป็น USB-C",
        "connectivity": "Thunderbolt 4 / USB 4 จำนวน 2 หรือ 4 พอร์ต, Gigabit Ethernet, ช่องต่อหูฟัง 3.5 มม., Wi-Fi 6E, Bluetooth 5.3",
        "material": "ดีไซน์บางเฉียบเพียง 11.5 มม. โครงสร้างอะลูมิเนียมชุบผิวหลากสีสันสดใส",
        "starting_price_thb": 44900,
        "capacities_prices": {
            "M4 8-core (16GB / 256GB 2 พอร์ต)": 44900,
            "M4 10-core (16GB / 256GB 4 พอร์ต)": 51900,
            "M4 10-core (16GB / 512GB 4 พอร์ต)": 58900,
            "M4 10-core (24GB / 512GB 4 พอร์ต)": 65900
        },
        "colors": [
            {"id": "blue", "th": "ฟ้า", "en": "Blue", "hex": "#3E536B"},
            {"id": "purple", "th": "ม่วง", "en": "Purple", "hex": "#D1CDDA"},
            {"id": "pink", "th": "ชมพู", "en": "Pink", "hex": "#E3A3B1"},
            {"id": "orange", "th": "ส้ม", "en": "Orange", "hex": "#E7643E"},
            {"id": "yellow", "th": "เหลือง", "en": "Yellow", "hex": "#FBE27D"},
            {"id": "green", "th": "เขียว", "en": "Green", "hex": "#43594B"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/imac/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/imac",
        "overview_url": "https://www.apple.com/th/imac/"
    },
    "mac-mini": {
        "family_id": "mac-mini",
        "category_id": "mac",
        "family_name": "Mac mini",
        "sub_model_id": "mac-mini-m4",
        "name_th": "Mac mini (M4 / M4 Pro)",
        "name_en": "Mac mini (M4 / M4 Pro)",
        "screen_size": "Desktop",
        "dimensions_mm": "127.0 x 127.0 x 50.0 มม.",
        "weight_grams": "670 กรัม (M4) / 730 กรัม (M4 Pro)",
        "chip_specs": "ชิป M4 (CPU 10-core, GPU 10-core) หรือชิป M4 Pro (CPU 12/14-core, GPU 16/20-core), หน่วยความจำเริ่มต้น 16GB (M4) หรือ 24GB (M4 Pro)",
        "display_specs": "รองรับจอภาพภายนอกสูงสุด 3 จอ (สูงสุดความละเอียด 8K 60Hz หรือ 4K 240Hz ผ่าน HDMI)",
        "camera_specs": "ไม่มีในตัว (รองรับ Continuity Camera ผ่าน iPhone หรือกล้องเว็บแคม USB)",
        "battery_specs": "ใช้ไฟบ้านผ่านสายไฟ AC โดยตรง กำลังไฟสูงสุด 150W ต่อเนื่อง",
        "box_contents": "Mac mini, สายไฟ AC (1.8 ม.)",
        "connectivity": "ด้านหน้า: พอร์ต USB-C (USB 3) x 2, ช่องหูฟัง 3.5 มม. / ด้านหลัง: Thunderbolt 4 (M4) หรือ Thunderbolt 5 (M4 Pro) x 3, HDMI, Gigabit Ethernet (อัปเกรด 10Gb ได้), Wi-Fi 6E, Bluetooth 5.3",
        "material": "ตัวเครื่องอะลูมิเนียมกะทัดรัดขนาดเพียง 5 x 5 นิ้ว ถือเป็นผลิตภัณฑ์ Carbon Neutral รุ่นแรกของ Mac",
        "starting_price_thb": 20900,
        "capacities_prices": {
            "M4 (16GB / 256GB SSD)": 20900,
            "M4 (16GB / 512GB SSD)": 27900,
            "M4 (24GB / 512GB SSD)": 34900,
            "M4 Pro (24GB / 512GB SSD)": 49900
        },
        "colors": [
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/mac-mini/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/mac-mini",
        "overview_url": "https://www.apple.com/th/mac-mini/"
    },
    "mac-studio": {
        "family_id": "mac-studio",
        "category_id": "mac",
        "family_name": "Mac Studio",
        "sub_model_id": "mac-studio-m2",
        "name_th": "Mac Studio (M2 Max / M2 Ultra)",
        "name_en": "Mac Studio (M2 Max / M2 Ultra)",
        "screen_size": "Desktop",
        "dimensions_mm": "197.0 x 197.0 x 95.0 มม.",
        "weight_grams": "2,700 กรัม (M2 Max) / 3,600 กรัม (M2 Ultra)",
        "chip_specs": "ชิป M2 Max (CPU 12-core, GPU 30/38-core) หรือ M2 Ultra (CPU 24-core, GPU 60/76-core, Neural Engine 32-core)",
        "display_specs": "รองรับจอภาพภายนอกสูงสุด 8 จอภาพพร้อมกัน",
        "camera_specs": "ไม่มีในตัว (รองรับกล้องสตูดิโอและ Continuity Camera)",
        "battery_specs": "ใช้ไฟบ้าน กำลังไฟสูงสุด 370W",
        "box_contents": "Mac Studio, สายไฟ AC",
        "connectivity": "Thunderbolt 4 x 4 (M2 Max) หรือ x 6 (M2 Ultra), USB-A x 2, HDMI, 10Gb Ethernet, ช่องใส่ SDXC ด้านหน้า",
        "material": "ตัวเครื่องอะลูมิเนียมชิ้นเดียวพร้อมระบบพัดลมคู่แบบหมุนเวียนคู่ขนาน",
        "starting_price_thb": 74900,
        "capacities_prices": {
            "M2 Max (32GB / 512GB SSD)": 74900,
            "M2 Ultra (64GB / 1TB SSD)": 149900
        },
        "colors": [
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/mac-studio/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-mac/mac-studio",
        "overview_url": "https://www.apple.com/th/mac-studio/"
    },

    # =========================================================================
    # Apple Watch Family (Series 10, Ultra 2, SE)
    # =========================================================================
    "apple-watch-series-10-42": {
        "family_id": "apple-watch-series-10",
        "category_id": "watch",
        "family_name": "Apple Watch Series 10",
        "sub_model_id": "apple-watch-s10-42",
        "name_th": "Apple Watch Series 10 (42 มม.)",
        "name_en": "Apple Watch Series 10 (42mm)",
        "screen_size": "42mm",
        "dimensions_mm": "42.0 x 36.0 x 9.7 มม.",
        "weight_grams": "30.0 กรัม (อะลูมิเนียม) / 34.4 กรัม (ไทเทเนียม)",
        "chip_specs": "ชิป S10 SiP พร้อมโปรเซสเซอร์แบบ 64-bit 2-core และ Neural Engine แบบ 4-core",
        "display_specs": "จอภาพ OLED แบบ Wide-angle ที่มุมมองกว้างขึ้น สว่างขึ้นเมื่อมองจากมุมเฉียงสูงสุด 40%, ความสว่างสูงสุด 2,000 นิต, หนาเพียง 9.7 มม. (บางลง 10%)",
        "camera_specs": "ไม่มีในตัว (รองรับรีโมทควบคุมกล้อง iPhone)",
        "battery_specs": "ใช้งานได้นานสูงสุด 18 ชั่วโมง (โหมดประหยัดพลังงานสูงสุด 36 ชั่วโมง), ชาร์จเร็ว 80% ได้ในเวลาเพียง 30 นาที",
        "box_contents": "ตัวเรือน Apple Watch Series 10 (42 มม.), สายนาฬิกาตามแบบที่เลือก, สายชาร์จเร็วแบบแม่เหล็กเป็น USB-C (1 ม.)",
        "connectivity": "GPS หรือ GPS + Cellular (4G LTE), Wi-Fi 4 (802.11n), Bluetooth 5.3, ชิป Ultra Wideband รุ่นที่ 2",
        "material": "มีให้เลือกทั้งอะลูมิเนียมขัดเงา (ดำเจ็ทแบล็ค) หรือไทเทเนียมเกรดอากาศยานขัดเงา กระจกหน้าจอ Sapphire Crystal",
        "starting_price_thb": 14900,
        "capacities_prices": {
            "อะลูมิเนียม GPS": 14900,
            "อะลูมิเนียม GPS + Cellular": 18900,
            "ไทเทเนียม GPS + Cellular": 25900
        },
        "colors": [
            {"id": "jet-black", "th": "ดำเจ็ทแบล็ค", "en": "Jet Black", "hex": "#0F0F10"},
            {"id": "rose-gold", "th": "โรสโกลด์", "en": "Rose Gold", "hex": "#E0A39A"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"},
            {"id": "natural-titanium", "th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
            {"id": "gold", "th": "ทองไทเทเนียม", "en": "Gold Titanium", "hex": "#E2D2B4"},
            {"id": "slate", "th": "เทาสเลทไทเทเนียม", "en": "Slate Titanium", "hex": "#43464B"}
        ],
        "specs_url": "https://www.apple.com/th/apple-watch-series-10/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch",
        "overview_url": "https://www.apple.com/th/apple-watch-series-10/"
    },
    "apple-watch-series-10-46": {
        "family_id": "apple-watch-series-10",
        "category_id": "watch",
        "family_name": "Apple Watch Series 10",
        "sub_model_id": "apple-watch-s10-46",
        "name_th": "Apple Watch Series 10 (46 มม.)",
        "name_en": "Apple Watch Series 10 (46mm)",
        "screen_size": "46mm",
        "dimensions_mm": "46.0 x 39.0 x 9.7 มม.",
        "weight_grams": "36.4 กรัม (อะลูมิเนียม) / 41.7 กรัม (ไทเทเนียม)",
        "chip_specs": "ชิป S10 SiP พร้อม Neural Engine แบบ 4-core",
        "display_specs": "จอภาพ OLED แบบ Wide-angle พื้นที่หน้าจอใหญ่กว่า Series 6 ถึงเกือบ 30%, ความสว่างสูงสุด 2,000 นิต",
        "camera_specs": "ไม่มีในตัว (รองรับรีโมทควบคุมกล้อง iPhone)",
        "battery_specs": "ใช้งานปกติสูงสุด 18 ชั่วโมง (โหมดประหยัดพลังงานสูงสุด 36 ชั่วโมง), ชาร์จเร็ว 80% ใน 30 นาที",
        "box_contents": "ตัวเรือน Apple Watch Series 10 (46 มม.), สายนาฬิกา, สายชาร์จเร็วแบบแม่เหล็กเป็น USB-C (1 ม.)",
        "connectivity": "GPS หรือ GPS + Cellular, Wi-Fi, Bluetooth 5.3, Ultra Wideband 2",
        "material": "ตัวเรือนอะลูมิเนียม หรือไทเทเนียมเกรด 5 พร้อมหน้าปัดกระจกแซฟไฟร์",
        "starting_price_thb": 15900,
        "capacities_prices": {
            "อะลูมิเนียม GPS": 15900,
            "อะลูมิเนียม GPS + Cellular": 19900,
            "ไทเทเนียม GPS + Cellular": 27900
        },
        "colors": [
            {"id": "jet-black", "th": "ดำเจ็ทแบล็ค", "en": "Jet Black", "hex": "#0F0F10"},
            {"id": "rose-gold", "th": "โรสโกลด์", "en": "Rose Gold", "hex": "#E0A39A"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"},
            {"id": "natural-titanium", "th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
            {"id": "gold", "th": "ทองไทเทเนียม", "en": "Gold Titanium", "hex": "#E2D2B4"},
            {"id": "slate", "th": "เทาสเลทไทเทเนียม", "en": "Slate Titanium", "hex": "#43464B"}
        ],
        "specs_url": "https://www.apple.com/th/apple-watch-series-10/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch",
        "overview_url": "https://www.apple.com/th/apple-watch-series-10/"
    },
    "apple-watch-ultra-2": {
        "family_id": "apple-watch-ultra-2",
        "category_id": "watch",
        "family_name": "Apple Watch Ultra 2",
        "sub_model_id": "apple-watch-ultra-2",
        "name_th": "Apple Watch Ultra 2 (49 มม.)",
        "name_en": "Apple Watch Ultra 2 (49mm)",
        "screen_size": "49mm",
        "dimensions_mm": "49.0 x 44.0 x 14.4 มม.",
        "weight_grams": "61.4 กรัม (ไทเทเนียมธรรมชาติ) / 61.8 กรัม (ไทเทเนียมดำ)",
        "chip_specs": "ชิป S9 SiP พร้อมโปรเซสเซอร์ 64-bit แบบ 2-core และ Neural Engine แบบ 4-core, คำสั่งนิ้ว 'แตะสองครั้ง' (Double Tap)",
        "display_specs": "จอภาพ Always-On Retina LTPO OLED ความสว่างสูงสุดถึง 3,000 นิต (สว่างที่สุดในบรรดาอุปกรณ์พกพา Apple ทั้งหมด), ความสว่างต่ำสุด 1 นิตในที่มืด, ผลึกแซฟไฟร์แบนเรียบพร้อมขอบยกสูงป้องกันแรงกระแทก",
        "camera_specs": "ไม่มีในตัว (รองรับรีโมทควบคุมกล้อง iPhone)",
        "battery_specs": "การใช้งานปกติสูงสุด 36 ชั่วโมง, ในโหมดประหยัดพลังงานสูงสุด 72 ชั่วโมง, ใช้งานกิจกรรมกลางแจ้งพร้อม GPS และวัดอัตราการเต้นของหัวใจสูงสุด 17 ชั่วโมง",
        "box_contents": "Apple Watch Ultra 2, สายนาฬิกา (Trail Loop, Alpine Loop, หรือ Ocean Band), สายชาร์จเร็วแบบแม่เหล็กเป็น USB-C แบบถัก (1 ม.)",
        "connectivity": "GPS ความถี่คู่ที่มีความแม่นยำสูง (L1 และ L5), GPS + Cellular ในตัวทุกเรือน, Bluetooth 5.3, Ultra Wideband 2, มาตรวัดความลึกพร้อมเซ็นเซอร์วัดอุณหภูมิน้ำ, ไซเรน 86 เดซิเบลได้ยินไกลถึง 180 ม.",
        "material": "ตัวเรือนไทเทเนียมเกรดอากาศยาน 95% รีไซเคิล แข็งแกร่ง ทนต่อการกัดกร่อน กันน้ำลึก 100 ม. มาตรฐาน EN13319 สำหรับการดำน้ำลึก 40 ม.",
        "starting_price_thb": 29900,
        "capacities_prices": {
            "ไทเทเนียม GPS + Cellular (Trail Loop)": 29900,
            "ไทเทเนียม GPS + Cellular (Alpine Loop)": 29900,
            "ไทเทเนียม GPS + Cellular (Ocean Band)": 29900,
            "ไทเทเนียม GPS + Cellular (Titanium Milanese Loop)": 33900
        },
        "colors": [
            {"id": "natural-titanium", "th": "ไทเทเนียมธรรมชาติ", "en": "Natural Titanium", "hex": "#9A958E"},
            {"id": "black-titanium", "th": "ไทเทเนียมดำ", "en": "Black Titanium", "hex": "#3A393E"}
        ],
        "specs_url": "https://www.apple.com/th/apple-watch-ultra-2/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch-ultra",
        "overview_url": "https://www.apple.com/th/apple-watch-ultra-2/"
    },
    "apple-watch-se": {
        "family_id": "apple-watch-se",
        "category_id": "watch",
        "family_name": "Apple Watch SE",
        "sub_model_id": "apple-watch-se-40",
        "name_th": "Apple Watch SE (40 มม. / 44 มม.)",
        "name_en": "Apple Watch SE (40mm / 44mm)",
        "screen_size": "40mm",
        "dimensions_mm": "40.0 x 34.0 x 10.7 มม. (40mm) / 44.0 x 38.0 x 10.7 มม. (44mm)",
        "weight_grams": "26.4 กรัม (40mm GPS) / 32.9 กรัม (44mm GPS)",
        "chip_specs": "ชิป S8 SiP พร้อมโปรเซสเซอร์แบบ 64-bit 2-core",
        "display_specs": "จอภาพ Retina LTPO OLED ความสว่างสูงสุด 1,000 นิต, กระจกหน้าจอ Ion-X",
        "camera_specs": "ไม่มีในตัว (รองรับรีโมทควบคุมกล้อง iPhone)",
        "battery_specs": "แบตเตอรี่ใช้งานได้นานสูงสุด 18 ชั่วโมง",
        "box_contents": "Apple Watch SE, สายนาฬิกา, สายชาร์จแบบแม่เหล็กเป็น USB-C (1 ม.)",
        "connectivity": "GPS หรือ GPS + Cellular, Wi-Fi, Bluetooth 5.3, การตรวจจับการชนกัน (Crash Detection)",
        "material": "ตัวเรือนอะลูมิเนียมรีไซเคิล 100% พร้อมฝาหลังวัสดุคอมโพสิตไนลอนที่เข้าคู่กัน",
        "starting_price_thb": 7900,
        "capacities_prices": {
            "40mm GPS": 7900,
            "40mm GPS + Cellular": 9900,
            "44mm GPS": 8900,
            "44mm GPS + Cellular": 10900
        },
        "colors": [
            {"id": "midnight", "th": "มิดไนท์", "en": "Midnight", "hex": "#1E222A"},
            {"id": "starlight", "th": "สตาร์ไลท์", "en": "Starlight", "hex": "#F0ECE1"},
            {"id": "silver", "th": "เงิน", "en": "Silver", "hex": "#E3E4E5"}
        ],
        "specs_url": "https://www.apple.com/th/apple-watch-se/specs/",
        "buy_url": "https://www.apple.com/th/shop/buy-watch/apple-watch-se",
        "overview_url": "https://www.apple.com/th/apple-watch-se/"
    }
}
