#!/usr/bin/env python3
# ==============================================================================
# 🎭 Playwright Browser Automation Script
# Fallback Route: สำหรับใช้กรณีที่ API ยิงตรงไม่ได้ (ติด Cloudflare / Captcha / Signatures)
# ==============================================================================

import asyncio
from playwright.async_api import async_playwright

async def run_form_automation():
    async with async_playwright() as p:
        # เปิดเบราว์เซอร์ Chromium จำลองสภาพแวดล้อมคนใช้จริง
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🌐 กำลังเปิดหน้าเว็บ: https://httpbin.org/post")
        await page.goto("https://httpbin.org/post", wait_until="networkidle")

        print("📝 กำลังกรอกข้อมูลลงฟอร์มอัตโนมัติตามพฤติกรรมจริง...")
        # ชื่อ
        await page.locator('#fn').fill('กฤษณะ')
        # อีเมล
        await page.locator('#em').fill('boss@meuu.club')

        print("🔘 กำลังกดส่งข้อมูล (Submit)...")
        # กดปุ่ม ส่งข้อมูล
        await page.locator('#btn-submit').click()

        # รอให้ระบบปลายทางประมวลผล
        await page.wait_for_timeout(3000)
        print("✅ ดำเนินการกรอกฟอร์มและส่งข้อมูลสำเร็จเรียบร้อยแล้ว!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_form_automation())
