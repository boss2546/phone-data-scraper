#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
💻 GEMINI CMD TERMINAL CHAT (Headless API Bridge)
--------------------------------------------------------------------
- คุยกับ Google Gemini ผ่านหน้าต่าง Terminal (CMD) 100%
- เบราว์เซอร์ทำงานเบื้องหลังแบบ Headless ไม่เด้งหน้าเว็บมากวนสายตา
- ซิงค์ประวัติขึ้นสู่บัญชี Google Gemini บนเว็บจริงแบบเรียลไทม์
====================================================================
"""

import asyncio
import json
import os
import sys

# Auto-redirect to Python with Playwright if missing in current environment
try:
    import playwright
except ImportError:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "python")),
        "/Users/meuu/Desktop/รวมโปรเจ็ค/ai_qa_court/.venv/bin/python",
        "/Users/meuu/Desktop/รวมโปรเจ็ค/test_skyvern/.venv/bin/python"
    ]
    for py in candidates:
        if os.path.exists(py) and py != sys.executable:
            os.execv(py, [py] + sys.argv)
    print("❌ ไม่พบโมดูล Playwright ในระบบ กรุณาติดตั้งด้วย: pip install playwright")
    sys.exit(1)

COOKIE_FILE = '/tmp/gemini_cookies.json'
CHAT_URL = 'https://gemini.google.com/app/4d89270bcb1c9137?hl=th'

# ANSI Color Codes สำหรับแต่งหน้าต่าง Terminal สไตล์ Mint & Emerald
GREEN = '\033[92m'
MINT = '\033[38;5;121m'
EMERALD = '\033[38;5;48m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
WHITE = '\033[97m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'

def load_cookies():
    if not os.path.exists(COOKIE_FILE):
        return None
    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def start_terminal_chat():
    os.system('clear' if os.name != 'nt' else 'cls')
    print(f"{MINT}{BOLD}")
    print(r"""
  ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██╗     ██████╗██╗  ██╗ █████╗ ████████╗
 ██╔════╝ ██╔════╝████╗ ████║██║████╗  ██║██║    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
 ██║  ███╗█████╗  ██╔████╔██║██║██╔██╗ ██║██║    ██║     ███████║███████║   ██║   
 ██║   ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║    ██║     ██╔══██║██╔══██║   ██║   
 ╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██║    ╚██████╗██║  ██║██║  ██║   ██║   
  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
    """)
    print(f"{RESET}{EMERALD}   ✨ ระบบแชท Gemini ผ่านหน้าต่าง Terminal (ซิงค์ตรงกับบัญชีจริงบนเว็บ) ✨{RESET}")
    print(f"{GRAY}   (Headless Background Mode — ไม่มีหน้าต่างเบราว์เซอร์เด้งกวนใจ){RESET}")
    print(f"{MINT}-------------------------------------------------------------------------------{RESET}")

    cookies = load_cookies()
    if not cookies:
        print(f"{YELLOW}❌ ไม่พบคุกกี้บัญชี กรุณาดักจับข้อมูลจาก Extension ก่อนนะคะ{RESET}")
        return

    from playwright.async_api import async_playwright

    print(f"{CYAN}⏳ กำลังเชื่อมต่อเข้าสู่เซสชัน Gemini ({CHAT_URL})...{RESET}")

    async with async_playwright() as p:
        # เปิดแบบ Headless เงียบๆ ไม่เด้งหน้าจอเบราว์เซอร์
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900}
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        try:
            await page.goto(CHAT_URL, wait_until='domcontentloaded', timeout=30000)
            editor_sel = 'div.ql-editor[contenteditable="true"]'
            await page.wait_for_selector(editor_sel, timeout=20000)
            # เลื่อนลงล่างสุดเพื่อพร้อมแชท
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print(f"{GREEN}🟢 เชื่อมต่อสำเร็จ! คุณกำลังคุยอยู่ในห้อง 'ฝึกงาน บริษัท อธีนาฯ' บนเว็บจริง{RESET}")
            print(f"{GRAY}👉 พิมพ์คำถามแล้วกด Enter | พิมพ์ 'exit' เพื่อจบการทำงาน{RESET}")
            print(f"{MINT}-------------------------------------------------------------------------------{RESET}\n")
        except Exception as e:
            print(f"{YELLOW}⚠️ โหลดหน้าเว็บช้าหรือเซสชันมีปัญหา: {e}{RESET}")
            await browser.close()
            return

        while True:
            try:
                # รับอินพุตจากบอสใน Terminal
                user_msg = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"{BOLD}{MINT}บอส ❯ {RESET}"
                )
            except (KeyboardInterrupt, EOFError):
                break

            user_msg = user_msg.strip()
            if not user_msg:
                continue

            if user_msg.lower() in ['exit', 'quit', 'q', 'ออก']:
                print(f"\n{EMERALD}👋 บ๊ายบายค่ะบอส! ไว้คุยกันใหม่น้า 💖{RESET}\n")
                break

            if user_msg.lower() in ['clear', 'cls']:
                os.system('clear' if os.name != 'nt' else 'cls')
                continue

            print(f"{GRAY}   (ส่งข้อความเข้าสู่ระบบ...){RESET}", end="\r")

            try:
                # พิมพ์ข้อความลงในช่องของ Gemini
                editor = await page.wait_for_selector(editor_sel, timeout=10000)
                await editor.click()
                await page.keyboard.type(user_msg, delay=15)
                await asyncio.sleep(0.3)

                # กดปุ่มส่งข้อความ
                send_btn = await page.query_selector('button[aria-label="ส่งข้อความ"]')
                if send_btn and await send_btn.is_visible():
                    await send_btn.click()
                else:
                    await page.keyboard.press('Enter')

                # รอคำตอบ
                print(f"{CYAN}   🤖 Gemini กำลังพิมพ์คำตอบ...{RESET}", end="", flush=True)
                
                last_reply = ""
                stable_ticks = 0
                await asyncio.sleep(2)

                for _ in range(60):
                    await asyncio.sleep(1)
                    print(f"{CYAN}.{RESET}", end="", flush=True)

                    stop_btn = await page.query_selector('button[aria-label*="หยุด"], button[aria-label*="Stop"]')
                    mrs = await page.query_selector_all('model-response')
                    if mrs:
                        curr_txt = await mrs[-1].inner_text()
                        if curr_txt and curr_txt == last_reply and not stop_btn:
                            stable_ticks += 1
                            if stable_ticks >= 2:
                                break
                        else:
                            stable_ticks = 0
                            last_reply = curr_txt

                print("\r" + " " * 45 + "\r", end="") # ล้างบรรทัดสถานะ

                # กรองคำว่า "Gemini บอกว่า" ออกเพื่อความสวยงาม
                clean_ans = last_reply.replace("Gemini บอกว่า", "").strip()
                print(f"\n{BOLD}{GREEN}🤖 Gemini ❯{RESET}\n{clean_ans}\n")
                print(f"{GRAY}-------------------------------------------------------------------------------{RESET}")

            except Exception as err:
                print(f"\n{YELLOW}⚠️ เกิดข้อผิดพลาดในการส่ง: {err}{RESET}")

        await browser.close()

if __name__ == '__main__':
    try:
        asyncio.run(start_terminal_chat())
    except KeyboardInterrupt:
        print("\n\n👋 ปิดโปรแกรมเรียบร้อยค่ะ!")
