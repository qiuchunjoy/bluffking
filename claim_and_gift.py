#!/usr/bin/env python3
"""Claim recovery beans and gift all to 克劳德."""
import asyncio
import re
from playwright.async_api import async_playwright

ACCOUNTS = [
    ("erikhappy0513@gmail.com", "澳门niko"),
    ("erikchiuhappy@gmail.com", "迷路的土豆骑士"),
    ("zhangerik0513@gmail.com", "贪吃的chris"),
    ("erikzhang0513@gmail.com", "新加坡夜宵博士"),
    ("happyerik0513@gmail.com", "抖腿的chris"),
    ("erikcchatgptup@gmail.com", "暴走的橘猫掌门"),
    ("qiuchunhappy@gmail.com", "旺旺"),
    ("bluffking01@tutamail.com", "成都mason"),
    ("bluffking02@tutamail.com", "小号土豆骑士"),
]
PASSWORD = "Qc111111"


async def safe_click(loc, timeout=2000):
    try:
        if await loc.count() > 0 and await loc.first.is_enabled():
            await loc.first.click(timeout=timeout)
            return True
    except Exception:
        pass
    return False


async def get_available(page):
    text = await page.evaluate("() => document.body.innerText")
    m = re.search(r"Available\s+([\d,]+)", text)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


async def process(page, email, nick):
    await page.goto("https://app.bluffking.ai/login", wait_until="domcontentloaded", timeout=25000)
    await page.wait_for_timeout(400)
    await page.get_by_role("textbox", name="Account or email").fill(email)
    await page.get_by_role("textbox", name="Password").fill(PASSWORD)
    await page.get_by_role("button", name="Sign in", exact=True).click()
    await page.wait_for_timeout(1800)
    print(f"{nick} logged in")

    await page.goto("https://app.bluffking.ai/me", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(700)
    before = await get_available(page)
    print(f"  before: {before}")

    await safe_click(page.locator("button").filter(has_text="Recovery beans"))
    await page.wait_for_timeout(600)
    if await safe_click(page.locator("button").filter(has_text="Claim recovery")):
        print(f"  claimed recovery")
        await page.wait_for_timeout(500)
    if await safe_click(page.locator("button").filter(has_text="Claim extra")):
        print(f"  claimed daily")
        await page.wait_for_timeout(400)

    await page.reload(wait_until="domcontentloaded", timeout=15000)
    await page.wait_for_timeout(600)
    after = await get_available(page)
    print(f"  after claim: {after}")

    if after >= 10:
        await safe_click(page.locator("button").filter(has_text="Gold bean balance"))
        await page.wait_for_timeout(600)
        await safe_click(page.get_by_role("button", name="Gift", exact=True))
        await page.wait_for_timeout(800)
        ok = await page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('*'));
            const el = all.find(e => e.childNodes.length <= 3 && e.innerText && e.innerText.trim() === '克劳德');
            if (!el) return false;
            let p = el;
            for (let i = 0; i < 6; i++) {
                p = p.parentElement;
                if (!p) break;
                const btn = Array.from(p.querySelectorAll('button')).find(b => b.innerText.trim() === 'Gift');
                if (btn) { btn.click(); return true; }
            }
            return false;
        }""")
        if ok:
            await page.wait_for_timeout(500)
            max_btn = page.get_by_test_id("beans-gift-modal").get_by_role("button", name="Max")
            if await max_btn.count() == 0:
                max_btn = page.locator("button.preset").filter(has_text="Max")
            await max_btn.first.click()
            await page.wait_for_timeout(250)
            pay = page.locator("button").filter(has_text="Pay")
            if await pay.count() > 0:
                await pay.first.click()
                await page.wait_for_timeout(1200)
                print(f"  gifted to 克劳德")
            else:
                print(f"  no Pay button")
        else:
            print(f"  no 克劳德 gift button")
    else:
        print(f"  too low ({after})")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for email, nick in ACCOUNTS:
            ctx = await browser.new_context(viewport={"width": 1000, "height": 700})
            page = await ctx.new_page()
            try:
                await process(page, email, nick)
            except Exception as e:
                print(f"{nick} ERROR: {e}")
            await ctx.close()
            await asyncio.sleep(0.5)
        await browser.close()
        print("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
