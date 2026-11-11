#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VesselFinder.com Master CLI & AIS Maritime Intelligence Pipeline
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import MARITIME_ZONES
from src.scrapers.vessel_scraper import VesselFinderScraper
from src.services.storage_service import VesselStorageService


def print_banner():
    print("=" * 76)
    print("🚢 VesselFinder Scraper & Live AIS Maritime Radar Intelligence Suite")
    print("   ระบบดึงข้อมูลเรือเดินสมุทร เรดาร์ AIS สด เส้นทางเดินเรือ และฐานข้อมูลท่าเรือทั่วโลก")
    print("=" * 76)


def cmd_radar(zone_key: str = "thailand_all_seas", enrich_limit: int = 50):
    scraper = VesselFinderScraper()
    zone_info = MARITIME_ZONES.get(zone_key) or MARITIME_ZONES["thailand_all_seas"]
    print(f"\n📡 กำลังสแกนเรดาร์ AIS สดในโซน: {zone_info['name_th']} ...")
    radar_data = scraper.fetch_zone_vessels(zone_key=zone_key, enrich_limit=enrich_limit)
    vessels = radar_data["vessels"]

    print(f"✅ พบเรือออนไลน์ทั่วโลกขณะนี้: {radar_data['global_online_ships']:,} ลำ")
    print(f"🚢 พบเรือกำลังแล่นในน่านน้ำไทย (ไม่ซ้ำ MMSI): {len(vessels):,} ลำ (ดึงข้อมูลเชิงลึกสำเร็จ {radar_data.get('enriched_vessels_count', 0)} ลำ)")

    if radar_data.get("sector_breakdown"):
        print(f"\n🗺️  สรุปจำนวนเรือแยกตาม {len(radar_data['sector_breakdown'])} โซนย่อย (Multi-Grid Sub-Sector Breakdown):")
        print("-" * 76)
        for sb in radar_data["sector_breakdown"]:
            cnt = sb.get("vessels_count", sb.get("raw_count", 0))
            print(f"  • {sb['name_th']:<62} : {cnt:>4} ลำ")
        print("-" * 76)

    if radar_data.get("category_breakdown"):
        print("\n📊 สรุปจำนวนเรือแยกตามประเภทเรือ (Vessel Type Breakdown):")
        for cat, cnt in sorted(radar_data["category_breakdown"].items(), key=lambda x: -x[1]):
            print(f"  • {cat:<38} : {cnt:>4} ลำ")

    # Attach historical tracks & local HD photos from cache for commercial vessels
    import json
    from config.settings import JSON_DIR, IMAGES_DIR
    commercial = [v for v in vessels if v.get("imo") and v.get("imo") > 0][:10]
    tracked_vessels = []
    downloaded_photos = len(list(IMAGES_DIR.glob("*.jpg")))
    for cv in commercial:
        mmsi = cv["mmsi"]
        cached_v_file = JSON_DIR / f"vessel_{mmsi}.json"
        if cached_v_file.exists():
            try:
                with open(cached_v_file, "r", encoding="utf-8") as f:
                    v_doc = json.load(f)
                if v_doc.get("track_points"):
                    cv["track_points"] = v_doc["track_points"]
                    tracked_vessels.append(cv)
            except Exception:
                pass
        safe_name = "".join(c if c.isalnum() else "_" for c in cv["name"]).strip("_").lower()
        img_candidate = IMAGES_DIR / f"{safe_name}_{mmsi}.jpg"
        if img_candidate.exists():
            cv["local_photo"] = f"data/images/{img_candidate.name}"

    # Also fetch Thailand ports for overlay
    th_ports = scraper.fetch_global_ports(country_code="th")
    radar_data["thailand_ports_count"] = len(th_ports)
    radar_data["thailand_ports"] = th_ports

    # Save JSON, CSV, GeoJSON & Studio JS Bundle
    json_path = VesselStorageService.save_json(radar_data, f"live_radar_{zone_key}.json")
    csv_path = VesselStorageService.export_vessels_csv(vessels, f"vessels_{zone_key}.csv")
    geojson_path = VesselStorageService.export_geojson(vessels, tracked_vessels, f"radar_{zone_key}.geojson")
    bundle_path = VesselStorageService.build_studio_js_bundle(radar_data, "vesselfinder_live_bundle.js")

    patrol_list = radar_data.get("patrol_military_vessels", [])
    if patrol_list:
        VesselStorageService.save_json(patrol_list, "patrol_and_military_vessels.json")
        VesselStorageService.export_vessels_csv(patrol_list, "patrol_and_military_vessels.csv")

    print("\n" + "-" * 76)
    print("📋 ตัวอย่างเรือเดินสมุทรในพื้นที่ (Top 10 Enriched Vessels):")
    for idx, s in enumerate([v for v in vessels if v.get("type")][:10], 1):
        voyage = s.get("voyage") or {}
        dest = voyage.get("next_port_name") or s.get("destination_raw") or "-"
        sog = f"{s['sog_knots']} kn" if s.get("sog_knots") is not None else "-"
        print(
            f"  {idx:2d}. {s['name']:<22} | MMSI: {s['mmsi']} | IMO: {s.get('imo') or '-':<8} "
            f"| {s.get('type', s['category_group']):<24} | ความเร็ว: {sog:<7} | ปลายทาง: {dest}"
        )
    print("-" * 76)
    print(f"💾 บันทึก JSON:          {json_path.relative_to(BASE_DIR)}")
    print(f"📊 ส่งออก Excel CSV:     {csv_path.relative_to(BASE_DIR)}")
    print(f"🗺️  ส่งออกแผนที่ GeoJSON:  {geojson_path.relative_to(BASE_DIR)}")
    if patrol_list:
        print(f"🛡️  ส่งออกเรือตรวจการณ์:  data/exports/patrol_and_military_vessels.csv ({len(patrol_list)} ลำ)")
    print(f"📸 ดาวน์โหลดรูปเรือ HD:   {downloaded_photos} รูป (ใน data/images/)")
    print(f"🌐 อัปเดต Web Studio SDK: {bundle_path.relative_to(BASE_DIR)} (เปิดดูที่ vesselfinder_studio.html)")
    return radar_data


