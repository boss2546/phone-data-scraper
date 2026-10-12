#!/usr/bin/env python3
"""
REA Runner — Python Automation & Analysis Wrapper for REA (Reverse Engineer Anything)
Powered by https://github.com/morluto/rea (rea-agents v6.4.0+)
"""

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MODULE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = MODULE_DIR / "config" / "config.json"
RESULTS_DIR = MODULE_DIR / "data" / "results"
SAMPLES_DIR = MODULE_DIR / "data" / "samples"


class ReaRunner:
    def __init__(self):
        self.config = self._load_config()
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir = SAMPLES_DIR

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "rea_cli_runner": "npx -y rea-agents",
            "default_format": "json"
        }

    @staticmethod
    def check_environment() -> Tuple[bool, str]:
        """Check if Node.js and npx are installed in the system."""
        node_path = shutil.which("node")
        npx_path = shutil.which("npx")

        if not node_path or not npx_path:
            return False, "❌ ไม่พบ Node.js หรือ npx ในระบบ กรุณาติดตั้ง Node.js (v18+) ก่อนใช้งาน"

        try:
            node_ver = subprocess.check_output(["node", "-v"], text=True).strip()
            npx_ver = subprocess.check_output(["npx", "-v"], text=True).strip()
            return True, f"✅ สิ่งแวดล้อมพร้อมใช้งาน (Node.js: {node_ver}, npx: {npx_ver})"
        except Exception as e:
            return False, f"⚠️ เกิดข้อผิดพลาดขณะตรวจสอบ Node.js: {e}"

    def execute_rea(self, sub_command: str, args: Optional[List[str]] = None, output_format: str = "json", timeout: int = 45) -> Dict[str, Any]:
        """Execute a REA command via npx and return parsed output and status."""
        args = args or []
        cmd = ["npx", "-y", "rea-agents", sub_command] + args
        if output_format and "--format" not in args:
            cmd.extend(["--format", output_format])

        start_time = time.time()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = round(time.time() - start_time, 2)
            stdout = res.stdout.strip()
            stderr = res.stderr.strip()

            parsed_data = None
            if stdout:
                try:
                    parsed_data = json.loads(stdout)
                except json.JSONDecodeError:
                    parsed_data = stdout

            return {
                "success": res.returncode == 0,
                "returncode": res.returncode,
                "elapsed_sec": elapsed,
                "command": " ".join(cmd),
                "data": parsed_data,
                "raw_stdout": stdout,
                "raw_stderr": stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "elapsed_sec": timeout,
                "command": " ".join(cmd),
                "data": None,
                "raw_stdout": "",
                "raw_stderr": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "elapsed_sec": 0,
                "command": " ".join(cmd),
                "data": None,
                "raw_stdout": "",
                "raw_stderr": str(e)
            }

    def save_result(self, operation: str, result: Dict[str, Any]) -> Path:
        """Save analysis output to data/results/ as JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_op = operation.replace("-", "_").replace(" ", "_")
        filename = f"{timestamp}_{safe_op}.json"
        dest = self.results_dir / filename
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return dest

    def inspect_signature(self, binary_path: str) -> Dict[str, Any]:
        """Inspect digital signatures and certificates (Codesign / Mach-O / ELF)."""
        abs_path = str(Path(binary_path).resolve())
        res = self.execute_rea("inspect-signature", [abs_path])
        if res["success"]:
            self.save_result("inspect_signature", res)
        return res

    def list_architectures(self, binary_path: str) -> Dict[str, Any]:
        """List CPU architectures and Mach-O / ELF slices."""
        abs_path = str(Path(binary_path).resolve())
        res = self.execute_rea("list-architectures", [abs_path])
        if res["success"]:
            self.save_result("list_architectures", res)
        return res

    def inspect_plist(self, app_or_plist_path: str) -> Dict[str, Any]:
        """Inspect Apple Info.plist without launching external UI tools."""
        abs_path = str(Path(app_or_plist_path).resolve())
        res = self.execute_rea("inspect-plist", [abs_path])
        if res["success"]:
            self.save_result("inspect_plist", res)
        return res

    def trace_dylib(self, binary_path: str) -> Dict[str, Any]:
        """Trace dyld resolution and dynamic library linkages."""
        abs_path = str(Path(binary_path).resolve())
        res = self.execute_rea("trace-dylib-resolution", [abs_path])
        if res["success"]:
            self.save_result("trace_dylib_resolution", res)
        return res

    def inspect_har(self, har_path: str) -> Dict[str, Any]:
        """Inspect HTTP/API network transactions in a HAR file."""
        abs_path = str(Path(har_path).resolve())
        res = self.execute_rea("inspect-web-network-capture", [abs_path, "har"])
        if res["success"]:
            self.save_result("inspect_web_network_capture", res)
        return res

    def mcp_doctor(self) -> Dict[str, Any]:
        """Run REA MCP doctor diagnostics."""
        return self.execute_rea("mcp", ["doctor"], output_format="")

    def run_diagnostics(self) -> List[Dict[str, Any]]:
        """Run a full self-test suite covering core REA capabilities."""
        tests = []
        sample_har = str(self.samples_dir / "sample_api.har")
        sample_bin = "/bin/ls"
        sample_app = "/System/Applications/Calculator.app"

        # 1. Signature
        r1 = self.inspect_signature(sample_bin)
        tests.append({"name": "Signature Inspection (/bin/ls)", "pass": r1["success"], "details": r1.get("elapsed_sec")})

        # 2. Architectures
        r2 = self.list_architectures(sample_bin)
        tests.append({"name": "Architecture Slices (/bin/ls)", "pass": r2["success"], "details": r2.get("elapsed_sec")})

        # 3. Plist
        r3 = self.inspect_plist(sample_app)
        tests.append({"name": f"App Plist Inspection ({sample_app})", "pass": r3["success"], "details": r3.get("elapsed_sec")})

        # 4. Network HAR
        r4 = self.inspect_har(sample_har)
        tests.append({"name": "Web Network Capture (sample_api.har)", "pass": r4["success"], "details": r4.get("elapsed_sec")})

        # 5. MCP Doctor
        r5 = self.mcp_doctor()
        tests.append({"name": "MCP Server Doctor Status", "pass": r5["success"], "details": r5.get("elapsed_sec")})

        return tests
