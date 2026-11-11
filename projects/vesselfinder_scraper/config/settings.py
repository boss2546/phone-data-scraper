# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json"
EXPORTS_DIR = DATA_DIR / "exports"
IMAGES_DIR = DATA_DIR / "images"

for _d in (DATA_DIR, JSON_DIR, EXPORTS_DIR, IMAGES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.vesselfinder.com"
STATIC_URL = "https://static.vesselfinder.net"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
    "Referer": "https://www.vesselfinder.com/",
}

# Constants from reverse-engineered VesselFinder Web Worker (index.500118.js & map.500118.js)
COORD_FACTOR = 600000.0  # CF = 6e5
TRACK_LON_LAT_XOR = 1431655765  # 0x55555555
TRACK_COG_SOG_XOR = 21845       # 0x5555

# Vessel Type Color Code Mapping on VesselFinder Map
VESSEL_COLOR_TYPES = {
    0: "Other / Unknown",
    1: "Reserved / Wing in Ground",
    2: "High Speed Craft",
    3: "Tug / Special / Pilot / SAR",
    4: "Passenger / Cruise / Ferry",
    5: "Fishing Vessel",
    6: "Cargo / Container / Bulk Carrier",
    7: "Cargo (Hazard)",
    8: "Tanker (Oil / Chemical / LPG / LNG)",
    9: "Pleasure Craft / Sailing Yacht",
    14: "Navigation Aid / Base Station",
}

# Predefined Maritime Radar Zones (lon_min, lat_min, lon_max, lat_max, default_zoom)
MARITIME_ZONES = {
    "thailand_all_seas": {
        "name_th": "น่านน้ำไทยทั้งหมดครบ 2 ฝั่งทะเล (อ่าวไทย 7 โซน + ทะเลอันดามัน 3 โซน)",
        "name_en": "All Thailand Waters (Gulf of Thailand + Andaman Sea 10 Sectors)",
        "bbox": (97.50, 5.80, 103.50, 13.80),
        "zoom": 10,
    },
    "andaman_th": {
        "name_th": "ทะเลอันดามันทั้งหมด (ระนอง - พังงา - ภูเก็ต - กระบี่ - ตรัง - สตูล)",
        "name_en": "Thailand Andaman Sea (Ranong, Phuket, Krabi & Satun)",
        "bbox": (97.50, 6.20, 100.00, 10.50),
        "zoom": 11,
    },
    "gulf_of_thailand_all": {
        "name_th": "อ่าวไทยทั้งหมดครบทุกโซน (Multi-Grid Full Gulf of Thailand Sweep)",
        "name_en": "Full Gulf of Thailand (Multi-Grid High-Density Sweep)",
        "bbox": (99.00, 5.80, 103.00, 13.78),
        "zoom": 11,
    },
    "upper_gulf_th": {
        "name_th": "อ่าวไทยตอนบน (กรุงเทพฯ - แหลมฉบัง - ศรีราชา - มาบตาพุด)",
        "name_en": "Upper Gulf of Thailand (Bangkok & Laem Chabang)",
        "bbox": (100.40, 12.50, 101.25, 13.75),
        "zoom": 12,
    },
    "laem_chabang": {
        "name_th": "ท่าเรือแหลมฉบัง & ศรีราชา (ซูมละเอียดระดับท่าเทียบเรือ)",
        "name_en": "Laem Chabang & Si Racha Port (High-Detail Zoom 14)",
        "bbox": (100.82, 13.03, 100.92, 13.16),
        "zoom": 14,
    },
    "bangkok_port": {
        "name_th": "ท่าเรือกรุงเทพ (คลองเตย - แม่น้ำเจ้าพระยา - สมุทรปราการ)",
        "name_en": "Bangkok Port & Chao Phraya River",
        "bbox": (100.50, 13.52, 100.62, 13.72),
        "zoom": 14,
    },
    "singapore_strait": {
        "name_th": "ช่องแคบสิงคโปร์ (Singapore Strait)",
        "name_en": "Singapore Strait",
        "bbox": (103.60, 1.15, 104.10, 1.35),
        "zoom": 12,
    },
    "southern_th": {
        "name_th": "ภาคใต้ฝั่งอ่าวไทย & อันดามัน (สุราษฎร์ - สมุย - สงขลา - ภูเก็ต)",
        "name_en": "Southern Thailand (Samui, Songkhla & Phuket)",
        "bbox": (98.20, 7.00, 100.80, 9.60),
        "zoom": 10,
    },
}

