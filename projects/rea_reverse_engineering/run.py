#!/usr/bin/env python3
"""
Launcher for REA Reverse Engineering Module
Modular Suite component for reverse engineering binaries, formats, and network captures.
"""

import sys
import json
from pathlib import Path

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from rea_runner import ReaRunner


def print_banner():
    print("=" * 72)
    print("🔬 REA Reverse Engineering Suite — Reverse Engineer Anything")
    print("   ระบบวิเคราะห์โครงสร้าง Binary, Plist, Dynamic Library & Network HAR")
    print("   (อ้างอิงและขับเคลื่อนด้วย https://github.com/morluto/rea)")
    print("=" * 72)


def format_json_output(data):
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)


def handle_signature(runner: ReaRunner, target: str = None):
    target = target or input("📁 ระบุพาธไฟล์ Binary (ค่าเริ่มต้น: /bin/ls): ").strip() or "/bin/ls"
    print(f"\n🔍 กำลังตรวจสอบ Digital Signature: {target} ...")
    res = runner.inspect_signature(target)
    if res["success"]:
        print(f"✅ สำเร็จใน {res['elapsed_sec']} วินาที!")
        norm = res.get("data", {}).get("normalized_result", {})
        print(f"   • Signed: {norm.get('signed')}")
        print(f"   • Identifier: {norm.get('identifier')}")
        print(f"   • Format: {norm.get('format')}")
        print(f"   • Authorities: {', '.join(norm.get('authorities', []))}")
        print(f"   • Designated Requirement: {norm.get('designated_requirement')}")
    else:
        print("❌ การตรวจสอบล้มเหลว:")
        print(res.get("raw_stderr") or res.get("raw_stdout"))


def handle_architectures(runner: ReaRunner, target: str = None):
    target = target or input("📁 ระบุพาธไฟล์ Binary (ค่าเริ่มต้น: /bin/ls): ").strip() or "/bin/ls"
    print(f"\n🏗️ กำลังวิเคราะห์สถาปัตยกรรม CPU: {target} ...")
    res = runner.list_architectures(target)
    if res["success"]:
        print(f"✅ สำเร็จใน {res['elapsed_sec']} วินาที!")
        norm = res.get("data", {}).get("normalized_result", {})
        archs = norm.get("architectures", {}).get("items", [])
        print(f"   • รวมทั้งหมด: {len(archs)} สถาปัตยกรรม")
        for item in archs:
            print(f"     - สถาปัตยกรรม: {item.get('name')} | ขนาด: {item.get('size')} bytes | Offset: {item.get('file_offset')}")
    else:
        print("❌ การตรวจสอบล้มเหลว:")
        print(res.get("raw_stderr") or res.get("raw_stdout"))


def handle_plist(runner: ReaRunner, target: str = None):
    target = target or input("📱 ระบุพาธ App Bundle หรือ Plist (ค่าเริ่มต้น: /System/Applications/Calculator.app): ").strip() or "/System/Applications/Calculator.app"
    print(f"\n📱 กำลังถอดรหัส Property List: {target} ...")
    res = runner.inspect_plist(target)
    if res["success"]:
        print(f"✅ สำเร็จใน {res['elapsed_sec']} วินาที!")
        norm = res.get("data", {}).get("normalized_result", {})
        bundle = norm.get("bundle", {})
        val = norm.get("value", {})
        print(f"   • Bundle ID: {bundle.get('identifier')}")
        print(f"   • Executable: {bundle.get('executable')}")
        print(f"   • Version: {bundle.get('short_version')} (Build {bundle.get('version')})")
        print(f"   • Min OS Version: {val.get('LSMinimumSystemVersion', 'N/A')}")
        print(f"   • URL Schemes: {val.get('PrivateURLSchemes', [])}")
    else:
        print("❌ การตรวจสอบล้มเหลว:")
        print(res.get("raw_stderr") or res.get("raw_stdout"))


def handle_dylib(runner: ReaRunner, target: str = None):
    target = target or input("🔗 ระบุพาธไฟล์ Binary เพื่อตรวจ dependencies (ค่าเริ่มต้น: /bin/ls): ").strip() or "/bin/ls"
    print(f"\n🔗 กำลังวิเคราะห์ Dynamic Library Dependencies: {target} ...")
    res = runner.trace_dylib(target)
    if res["success"]:
        print(f"✅ สำเร็จใน {res['elapsed_sec']} วินาที!")
        norm = res.get("data", {}).get("normalized_result", {})
        edges = norm.get("edges", [])
        print(f"   • พบการเชื่อมโยง: {len(edges)} เส้นทาง")
        seen_dylibs = set()
        for edge in edges:
            dylib = edge.get("install_name")
            if dylib and dylib not in seen_dylibs:
                seen_dylibs.add(dylib)
                print(f"     ↳ {dylib} (Arch: {edge.get('architecture')})")
    else:
        print("❌ การตรวจสอบล้มเหลว:")
        print(res.get("raw_stderr") or res.get("raw_stdout"))