def cmd_patrol():
    scraper = VesselFinderScraper()
    print("\n⚓ 🛡️ กำลังสแกนเรดาร์ตรวจจับ 'เรือรบ • เรือตรวจการณ์ชายฝั่ง • เรือตำรวจน้ำ' ทั่วทั้ง 2 ฝั่งทะเลไทย (อ่าวไทย + อันดามัน) ...")
    radar_data = scraper.scan_all_thailand_waters(enrich_limit=30)
    patrol_vessels = radar_data.get("patrol_military_vessels", [])

    print(f"\n✅ ตรวจพบเรือตรวจการณ์ / เรือรบ / เรือตำรวจน้ำ / เรือราชการในน่านน้ำไทยทั้งหมด: {len(patrol_vessels)} ลำ")
    print("=" * 80)
    for idx, v in enumerate(patrol_vessels, 1):
        sog = f"{v['sog_knots']} kn" if v.get("sog_knots") is not None else "-"
        role = v.get("patrol_military_role", "Government Craft")
        print(f"  {idx:2d}. {v['name']:<26} | MMSI: {str(v['mmsi']):<10} | {role}")
        print(f"      📍 พิกัด: {v['lat']:.4f}°N, {v['lon']:.4f}°E | ความเร็ว: {sog:<7} | โซน: {v.get('sector_name_th', '-')}")
    print("=" * 80)

    json_path = VesselStorageService.save_json(patrol_vessels, "patrol_and_military_vessels.json")
    csv_path = VesselStorageService.export_vessels_csv(patrol_vessels, "patrol_and_military_vessels.csv")
    print(f"💾 บันทึก JSON เรือตรวจการณ์:  {json_path.relative_to(BASE_DIR)}")
    print(f"📊 ส่งออก Excel CSV เรือตรวจการณ์: {csv_path.relative_to(BASE_DIR)}")
    return patrol_vessels


