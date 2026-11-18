"""
Gemini Web Auto-Ask Bot
ระบบบอทถาม-ตอบอัตโนมัติบน Google Gemini ผ่าน Playwright
ใช้ Cookies และข้อมูลที่ดักจับได้จาก Form & API Interceptor
"""

import asyncio
import json
import os
import sys

COOKIE_FILE = '/tmp/gemini_cookies.json'

async def ask_gemini(prompt_text: str):
    from playwright.async_api import async_playwright

    if not os.path.exists(COOKIE_FILE):
        print(f"Error: Cookie file {COOKIE_FILE} not found.")
        return

    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    print("🚀 [1/5] กำลังเปิด Browser เบื้องหลัง...")
    async with async_playwright() as p:
        # เปิด browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        print("🌐 [2/5] เข้าสู่หน้า Google Gemini (สร้างแชทใหม่)...")
        await page.goto('https://gemini.google.com/app?hl=th', wait_until='domcontentloaded')
        
        # รอให้หน้าเว็บและช่องพิมพ์พร้อม
        print("⏳ [3/5] กำลังรอช่องแชทพร้อมรับคำถาม...")
        input_selector = 'rich-textarea p, div[contenteditable="true"], textarea'
        try:
            await page.wait_for_selector(input_selector, timeout=15000)
        except Exception:
            print("⚠️ หาช่องพิมพ์ไม่เจอ กำลังลองโหลดใหม่...")
            await asyncio.sleep(5)

        # Focus และพิมพ์ข้อความ
        print(f"✍️ [4/5] กำลังพิมพ์คำถาม: \"{prompt_text}\"")
        input_el = await page.query_selector(input_selector)
        if not input_el:
            print("❌ ไม่พบช่องพิมพ์ข้อความ")
            await browser.close()
            return

        await input_el.click()
        await input_el.fill(prompt_text)
        await asyncio.sleep(1)

        # กดส่งคำถาม (Enter หรือปุ่มส่ง)
        send_btn_selector = 'button[aria-label*="ส่ง"], button[aria-label*="Send"], .send-button'
        send_btn = await page.query_selector(send_btn_selector)
        if send_btn and await send_btn.is_enabled():
            await send_btn.click()
        else:
            await page.keyboard.press('Enter')

        print("⏳ [5/5] ส่งคำถามแล้ว กำลังรอคำตอบจาก Gemini...")
        
        # รอคำตอบจาก Gemini (ตรวจจับว่ามี model-response ขึ้นมาใหม่และตอบเสร็จ)
        # รอให้อนิเมชั่นตอบคำถามเริ่มและจบ
        await asyncio.sleep(5)
        
        # วนลูปเช็คจนกว่าข้อความจะไม่เปลี่ยน (แปลว่าตอบเสร็จแล้ว)
        last_text = ""
        same_count = 0
        for _ in range(30):
            responses = await page.query_selector_all('model-response')
            if responses:
                latest_res = responses[-1]
                current_text = await latest_res.inner_text()
                if current_text and current_text == last_text:
                    same_count += 1
                    if same_count >= 3:
                        break
                else:
                    same_count = 0
                    last_text = current_text
            await asyncio.sleep(1)

        print("\n" + "="*50)
        print("✨ [คำตอบจาก Google Gemini] ✨")
        print("="*50)
        clean_res = last_text.replace("Gemini บอกว่า", "").strip()
        print(clean_res)
        print("="*50 + "\n")

        # บันทึกคำตอบ
        with open("projects/form_api_interceptor/docs/gemini_auto_ask_result.txt", "w", encoding="utf-8") as out:
            out.write(f"คำถาม: {prompt_text}\n\nคำตอบ:\n{clean_res}\n")

        print("📁 บันทึกคำตอบลงใน 'projects/form_api_interceptor/docs/gemini_auto_ask_result.txt' สำเร็จ!")
        await browser.close()

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv) > 1 else "สวัสดี Gemini ช่วยแนะนำเทคนิคการทำงานร่วมกับ AI สั้นๆ 3 ข้อสำหรับคนไม่เขียนโค้ดหน่อยครับ"
    asyncio.run(ask_gemini(prompt))
