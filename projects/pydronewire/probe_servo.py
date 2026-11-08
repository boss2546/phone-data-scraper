#!/usr/bin/env python3
"""
Brute-force probe for camera servo control.

Tests each of the 10 unknown bytes (indices 9-18) in the 21-byte
control packet by sweeping values while keeping all sticks centered.

Usage:
  1. Connect to FLOW-UFO WiFi
  2. ARM the drone (or just power it on — servo may respond without arming)
  3. Run:  python3 probe_servo.py
  4. Watch the camera servo — if it moves during a test, note the byte index

The script tests one byte at a time, sweeping from 0x00 -> 0xFF -> 0x00
over ~4 seconds per byte, with a 2-second pause between bytes.
Total time: ~60 seconds for all 10 bytes.

Press Ctrl+C to stop at any time. The current byte index being tested
is printed to the terminal so you know which one caused movement.
"""

import socket
import time
import sys

DRONE_IP   = "192.168.1.1"
CTRL_PORT  = 7099
HB_INTERVAL = 1.0

# Idle packet template (sticks centered, no command)
#  [0x03, 0x66, 0x14, roll=0x80, pitch=0x80, thr=0x80, yaw=0x80,
#   cmd=0x00, spd=0x02, b9..b18=0x00, checksum, 0x99]
IDLE = [0x03, 0x66, 0x14,
        0x80, 0x80, 0x80, 0x80,  # sticks centered
        0x00, 0x02,              # cmd=idle, speed=0x02
        0x00, 0x00, 0x00, 0x00, 0x00,  # bytes 9-13
        0x00, 0x00, 0x00, 0x00, 0x00]  # bytes 14-18
# checksum and footer appended by build_pkt()

def build_pkt(template):
    """Compute XOR checksum over bytes[3:19] and append checksum + 0x99."""
    pkt = list(template)
    chk = 0
    for b in pkt[3:19]:
        chk ^= b
    pkt.append(chk)
    pkt.append(0x99)
    return bytes(pkt)

def send(sock, pkt):
    try:
        sock.sendto(pkt, (DRONE_IP, CTRL_PORT))
    except OSError:
        pass

def send_heartbeat(sock):
    send(sock, bytes([0x01, 0x01]))

