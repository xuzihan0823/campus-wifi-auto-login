import os
import sys
import time
import subprocess
import requests
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PORTAL      = os.environ.get("CAMPUS_PORTAL", "http://172.16.54.18/eportal/")
LOGIN_URL   = os.environ.get("CAMPUS_LOGIN_URL", "http://172.16.54.18/eportal/Interface.do?method=login")
USER        = os.environ.get("CAMPUS_USER", "").strip()
PASS        = os.environ.get("CAMPUS_PASS", "").strip()
ISP         = os.environ.get("CAMPUS_ISP", "移动").strip()  # 电信/移动/联通/校园网
WIFI_SSID   = os.environ.get("CAMPUS_SSID", "").strip()    # 校园WiFi热点名称，如 NJUPT-CMCC
WIFI_WAIT_SEC = int(os.environ.get("CAMPUS_WIFI_WAIT", "6"))  # 连上WiFi后等待秒数

# ISP 名称 → service 字段映射（从抓包载荷确认：移动=YD）
ISP_SERVICE_MAP = {
    "移动": "YD",
    "电信": "DX",
    "联通": "LT",
    "校园网": "",
}

# 断网巡检相关（可用环境变量覆盖）
CHECK_INTERVAL_SEC = int(os.environ.get("CAMPUS_CHECK_INTERVAL", "60"))  # 每60秒检查一次
MONITOR_SECONDS = int(os.environ.get("CAMPUS_MONITOR_SECONDS", "0"))     # 0=只跑一次；>0=运行N秒后退出
RETRY_TIMES = int(os.environ.get("CAMPUS_RETRY_TIMES", "3"))             # 单次掉线最多重试3次
RETRY_BACKOFF_SEC = int(os.environ.get("CAMPUS_RETRY_BACKOFF", "3"))     # 重试间隔递增基数


def connect_wifi(ssid: str) -> bool:
    """
    通过 netsh wlan connect 连接已保存的 WiFi 配置文件。
    前提：该 WiFi 曾经手动连接过（Windows 有保存的配置）。
    """
    if not ssid:
        return True  # 未配置 SSID 则跳过
    print(f"[WiFi] Connecting to '{ssid}' ...")
    result = subprocess.run(
        ["netsh", "wlan", "connect", f"name={ssid}"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    output = result.stdout + result.stderr
    if result.returncode == 0 and ("成功" in output or "successfully" in output.lower()):
        print(f"[WiFi] Connect command accepted, waiting {WIFI_WAIT_SEC}s for association...")
        time.sleep(WIFI_WAIT_SEC)
        return True
    print(f"[WiFi] Connect failed: {output.strip()}")
    return False


def is_online() -> bool:
    """
    未登录时往往会 302 跳 portal；allow_redirects=False 便于判断。
    """
    try:
        r = requests.get("http://www.baidu.com", timeout=3, allow_redirects=False)
        return r.status_code == 200
    except Exception:
        return False


def _get_query_string(session: requests.Session) -> str:
    """
    访问外网，portal 会将请求重定向到自身并在 URL 里携带网络参数
    （wlanuserip、wlanacname、nasip 等），从重定向 Location 中提取。
    """
    try:
        r = session.get("http://www.msftconnecttest.com/redirect",
                        timeout=4, allow_redirects=False)
        loc = r.headers.get("Location", "")
        # portal 重定向地址形如 http://172.x.x.x/eportal/?wlanuserip=...&...
        if loc and "wlanuserip" in loc:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(loc)
            # queryString 是 portal URL 中去掉其他字段后的原始查询串
            qs = parsed.query
            print(f"Captured queryString: {qs[:80]}...")
            return qs
    except Exception as e:
        print(f"queryString capture failed: {e}")
    return ""


def do_login_post() -> bool:
    """
    直接用 requests.post() 登录 eportal，无需浏览器。
    - service   字段已按抓包修正（移动=YD）
    - queryString 自动从 portal 重定向中捕获
    - 先尝试明文密码（passwordEncrypt=false），若服务端拒绝请改为加密
    """
    if not USER or not PASS:
        print("Missing CAMPUS_USER / CAMPUS_PASS.")
        return False

    service = ISP_SERVICE_MAP.get(ISP, "")

    session = requests.Session()

    # 1. 先访问 portal 首页，建立 session / 获取 cookies
    try:
        session.get(PORTAL, timeout=5, allow_redirects=True)
    except Exception:
        pass

    # 2. 动态捕获 queryString（网络设备注入的重定向参数）
    query_string = _get_query_string(session)

    # 3. 构造表单载荷（字段名与顺序来自抓包）
    payload = {
        "userId":          USER,
        "password":        PASS,          # 明文；如服务端要求加密见注释
        "service":         service,
        "queryString":     query_string,
        "operatorPwd":     "",
        "operatorUserId":  "",
        "validcode":       "",
        "passwordEncrypt": "false",       # 明文模式；加密模式改为 "true"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept":        "*/*",
        "Connection":    "keep-alive",
        "Referer":       PORTAL,
    }

    try:
        resp = session.post(
            LOGIN_URL,
            data=payload,
            headers=headers,
            timeout=10,
            allow_redirects=True,
        )
        print(f"POST login → HTTP {resp.status_code}")
        print(f"Response body: {resp.text[:300]}")
        if resp.status_code == 200:
            return is_online()
        return False
    except Exception as e:
        print(f"POST login error: {e}")
        return False


def pick_isp(page, isp_text: str) -> bool:
    """
    选择运营商。若页面上根本没有该元素（已认证/页面结构不同），返回 False 跳过。
    """
    trigger = page.locator("#selectDisname")
    try:
        trigger.wait_for(timeout=5000, state="visible")
    except Exception:
        print("[login] #selectDisname not found, portal may not require login.")
        return False
    trigger.hover()
    try:
        trigger.click(timeout=300)
    except Exception:
        pass

    opt = page.get_by_text(isp_text, exact=True)
    opt.wait_for(timeout=3000, state="visible")
    opt.click()
    return True


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
    已在线则直接返回 True；否则先尝试 POST 直连登录，失败再回退到 Playwright。
    """
    if is_online():
        print("Already online.")
        return True

    # 尝试连接校园 WiFi 热点（睡眠唤醒后可能未连接）
    connect_wifi(WIFI_SSID)

    for i in range(1, RETRY_TIMES + 1):
        print(f"Offline -> login attempt {i}/{RETRY_TIMES} (ISP={ISP})")

        # 优先用 POST 直连，速度更快
        ok = do_login_post()
        if not ok:
            print("POST login failed, falling back to Playwright...")
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