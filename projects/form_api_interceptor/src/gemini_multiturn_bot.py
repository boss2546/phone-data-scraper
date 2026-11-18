"""
Gemini Multi-turn Auto-Ask Bot & Chat Backupper
รันสนทนาอัตโนมัติหลายรอบในห้องเดิม และบันทึกประวัติการแชททั้งหมด
"""

import asyncio
import json
import os
import sys

COOKIE_FILE = '/tmp/gemini_cookies.json'
CHAT_URL = 'https://gemini.google.com/app/4d89270bcb1c9137?hl=th'

async def wait_until_gemini_finishes(page):
    """รอจนกว่า Gemini จะตอบเสร็จสมบูรณ์ (ปุ่มหยุดหายไป และข้อความนิ่ง)"""
    print("      ⏳ กำลังรอ Gemini ตอบกลับ...", end="", flush=True)
    # รอให้เริ่มตอบ
    await asyncio.sleep(3)
    
    last_text = ""
    stable_count = 0
    max_wait = 90  # สูงสุด 90 วินาที
    
    for _ in range(max_wait):
        await asyncio.sleep(1)
        print(".", end="", flush=True)
        
        # เช็คว่ายังมีปุ่ม 'หยุด' หรือไม่
        stop_btn = await page.query_selector('button[aria-label*="หยุด"], button[aria-label*="Stop"]')
        
        # เช็คข้อความล่าสุด
        responses = await page.query_selector_all('model-response')
        if responses:
            current_text = await responses[-1].inner_text()
            if current_text and current_text == last_text and not stop_btn:
                stable_count += 1
                if stable_count >= 3:
                    print(" [เสร็จสิ้น!]")
                    return current_text.replace("Gemini บอกว่า", "").strip()
            else:
                stable_count = 0
                last_text = current_text
                
    print(" [หมดเวลารอ]")
    return last_text.replace("Gemini บอกว่า", "").strip()

async def send_turn(page, message: str, turn_num: int):
    print(f"\n=======================================================")
    print(f"💬 [บทสนทนาที่ {turn_num}] ส่งคำถาม:")
    print(f"👉 \"{message}\"")
    print(f"=======================================================")
    
    editor_selector = 'div.ql-editor[contenteditable="true"]'
    editor = await page.wait_for_selector(editor_selector, timeout=15000)
    await editor.click()
    await page.keyboard.type(message, delay=35)
    await asyncio.sleep(1)
    
    # กดปุ่มส่ง
    await page.click('button[aria-label="ส่งข้อความ"]', force=True)
    
    # รอจนกว่า Gemini จะตอบเสร็จ
    reply = await wait_until_gemini_finishes(page)
    
    print(f"\n✨ [คำตอบจาก Gemini]:\n")
    print(reply)
    print("\n" + "-"*55)
    return reply

async def main():
    from playwright.async_api import async_playwright

    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    # รายการคำถามจำลองการคุยต่อเนื่องในเรื่องเดิม (การเจรจาเงินเดือน & การฝึกงานที่อธีนา)
    conversation_queue = [
        "ถ้าพี่ดรบอกว่า 'บริษัทมีงบจำกัด ให้ได้เต็มที่แค่ 30,000' ผมควรมีกลยุทธ์ต่อรองอย่างไรให้ได้ประโยชน์สูงสุดครับ?",
        "ช่วยแนะนำข้อตกลงเรื่องโบนัสหรือผลตอบแทนตามผลงาน (KPI) ที่ควรเสนอเพิ่มในกรณีนี้หน่อยครับ"
    ]

    async with async_playwright() as p:
        print("🚀 [Step 1] กำลังเปิด Browser และโหลด Session Gemini...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900}
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        print(f"🔗 [Step 2] เข้าสู่ห้องแชทเดิม: {CHAT_URL}")
        await page.goto(CHAT_URL, wait_until='domcontentloaded')
        await page.wait_for_selector('div.ql-editor[contenteditable="true"]', timeout=20000)
        await asyncio.sleep(3)
        print("✅ พร้อมเริ่มการสนทนาต่อเนื่องอัตโนมัติ!\n")

        history = []
        for i, q in enumerate(conversation_queue, 1):
            ans = await send_turn(page, q, i)
            history.append({"turn": i, "question": q, "answer": ans})
            await asyncio.sleep(2)

        # บันทึกเป็นเอกสารหลักฐาน
        output_file = "projects/form_api_interceptor/docs/gemini_multiturn_live_result.md"
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("# 🤖 บันทึกการรันเทสต์ Auto-Ask Bot สนทนาต่อเนื่องในห้องแชทเดิม\n\n")
            out.write(f"> **ห้องแชท:** `c_4d89270bcb1c9137` (ฝึกงาน บริษัท อธีนา อินเทลลิเจนซ์ ซิสเต็มส์ จำกัด)\n")
            out.write(f"> **วันที่/เวลา:** 18 พฤศจิกายน 2569\n")
            out.write(f"> **วิธีทดสอบ:** Playwright Browser Automation + Cookies จากส่วนขยาย\n\n---\n\n")
            for item in history:
                out.write(f"### 👤 บอส (รอบที่ {item['turn']}):\n> {item['question']}\n\n")
                out.write(f"### 🤖 Gemini ตอบกลับ:\n{item['answer']}\n\n---\n\n")

        print(f"🎉 สำเร็จทุกขั้นตอน! บันทึกผลไว้ที่: {output_file}")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
