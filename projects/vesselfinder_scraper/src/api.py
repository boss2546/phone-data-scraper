# -*- coding: utf-8 -*-
"""
VesselFinder Standalone Microservice API
----------------------------------------
Zero-Auth, Universal CORS, Lightning-Fast REST API for Live AIS Maritime Radar.
Connectable from any frontend, backend, dashboard, curl, or webhook.
"""

import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from config.settings import BASE_DIR, DATA_DIR, JSON_DIR, EXPORTS_DIR, IMAGES_DIR, MARITIME_ZONES
from src.scrapers.vessel_scraper import VesselFinderScraper
from src.services.storage_service import VesselStorageService

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vesselfinder_api")

# In-memory radar cache
_CACHE_LOCK = threading.Lock()
_RADAR_CACHE: Dict[str, Any] = {}
_LAST_REFRESH_UTC: Optional[str] = None
_IS_REFRESHING = False

scraper = VesselFinderScraper()


def _load_cached_files_into_memory():
    """Warm boot: loads existing JSON radar files from disk into memory."""
    global _RADAR_CACHE, _LAST_REFRESH_UTC
    target_file = JSON_DIR / "live_radar_thailand_all_seas.json"
    if not target_file.exists():
        target_file = JSON_DIR / "live_radar_gulf_of_thailand_all.json"
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            with _CACHE_LOCK:
                _RADAR_CACHE["thailand_all_seas"] = data
                _RADAR_CACHE["gulf_of_thailand_all"] = data
                _LAST_REFRESH_UTC = data.get("scraped_at_utc")
            logger.info("Warm cache loaded successfully (%d vessels in memory).", len(data.get("vessels", [])))
        except Exception as e:
            logger.warning("Could not pre-load cache: %s", e)


# Preload immediately on module load for instant response (<10ms)
_load_cached_files_into_memory()


def _background_radar_loop(interval_seconds: int = 120):
    """Background worker that continuously sweeps Thai waters to keep cache fresh."""
    global _IS_REFRESHING, _LAST_REFRESH_UTC
    # Initial sleep to allow fast container startup
    time.sleep(5)
    while True:
        try:
            _IS_REFRESHING = True
            logger.info("Background Auto-Refresh: Sweeping Thailand territorial waters...")
            data = scraper.scan_all_thailand_waters(enrich_limit=50)
            with _CACHE_LOCK:
                _RADAR_CACHE["thailand_all_seas"] = data
                _LAST_REFRESH_UTC = data.get("scraped_at_utc")

            # Persist to disk for consistency
            VesselStorageService.save_json(data, "live_radar_thailand_all_seas.json")
            VesselStorageService.export_vessels_csv(data.get("vessels", []), "vessels_thailand_all_seas.csv")
            VesselStorageService.export_geojson(data.get("vessels", []), [], "radar_thailand_all_seas.geojson")
            VesselStorageService.build_studio_js_bundle(data, "vesselfinder_live_bundle.js")

            patrols = data.get("patrol_military_vessels", [])
            if patrols:
                VesselStorageService.save_json(patrols, "patrol_and_military_vessels.json")
                VesselStorageService.export_vessels_csv(patrols, "patrol_and_military_vessels.csv")

            logger.info("Background Auto-Refresh completed: %d vessels live.", len(data.get("vessels", [])))
        except Exception as err:
            logger.error("Background Auto-Refresh error: %s", err)
        finally:
            _IS_REFRESHING = False
        time.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm boot cache & launch background worker thread
    _load_cached_files_into_memory()
    bg_thread = threading.Thread(target=_background_radar_loop, args=(120,), daemon=True)
    bg_thread.start()
    yield
    # Shutdown


app = FastAPI(
    title="🚢 VesselFinder AIS Maritime Radar Microservice",
    description="Universal Zero-Auth Microservice for Real-Time Vessel Intelligence, Coastal Patrols & Maritime Radar across Thailand and Worldwide.",
    version="1.0.0",
    lifespan=lifespan,
)

