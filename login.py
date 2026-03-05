import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PORTAL = os.environ.get("CAMPUS_PORTAL", "http://172.16.54.18/eportal/")
USER = os.environ.get("CAMPUS_USER", "").strip()
PASS = os.environ.get("CAMPUS_PASS", "").strip()
ISP = os.environ.get("CAMPUS_ISP", "移动").strip()  # 电信/移动/联通/校园网

# 断网巡检相关（可用环境变量覆盖）
CHECK_INTERVAL_SEC = int(os.environ.get("CAMPUS_CHECK_INTERVAL", "60"))  # 每60秒检查一次
MONITOR_SECONDS = int(os.environ.get("CAMPUS_MONITOR_SECONDS", "0"))     # 0=只跑一次；>0=运行N秒后退出
RETRY_TIMES = int(os.environ.get("CAMPUS_RETRY_TIMES", "3"))             # 单次掉线最多重试3次
RETRY_BACKOFF_SEC = int(os.environ.get("CAMPUS_RETRY_BACKOFF", "3"))     # 重试间隔递增基数


def is_online() -> bool:
    """
    未登录时往往会 302 跳 portal；allow_redirects=False 便于判断。
    """
    try:
        r = requests.get("http://www.baidu.com", timeout=3, allow_redirects=False)
        return r.status_code == 200
    except Exception:
        return False


def pick_isp(page, isp_text: str) -> None:
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
    已在线则直接返回 True；否则尝试登录若干次。
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


def monitor_loop(headless: bool = True, seconds: int = 0) -> None:
    """
    seconds=0：只执行一次 ensure_online 就退出
    seconds>0：循环巡检 seconds 秒（适合睡眠唤醒后短时间观察）
    """
    start = time.time()

    # 第一次立即处理
    ensure_online(headless=headless)

    if seconds <= 0:
        return

    while True:
        if time.time() - start >= seconds:
            return
        time.sleep(CHECK_INTERVAL_SEC)
        if not is_online():
            ensure_online(headless=headless)


def main() -> None:
    headless = ("--show" not in sys.argv)

    if "--monitor" in sys.argv:
        # 默认监控 10 分钟（可用 env 或参数改）
        secs = MONITOR_SECONDS if MONITOR_SECONDS > 0 else 600
        monitor_loop(headless=headless, seconds=secs)
        sys.exit(0)

    ok = ensure_online(headless=headless)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()