def cmd_fishing():
    scraper = VesselFinderScraper()
    print("\n🐟 🎣 กำลังสแกนเรดาร์ตรวจจับ 'เรือประมงไทย' (Fishing Vessels) ทั่ว 2 ฝั่งทะเลไทย ...")
    radar_data = scraper.scan_all_thailand_waters(enrich_limit=30)
    vessels = radar_data.get("vessels", [])
    fishing_vessels = []
    for v in vessels:
        vtype = str(v.get("type", "")).upper()
        cat = str(v.get("category_group", "")).upper()
        name = str(v.get("name", "")).upper()
        if "FISH" in vtype or "FISH" in cat or "MFV" in name or "F/V" in name or "ประมง" in name or "PRAMONG" in name or "CHOK" in name or "โชค" in name:
            fishing_vessels.append(v)

    print(f"\n✅ ตรวจพบเรือประมงกำลังออกหาปลาในน่านน้ำไทย: {len(fishing_vessels)} ลำ")
    print("=" * 80)
    for idx, v in enumerate(fishing_vessels[:20], 1):
        sog = f"{v['sog_knots']} kn" if v.get("sog_knots") is not None else "-"
        print(f"  {idx:2d}. {v['name']:<26} | MMSI: {str(v['mmsi']):<10} | ความเร็ว: {sog:<7} | โซน: {v.get('sector_name_th', '-')[:32]}")
    if len(fishing_vessels) > 20:
        print(f"  ... และอีก {len(fishing_vessels) - 20} ลำ (ดูต่อได้ในไฟล์ Excel ค่ะ)")
    print("=" * 80)

    json_path = VesselStorageService.save_json(fishing_vessels, "fishing_vessels.json")
    csv_path = VesselStorageService.export_vessels_csv(fishing_vessels, "fishing_vessels.csv")
    print(f"💾 บันทึก JSON เรือประมง:  {json_path.relative_to(BASE_DIR)}")
    print(f"📊 ส่งออก Excel CSV เรือประมง: {csv_path.relative_to(BASE_DIR)}")
    return fishing_vessels


def cmd_photos():
    from src.services.photo_harvester import PhotoHarvester
    print("\n" + "=" * 76)
    print("📸 🚢 โครงการกวาดรูปถ่ายเรือเดินสมุทรทั้งหมด (All Ship Photos & Multi-Galleries)")
    print("   ดาวน์โหลดรูปถ่ายเรือ HD ทั้งหมดลงเครื่อง และสร้างแกลเลอรีภาพถ่ายเรือหลายมุมมอง")
    print("=" * 76)
    harvester = PhotoHarvester(max_workers=8)
    summary = harvester.harvest_all(update_databases=True)
    return summary


def cmd_serve(port: int = 8000):
    import uvicorn
    print("\n" + "=" * 76)
    print(f"🚀 กำลังสตาร์ท VesselFinder Live Maritime Radar Microservice ที่พอร์ต {port}...")
    print(f"📖 Swagger UI API Docs : http://localhost:{port}/docs")
    print(f"🌐 Interactive Studio   : http://localhost:{port}/")
    print(f"📡 Radar Endpoint       : http://localhost:{port}/api/radar")
    print(f"⚓ Patrol Endpoint      : http://localhost:{port}/api/patrol")
    print(f"🐟 Fishing Endpoint     : http://localhost:{port}/api/fishing")
    print(f"❤️  Healthcheck         : http://localhost:{port}/health")
    print("=" * 76)
    uvicorn.run("src.api:app", host="0.0.0.0", port=port, reload=False)


