#!/usr/bin/env python3
"""
Test suite for REA Reverse Engineering integration
"""

import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from rea_runner import ReaRunner


class TestReaRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ReaRunner()

    def test_environment_check(self):
        ok, msg = self.runner.check_environment()
        self.assertTrue(ok, f"Environment check failed: {msg}")

    def test_inspect_signature(self):
        res = self.runner.inspect_signature("/bin/ls")
        self.assertTrue(res["success"], f"Failed inspect_signature: {res.get('raw_stderr')}")
        norm = res.get("data", {}).get("normalized_result", {})
        self.assertIn("signed", norm)
        self.assertEqual(norm.get("identifier"), "com.apple.ls")

    def test_list_architectures(self):
        res = self.runner.list_architectures("/bin/ls")
        self.assertTrue(res["success"], f"Failed list_architectures: {res.get('raw_stderr')}")
        norm = res.get("data", {}).get("normalized_result", {})
        archs = norm.get("architectures", {}).get("items", [])
        self.assertGreater(len(archs), 0)

    def test_inspect_har(self):
        har_path = str(BASE_DIR / "data" / "samples" / "sample_api.har")
        res = self.runner.inspect_har(har_path)
        self.assertTrue(res["success"], f"Failed inspect_har: {res.get('raw_stderr')}")
        norm = res.get("data", {}).get("normalized_result", {})
        self.assertGreaterEqual(norm.get("total_records", 0), 1)

    def test_mcp_doctor(self):
        res = self.runner.mcp_doctor()
        self.assertTrue(res["success"], f"Failed mcp_doctor: {res.get('raw_stderr')}")
        self.assertIn("healthy: true", res.get("raw_stdout", ""))


if __name__ == "__main__":
    unittest.main()
