"""ทดสอบโปรโตคอลและตัวป้องกันคำสั่ง — รันด้วย: python3 -m unittest discover tests"""
import os
import socket
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import web_controller as wc  # noqa: E402


class ProtocolTest(unittest.TestCase):
    def test_center_packet_matches_original(self):
        # ค่ากลางทุกก้าน, ไม่มีคำสั่ง — ต้องตรงกับที่ drone_controller.py ต้นฉบับส่ง
        self.assertEqual(wc.build_ctrl(0x80, 0x80, 0x80, 0x80, 0).hex(),
                         "036614808080800002000000000000000000000299")

    def test_checksum_is_xor_of_bytes_3_to_18(self):
        pkt = wc.build_ctrl(0x10, 0xF0, 0x80, 0x7F, wc.CMD_TAKEOFF_LAND)
        chk = 0
        for b in pkt[3:19]:
            chk ^= b
        self.assertEqual(len(pkt), 21)
        self.assertEqual(pkt[19], chk)
        self.assertEqual(pkt[20], 0x99)

    def test_stick_byte_scaling_and_clamp(self):
        self.assertEqual(wc.stick_byte(0, 1.0), 0x80)
        self.assertEqual(wc.stick_byte(1, 1.0), 0xFF)
        self.assertEqual(wc.stick_byte(-1, 1.0), 0x01)
        self.assertEqual(wc.stick_byte(1, 0.3), 0x80 + round(127 * 0.3))
        self.assertEqual(wc.stick_byte(9, 1.0), 0xFF)          # เกินช่วง -> ตัด
        self.assertEqual(wc.stick_byte(float("nan"), 1.0), 0x80)
        self.assertEqual(wc.stick_byte("x", 1.0), 0x80)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.d = wc.Drone("127.0.0.1", 9, live=False)

    def tearDown(self):
        self.d.stop()

    def test_land_refused_when_grounded(self):
        ok, _ = self.d.command("land")
        self.assertFalse(ok)

    def test_takeoff_refused_when_flying(self):
        self.assertTrue(self.d.command("takeoff")[0])
        self.assertFalse(self.d.command("takeoff")[0])

    def test_disarm_refused_when_flying(self):
        self.d.command("takeoff")
        self.assertFalse(self.d.command("disarm")[0])

    def test_estop_always_allowed(self):
        self.d.command("takeoff")
        ok, _ = self.d.command("estop")
        self.assertTrue(ok)
        self.assertFalse(self.d.flying)

    def test_output_respects_speed_and_deadman(self):
        self.d.set_sticks(0, 1, 0, 0)
        self.assertEqual(self.d.snapshot()["out"], [0, 30, 0, 0])   # 30% เริ่มต้น
        self.d.last_input = time.monotonic() - 1                    # เกิน deadman
        self.assertEqual(self.d.snapshot()["out"], [0, 0, 0, 0])


class LiveSendTest(unittest.TestCase):
    def test_packets_reach_udp_target_only_when_armed(self):
        rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rx.bind(("127.0.0.1", 0))
        rx.settimeout(0.5)
        d = wc.Drone("127.0.0.1", rx.getsockname()[1], live=True)
        d.start()
        try:
            got = []
            end = time.monotonic() + 0.6
            while time.monotonic() < end:
                try:
                    got.append(rx.recv(64))
                except socket.timeout:
                    break
            self.assertTrue(all(len(p) == 2 for p in got), "ก่อน ARM ต้องมีแค่ heartbeat")
            d.command("arm")
            pkt = rx.recv(64)
            while len(pkt) != 21:
                pkt = rx.recv(64)
            self.assertEqual(pkt[:3], bytes([0x03, 0x66, 0x14]))
        finally:
            d.stop()
            rx.close()


if __name__ == "__main__":
    unittest.main()