# 100% Permissive Open CORS: connect from React, Vue, Next.js, mobile app, or curl without security friction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    """Healthcheck endpoint for Docker, Kubernetes, or load balancers."""
    with _CACHE_LOCK:
        v_count = len(_RADAR_CACHE.get("thailand_all_seas", {}).get("vessels", []))
    return {
        "status": "healthy",
        "service": "vesselfinder-radar-microservice",
        "vessels_in_cache": v_count,
        "last_refresh_utc": _LAST_REFRESH_UTC,
        "is_refreshing_now": _IS_REFRESHING,
        "server_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


@app.get("/", response_class=HTMLResponse, tags=["Web Studio"])
def serve_web_studio():
    """Serves the Interactive 2D Maritime Radar Studio Web App directly at root."""
    studio_path = BASE_DIR / "vesselfinder_studio.html"
    if studio_path.exists():
        with open(studio_path, "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(content=html)
    return HTMLResponse("<h2>🚢 VesselFinder Radar API is Online! Visit <a href='/docs'>/docs</a> for API.</h2>")


@app.get("/data/exports/{file_name}", tags=["Static Assets"])
def serve_exported_file(file_name: str):
    """Serves generated bundle JS, GeoJSON, and CSV files directly."""
    target = EXPORTS_DIR / file_name
    if target.exists():
        media_type = "application/javascript" if file_name.endswith(".js") else ("application/geo+json" if file_name.endswith(".geojson") else "text/csv")
        return FileResponse(target, media_type=media_type)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/data/images/{image_name}", tags=["Static Assets"])
def serve_image(image_name: str):
    """Serves high-resolution downloaded vessel photos directly from local disk."""
    target = IMAGES_DIR / image_name
    if target.exists():
        return FileResponse(target, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/api/radar", tags=["Radar Intelligence"])
def get_live_radar(
    zone: str = Query("thailand_all_seas", description="Zone key: 'thailand_all_seas', 'gulf_of_thailand_all', 'andaman_th'"),
    refresh: bool = Query(False, description="Set true to force a live on-demand sweep instead of cached response"),
):
    """
    Returns full live radar contacts, coordinates, speeds, headings, and 10-sector breakdown.
    Default responds in <10ms from in-memory cache.
    """
    if refresh:
        data = scraper.fetch_zone_vessels(zone_key=zone, enrich_limit=30)
        with _CACHE_LOCK:
            _RADAR_CACHE[zone] = data
        return data

    with _CACHE_LOCK:
        cached = _RADAR_CACHE.get(zone) or _RADAR_CACHE.get("thailand_all_seas")

    if cached:
        return cached

    # Fallback to direct scan if cache empty
    data = scraper.fetch_zone_vessels(zone_key=zone, enrich_limit=30)
    with _CACHE_LOCK:
        _RADAR_CACHE[zone] = data
    return data


@app.get("/api/patrol", tags=["Patrol & Military"])
def get_patrol_vessels(
    refresh: bool = Query(False, description="Set true to force a live on-demand sweep"),
):
    """
    Returns only naval warships, coastal patrol gunboats, marine police, customs, SAR, and pilot vessels.
    """
    radar_data = get_live_radar(zone="thailand_all_seas", refresh=refresh)
    patrols = radar_data.get("patrol_military_vessels", [])
    if not patrols:
        patrols = scraper.filter_patrol_and_military_vessels(radar_data.get("vessels", []))
    return {
        "count": len(patrols),
        "last_report_utc": radar_data.get("scraped_at_utc"),
        "vessels": patrols,
    }


@app.get("/api/fishing", tags=["Fishing Fleet"])
def get_fishing_vessels(
    refresh: bool = Query(False, description="Set true to force a live on-demand sweep"),
):
    """
    Returns all active fishing vessels and trawlers across Thailand territorial waters.
    """
    radar_data = get_live_radar(zone="thailand_all_seas", refresh=refresh)
    vessels = radar_data.get("vessels", [])
    fishing = []
    for v in vessels:
        vtype = str(v.get("type", "")).upper()
        cat = str(v.get("category_group", "")).upper()
        name = str(v.get("name", "")).upper()
        if "FISH" in vtype or "FISH" in cat or "MFV" in name or "F/V" in name or "ประมง" in name or "PRAMONG" in name or "CHOK" in name or "โชค" in name:
            fishing.append(v)
    return {
        "count": len(fishing),
        "last_report_utc": radar_data.get("scraped_at_utc"),
        "vessels": fishing,
    }


@app.get("/api/vessel/{mmsi}", tags=["Vessel Telemetry"])
def get_vessel_telemetry(mmsi: int):
    """
    Returns 360° vessel specifications, live voyage, current marine weather, and decoded XOR historical track.
    """
    # 1. Check radar cache first
    cached_vessel = None
    with _CACHE_LOCK:
        for z_data in _RADAR_CACHE.values():
            for v in z_data.get("vessels", []):
                if v.get("mmsi") == mmsi:
                    cached_vessel = dict(v)
                    break
            if cached_vessel:
                break

    try:
        data = scraper.fetch_vessel_full_intelligence(mmsi, fetch_track=True, fetch_weather=True)
    except Exception:
        data = {}

    res = None
    if cached_vessel:
        res = dict(cached_vessel)
        res.update({k: v for k, v in data.items() if v is not None and v != ""})

    # Enrich with photo gallery if available
    gallery_file = JSON_DIR / "vessel_photo_gallery.json"
    if gallery_file.exists():
        try:
            with open(gallery_file, "r", encoding="utf-8") as gf:
                g_data = json.load(gf)
            v_g = g_data.get("galleries", {}).get(str(mmsi))
            if v_g and v_g.get("photos"):
                if res is not None:
                    res["photos"] = v_g["photos"]
                    res["photos_count"] = v_g.get("photos_count", len(v_g["photos"]))
                    res["local_photo"] = v_g.get("primary_photo")
                elif data:
                    data["photos"] = v_g["photos"]
                    data["photos_count"] = v_g.get("photos_count", len(v_g["photos"]))
                    data["local_photo"] = v_g.get("primary_photo")
        except Exception:
            pass

    if res is not None:
        return res

    if data and any(v is not None for v in data.values()):
        return data

    raise HTTPException(status_code=404, detail=f"Vessel with MMSI {mmsi} not found in live radar or registry.")


@app.get("/api/vessel/{mmsi}/photo", tags=["Vessel Telemetry & Photo Gallery"])
def get_vessel_photo(
    mmsi: int,
    index: int = Query(1, ge=1, description="Photo index (1-based, e.g. 1 for primary photo, 2 for second photo, etc.)"),
):
    """
    Serves a specific vessel photo directly as an image/jpeg stream, or redirects to its CDN image.
    Supports multi-photo vessels with index=1, 2, 3...
    """
    # 1. Search for indexed local file first (*_{mmsi}_{index}.jpg)
    for f in IMAGES_DIR.glob(f"*_{mmsi}_{index}.jpg"):
        if f.exists() and f.stat().st_size > 1000:
            return FileResponse(f, media_type="image/jpeg")

    # 2. Fallback to un-indexed primary file (*_{mmsi}.jpg) if index == 1
    if index == 1:
        for f in IMAGES_DIR.glob(f"*_{mmsi}.jpg"):
            if f.exists() and f.stat().st_size > 1000:
                return FileResponse(f, media_type="image/jpeg")

    # 3. Check vessel photo gallery JSON for specific index
    gallery_file = JSON_DIR / "vessel_photo_gallery.json"
    if gallery_file.exists():
        try:
            with open(gallery_file, "r", encoding="utf-8") as gf:
                g_data = json.load(gf)
            v_gallery = g_data.get("galleries", {}).get(str(mmsi))
            if v_gallery and v_gallery.get("photos"):
                for p in v_gallery["photos"]:
                    if p.get("index") == index:
                        local_p = BASE_DIR / p["local_path"]
                        if local_p.exists() and local_p.stat().st_size > 1000:
                            return FileResponse(local_p, media_type="image/jpeg")
                        if p.get("url_hd"):
                            return Response(status_code=307, headers={"Location": p["url_hd"]})
        except Exception:
            pass

    # 4. Check radar cache as last resort for primary photo
    with _CACHE_LOCK:
        for z in _RADAR_CACHE.values():
            for v in z.get("vessels", []):
                if v.get("mmsi") == mmsi and v.get("photo_url_hd") and index == 1:
                    return Response(status_code=307, headers={"Location": v["photo_url_hd"]})

    raise HTTPException(
        status_code=404,
        detail=f"No photo found at index {index} for vessel MMSI {mmsi}.",
    )


@app.get("/api/vessel/{mmsi}/photos", tags=["Vessel Telemetry & Photo Gallery"])
def get_vessel_all_photos(mmsi: int):
    """
    Returns the complete photo gallery array for a vessel (all angles, resolutions, file paths, and CDN URLs).
    """
    # 1. Check vessel photo gallery JSON
    gallery_file = JSON_DIR / "vessel_photo_gallery.json"
    if gallery_file.exists():
        try:
            with open(gallery_file, "r", encoding="utf-8") as gf:
                g_data = json.load(gf)
            v_gallery = g_data.get("galleries", {}).get(str(mmsi))
            if v_gallery:
                return v_gallery
        except Exception:
            pass

    # 2. Check local disk for any matching images (*_{mmsi}*.jpg)
    found_photos = []
    idx = 1
    for f in sorted(IMAGES_DIR.glob(f"*_{mmsi}*.jpg")):
        if f.exists() and f.stat().st_size > 1000:
            found_photos.append({
                "index": idx,
                "filename": f.name,
                "local_path": f"data/images/{f.name}",
                "local_url": f"/data/images/{f.name}",
                "api_url": f"/api/vessel/{mmsi}/photo?index={idx}",
                "size_bytes": f.stat().st_size,
                "is_primary": (idx == 1),
            })
            idx += 1

    if found_photos:
        return {
            "mmsi": mmsi,
            "photos_count": len(found_photos),
            "primary_photo": found_photos[0]["local_path"],
            "photos": found_photos,
        }

    # 3. Check radar cache
    with _CACHE_LOCK:
        for z in _RADAR_CACHE.values():
            for v in z.get("vessels", []):
                if v.get("mmsi") == mmsi:
                    if v.get("photos"):
                        return {
                            "mmsi": mmsi,
                            "name": v.get("name"),
                            "photos_count": len(v["photos"]),
                            "photos": v["photos"],
                        }
                    elif v.get("photo_url_hd"):
                        single_p = [{
                            "index": 1,
                            "url_hd": v["photo_url_hd"],
                            "api_url": f"/api/vessel/{mmsi}/photo?index=1",
                            "is_primary": true,
                        }]
                        return {
                            "mmsi": mmsi,
                            "name": v.get("name"),
                            "photos_count": 1,
                            "photos": single_p,
                        }

    raise HTTPException(status_code=404, detail=f"No photos found for vessel MMSI {mmsi}.")


@app.get("/api/photos/stats", tags=["Vessel Telemetry & Photo Gallery"])
def get_photo_gallery_stats():
    """
    Returns high-level statistics for all ship photos saved on disk and indexed in the gallery.
    """
    gallery_file = JSON_DIR / "vessel_photo_gallery.json"
    gallery_data = {}
    if gallery_file.exists():
        try:
            with open(gallery_file, "r", encoding="utf-8") as gf:
                gallery_data = json.load(gf)
        except Exception:
            pass

    disk_files = list(IMAGES_DIR.glob("*.jpg"))
    total_bytes = sum(f.stat().st_size for f in disk_files if f.exists())

    return {
        "status": "healthy",
        "total_files_on_disk": len(disk_files),
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "total_vessels_with_photos": gallery_data.get("total_vessels_with_photos", len(disk_files)),
        "multi_photo_vessels_count": gallery_data.get("multi_photo_vessels_count", 0),
        "last_harvest_utc": gallery_data.get("updated_at_utc"),
        "images_directory": str(IMAGES_DIR.relative_to(BASE_DIR)),
    }


@app.post("/api/photos/harvest", tags=["Vessel Telemetry & Photo Gallery"])
def trigger_photo_harvest():
    """
    Triggers an on-demand scan and harvest of all vessel photos across Thailand territorial waters.
    """
    from src.services.photo_harvester import PhotoHarvester
    harvester = PhotoHarvester(max_workers=8)
    summary = harvester.harvest_all(update_databases=True)
    return {
        "status": "success",
        "message": "Photo harvest completed successfully.",
        "summary": summary,
    }


@app.get("/api/ports", tags=["Ports Database"])
def get_ports(
    country: str = Query("th", description="Country code (e.g. 'th' for Thailand 49 ports, or 'all' for 11,367 global ports)"),
):
    """
    Returns decoded global ports database with coordinates and UN/LOCODE.
    """
    c_code = None if country.lower() in ("all", "global", "*") else country.lower()
    ports = scraper.fetch_global_ports(country_code=c_code)
    return {
        "country": country.upper(),
        "total_ports": len(ports),
        "ports": ports,
    }


@app.get("/api/search", tags=["Vessel Search"])
def search_vessel(
    q: str = Query(..., description="Vessel name, IMO number, or MMSI to search worldwide"),
):
    """
    Performs real-time binary search across the global VesselFinder vessel registry.
    """
    results = scraper.search_vessels(q)
    return {
        "query": q,
        "results_count": len(results),
        "results": results,
    }