def send_idle(sock, n=20, hz=20):
    """Send idle packets for n packets at hz rate."""
    pkt = build_pkt(IDLE)
    interval = 1.0 / hz
    for _ in range(n):
        send(sock, pkt)
        time.sleep(interval)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("\n  FLOW-UFO Camera Servo Probe")
    print("  ===========================")
    print(f"  Target: {DRONE_IP}:{CTRL_PORT}")
    print(f"  Testing 10 unknown bytes (indices 9-18)")
    print(f"  Each byte: sweep 0x00 -> 0xFF -> 0x00 over ~4s")
    print(f"  Total estimated time: ~60 seconds")
    print(f"\n  Watch the camera servo. If it moves, note the byte index!")
    print(f"  Press Ctrl+C to stop.\n")

    # Send heartbeats + idle for 2 seconds to establish connection
    print("  [INIT] Establishing connection (2s)...")
    t0 = time.monotonic()
    last_hb = 0
    while time.monotonic() - t0 < 2.0:
        now = time.monotonic()
        if now - last_hb >= HB_INTERVAL:
            send_heartbeat(sock)
            last_hb = now
        send(sock, build_pkt(IDLE))
        time.sleep(0.05)

    # NOTE: No cmd=0x01 sent — that triggers full takeoff!
    # "Armed" just means we're sending control packets (sticks centered).
    # The drone's servo should respond to byte changes without flying.
    print("  [READY] Sending idle control packets (no takeoff).")
    print("  NOTE: If servo needs motors spinning, take off manually")
    print("        with the main controller first, then run this script.\n")

    results = []

    for byte_idx in range(9, 19):
        byte_num = byte_idx - 9 + 1
        print(f"  [{byte_num:2d}/10] Testing byte {byte_idx} ...", end="", flush=True)

        # Phase 1: sweep UP  0x00 -> 0xFF
        # Phase 2: sweep DOWN 0xFF -> 0x00
        # Total 512 steps at 20Hz = ~25 seconds... too slow.
        # Instead: test key values: 0, 64, 128, 192, 255, 192, 128, 64, 0
        # Hold each for 0.4s (8 packets at 20Hz) = ~3.6s per byte
        test_values = [0x00, 0x40, 0x80, 0xC0, 0xFF, 0xC0, 0x80, 0x40, 0x00]
        hold_packets = 8  # packets per value at 20Hz = 0.4s

        t_start = time.monotonic()
        for val in test_values:
            template = list(IDLE)
            template[byte_idx] = val
            pkt = build_pkt(template)
            for _ in range(hold_packets):
                now = time.monotonic()
                if now - last_hb >= HB_INTERVAL:
                    send_heartbeat(sock)
                    last_hb = now
                send(sock, pkt)
                time.sleep(0.05)
        elapsed = time.monotonic() - t_start

        print(f"  done ({elapsed:.1f}s)")

        # Brief pause — send idle for 1 second to let servo settle
        print(f"         Settling (1s idle)...", flush=True)
        t_settle = time.monotonic()
        while time.monotonic() - t_settle < 1.0:
            now = time.monotonic()
            if now - last_hb >= HB_INTERVAL:
                send_heartbeat(sock)
                last_hb = now
            send(sock, build_pkt(IDLE))
            time.sleep(0.05)

    print("\n  ========== PROBE COMPLETE ==========")
    print("  If the camera servo moved during any test,")
    print("  the byte index printed at that moment is your servo control byte.")
    print("  Re-run with just that byte to confirm:")
    print("    python3 probe_servo.py --byte <INDEX>")
    print()

    # Single-byte confirmation mode
    if len(sys.argv) >= 3 and sys.argv[1] == "--byte":
        pass  # handled below

    sock.close()

def confirm_byte(byte_idx):
    """Repeatedly sweep a single byte to confirm servo control."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"\n  CONFIRM MODE — Byte {byte_idx}")
    print(f"  Sweeping byte {byte_idx}: 0x00 -> 0xFF -> 0x00 continuously")
    print(f"  Press Ctrl+C to stop.\n")

    last_hb = time.monotonic()
    send_heartbeat(sock)

    # Establish connection
    print("  [INIT] Connecting (2s)...")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 2.0:
        now = time.monotonic()
        if now - last_hb >= HB_INTERVAL:
            send_heartbeat(sock)
            last_hb = now
        send(sock, build_pkt(IDLE))
        time.sleep(0.05)

    print("  [READY] Starting sweep (no takeoff)...\n")

    try:
        while True:
            # Slow continuous sweep: 256 steps up, 256 steps down
            for direction in [range(0, 256, 2), range(255, -1, -2)]:
                for val in direction:
                    now = time.monotonic()
                    if now - last_hb >= HB_INTERVAL:
                        send_heartbeat(sock)
                        last_hb = now
                    template = list(IDLE)
                    template[byte_idx] = val
                    pkt = build_pkt(template)
                    send(sock, pkt)
                    sys.stdout.write(f"\r  byte[{byte_idx}] = 0x{val:02X} ({val:3d})  ")
                    sys.stdout.flush()
                    time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\n  Stopped. Sending idle...")
        send_idle(sock, n=40)
        sock.close()
        print("  Done.")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--byte":
        try:
            idx = int(sys.argv[2])
            if idx < 9 or idx > 18:
                print(f"  Error: byte index must be 9-18, got {idx}")
                sys.exit(1)
            confirm_byte(idx)
        except ValueError:
            print(f"  Error: invalid byte index '{sys.argv[2]}'")
            sys.exit(1)
    else:
        main()