# 7 Sub-Grid Sectors covering 100% of the Gulf of Thailand at high resolution
GULF_OF_THAILAND_SECTORS = [
    {
        "sector_id": "chao_phraya_west_bight",
        "name_th": "1. ก้นอ่าวไทยฝั่งตะวันตก & แม่น้ำเจ้าพระยา (กรุงเทพฯ - สมุทรปราการ - สมุทรสาคร - เพชรบุรี)",
        "bbox": (99.85, 12.80, 100.68, 13.78),
        "zoom": 12,
    },
    {
        "sector_id": "eastern_seaboard_lch",
        "name_th": "2. อีสเทิร์นซีบอร์ด & แหลมฉบัง (ชลบุรี - ศรีราชา - เกาะสีชัง - แหลมฉบัง - พัทยา - สัตหีบ)",
        "bbox": (100.68, 12.50, 101.05, 13.55),
        "zoom": 12,
    },
    {
        "sector_id": "rayong_maptaphut_trat",
        "name_th": "3. ชายฝั่งตะวันออก (ระยอง - มาบตาพุด - จันทบุรี - ตราด - เกาะช้าง)",
        "bbox": (101.05, 11.40, 102.95, 12.85),
        "zoom": 11,
    },
    {
        "sector_id": "prachuap_chumphon",
        "name_th": "4. อ่าวไทยตอนกลางฝั่งตะวันตก (หัวหิน - ประจวบฯ - บางสะพาน - ชุมพร - เกาะเต่า)",
        "bbox": (99.00, 9.80, 100.55, 12.80),
        "zoom": 11,
    },
    {
        "sector_id": "surat_samui_nakhon",
        "name_th": "5. อ่าวไทยตอนล่าง (สุราษฎร์ธานี - เกาะสมุย - เกาะพะงัน - ขนอม - นครศรีธรรมราช)",
        "bbox": (99.10, 8.00, 100.65, 9.80),
        "zoom": 11,
    },
    {
        "sector_id": "songkhla_pattani_narathiwat",
        "name_th": "6. อ่าวไทยตอนใต้สุด (สงขลา - ปัตตานี - นราธิวาส)",
        "bbox": (100.00, 5.80, 102.40, 8.00),
        "zoom": 11,
    },
    {
        "sector_id": "central_gulf_offshore",
        "name_th": "7. กลางอ่าวไทย & แหล่งปิโตรเลียม (แหล่งก๊าซเอราวัณ - บงกช - อาทิตย์ & เส้นทางเดินเรือหลัก)",
        "bbox": (100.55, 8.00, 102.80, 12.50),
        "zoom": 10,
    },
]

# 3 Sub-Grid Sectors covering Thailand's Andaman Sea (Indian Ocean)
ANDAMAN_SECTORS = [
    {
        "sector_id": "north_andaman_ranong",
        "name_th": "8. ทะเลอันดามันตอนบน (ระนอง - เกาะพยาม - ปากจั่น - ชายแดนเมียนมา)",
        "bbox": (97.80, 9.20, 98.80, 10.50),
        "zoom": 12,
    },
    {
        "sector_id": "central_andaman_phuket_krabi",
        "name_th": "9. ทะเลอันดามันตอนกลาง (พังงา - ภูเก็ต - อ่าวพังงา - กระบี่ - เกาะพีพี)",
        "bbox": (98.00, 7.60, 99.20, 9.20),
        "zoom": 12,
    },
    {
        "sector_id": "south_andaman_trang_satun",
        "name_th": "10. ทะเลอันดามันตอนล่าง (ตรัง - เกาะลันตา - สตูล - เกาะตะรุเตา - เกาะหลีเป๊ะ)",
        "bbox": (99.00, 6.20, 100.00, 7.60),
        "zoom": 12,
    },
]

# All 10 Sectors covering 100% of Thailand Maritime Waters (Gulf + Andaman)
ALL_THAILAND_SECTORS = GULF_OF_THAILAND_SECTORS + ANDAMAN_SECTORS

# Navigation Status Codes (AIS Standard)
AIS_NAV_STATUS = {
    -1: "Unknown / Not Reported",
    0: "Under way using engine (กำลังแล่นด้วยเครื่องยนต์)",
    1: "At anchor (ทอดสมอ)",
    2: "Not under command (ไม่พร้อมควบคุม)",
    3: "Restricted manoeuvrability (จำกัดความคล่องตัว)",
    4: "Constrained by her draught (จำกัดด้วยระยะกินน้ำลึก)",
    5: "Moored (จอดเทียบท่า)",
    6: "Aground (เกยตื้น)",
    7: "Engaged in Fishing (กำลังทำการประมง)",
    8: "Under way sailing (กำลังแล่นใบ)",
    15: "Undefined",
}

