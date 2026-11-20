#!/usr/bin/env python3
"""Claim eligible beans and report each account’s verified rewards and balance."""
import asyncio
import re
from collections import Counter

from playwright.async_api import Error as PlaywrightError, async_playwright, expect

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

PROFILE = "https://app.bluffking.ai/me"
LOGIN = "https://app.bluffking.ai/login?redirect=/me"
AVAILABLE = re.compile(r"Available\s+([\d,]+)")


async def open_wallet(page, email):
    profile = page.get_by_role("button", name=re.compile(re.escape(email), re.I))
    await profile.wait_for(timeout=20000)
    wallet = page.get_by_test_id("me-beans")
    await expect(wallet).to_contain_text(AVAILABLE, timeout=15000)
    await wallet.click()
    return await available_balance(page)


async def available_balance(page):
    field = page.get_by_test_id("beans-available")
    await expect(field).to_contain_text(AVAILABLE, timeout=15000)
    match = AVAILABLE.search(await field.inner_text())
    if match is None:
        raise ValueError("钱包余额暂不可读")
    return int(match.group(1).replace(",", ""))


async def reward_entries(page, kind):
    await page.get_by_test_id("beans-view-history").click()
    history = page.get_by_test_id("beans-history")
    await expect(history).to_have_attribute("aria-busy", "false", timeout=15000)
    if await history.get_by_role("alert").count():
        raise RuntimeError("钱包流水加载失败")
    rows = await history.get_by_test_id("beans-history-row").all_inner_texts()
    # Include the displayed time and closing balance to distinguish equal awards.
    return Counter(row for row in rows if row.splitlines()[:1] == [kind])


async def claim(page, button_id, kind):
    overview = page.get_by_test_id("beans-view-overview")
    await overview.click()
    button = page.get_by_test_id(button_id)
    await button.wait_for()
    if not await button.is_enabled():
        return f"0（{await button.inner_text()}）"

    before = await reward_entries(page, kind)
    await overview.click()
    await button.wait_for()
    if not await button.is_enabled():
        return f"0（{await button.inner_text()}）"

    balance = await available_balance(page)
    await button.click(timeout=5000)
    # A click alone does not confirm a credit. Give the wallet time to update,
    # then verify the amount against a newly posted ledger entry.
    try:
        await expect(page.get_by_test_id("beans-available")).not_to_contain_text(
            re.compile(rf"Available\s+{balance:,}(?![\d,])"), timeout=8000
        )
    except AssertionError:
        pass
    new_entries = await reward_entries(page, kind) - before
    if sum(new_entries.values()) == 1:
        amount = next(iter(new_entries)).splitlines()[-1].strip()
        if re.fullmatch(r"\+[\d,]+", amount):
            return amount
    raise RuntimeError("未能匹配到唯一的新流水")


async def process(page, email, nick):
    await page.goto(LOGIN, wait_until="domcontentloaded", timeout=25000)
    await page.get_by_placeholder("Account or email", exact=True).fill(email)
    await page.get_by_placeholder("Password", exact=True).fill(PASSWORD)
    await page.get_by_role("button", name="Sign in", exact=True).click()
    await open_wallet(page, email)
    unverified = []
    for label, button_id, kind in (
        ("救济豆", "beans-recovery", "Recovery grant"),
        ("每日补贴", "beans-daily", "Daily claim"),
    ):
        try:
            result = await claim(page, button_id, kind)
        except (PlaywrightError, AssertionError, ValueError, RuntimeError) as exc:
            unverified.append(label)
            result = f"待核实（{exc}）"
        print(f"{nick} | {label}：{result}", flush=True)
    await page.reload(wait_until="domcontentloaded")
    final = await open_wallet(page, email)
    print(f"{nick} | 领取后可用余额：{final:,}", flush=True)
    if unverified:
        raise RuntimeError(f"待核实：{'、'.join(unverified)}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(locale="en-US", viewport={"width": 1000, "height": 700})
        page = await context.new_page()
        errors = []
        try:
            for email, nick in ACCOUNTS:
                try:
                    await process(page, email, nick)
                except (PlaywrightError, AssertionError, ValueError, RuntimeError) as exc:
                    errors.append(nick)
                    print(f"{nick} | 核对失败：{exc}", flush=True)
                # Use the site's normal account switch so its device checks are preserved.
                await page.goto(PROFILE, wait_until="domcontentloaded")
                logout = page.get_by_role("button", name="Log out", exact=True)
                login = page.get_by_placeholder("Account or email", exact=True)
                await logout.or_(login).first.wait_for(timeout=20000)
                if await logout.is_visible():
                    await logout.click()
                    await login.wait_for(timeout=20000)
        finally:
            await browser.close()
        if errors:
            raise SystemExit(f"以下账号的结果不完整：{', '.join(errors)}")


if __name__ == "__main__":
    asyncio.run(main())
