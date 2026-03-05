import os
import sys
import time

import requests
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

PORTAL = os.environ.get("CAMPUS_PORTAL", "http://172.16.54.18/")
USER = os.environ.get("CAMPUS_USER", "").strip()
PASS = os.environ.get("CAMPUS_PASS", "").strip()
ISP = os.environ.get("CAMPUS_ISP", "绉诲姩").strip()  # 鐢典俊/绉诲姩/鑱旈€?鏍″洯缃?

# 鏂綉宸℃鐩稿叧锛堝彲鐢ㄧ幆澧冨彉閲忚鐩栵級
CHECK_INTERVAL_SEC = int(os.environ.get("CAMPUS_CHECK_INTERVAL", "60"))  # 姣?0绉掓鏌ヤ竴娆?
MONITOR_SECONDS = int(os.environ.get("CAMPUS_MONITOR_SECONDS", "0"))  # 0=鍙窇涓€娆★紱>0=杩愯N绉掑悗閫€鍑?
RETRY_TIMES = int(os.environ.get("CAMPUS_RETRY_TIMES", "3"))  # 鍗曟鎺夌嚎鏈€澶氶噸璇?娆?
RETRY_BACKOFF_SEC = int(os.environ.get("CAMPUS_RETRY_BACKOFF", "3"))  # 閲嶈瘯闂撮殧閫掑鍩烘暟


def is_online() -> bool:
    """
    鏈櫥褰曟椂寰€寰€浼?302 璺?portal锛沘llow_redirects=False 渚夸簬鍒ゆ柇銆?
    """
    try:
        r = requests.get("http://www.baidu.com", timeout=3, allow_redirects=False)
        return r.status_code == 200
    except Exception:
        return False


def pick_isp(page, isp_text: str):
    trigger = page.locator("#selectDisname")
    trigger.wait_for(timeout=8000, state="visible")
    trigger.hover()
    try:
        trigger.click(timeout=300)
    except Exception:
        pass

    opt = page.get_by_text(isp_text, exact=True)
    opt.wait_for(timeout=3000, state="visible")
    opt.click()


def do_login(headless: bool = True) -> bool:
    if not USER or not PASS:
        print("Missing CAMPUS_USER / CAMPUS_PASS.")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        page.goto(PORTAL, wait_until="domcontentloaded")

        page.locator("#username").wait_for(timeout=10000, state="visible")
        page.locator("#username").fill(USER)

        if page.locator("#pwd_tip").count() > 0:
            page.locator("#pwd_tip").click()

        page.locator("#pwd").wait_for(timeout=10000, state="visible")
        page.locator("#pwd").fill(PASS)

        pick_isp(page, ISP)

        if page.locator("#jishuhaoNo").count() > 0:
            page.locator("#jishuhaoNo").click()

        page.locator("#loginLink").wait_for(timeout=10000, state="visible")
        page.locator("#loginLink").click()

        try:
            page.wait_for_url("**/success.jsp**", timeout=12000)
        except PWTimeout:
            pass

        browser.close()

    return is_online()


def ensure_online(headless: bool = True) -> bool:
    """
    宸插湪绾垮垯鐩存帴杩斿洖 True锛涘惁鍒欏皾璇曠櫥褰曡嫢骞叉銆?
    """
    if is_online():
        print("Already online.")
        return True

    for i in range(1, RETRY_TIMES + 1):
        print(f"Offline -> login attempt {i}/{RETRY_TIMES} (ISP={ISP})")
        ok = do_login(headless=headless)
        if ok:
            print("Login OK.")
            return True

        sleep_s = RETRY_BACKOFF_SEC * i
        print(f"Login FAIL. retry in {sleep_s}s")
        time.sleep(sleep_s)

    print("All login attempts failed.")
    return False


def monitor_loop(headless: bool = True, seconds: int = 0):
    """
    seconds=0锛氬彧鎵ц涓€娆?ensure_online 灏遍€€鍑?
    seconds>0锛氬惊鐜贰妫€ seconds 绉掞紙閫傚悎鐫＄湢鍞ら啋鍚庣煭鏃堕棿瑙傚療锛?
    """
    start = time.time()
    # 绗竴娆＄珛鍗冲鐞?
    ensure_online(headless=headless)

    if seconds <= 0:
        return

    while True:
        if time.time() - start >= seconds:
            return
        time.sleep(CHECK_INTERVAL_SEC)
        if not is_online():
            ensure_online(headless=headless)


def main():
    headless = "--show" not in sys.argv

    if "--monitor" in sys.argv:
        # 榛樿鐩戞帶 10 鍒嗛挓锛堝彲鐢?env 鎴栧弬鏁版敼锛?
        secs = MONITOR_SECONDS if MONITOR_SECONDS > 0 else 600
        monitor_loop(headless=headless, seconds=secs)
        sys.exit(0)

    ok = ensure_online(headless=headless)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
