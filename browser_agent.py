"""
VERONICA Browser Agent
Automates web browsing tasks using Playwright
"""
import asyncio
import time
import subprocess
from pathlib import Path

async def complete_course(url: str, callback=None) -> str:
    """Attempt to navigate and complete an online course."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            if callback:
                await callback({"type": "token",
                    "content": f"🌐 Opening course: {url}\n"})

            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Take screenshot
            screenshot_path = "D:/jarvis-agent/agent/data/course_screenshot.png"
            await page.screenshot(path=screenshot_path)

            if callback:
                await callback({"type": "token",
                    "content": "📸 Screenshot taken\n"})

            # Get page content
            title = await page.title()
            content = await page.inner_text("body")
            content = content[:500]

            if callback:
                await callback({"type": "token",
                    "content": f"📖 Course: {title}\n"})
                await callback({"type": "token",
                    "content": f"📝 Content preview:\n{content[:200]}...\n"})

            # Try to find and click first lesson
            selectors = [
                "a[href*='lesson']",
                "a[href*='module']",
                "a[href*='chapter']",
                ".lesson-item",
                ".course-item",
                "button:has-text('Start')",
                "button:has-text('Continue')",
                "a:has-text('Start Learning')",
                "a:has-text('Begin')",
            ]

            clicked = False
            for sel in selectors:
                try:
                    elem = await page.query_selector(sel)
                    if elem:
                        await elem.click()
                        await asyncio.sleep(2)
                        if callback:
                            await callback({"type": "token",
                                "content": f"✅ Clicked: {sel}\n"})
                        clicked = True
                        break
                except: pass

            if not clicked and callback:
                await callback({"type": "token",
                    "content": "ℹ️ Course opened. Please click Start manually.\n"})

            # Keep browser open for user
            await asyncio.sleep(5)
            # Don't close browser — let user interact
            # await browser.close()

            return (f"Course page opened, Sir. Title: {title}. "
                   f"Browser is ready for you to interact with.")

    except Exception as e:
        return f"Browser agent error, Sir: {str(e)[:100]}"

async def browse_and_extract(url: str) -> str:
    """Browse a URL and extract useful content."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle")
            title = await page.title()
            text = await page.inner_text("body")
            await browser.close()
            return f"Title: {title}\n\n{text[:800]}"
    except Exception as e:
        return f"Error: {e}"

async def auto_click(url: str, selector: str) -> str:
    """Open URL and click a specific element."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle")
            await page.click(selector)
            await asyncio.sleep(2)
            title = await page.title()
            await asyncio.sleep(10)
            return f"Clicked {selector} on {title}, Sir."
    except Exception as e:
        return f"Click error: {e}"

if __name__ == "__main__":
    async def main():
        result = await complete_course(
            "https://www.codechef.com/learn/course/java")
        print(result)
    asyncio.run(main())