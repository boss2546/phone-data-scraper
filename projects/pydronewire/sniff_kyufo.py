#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sniff_kyufo.py — อ่านไฟล์ดักจับ (.pcap / .pcapng) แล้วบอกว่าแอป KY UFO ส่งอะไรไปที่โดรน
ใช้หาไบต์ของปุ่มที่ pyDroneWire ยังไม่รู้จัก เช่น หลบสิ่งกีดขวาง, ไฟ, โหมดความเร็ว

ใช้ได้กับไฟล์จาก:
  - tcpdump บน rvi0 (ดักจาก iPhone ที่เสียบสาย ผ่าน rvictl)
  - Wireless Diagnostics > Sniffer ของ macOS (ถ้า WiFi โดรนไม่มีรหัส)
  - Wireshark

วิธีใช้:
    python3 sniff_kyufo.py capture.pcap
    python3 sniff_kyufo.py capture.pcap --marks 12.5,20,31      # เวลาที่คุณกดปุ่มในแอป (วินาทีนับจากเริ่มดักจับ)
    python3 sniff_kyufo.py capture.pcap --dump                  # พิมพ์ทุกแพ็กเก็ต

ไม่ต้องติดตั้งอะไรเพิ่ม (ใช้แค่ Python มาตรฐาน)
"""
import argparse
import struct
import sys
from collections import Counter, OrderedDict

DRONE_IP_DEFAULT = "192.168.1.1"
CTRL_PORT_DEFAULT = 7099
STICK_IDX = (3, 4, 5, 6)          # roll, pitch, throttle, yaw — เปลี่ยนตลอด ไม่สนใจ
CHK_IDX = 19                      # checksum เปลี่ยนตามค่าอื่น ไม่สนใจ
KNOWN_CMD = {0x01: "ขึ้นบิน/ลงจอด", 0x02: "STOP", 0x08: "ตีลังกา", 0x10: "Headless", 0x80: "คาลิเบรตไจโร"}
FIELD_NAME = {7: "cmd", 8: "speed"}


# ───────────── อ่านไฟล์ pcap / pcapng ─────────────
def read_capture(path):
    """คืน list ของ (เวลา_วินาที, bytes ของแพ็กเก็ตดิบ)"""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 24:
        raise ValueError("ไฟล์สั้นเกินไป ไม่ใช่ไฟล์ดักจับ")
    magic = data[:4]
    if magic == b"\x0a\x0d\x0d\x0a":
        return list(_read_pcapng(data))
    return list(_read_pcap(data))


def _read_pcap(data):
    magic = struct.unpack("<I", data[:4])[0]
    if magic in (0xA1B2C3D4, 0xA1B23C4D):
        e = "<"
    elif magic in (0xD4C3B2A1, 0x4D3CB2A1):
        e = ">"
    else:
        raise ValueError("ไม่รู้จักรูปแบบไฟล์ (ไม่ใช่ pcap/pcapng)")
        # noqa
    nano = magic in (0xA1B23C4D, 0x4D3CB2A1)
    off = 24
    while off + 16 <= len(data):
        sec, frac, incl, _ = struct.unpack(e + "IIII", data[off:off + 16])
        off += 16
        pkt = data[off:off + incl]
        off += incl
        yield sec + frac / (1e9 if nano else 1e6), pkt


def _read_pcapng(data):
    off, e, tsres = 0, "<", {}
    while off + 12 <= len(data):
        btype = struct.unpack(e + "I", data[off:off + 4])[0]
        if btype == 0x0A0D0D0A:                     # Section Header: กำหนด endian
            bom = data[off + 8:off + 12]
            e = "<" if bom == b"\x4d\x3c\x2b\x1a" else ">"
            tsres = {}
        blen = struct.unpack(e + "I", data[off + 4:off + 8])[0]
        if blen < 12 or off + blen > len(data):
            break
        body = data[off + 8:off + blen - 4]
        if btype == 1:                              # Interface Description
            iface = len(tsres)
            res = 1e-6
            o = 8
            while o + 4 <= len(body):
                code, ln = struct.unpack(e + "HH", body[o:o + 4])
                if code == 0:
                    break
                if code == 9 and ln >= 1:
                    v = body[o + 4]
                    res = 2 ** -(v & 0x7F) if v & 0x80 else 10 ** -v
                o += 4 + ((ln + 3) & ~3)
            tsres[iface] = res
        elif btype == 6 and len(body) >= 20:        # Enhanced Packet
            iface, hi, lo, cap, _ = struct.unpack(e + "IIIII", body[:20])
            ts = ((hi << 32) | lo) * tsres.get(iface, 1e-6)
            yield ts, body[20:20 + cap]
        elif btype == 3 and len(body) >= 4:         # Simple Packet
            yield 0.0, body[4:]
        off += blen


# ───────────── หา UDP ในแพ็กเก็ต (ไม่ขึ้นกับชนิดลิงก์) ─────────────
def ip_bytes(ip):
    return bytes(int(x) for x in ip.split("."))


def find_udp(pkt, drone_ip_b):
    """หา IPv4/UDP ที่มี IP โดรนเป็นต้นทางหรือปลายทาง คืน (src, sport, dst, dport, payload) หรือ None
    ค้นหาหัว IPv4 จากตำแหน่ง IP โดรน จึงใช้ได้กับ Ethernet, RAW, PKTAP (rvi0) และ 802.11 ที่ไม่เข้ารหัส"""
    start = 0
    while True:
        i = pkt.find(drone_ip_b, start)
        if i < 0:
            return None
        start = i + 1
        for hdr in (i - 16, i - 12):                # IP โดรนอยู่ช่องปลายทาง (16) หรือต้นทาง (12)
            if hdr < 0 or hdr + 20 > len(pkt):
                continue
            vihl = pkt[hdr]
            if vihl >> 4 != 4 or (vihl & 0xF) < 5 or pkt[hdr + 9] != 17:
                continue
            ihl = (vihl & 0xF) * 4
            total = struct.unpack(">H", pkt[hdr + 2:hdr + 4])[0]
            u = hdr + ihl
            if u + 8 > len(pkt) or total < ihl + 8:
                continue
            sport, dport, ulen = struct.unpack(">HHH", pkt[u:u + 6])
            payload = pkt[u + 8:u + max(8, ulen)]
            src = ".".join(str(b) for b in pkt[hdr + 12:hdr + 16])
            dst = ".".join(str(b) for b in pkt[hdr + 16:hdr + 20])
            return src, sport, dst, dport, payload


# ───────────── วิเคราะห์ ─────────────
def is_ctrl(p):
    return len(p) == 21 and p[0] == 0x03 and p[1] == 0x66 and p[2] == 0x14 and p[20] == 0x99


def describe_cmd(v):
    if v == 0:
        return "0x00 (ไม่มีคำสั่ง)"
    names = [n for b, n in KNOWN_CMD.items() if v & b]
    unknown = v & ~sum(KNOWN_CMD)
    s = "0x%02x" % v
    if names:
        s += " (" + ", ".join(names) + ")"
    if unknown:
        s += "  << บิตที่ยังไม่รู้จัก 0x%02x" % unknown
    return s


def main():
    ap = argparse.ArgumentParser(description="วิเคราะห์คำสั่งที่แอป KY UFO ส่งไปที่โดรน")
    ap.add_argument("capture", help="ไฟล์ .pcap หรือ .pcapng")
    ap.add_argument("--drone-ip", default=DRONE_IP_DEFAULT)
    ap.add_argument("--port", type=int, default=CTRL_PORT_DEFAULT)
    ap.add_argument("--marks", default="", help="เวลาที่กดปุ่มในแอป (วินาที) คั่นด้วยจุลภาค")
    ap.add_argument("--dump", action="store_true", help="พิมพ์ทุกแพ็กเก็ตที่ส่งไปที่โดรน")
    a = ap.parse_args()

    try:
        pkts = read_capture(a.capture)
    except (OSError, ValueError) as e:
        sys.exit("อ่านไฟล์ไม่ได้: %s" % e)
    dip = ip_bytes(a.drone_ip)
    marks = [float(x) for x in a.marks.split(",") if x.strip()]

    t0 = None
    flows = Counter()
    ctrl = []                 # (t, payload) ที่ส่งไปพอร์ตควบคุม
    other = OrderedDict()     # payload อื่นที่ส่งไปพอร์ตควบคุม -> [ครั้งแรก, จำนวน]
    for ts, raw in pkts:
        u = find_udp(raw, dip)
        if not u:
            continue
        src, sport, dst, dport, pl = u
        if t0 is None:
            t0 = ts
        t = ts - t0
        flows[("ส่งไปโดรน" if dst == a.drone_ip else "จากโดรน", dport if dst == a.drone_ip else sport)] += 1
        if dst == a.drone_ip and dport == a.port:
            if is_ctrl(pl):
                ctrl.append((t, pl))
            else:
                k = pl.hex()
                if k not in other:
                    other[k] = [t, 0]
                other[k][1] += 1
            if a.dump:
                print("%8.3f  %s" % (t, pl.hex()))

    print("\nไฟล์: %s  (%d แพ็กเก็ตทั้งหมด)" % (a.capture, len(pkts)))
    if not flows:
        print("ไม่พบ UDP ที่ไป/มาจาก %s" % a.drone_ip)
        print("ตรวจว่า: iPhone ต่อ WiFi โดรนและเปิดแอปอยู่ตอนดักจับ หรือ IP โดรนไม่ใช่ %s (ใช้ --drone-ip)" % a.drone_ip)
        return
    print("\nการรับส่ง UDP กับโดรน")
    for (d, port), n in flows.most_common():
        print("  %-10s พอร์ต %-6d %6d แพ็กเก็ต" % (d, port, n))

    print("\nแพ็กเก็ตควบคุม 21 ไบต์: %d ครั้ง" % len(ctrl))
    if ctrl:
        print("\nการเปลี่ยนแปลงของไบต์ที่ไม่ใช่ก้านจอย (นี่คือสิ่งที่ต้องดู)")
        prev = None
        changes = 0
        for t, p in ctrl:
            fields = {i: p[i] for i in range(7, 19)}
            if prev is not None:
                for i, v in fields.items():
                    if v != prev[i]:
                        changes += 1
                        name = FIELD_NAME.get(i, "ไบต์ %d" % i)
                        desc = describe_cmd(v) if i == 7 else "0x%02x" % v
                        near = ""
                        if marks:
                            m = min(marks, key=lambda x: abs(x - t))
                            if abs(m - t) <= 1.5:
                                near = "   <- ใกล้จังหวะที่กด (%.1fs)" % m
                        print("  %8.2fs  %-7s 0x%02x -> %s%s" % (t, name, prev[i], desc, near))
            prev = fields
        if not changes:
            print("  ไม่มีการเปลี่ยน ไบต์ 7-18 คงที่ตลอดไฟล์ = %s" % ctrl[0][1][7:19].hex())
        cmd_seen = Counter(p[7] for _, p in ctrl if p[7])
        if cmd_seen:
            print("\nค่า cmd ที่เจอ")
            for v, n in cmd_seen.most_common():
                print("  %-45s %5d แพ็กเก็ต (~%.1f วินาที)" % (describe_cmd(v), n, n / 20.0))

    print("\nแพ็กเก็ตอื่นที่ส่งไปพอร์ต %d (ไม่ใช่แพ็กเก็ตควบคุม)" % a.port)
    if not other:
        print("  ไม่มี")
    for k, (t, n) in other.items():
        tag = "heartbeat" if k == "0101" else ("สลับกล้อง" if len(k) == 4 and k.startswith("06") else "<< ยังไม่รู้จัก")
        print("  ครั้งแรก %8.2fs  %4d ครั้ง  %-20s %s" % (t, n, k, tag))
    print()


if __name__ == "__main__":
    main()