def cmd_search(query: str):
    scraper = VesselFinderScraper()
    print(f"\n🔍 กำลังค้นหาเรือทั่วโลกด้วยคำค้น: '{query}' ...")
    results = scraper.search_vessels(query)
    print(f"✅ พบผลลัพธ์ทั้งหมด {len(results)} ลำ:")
    print("-" * 76)
    for idx, r in enumerate(results, 1):
        print(
            f"  {idx:2d}. {r['name']:<25} | IMO: {r['imo']:<9} | MMSI: {r['mmsi']:<10} "
            f"| ธง: {r['flag_code'].upper()} ({r['country']}) | ประเภท: {r['type']}"
        )
    print("-" * 76)
    if results:
        out = VesselStorageService.save_json(results, f"search_{query.strip().lower().replace(' ', '_')}.json")
        print(f"💾 บันทึกผลการค้นหาที่: {out.relative_to(BASE_DIR)}")
    return results


def cmd_ship_detail(mmsi_or_imo_str: str):
    digits = "".join(ch for ch in str(mmsi_or_imo_str) if ch.isdigit())
    if not digits:
        print("❌ กรุณาระบุเลข MMSI (9 หลัก) หรือ IMO (7 หลัก)")
        return None

    target_id = int(digits)
    scraper = VesselFinderScraper()
    print(f"\n🛳️  กำลังดึงข้อมูลเชิงลึก 360° ของเรือรหัส {target_id} ...")
    intel = scraper.fetch_vessel_full_intelligence(target_id)

    name = intel.get("name") or intel.get("technical_specs", {}).get("Vessel Name") or f"Vessel_{target_id}"
    photo_path = None
    if intel.get("photo_url_hd"):
        photo_path = VesselStorageService.download_ship_photo(
            intel["photo_url_hd"], name, intel.get("mmsi") or target_id
        )
        if photo_path:
            intel["local_photo"] = f"data/images/{photo_path.name}"

    json_path = VesselStorageService.save_json(intel, f"vessel_{target_id}.json")
    if intel.get("track_points"):
        VesselStorageService.export_geojson([intel], [intel], f"vessel_{target_id}_track.geojson")

    voyage = intel.get("voyage") or {}
    weather = intel.get("weather") or {}
    print("\n" + "=" * 76)
    print(f"🚢 ชื่อเรือ:          {name}")
    print(f"🆔 IMO / MMSI:       IMO {intel.get('imo') or '-'} / MMSI {intel.get('mmsi') or '-'}")
    print(f"🏷️  ประเภท / ธงชาติ:   {intel.get('type', '-')} / {intel.get('country', '-')} ({intel.get('flag_code', '-').upper()})")
    print(f"📐 ขนาด / ตันกรอส:   ยาว {intel.get('length_m') or '-'} m × กว้าง {intel.get('beam_m') or '-'} m | GT: {intel.get('gt') or '-'} | DWT: {intel.get('dwt') or '-'}")
    print(f"📍 พิกัดปัจจุบัน:       Lat {intel.get('lat', '-')}, Lon {intel.get('lon', '-')}")
    print(f"⚡ ความเร็ว / ทิศทาง:  {intel.get('sog_knots', '-')} knots / {intel.get('cog_deg', '-')}° ({intel.get('nav_status', '-')})")
    print(f"⚓ ท่าเรือต้นทางล่าสุด:  {voyage.get('last_port_name') or '-'} ({voyage.get('last_port_country') or '-'}) [ออกเมื่อ: {voyage.get('last_port_atd_utc') or '-'}]")
    print(f"🎯 ท่าเรือปลายทาง:     {voyage.get('next_port_name') or intel.get('destination_raw') or '-'} [ETA: {voyage.get('next_port_eta_utc') or intel.get('eta_utc') or '-'}]")
    if weather:
        print(
            f"🌊 สภาพอากาศจุดเรือ:  อุณหภูมิ {weather.get('air_temp_c')}°C | ลม {weather.get('wind_speed_knots')} kn ({weather.get('wind_dir_deg')}°) "
            f"| คลื่นสูง {weather.get('wave_height_m')} m"
        )
    print(f"🛤️  จุดพิกัดย้อนหลัง:    {intel.get('track_points_count', 0)} จุด (ถอดรหัส XOR Binary Track)")
    if photo_path:
        print(f"📸 รูปถ่ายเรือ HD:     {photo_path.relative_to(BASE_DIR)}")
    print(f"💾 ไฟล์ JSON ข้อมูลเต็ม: {json_path.relative_to(BASE_DIR)}")
    print("=" * 76)
    return intel


