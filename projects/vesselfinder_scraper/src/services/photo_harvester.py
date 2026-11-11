# -*- coding: utf-8 -*-
"""
Vessel Photo Harvester & Multi-Gallery Preservation Engine
---------------------------------------------------------
Automated bulk downloader and gallery manager for Thai and international vessels.
Discovers, validates, downloads, and preserves EVERY photo for every vessel.
If a vessel has multiple photos (gallery/angles/albums), harvests all of them!
"""

import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

from config.settings import (
    BASE_DIR,
    DATA_DIR,
    EXPORTS_DIR,
    IMAGES_DIR,
    JSON_DIR,
    DEFAULT_HEADERS,
    STATIC_URL,
)
from src.services.storage_service import VesselStorageService

logger = logging.getLogger("photo_harvester")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class PhotoHarvester:
    """
    Automated Multi-Photo Discovery, Bulk Downloader & Gallery Builder.
    Preserves 100% of available ship photos on local disk and generates rich galleries.
    """

    def __init__(self, max_workers: int = 8, timeout: int = 15):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.lock = threading.Lock()

    @staticmethod
    def _sanitize_name(name: Optional[str]) -> str:
        if not name:
            return "vessel"
        sanitized = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name.strip()).strip("_").lower()
        return sanitized or "vessel"

    @staticmethod
    def _is_valid_jpeg(content: bytes) -> bool:
        """Verifies if the downloaded payload is a valid JPEG image."""
        if len(content) < 1000:
            return False
        # JPEG SOI marker: FF D8
        return content.startswith(b"\xff\xd8")

    def download_single_photo(
        self,
        token: str,
        ship_name: str,
        mmsi: int,
        photo_index: int = 1,
        is_primary: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Downloads a single HD photo from VesselFinder CDN, validates integrity, and saves to disk.
        Returns photo metadata record.
        """
        safe_name = self._sanitize_name(ship_name)
        # Naming convention: {safe_name}_{mmsi}_{index}.jpg
        filename_indexed = f"{safe_name}_{mmsi}_{photo_index}.jpg"
        filepath_indexed = IMAGES_DIR / filename_indexed
        filename_compat = f"{safe_name}_{mmsi}.jpg"
        filepath_compat = IMAGES_DIR / filename_compat

        url_hd = f"{STATIC_URL}/ship-photo/{token}/1"
        url_thumb = f"{STATIC_URL}/ship-photo/{token}/3"

        # Check if already cached and valid on disk
        if filepath_indexed.exists() and filepath_indexed.stat().st_size > 1000:
            size = filepath_indexed.stat().st_size
            # Ensure compatibility alias exists for primary
            if is_primary and not filepath_compat.exists():
                try:
                    with open(filepath_indexed, "rb") as src, open(filepath_compat, "wb") as dst:
                        dst.write(src.read())
                except Exception:
                    pass

            return {
                "index": photo_index,
                "token": token,
                "filename": filename_indexed,
                "local_path": f"data/images/{filename_indexed}",
                "local_url": f"/data/images/{filename_indexed}",
                "api_url": f"/api/vessel/{mmsi}/photo?index={photo_index}",
                "url_hd": url_hd,
                "url_thumb": url_thumb,
                "size_bytes": size,
                "is_primary": is_primary,
                "status": "cached",
            }

        # Otherwise download from CDN
        try:
            resp = self.session.get(url_hd, timeout=self.timeout)
            if resp.status_code == 200 and self._is_valid_jpeg(resp.content):
                content = resp.content
                size = len(content)

                with open(filepath_indexed, "wb") as f:
                    f.write(content)

                # If primary, also write the un-indexed compatibility filename
                if is_primary:
                    with open(filepath_compat, "wb") as f:
                        f.write(content)

                return {
                    "index": photo_index,
                    "token": token,
                    "filename": filename_indexed,
                    "local_path": f"data/images/{filename_indexed}",
                    "local_url": f"/data/images/{filename_indexed}",
                    "api_url": f"/api/vessel/{mmsi}/photo?index={photo_index}",
                    "url_hd": url_hd,
                    "url_thumb": url_thumb,
                    "size_bytes": size,
                    "is_primary": is_primary,
                    "status": "downloaded",
                }
        except Exception as e:
            logger.debug("Failed downloading photo token %s for %s (%s): %s", token, ship_name, mmsi, e)

        return None

    def discover_all_vessel_photos(self) -> Dict[int, Dict[str, Any]]:
        """
        Scans all JSON, CSV, and export databases to extract and group ALL photo tokens by MMSI / IMO.
        Supports multi-photo vessels with 2, 3, or more photos.
        """
        # Map: mmsi -> {name, imo, mmsi, tokens: list[str]}
        vessels_map: Dict[int, Dict[str, Any]] = {}

        # 1. Scan all JSON files in data/json
        for f in JSON_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)

                def scan_obj(obj):
                    if isinstance(obj, dict):
                        mmsi = obj.get("mmsi")
                        if mmsi and isinstance(mmsi, int) and mmsi > 0:
                            if mmsi not in vessels_map:
                                vessels_map[mmsi] = {
                                    "mmsi": mmsi,
                                    "imo": obj.get("imo"),
                                    "name": obj.get("name", f"Vessel_{mmsi}"),
                                    "type": obj.get("type") or obj.get("category_group", "Unknown"),
                                    "tokens": [],
                                }
                            # Collect token
                            token = obj.get("photo_token")
                            if token and isinstance(token, str) and "-" in token:
                                if token not in vessels_map[mmsi]["tokens"]:
                                    vessels_map[mmsi]["tokens"].append(token)

                            # Collect full photo URLs if token not set
                            url = obj.get("photo_url_hd") or obj.get("photo_url")
                            if url and "ship-photo/" in url:
                                m = re.search(r"ship-photo/([0-9]+-[0-9]+-[a-f0-9]{32})", url)
                                if m and m.group(1) not in vessels_map[mmsi]["tokens"]:
                                    vessels_map[mmsi]["tokens"].append(m.group(1))

                        for val in obj.values():
                            scan_obj(val)
                    elif isinstance(obj, list):
                        for itm in obj:
                            scan_obj(itm)

                scan_obj(data)
            except Exception as e:
                logger.debug("Error reading %s: %s", f, e)

        # 2. Scan CSV and JS files for any missing tokens
        for f in list(EXPORTS_DIR.glob("*.csv")) + list(EXPORTS_DIR.glob("*.js")):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    text = fp.read()
                matches = re.findall(r"ship-photo/([0-9]+-[0-9]+-[a-f0-9]{32})", text)
                for t in matches:
                    parts = t.split("-")
                    if len(parts) == 3:
                        imo_str, mmsi_str, _ = parts
                        if mmsi_str.isdigit() and int(mmsi_str) > 0:
                            mmsi = int(mmsi_str)
                            if mmsi not in vessels_map:
                                vessels_map[mmsi] = {
                                    "mmsi": mmsi,
                                    "imo": int(imo_str) if imo_str.isdigit() and int(imo_str) > 0 else None,
                                    "name": f"Vessel_{mmsi}",
                                    "type": "Unknown",
                                    "tokens": [],
                                }
                            if t not in vessels_map[mmsi]["tokens"]:
                                vessels_map[mmsi]["tokens"].append(t)
            except Exception:
                pass

        # 3. Cross-reference existing files in data/images to discover already-downloaded vessel photos
        for img_file in IMAGES_DIR.glob("*.jpg"):
            m = re.search(r"^(.*)_(\d{7,9})(?:_(\d+))?\.jpg$", img_file.name)
            if m:
                raw_name, id_str, idx_str = m.groups()
                vid = int(id_str)
                if vid in vessels_map:
                    if raw_name and vessels_map[vid]["name"].startswith("Vessel_"):
                        vessels_map[vid]["name"] = raw_name.replace("_", " ").title()

        return vessels_map

    def harvest_all(self, update_databases: bool = True) -> Dict[str, Any]:
        """
        Executes complete multi-photo harvest:
        1. Discovers all vessels with photos.
        2. Concurrently downloads every photo (including multiple photos per ship).
        3. Updates vessel records with rich photo gallery arrays.
        4. Saves centralized gallery index and exports updated CSV/JSON/JS bundle.
        """
        start_time = time.time()
        vessels_map = self.discover_all_vessel_photos()

        total_vessels = len(vessels_map)
        vessels_with_tokens = {m: v for m, v in vessels_map.items() if v["tokens"]}
        total_tokens = sum(len(v["tokens"]) for v in vessels_with_tokens.values())

        print(f"\n📸 [Photo Harvester] เริ่มกระบวนการกวาดรูปถ่ายเรือเดินสมุทรทั้งหมด...")
        print(f"🚢 พบเรือที่มีรหัสรูปถ่ายในฐานข้อมูล: {len(vessels_with_tokens)} ลำ (รวมรูปถ่ายทั้งหมด {total_tokens} รูป)")
        print(f"⚡ กำลังดาวน์โหลดแบบขนาน {self.max_workers} Threads ด้วยความเร็วสูง...")

        # Tasks to execute: list of (token, ship_name, mmsi, photo_index, is_primary)
        tasks: List[Tuple[str, str, int, int, bool]] = []
        for mmsi, v in vessels_with_tokens.items():
            for idx, token in enumerate(v["tokens"], 1):
                is_pri = (idx == 1)
                tasks.append((token, v["name"], mmsi, idx, is_pri))

        # Photo results by MMSI
        gallery_by_mmsi: Dict[int, List[Dict[str, Any]]] = {m: [] for m in vessels_with_tokens}
        downloaded_count = 0
        cached_count = 0
        error_count = 0
        total_bytes = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(
                    self.download_single_photo,
                    token=t[0],
                    ship_name=t[1],
                    mmsi=t[2],
                    photo_index=t[3],
                    is_primary=t[4],
                ): t
                for t in tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                mmsi = task[2]
                try:
                    res = future.result()
                    if res:
                        gallery_by_mmsi[mmsi].append(res)
                        total_bytes += res.get("size_bytes", 0)
                        if res.get("status") == "downloaded":
                            downloaded_count += 1
                        else:
                            cached_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.debug("Harvester worker error: %s", e)

        # Sort each vessel's gallery by index
        for mmsi in gallery_by_mmsi:
            gallery_by_mmsi[mmsi].sort(key=lambda x: x["index"])

        elapsed = time.time() - start_time
        mb_size = total_bytes / (1024 * 1024)

        print(f"\n✅ ดาวน์โหลดและตรวจสอบเสร็จสิ้นใน {elapsed:.2f} วินาที!")
        print(f"  • รูปที่ดาวน์โหลดใหม่สำเร็จ : {downloaded_count} รูป")
        print(f"  • รูปที่แคชสมบูรณ์บนดิสก์ : {cached_count} รูป")
        print(f"  • รวมรูปถ่ายเรือที่พร้อมใช้งาน : {downloaded_count + cached_count} รูป ({mb_size:.2f} MB)")
        print(f"  • เรือที่มีรูปถ่ายครบถ้วน    : {len([g for g in gallery_by_mmsi.values() if g])} ลำ")

        # Check multi-photo vessels
        multi_photo_vessels = {m: g for m, g in gallery_by_mmsi.items() if len(g) > 1}
        if multi_photo_vessels:
            print(f"🌟 พบเรือที่มีรูปถ่ายหลายรูป (Multi-Photo Gallery): {len(multi_photo_vessels)} ลำ!")
            for m, g in multi_photo_vessels.items():
                v_name = vessels_map.get(m, {}).get("name", f"MMSI_{m}")
                print(f"   - {v_name} (MMSI: {m}): {len(g)} รูป")

        # 4. Save centralized gallery index
        gallery_index_payload = {
            "updated_at_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_vessels_with_photos": len([g for g in gallery_by_mmsi.values() if g]),
            "total_photos_count": downloaded_count + cached_count,
            "total_size_mb": round(mb_size, 2),
            "multi_photo_vessels_count": len(multi_photo_vessels),
            "galleries": {
                str(m): {
                    "mmsi": m,
                    "name": vessels_map.get(m, {}).get("name"),
                    "imo": vessels_map.get(m, {}).get("imo"),
                    "type": vessels_map.get(m, {}).get("type"),
                    "photos_count": len(g),
                    "primary_photo": g[0]["local_path"] if g else None,
                    "photos": g,
                }
                for m, g in gallery_by_mmsi.items()
                if g
            },
        }
        gallery_path = JSON_DIR / "vessel_photo_gallery.json"
        with open(gallery_path, "w", encoding="utf-8") as f:
            json.dump(gallery_index_payload, f, ensure_ascii=False, indent=2)

        # 5. Enrich live radar databases with full photos array
        if update_databases:
            self._update_all_radar_datasets(gallery_by_mmsi)

        return gallery_index_payload

    def _update_all_radar_datasets(self, gallery_by_mmsi: Dict[int, List[Dict[str, Any]]]):
        """Injects `photos` arrays and `local_photo` paths into all active JSON & CSV radar files."""
        print(f"\n🔄 กำลังอัปเดตข้อมูลแกลเลอรีรูปถ่ายลงในฐานข้อมูลเรดาร์ทุกโซน...")

        target_files = [
            "live_radar_thailand_all_seas.json",
            "live_radar_gulf_of_thailand_all.json",
            "live_radar_upper_gulf_th.json",
            "patrol_and_military_vessels.json",
            "fishing_vessels.json",
        ]

        for fname in target_files:
            fpath = JSON_DIR / fname
            if not fpath.exists():
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as fp:
                    content = json.load(fp)

                vessel_list = content if isinstance(content, list) else content.get("vessels", [])
                updated_count = 0

                for v in vessel_list:
                    mmsi = v.get("mmsi")
                    if mmsi and mmsi in gallery_by_mmsi and gallery_by_mmsi[mmsi]:
                        gallery = gallery_by_mmsi[mmsi]
                        v["photos"] = gallery
                        v["photos_count"] = len(gallery)
                        v["local_photo"] = gallery[0]["local_path"]
                        v["photo_url_hd"] = gallery[0]["url_hd"]
                        v["photo_url_thumb"] = gallery[0]["url_thumb"]
                        updated_count += 1
                    else:
                        # Check if single file exists on disk
                        safe_name = self._sanitize_name(v.get("name"))
                        for candidate in [f"{safe_name}_{mmsi}.jpg", f"{safe_name}_{mmsi}_1.jpg"]:
                            if (IMAGES_DIR / candidate).exists():
                                v["local_photo"] = f"data/images/{candidate}"
                                v["photos_count"] = v.get("photos_count") or 1
                                break

                # Save updated JSON
                with open(fpath, "w", encoding="utf-8") as fp:
                    json.dump(content, fp, ensure_ascii=False, indent=2)

                # Re-export CSV if main radar
                if fname == "live_radar_thailand_all_seas.json":
                    VesselStorageService.export_vessels_csv(vessel_list, "vessels_thailand_all_seas.csv")
                    VesselStorageService.build_studio_js_bundle(content, "vesselfinder_live_bundle.js")

                logger.info("Updated %s with %d vessel photo galleries.", fname, updated_count)
            except Exception as e:
                logger.warning("Failed updating %s with photo galleries: %s", fname, e)

        print("✅ อัปเดตฐานข้อมูลเรดาร์, CSV, และ Web Studio JS Bundle สำเร็จเรียบร้อยค่ะ!")


if __name__ == "__main__":
    harvester = PhotoHarvester(max_workers=8)
    harvester.harvest_all()