def handle_har(runner: ReaRunner, target: str = None):
    default_sample = str(BASE_DIR / "data" / "samples" / "sample_api.har")
    target = target or input(f"🌐 ระบุพาธไฟล์ HAR (ค่าเริ่มต้น: {default_sample}): ").strip() or default_sample
    print(f"\n🌐 กำลังวิเคราะห์ HAR Network Capture: {target} ...")
    res = runner.inspect_har(target)
    if res["success"]:
        print(f"✅ สำเร็จใน {res['elapsed_sec']} วินาที!")
        norm = res.get("data", {}).get("normalized_result", {})
        total = norm.get("total_records", 0)
        print(f"   • จำนวน Records: {total}")
        for rec in norm.get("records", []):
            rep = rec.get("reported", {})
            req = rep.get("request", {})
            resp = rep.get("response", {})
            print(f"     ↳ [{req.get('method')}] {req.get('url')}")
            print(f"       Status: {resp.get('status')} | Content Size: {resp.get('content', {}).get('size')} bytes")
    else:
        print("❌ การตรวจสอบล้มเหลว:")
        print(res.get("raw_stderr") or res.get("raw_stdout"))


def handle_doctor(runner: ReaRunner):
    print("\n🤖 กำลังทดสอบสถานะ REA MCP Server (mcp doctor) ...")
    res = runner.mcp_doctor()
    print(res.get("raw_stdout") or res.get("raw_stderr"))


def handle_diagnostics(runner: ReaRunner):
    print("\n🧪 กำลังรันชุดทดสอบความสมบูรณ์ REA Diagnostics ทั้งหมด ...")
    tests = runner.run_diagnostics()
    print("-" * 60)
    all_pass = True
    for t in tests:
        mark = "✅ PASS" if t["pass"] else "❌ FAIL"
        if not t["pass"]:
            all_pass = False
        print(f"{mark} | {t['name']} ({t.get('details')}s)")
    print("-" * 60)
    if all_pass:
        print("🎉 ผลการทดสอบ: ผ่านครบ 100% ทุกชุดคำสั่ง!")
    else:
        print("⚠️ มีบางชุดการทดสอบไม่ผ่าน กรุณาตรวจสอบบันทึกผล")


def handle_custom(runner: ReaRunner):
    cmd_str = input("💻 ป้อนคำสั่ง REA (เช่น inspect-signature /bin/zsh หรือ trace-dylib-resolution /bin/zsh): ").strip()
    if not cmd_str:
        return
    parts = cmd_str.split()
    sub_cmd = parts[0]
    extra = parts[1:]
    print(f"\n🚀 กำลังรันคำสั่ง: rea {cmd_str} ...")
    res = runner.execute_rea(sub_cmd, extra, output_format="toon")
    print(res.get("raw_stdout") or res.get("raw_stderr"))


