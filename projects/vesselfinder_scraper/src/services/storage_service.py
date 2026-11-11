# -*- coding: utf-8 -*-
"""
Storage, Export (JSON, CSV UTF-8 BOM, GeoJSON, JS SDK) & Ship Photo Downloader
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests

from config.settings import JSON_DIR, EXPORTS_DIR, IMAGES_DIR, DEFAULT_HEADERS


class VesselStorageService:
    """Handles saving scraped VesselFinder data into JSON, CSV, GeoJSON, JS Bundle, and local images."""

    @staticmethod
    def save_json(data: Any, filename: str) -> Path:
        path = JSON_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    @staticmethod
    def export_vessels_csv(vessels: List[Dict[str, Any]], filename: str = "vesselfinder_vessels.csv") -> Path:
        path = EXPORTS_DIR / filename
        fieldnames = [
            "mmsi",
            "imo",
            "name",
            "type",
            "category_group",
            "country",
            "flag_code",
            "lat",
            "lon",
            "sog_knots",
            "cog_deg",
            "heading_deg",
            "nav_status",
            "destination_raw",
            "next_port_name",
            "eta_utc",
            "last_port_name",
            "last_port_country",
            "draught_m",
            "length_m",
            "beam_m",
            "gt",
            "dwt",
            "year_built",
            "photo_url_hd",
            "details_url",
        ]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for v in vessels:
                voyage = v.get("voyage") or {}
                dims = v.get("dimensions") or {}
                imo = v.get("imo") or 0
                mmsi = v.get("mmsi") or 0
                writer.writerow({
                    "mmsi": mmsi,
                    "imo": imo if imo > 0 else "",
                    "name": v.get("name", ""),
                    "type": v.get("type") or v.get("category_group", ""),
                    "category_group": v.get("category_group", ""),
                    "country": v.get("country", ""),
                    "flag_code": v.get("flag_code", ""),
                    "lat": v.get("lat", ""),
                    "lon": v.get("lon", ""),
                    "sog_knots": v.get("sog_knots", ""),
                    "cog_deg": v.get("cog_deg") if v.get("cog_deg") is not None else v.get("cog", ""),
                    "heading_deg": v.get("heading_deg", ""),
                    "nav_status": v.get("nav_status", ""),
                    "destination_raw": v.get("destination_raw", ""),
                    "next_port_name": voyage.get("next_port_name", ""),
                    "eta_utc": voyage.get("next_port_eta_utc") or v.get("eta_utc", ""),
                    "last_port_name": voyage.get("last_port_name", ""),
                    "last_port_country": voyage.get("last_port_country", ""),
                    "draught_m": v.get("draught_m", ""),
                    "length_m": v.get("length_m") or dims.get("length_m", ""),
                    "beam_m": v.get("beam_m") or dims.get("beam_m", ""),
                    "gt": v.get("gt", ""),
                    "dwt": v.get("dwt", ""),
                    "year_built": v.get("year_built", ""),
                    "photo_url_hd": v.get("photo_url_hd", ""),
                    "details_url": v.get("details_url") or (
                        f"https://www.vesselfinder.com/vessels/details/{imo if imo > 0 else mmsi}"
                    ),
                })
        return path

    @staticmethod
    def export_ports_csv(ports: List[Dict[str, Any]], filename: str = "vesselfinder_ports.csv") -> Path:
        path = EXPORTS_DIR / filename
        fieldnames = ["locode", "short_locode", "name", "country", "country_code", "lat", "lon", "port_type", "url"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for p in ports:
                writer.writerow(p)
        return path

    @staticmethod
    def export_geojson(
        vessels: List[Dict[str, Any]],
        track_vessels: Optional[List[Dict[str, Any]]] = None,
        filename: str = "vesselfinder_radar.geojson",
    ) -> Path:
        """Exports live vessels (Points) and historical tracks (LineStrings) as standard GeoJSON."""
        features: List[Dict[str, Any]] = []
        for v in vessels:
            if v.get("lat") is None or v.get("lon") is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [v["lon"], v["lat"]],
                },
                "properties": {
                    "feature_type": "vessel_position",
                    "mmsi": v.get("mmsi"),
                    "imo": v.get("imo"),
                    "name": v.get("name"),
                    "type": v.get("type") or v.get("category_group"),
                    "country": v.get("country"),
                    "sog_knots": v.get("sog_knots"),
                    "heading_deg": v.get("heading_deg"),
                    "destination": v.get("destination_raw"),
                },
            })

        if track_vessels:
            for tv in track_vessels:
                pts = tv.get("track_points") or []
                if len(pts) >= 2:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[p["lon"], p["lat"]] for p in pts],
                        },
                        "properties": {
                            "feature_type": "vessel_track",
                            "mmsi": tv.get("mmsi"),
                            "imo": tv.get("imo"),
                            "name": tv.get("name"),
                            "points_count": len(pts),
                        },
                    })

        geojson = {"type": "FeatureCollection", "features": features}
        path = EXPORTS_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        return path

    @staticmethod
    def build_studio_js_bundle(payload: Dict[str, Any], filename: str = "vesselfinder_live_bundle.js") -> Path:
        """Builds a self-contained JS bundle (`window.VESSELFINDER_DATA`) for `vesselfinder_studio.html`."""
        path = EXPORTS_DIR / filename
        js_content = (
            "// Auto-generated by VesselFinder Scraper Suite\n"
            f"window.VESSELFINDER_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return path

    @staticmethod
    def download_ship_photo(photo_url: str, ship_name: str, mmsi_or_imo: int) -> Optional[Path]:
        if not photo_url:
            return None
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", ship_name.strip()).strip("_").lower() or "vessel"
        out_path = IMAGES_DIR / f"{safe_name}_{mmsi_or_imo}.jpg"
        if out_path.exists() and out_path.stat().st_size > 1000:
            return out_path
        try:
            r = requests.get(photo_url, headers=DEFAULT_HEADERS, timeout=12)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return out_path
        except Exception:
            pass
        return None