def cmd_port_traffic(locode: str = "THLCH001"):
    scraper = VesselFinderScraper()
    print(f"\n⚓ กำลังปลดล็อกและสแกนเรือสดในท่าเรือ {locode.upper()} ...")
    data = scraper.scan_port_live_traffic(locode=locode, radius_deg=0.08, enrich_limit=30)
    port = data["port"]
    vessels = data["vessels"]

    json_path = VesselStorageService.save_json(data, f"port_traffic_{port['locode'].lower()}.json")
    csv_path = VesselStorageService.export_vessels_csv(vessels, f"port_traffic_{port['locode'].lower()}.csv")

    print(f"✅ ท่าเรือ: {port['name']} ({port['locode']}) — {port['country']} [Lat {port['lat']}, Lon {port['lon']}]")
    print(f"🚢 พบเรือในบริเวณท่าเรือทั้งหมด: {len(vessels)} ลำ")
    print("-" * 76)
    for idx, v in enumerate(vessels[:15], 1):
        sog = f"{v['sog_knots']} kn" if v.get("sog_knots") is not None else "-"
        print(
            f"  {idx:2d}. {v['name']:<22} | MMSI: {v['mmsi']} | {v.get('type', v['category_group']):<24} "
            f"| ความเร็ว: {sog:<7} | พิกัด: ({v['lat']}, {v['lon']})"
        )
    print("-" * 76)
    print(f"💾 บันทึก JSON:      {json_path.relative_to(BASE_DIR)}")
    print(f"📊 ส่งออก Excel CSV: {csv_path.relative_to(BASE_DIR)}")
    return data


def cmd_ports_database(country_code: str = ""):
    scraper = VesselFinderScraper()
    print("\n🌍 กำลังดึงและถอดรหัสฐานข้อมูลท่าเรือทั่วโลก (/api/pro/ports/v4/bin) ...")
    all_ports = scraper.fetch_global_ports()
    th_ports = [p for p in all_ports if p["country_code"] == "th"]

    VesselStorageService.save_json(all_ports, "global_ports_all.json")
    th_json = VesselStorageService.save_json(th_ports, "thailand_ports.json")
    th_csv = VesselStorageService.export_ports_csv(th_ports, "thailand_ports.csv")
    all_csv = VesselStorageService.export_ports_csv(all_ports, "global_ports_all.csv")

    print(f"✅ ถอดรหัสสำเร็จ: ท่าเรือทั่วโลก {len(all_ports):,} แห่ง | ท่าเรือในประเทศไทย {len(th_ports)} แห่ง")
    target_list = scraper.fetch_global_ports(country_code) if country_code else th_ports
    label = f"ประเทศ '{country_code.upper()}'" if country_code else "ประเทศไทย (Thailand)"
    print(f"\n📋 รายชื่อท่าเรือใน{label} ({len(target_list)} แห่ง):")
    print("-" * 76)
    for idx, p in enumerate(target_list[:25], 1):
        print(
            f"  {idx:2d}. [{p['locode']}] {p['name']:<24} | {p['country']:<12} "
            f"| Lat: {p['lat']:<9} Lon: {p['lon']:<10} | {p['port_type']}"
        )
    print("-" * 76)
    print(f"💾 ท่าเรือไทย JSON/CSV: {th_json.relative_to(BASE_DIR)}, {th_csv.relative_to(BASE_DIR)}")
    print(f"💾 ท่าเรือโลก CSV:      {all_csv.relative_to(BASE_DIR)}")
    return target_list


