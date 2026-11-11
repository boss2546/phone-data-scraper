# -*- coding: utf-8 -*-
"""
VesselFinder Binary Protocol Decoder (Reverse-Engineered from Web Worker & Map Bundles)
--------------------------------------------------------------------------------------
Decodes the proprietary binary ArrayBuffer streams returned by VesselFinder:
1. /api/pub/mp2          -> Live AIS vessels in a bounding box (drawShipsOnMapBinary)
2. /api/pub/ms?name=     -> Real-time ship autocomplete search (mapSearch)
3. /api/pub/ml/<mmsi>    -> High-precision live ship coordinates & SOG (mapLocation)
4. /api/pub/track/<mmsi> -> Historical voyage track XOR-encoded with 0x55555555 & 0x5555 (getTrack)
5. /api/pro/ports/v4/bin -> Global database of 257 countries and 11,367 ports with coordinates (getPorts)
"""

import struct
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

from config.settings import (
    COORD_FACTOR,
    TRACK_LON_LAT_XOR,
    TRACK_COG_SOG_XOR,
    VESSEL_COLOR_TYPES,
)


class VesselFinderBinaryDecoder:
    """Decodes proprietary binary responses from VesselFinder endpoints."""

    @staticmethod
    def decode_ships_on_map(buf: bytes, zoom: int = 12) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Decodes binary stream from `/api/pub/mp2?bbox=...&zoom=...&mmsi=0&ref=...&mcbe=1`.
        Returns (total_global_ships, list_of_vessel_dicts).
        """
        P = len(buf)
        if P < 4:
            return 0, []

        Y = struct.unpack_from(">H", buf, 1)[0] if P >= 12 else 0
        total_global_ships = struct.unpack_from(">i", buf, 8)[0] if (Y >= 8 and P >= 12) else 0

        I = 4 + Y
        if I > P or I < 4:
            return total_global_ships, []

        lt = struct.unpack_from(">i", buf, I - 4)[0]
        is_high_zoom = zoom > 13
        ships: List[Dict[str, Any]] = []

        while I < P:
            if I + 16 > P:
                break

            S = struct.unpack_from(">h", buf, I)[0]
            color_code = (S & 240) >> 4
            icon_num = (S & 16128) >> 8
            is_old = bool(S & 1)
            is_sar = (S & 2) != 0
            I += 2

            mmsi = struct.unpack_from(">i", buf, I)[0]
            I += 4
            is_selected = (mmsi == lt)

            lat = struct.unpack_from(">i", buf, I)[0] / COORD_FACTOR
            I += 4
            lon = struct.unpack_from(">i", buf, I)[0] / COORD_FACTOR
            I += 4

            cog: Optional[float] = None
            sog: Optional[float] = None
            if is_selected and I + 6 <= P:
                cog = round(struct.unpack_from(">h", buf, I)[0] / 10.0, 1)
                sog = round(struct.unpack_from(">h", buf, I + 2)[0] / 10.0, 1)
                I += 6

            if I + 2 > P:
                break
            td = struct.unpack_from(">b", buf, I)[0]
            I += 1
            name_len = struct.unpack_from(">B", buf, I)[0]
            I += 1

            if I + name_len > P:
                break
            name = buf[I : I + name_len].decode("utf-8", errors="replace").strip()
            I += name_len
            if not name:
                name = str(mmsi)

            tstamp = 0
            if is_selected and I + 4 <= P:
                tstamp = struct.unpack_from(">i", buf, I)[0]
                I += 4

            heading_deg: Optional[int] = int(icon_num * 11.25) if icon_num < 32 else None
            dimensions: Optional[Dict[str, int]] = None

            if is_high_zoom and I + 10 <= P:
                g, u_, m, p, q = struct.unpack_from(">hhhhh", buf, I)
                I += 10
                if 0 <= q <= 360:
                    heading_deg = int(q)
                length_m = g + u_
                beam_m = m + p
                if length_m > 0 and beam_m > 0:
                    dimensions = {
                        "length_m": length_m,
                        "beam_m": beam_m,
                        "bow_m": g,
                        "stern_m": u_,
                        "port_m": m,
                        "starboard_m": p,
                    }

            if is_sar:
                if not is_high_zoom and I + 2 <= P:
                    I += 2
                continue

            ships.append({
                "mmsi": mmsi,
                "name": name,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "heading_deg": heading_deg,
                "cog": cog,
                "sog_knots": sog,
                "type_color_code": color_code,
                "category_group": VESSEL_COLOR_TYPES.get(color_code, "Other / Unknown"),
                "is_old_signal": is_old,
                "td": td,
                "dimensions": dimensions,
                "timestamp": tstamp or None,
            })

        return total_global_ships, ships

    @staticmethod
    def decode_map_search(buf: bytes, country_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Decodes binary stream from `/api/pub/ms?name=<query>`.
        Returns list of matching vessels with IMO, MMSI, Flag, Name, and Ship Type.
        """
        total_len = len(buf)
        if total_len <= 2:
            return []

        results: List[Dict[str, Any]] = []
        pos = 0
        while pos + 12 <= total_len:
            imo, mmsi = struct.unpack_from(">ii", buf, pos)
            a2 = buf[pos + 8 : pos + 10].decode("latin1", errors="replace").lower().strip()
            r_flag = struct.unpack_from(">b", buf, pos + 10)[0]
            pos += 11

            if pos >= total_len:
                break
            name_len = struct.unpack_from(">B", buf, pos)[0]
            pos += 1
            if name_len & 1:
                pos += 1
            if pos + name_len > total_len:
                break
            name = buf[pos : pos + name_len].decode("utf-8", errors="replace").strip()
            pos += name_len
            if not name:
                name = str(mmsi)

            if pos >= total_len:
                break
            type_len = struct.unpack_from(">B", buf, pos)[0]
            pos += 1
            if pos + type_len > total_len:
                break
            ship_type = buf[pos : pos + type_len].decode("utf-8", errors="replace").strip()
            if type_len & 1:
                pos += 1
            pos += type_len

            flag_code = a2 if a2 else "unknown"
            results.append({
                "imo": imo,
                "mmsi": mmsi,
                "name": name,
                "type": ship_type,
                "flag_code": flag_code,
                "country": (country_map or {}).get(flag_code, ""),
                "r_flag": r_flag,
                "details_url": f"https://www.vesselfinder.com/vessels/details/{imo if imo > 0 else mmsi}",
            })

        return results

    @staticmethod
    def decode_map_location(buf: bytes, mmsi: int) -> Optional[Dict[str, Any]]:
        """
        Decodes binary stream from `/api/pub/ml/<mmsi>`.
        Returns exact live coordinates (lat, lon), speed (sog), and vessel title.
        """
        if len(buf) <= 2 or len(buf) < 13:
            return None

        flags = struct.unpack_from(">b", buf, 0)[0]
        is_sar = (flags & 2) > 0
        is_sl = (flags & 16) > 0
        sog = round(struct.unpack_from(">h", buf, 1)[0] / 10.0, 1)
        lon = round(struct.unpack_from(">i", buf, 3)[0] / COORD_FACTOR, 6)
        lat = round(struct.unpack_from(">i", buf, 7)[0] / COORD_FACTOR, 6)
        title_len = struct.unpack_from(">B", buf, 11)[0]

        if 12 + title_len + 4 > len(buf):
            return None

        title = buf[12 : 12 + title_len].decode("utf-8", errors="replace").strip()
        d_val = struct.unpack_from(">i", buf, 12 + title_len)[0]

        return {
            "mmsi": mmsi,
            "name": title,
            "lat": lat,
            "lon": lon,
            "sog_knots": sog,
            "is_sar": is_sar,
            "is_satellite": is_sl,
            "d_value": d_val,
        }

    @staticmethod
    def decode_vessel_track(buf: bytes, mmsi: int) -> List[Dict[str, Any]]:
        """
        Decodes XOR-obfuscated binary stream from `/api/pub/track/<mmsi>`.
        Each point is 16 bytes:
        - bytes 0..3:  uint32 timestamp
        - bytes 4..7:  int32  lon ^ 0x55555555 (1431655765) / 600000.0
        - bytes 8..11: int32  lat ^ 0x55555555 (1431655765) / 600000.0
        - bytes 12..13: uint16 cog ^ 0x5555 (21845) / 10.0
        - bytes 14..15: uint16 sog ^ 0x5555 (21845) / 10.0
        """
        total_len = len(buf)
        if total_len < 16:
            return []

        points: List[Dict[str, Any]] = []
        limit = total_len - (total_len % 16)
        for offset in range(0, limit, 16):
            ts, raw_lon, raw_lat, raw_cog, raw_sog = struct.unpack_from(">IiiHH", buf, offset)
            lon = round((TRACK_LON_LAT_XOR ^ raw_lon) / COORD_FACTOR, 6)
            lat = round((TRACK_LON_LAT_XOR ^ raw_lat) / COORD_FACTOR, 6)
            cog = round((TRACK_COG_SOG_XOR ^ raw_cog) / 10.0, 1)
            sog = round((TRACK_COG_SOG_XOR ^ raw_sog) / 10.0, 1)
            iso_time = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            points.append({
                "timestamp": ts,
                "datetime_utc": iso_time,
                "lat": lat,
                "lon": lon,
                "cog_deg": cog,
                "sog_knots": sog,
            })

        return points

    @staticmethod
    def decode_global_ports(buf: bytes) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        Decodes binary stream from `/api/pro/ports/v4/bin`.
        Returns (country_map, list_of_11367_global_ports).
        """
        e = len(buf)
        if e <= 4:
            return {}, []

        country_count = struct.unpack_from(">H", buf, 0)[0]
        i = 2
        country_map: Dict[str, str] = {}

        for _ in range(country_count):
            if i + 3 > e:
                break
            code = buf[i : i + 2].decode("latin1", errors="replace").lower()
            i += 2
            nlen = buf[i]
            i += 1
            if i + nlen > e:
                break
            cname = buf[i : i + nlen].decode("utf-8", errors="replace").strip()
            i += nlen
            country_map[code] = cname

        if i + 2 > e:
            return country_map, []

        port_count = struct.unpack_from(">H", buf, i)[0]
        i += 2
        ports: List[Dict[str, Any]] = []
        cnt = 0

        while i < e and cnt <= port_count:
            if i + 9 > e:
                break
            locode = buf[i : i + 8].decode("latin1", errors="replace").strip()
            a2 = locode[:2].lower()
            i += 8
            g = buf[i]
            status = (192 & g) >> 6
            nlen = g & 63
            i += 1
            if i + nlen + 8 > e:
                break
            pname = buf[i : i + nlen].decode("utf-8", errors="replace").strip()
            i += nlen
            lon = round(struct.unpack_from(">i", buf, i)[0] / COORD_FACTOR, 6)
            i += 4
            lat = round(struct.unpack_from(">i", buf, i)[0] / COORD_FACTOR, 6)
            i += 4

            ports.append({
                "locode": locode,
                "short_locode": locode[:5],
                "name": pname,
                "country_code": a2,
                "country": country_map.get(a2, ""),
                "lat": lat,
                "lon": lon,
                "status": status,
                "port_type": "Major Port" if status == 1 else ("Minor Port / Terminal" if status == 2 else "Anchorage / Offshore"),
                "url": f"https://www.vesselfinder.com/ports/{locode}",
            })
            cnt += 1

        return country_map, ports

