#!/usr/bin/env python3
"""
====================================================================
🤖 Gemini Interactive Live Chat Bot (Playwright Headed Edition)
--------------------------------------------------------------------
- เปิดหน้าต่างเบราว์เซอร์ Chrome ขึ้นมาให้เห็นจะๆ บนหน้าจอ
- พิมพ์คุยใน Terminal แล้วข้อความจะไปพิมพ์ในหน้าเว็บ Gemini จริงๆ
- ข้อความและประวัติทั้งหมดจะบันทึกอยู่ในหน้าเว็บและบัญชีจริง 100%
====================================================================
"""

import asyncio
import json
import os
import sys

COOKIE_FILE = '/tmp/gemini_cookies.json'
DEFAULT_CHAT_URL = 'https://gemini.google.com/app/4d89270bcb1c9137?hl=th'
NEW_CHAT_URL = 'https://gemini.google.com/app?hl=th'

def load_cookies():
    if not os.path.exists(COOKIE_FILE):
        print(f"❌ ไม่พบคุกกี้ที่ {COOKIE_FILE}")
        return []
    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def wait_for_gemini_stream(page):
    """ฟังก์ชันรอจนกว่า Gemini จะพิมพ์คำตอบเสร็จสมบูรณ์"""
    last_text = ""
    stable_count = 0
    max_wait = 120  # สูงสุด 2 นาที

    for _ in range(max_wait):
        await asyncio.sleep(1)
        
        # ตรวจสอบว่ายังมีปุ่มกำลังสร้างข้อความ/ปุ่มหยุด หรือไม่
        stop_btn = await page.query_selector('button[aria-label*="หยุด"], button[aria-label*="Stop"], mat-progress-bar')
        
        responses = await page.query_selector_all('model-response')
        if responses:
            current_text = await responses[-1].inner_text()
            if current_text and current_text == last_text and not stop_btn:
                stable_count += 1
                if stable_count >= 2:
                    return current_text.replace("Gemini บอกว่า", "").strip()
            else:
                stable_count = 0
                last_text = current_text

    return last_text.replace("Gemini บอกว่า", "").strip()

async def interactive_chat(target_url=DEFAULT_CHAT_URL):
    from playwright.async_api import async_playwright

    cookies = load_cookies()
    if not cookies:
        print("กรุณาตรวจสอบว่ามีคุกกี้ที่ดักจับได้เรียบร้อยแล้ว")
        return

    print("=" * 65)
    print("🌿 Gemini Live Chat Assistant — โหมดโต้ตอบสดผ่านหน้าเว็บ")
    print("=" * 65)
    print(f"📌 กำลังเปิดหน้าต่างเบราว์เซอร์จริง (Headed Mode)...")
    
    async with async_playwright() as p:
        # เปิด Chromium หน้าต่างจริง (headless=False)
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            no_viewport=True
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        print(f"🔗 กำลังโหลดหน้าเว็บ: {target_url}")
        await page.goto(target_url, wait_until='domcontentloaded')

        editor_selector = 'div.ql-editor[contenteditable="true"]'
        try:
            await page.wait_for_selector(editor_selector, timeout=25000)
            print("✅ เชื่อมต่อหน้าเว็บสำเร็จ! พร้อมส่งคำถามแล้ว\n")
        except Exception:
            print("⚠️ หน้าเว็บโหลดช้า กำลังรอดำเนินการต่อ...")

        print("-------------------------------------------------------")
        print("💡 พิมพ์คำถามที่ต้องการถาม Gemini ในนี้ได้เลย")
        print("💡 พิมพ์ 'exit' หรือ 'q' เมื่อต้องการปิดโปรแกรม")
        print("-------------------------------------------------------\n")

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        while True:
            # รับคำถามจากผู้ใช้ใน Terminal
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "👤 บอสพิมพ์ถาม: "
                )
            except (KeyboardInterrupt, EOFError):
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q', 'ออก']:
                print("\n👋 จบการสนทนา ปิดหน้าต่างเบราว์เซอร์เรียบร้อยค่ะ!")
                break

            print(f"🚀 กำลังพิมพ์และส่งข้อความไปที่หน้าต่างเบราว์เซอร์จริง...")

            # คลิกและพิมพ์ลงช่องข้อความจริงบนหน้าเว็บ
            try:
                editor = await page.wait_for_selector(editor_selector, timeout=10000)
                await editor.click()
                
                # พิมพ์แบบมีแอนิเมชันให้เห็นการพิมพ์ในหน้าต่างเบราว์เซอร์
                await page.keyboard.type(user_input, delay=20)
                await asyncio.sleep(0.5)

                # กดปุ่มส่งข้อความ
                send_btn = await page.query_selector('button[aria-label="ส่งข้อความ"]')
                if send_btn and await send_btn.is_visible():
                    await send_btn.click()
                else:
                    await page.keyboard.press('Enter')

                print("⏳ ส่งแล้ว! Gemini กำลังพิมพ์คำตอบบนหน้าจอ...")
                
                # ดึงคำตอบที่เพิ่งตอบกลับมา
                reply = await wait_for_gemini_stream(page)
                
                print("\n" + "=" * 55)
                print("✨ [คำตอบจาก Gemini ในเบราว์เซอร์]:")
                print("=" * 55)
                print(reply)
                print("=" * 55 + "\n")

            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการพิมพ์: {e}")

        await browser.close()

if __name__ == '__main__':
    url = DEFAULT_CHAT_URL
    if len(sys.argv) > 1 and sys.argv[1] == '--new':
        url = NEW_CHAT_URL
    asyncio.run(interactive_chat(url))