def cmd_catalog(page: int = 1, flag: str = ""):
    scraper = VesselFinderScraper()
    print(f"\n📚 กำลังดึงตารางฐานข้อมูลเรือจาก /vessels (หน้า {page}{', ธง ' + flag.upper() if flag else ''}) ...")
    items = scraper.scrape_vessels_catalog(page=page, flag=flag)
    print(f"✅ ดึงสำเร็จ {len(items)} ลำ:")
    print("-" * 76)
    for idx, it in enumerate(items, 1):
        print(
            f"  {idx:2d}. {it['name']:<24} | IMO: {it['imo']} | {it['type']:<24} "
            f"| ธง: {it['country']:<14} | ปี: {it['year_built'] or '-'} | ขนาด: {it['size_m']} m"
        )
    print("-" * 76)
    if items:
        suffix = f"_{flag.lower()}" if flag else ""
        jpath = VesselStorageService.save_json(items, f"catalog_page_{page}{suffix}.json")
        cpath = VesselStorageService.export_vessels_csv(items, f"catalog_page_{page}{suffix}.csv")
        print(f"💾 บันทึก JSON & CSV: {jpath.relative_to(BASE_DIR)}, {cpath.relative_to(BASE_DIR)}")
    return items


def cmd_run_all():
    print_banner()
    print("🚀 เริ่มรัน Full Pipeline ดึงข้อมูล VesselFinder.com ครบทุกมิติ...")
    cmd_ports_database("th")
    radar = cmd_radar("upper_gulf_th", enrich_limit=30)
    cmd_port_traffic("THLCH001")
    cmd_catalog(page=1, flag="TH")
    # Fetch one flagship vessel 360 intelligence
    enriched = [v for v in radar["vessels"] if v.get("imo") and v.get("imo") > 0]
    if enriched:
        cmd_ship_detail(str(enriched[0]["mmsi"]))
    print("\n🎉 เสร็จสมบูรณ์ 100%! สามารถเปิดดูแผนที่เรดาร์ได้ที่: projects/vesselfinder_scraper/vesselfinder_studio.html")