def handle_showcase_scraper(runner: ReaRunner):
    from scraper_re_toolkit import ScraperReverseToolkit
    print("\n" + "=" * 72)
    print("🪄 REA FOR WEB SCRAPING & INTERCEPTION SHOWCASE")
    print("   สาธิตการเชื่อมโยงพลัง REA เข้าสู่โปรเจกต์ดึงข้อมูล (Scraping Suite)")
    print("=" * 72)

    # 1. Reverse engineer HAR -> Python Scraper code
    har_path = str(BASE_DIR / "data" / "samples" / "sample_api.har")
    print(f"\n[Case 1] 🌐 ดักแกะ Network Capture ({har_path}) -> แปลงเป็น Code สำหรับดึงข้อมูล:")
    res_har = runner.inspect_har(har_path)
    if res_har["success"]:
        recipes = ScraperReverseToolkit.har_to_scraper_recipe(res_har["data"])
        for r in recipes["recipes"]:
            print(f"  • Endpoint ที่ตรวจพบ: [{r['method']}] {r['url']}")
            print(f"  • โค้ด Python Requests ที่สร้างให้อัตโนมัติ:\n")
            for line in r["generated_code"].splitlines():
                print(f"    {line}")
    
    # 2. Reverse engineer App Bundle -> Deeplinks
    app_path = "/System/Applications/Calculator.app"
    print(f"\n[Case 2] 📱 แกะสถาปัตยกรรม App Bundle ({app_path}) หา URL Scheme / Deeplink:")
    res_app = runner.inspect_plist(app_path)
    if res_app["success"]:
        intel = ScraperReverseToolkit.app_to_scraping_intel(res_app["data"])
        print(f"  • App Name: {intel['app_name']} | Bundle ID: {intel['bundle_id']}")
        print(f"  • URL Schemes: {intel['url_schemes']}")
        print(f"  • ประโยชน์ในการดึงข้อมูล: {intel['scraping_application']}")

    # 3. Security & Binary Integrity Check
    print(f"\n[Case 3] 🛡️ ตรวจสอบความถูกต้องของ Binary เครื่องมือ (curl / python / scraper drivers):")
    res_sig = runner.inspect_signature("/usr/bin/curl")
    if res_sig["success"]:
        norm = res_sig.get("data", {}).get("normalized_result", {})
        print(f"  • ไบนารี: /usr/bin/curl")
        print(f"  • Identifier: {norm.get('identifier')} | Format: {norm.get('format')}")
        print(f"  • สถานะ Signature: {'✅ ผ่านการรับรองถูกต้อง' if norm.get('signed') else '⚠️ ไม่ผ่านการรับรอง'}")
        print(f"  • ผู้ออกใบรับรอง: {', '.join(norm.get('authorities', []))}")


def interactive_menu():
    runner = ReaRunner()
    ok, env_msg = runner.check_environment()
    print_banner()
    print(env_msg)

    while True:
        print("\n" + "=" * 72)
        print("📋 เมนูคำสั่ง REA Reverse Engineering:")
        print("  [1] 🔍 ตรวจสอบ Digital Signature & Codesign (inspect-signature)")
        print("  [2] 🏗️ วิเคราะห์สถาปัตยกรรม CPU & Binary Slices (list-architectures)")
        print("  [3] 📱 ถอดรหัส Apple Property List (inspect-plist)")
        print("  [4] 🔗 ตรวจสอบ Dynamic Library Dependencies (trace-dylib-resolution)")
        print("  [5] 🌐 ตรวจสอบ Network Capture HAR File (inspect-web-network-capture)")
        print("  [6] 🤖 ตรวจสอบสถานะ MCP Server (mcp doctor)")
        print("  [7] 🧪 รันชุดทดสอบความสมบูรณ์ REA ทั้งหมด (Run Diagnostics)")
        print("  [8] 💻 รันคำสั่ง REA แบบกำหนดเอง (Custom REA Command)")
        print("  [9] 🪄 สาธิตการใช้งานจริงสำหรับ Web Scraping (Scraping Showcase)")
        print("  [0] ออกจากเมนู")
        print("-" * 72)

        choice = input("👉 เลือกเมนู (0-9): ").strip()

        if choice == "0":
            print("👋 ออกจากโปรแกรม REA Reverse Engineering")
            break
        elif choice == "1":
            handle_signature(runner)
        elif choice == "2":
            handle_architectures(runner)
        elif choice == "3":
            handle_plist(runner)
        elif choice == "4":
            handle_dylib(runner)
        elif choice == "5":
            handle_har(runner)
        elif choice == "6":
            handle_doctor(runner)
        elif choice == "7":
            handle_diagnostics(runner)
        elif choice == "8":
            handle_custom(runner)
        elif choice == "9":
            handle_showcase_scraper(runner)
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง")


if __name__ == "__main__":
    runner = ReaRunner()
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        target = sys.argv[2] if len(sys.argv) > 2 else None

        if cmd in ["sig", "signature", "sign"]:
            handle_signature(runner, target)
        elif cmd in ["arch", "architectures"]:
            handle_architectures(runner, target)
        elif cmd in ["plist", "info"]:
            handle_plist(runner, target)
        elif cmd in ["dylib", "deps", "dependencies"]:
            handle_dylib(runner, target)
        elif cmd in ["har", "network", "web"]:
            handle_har(runner, target)
        elif cmd in ["doctor", "mcp"]:
            handle_doctor(runner)
        elif cmd in ["test", "diag", "diagnostics"]:
            handle_diagnostics(runner)
        elif cmd in ["demo", "showcase"]:
            handle_showcase_scraper(runner)
        else:
            print(f"❌ ไม่รู้จักคำสั่ง '{cmd}'")
            print("💡 คำสั่ง CLI: signature, arch, plist, dylib, har, doctor, test, demo")
    else:
        interactive_menu()