def interactive_menu():
    while True:
        print_banner()
        print("เลือกโหมดการดึงข้อมูลจาก VesselFinder.com:")
        print("  [1] 📡 สแกนเรดาร์เรือสดในอ่าวไทย (กรุงเทพฯ - แหลมฉบัง - ศรีราชา) [Live AIS Radar]")
        print("  [2] ⚓ ปลดล็อกรายชื่อเรือสดในท่าเรือแหลมฉบัง (THLCH001) หรือท่าเรือกรุงเทพ (THBKK001)")
        print("  [3] 🔍 ค้นหาเรือทั่วโลกด้วยชื่อเรือ / IMO / MMSI (/api/pub/ms Binary Search)")
        print("  [4] 🛳️  เจาะลึกข้อมูลเรือรายลำ 360° (สเปก + พิกัดสด + สภาพอากาศ + เส้นทาง XOR Track + รูป HD)")
        print("  [5] 🌍 ดึงฐานข้อมูลท่าเรือทั่วโลก 11,367 แห่ง & ท่าเรือไทย 49 แห่ง (/api/pro/ports/v4/bin)")
        print("  [6] 📚 ดึงตารางแคตตาล็อกเรือเดินสมุทรจาก /vessels (กรองตามธงชาติได้ เช่น TH, SG, PA)")
        print("  [7] 🛡️  เรดาร์เรือรบ เรือตรวจการณ์ชายฝั่ง & เรือตำรวจน้ำ ทั่วอ่าวไทย (Patrol & Navy Radar)")
        print("  [8] 📸 กวาดและดาวน์โหลดรูปถ่ายเรือ HD ทั้งหมดลงเครื่อง (Multi-Photo Harvester)")
        print("  [9] 🚀 รันดึงข้อมูลครบวงจร (Full Pipeline + อัปเดต Web Radar Studio)")
        print("  [0] กลับเมนูหลัก / ออกจากโปรแกรม")
        print("-" * 76)
        choice = input("👉 เลือกเมนู (0-9): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            print("\nโซนเรดาร์ที่รองรับ:")
            for idx, (zk, zval) in enumerate(MARITIME_ZONES.items(), 1):
                print(f"  [{idx}] {zk:<18} -> {zval['name_th']}")
            z_in = input("เลือกโซน (กด Enter เพื่อใช้ค่าเริ่มต้น upper_gulf_th): ").strip()
            zone_keys = list(MARITIME_ZONES.keys())
            if z_in.isdigit() and 1 <= int(z_in) <= len(zone_keys):
                zk = zone_keys[int(z_in) - 1]
            else:
                zk = z_in if z_in in MARITIME_ZONES else "upper_gulf_th"
            cmd_radar(zk)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "2":
            loc = input("ระบุรหัสท่าเรือ UN/LOCODE (กด Enter สำหรับแหลมฉบัง THLCH001 หรือพิมพ์ THBKK001, SGSIN001): ").strip() or "THLCH001"
            cmd_port_traffic(loc)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "3":
            q = input("ระบุชื่อเรือ / IMO / MMSI ที่ต้องการค้นหา (เช่น maersk, evergreen, bhum): ").strip() or "maersk"
            cmd_search(q)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "4":
            sid = input("ระบุเลข MMSI หรือ IMO (กด Enter เพื่อดูตัวอย่าง 352002065 MAERSK ACADIA): ").strip() or "352002065"
            cmd_ship_detail(sid)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "5":
            cc = input("ระบุรหัสประเทศ 2 ตัวอักษร (กด Enter สำหรับประเทศไทย 'th' หรือพิมพ์ 'sg', 'jp'): ").strip() or "th"
            cmd_ports_database(cc)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "6":
            fl = input("ระบุรหัสธงชาติ เช่น TH, SG, PA (หรือกด Enter เพื่อดูเรือขนาดใหญ่ที่สุดในโลก): ").strip()
            cmd_catalog(page=1, flag=fl)
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "7":
            cmd_patrol()
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "8":
            cmd_photos()
            input("\nกด Enter เพื่อดำเนินการต่อ...")
        elif choice == "9":
            cmd_run_all()
            input("\nกด Enter เพื่อดำเนินการต่อ...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("radar", "live", "map", "gulf", "thailand", "all"):
            zone = sys.argv[2] if len(sys.argv) > 2 else "thailand_all_seas"
            cmd_radar(zone)
        elif cmd in ("patrol", "navy", "police", "military", "guard"):
            cmd_patrol()
        elif cmd in ("fishing", "fish", "pramong"):
            cmd_fishing()
        elif cmd in ("api", "serve", "microservice", "server", "web"):
            p = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8000
            cmd_serve(port=p)
        elif cmd == "search":
            q = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "maersk"
            cmd_search(q)
        elif cmd in ("ship", "vessel", "detail", "track"):
            sid = sys.argv[2] if len(sys.argv) > 2 else "352002065"
            cmd_ship_detail(sid)
        elif cmd == "port":
            loc = sys.argv[2] if len(sys.argv) > 2 else "THLCH001"
            cmd_port_traffic(loc)
        elif cmd == "ports":
            cc = sys.argv[2] if len(sys.argv) > 2 else "th"
            cmd_ports_database(cc)
        elif cmd in ("catalog",):
            fl = sys.argv[2] if len(sys.argv) > 2 else "TH"
            cmd_catalog(page=1, flag=fl)
        elif cmd in ("photos", "photo", "images", "gallery", "harvest-photos"):
            cmd_photos()
        elif cmd in ("all", "run"):
            cmd_run_all()
        else:
            print(f"❌ ไม่รู้จักคำสั่ง: {cmd}")
            print("💡 คำสั่งที่รองรับ: radar [zone] | patrol | fishing | photos | api [port] | search <query> | ship <mmsi/imo> | port <locode> | ports [cc] | catalog [flag] | all")
    else:
        interactive_menu()
