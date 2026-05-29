"""
crawler/fetch.py — lấy dữ liệu xổ số

Ưu tiên: gọi trực tiếp JSON API (không cần Selenium/Chrome).
Dự phòng: dùng Selenium nếu API không phản hồi.
"""

import time
import random
from datetime import date, timedelta
from typing import Optional, Dict

import requests as _requests

API_URL = "https://www.xosobinhduong.com.vn/get-lottery-mn"
BASE_URL = "https://www.xosobinhduong.com.vn/kqxsmiennam"

_API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Referer": "https://www.xosobinhduong.com.vn/kqxsmiennam",
}


# ── API (primary) ─────────────────────────────────────────────────────────

def fetch_api_by_date(draw_date: date, retry: int = 3) -> Optional[Dict]:
    """
    Gọi JSON API trực tiếp — nhanh, không cần Selenium.
    Trả về dict JSON hoặc None nếu thất bại.
    """
    date_str = draw_date.strftime("%Y-%m-%d")
    url = f"{API_URL}?mask=getResultLoteryMn&lotdate={date_str}&skip=true&flagNumber=-1"
    print(f"[API] {url}", flush=True)
    for attempt in range(retry):
        try:
            resp = _requests.get(url, headers=_API_HEADERS, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == 1 and data.get("data"):
                    print(f"[API] OK: {date_str}", flush=True)
                    return data
                else:
                    print(f"[API] Dữ liệu rỗng: {date_str}", flush=True)
                    return None
            print(f"[API] HTTP {resp.status_code} lần {attempt+1}")
        except Exception as e:
            print(f"[API] Lỗi lần {attempt+1}: {e}", flush=True)
        time.sleep(random.uniform(1, 3))
    return None


# ── Selenium (dự phòng nếu API thất bại) ─────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        USE_WDM = True
    except ImportError:
        USE_WDM = False
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False

_driver = None


def _get_driver():
    global _driver
    if _driver is not None:
        try:
            _ = _driver.current_url
            return _driver
        except Exception:
            _driver = None

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=vi-VN")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    prefs = {"profile.managed_default_content_settings.images": 2}
    opts.add_experimental_option("prefs", prefs)

    if USE_WDM:
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=opts)
    else:
        _driver = webdriver.Chrome(options=opts)
    _driver.set_page_load_timeout(30)
    return _driver


def close_driver():
    """Đóng browser khi thoát app"""
    global _driver
    if _driver:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None


def _fetch_selenium(draw_date: date, timeout: int = 25, retry: int = 2) -> Optional[str]:
    """Dùng Selenium lấy HTML đã render (chỉ khi API thất bại)."""
    if not SELENIUM_OK:
        return None
    url = f"{BASE_URL}?lotdate={draw_date.strftime('%Y-%m-%d')}"
    for attempt in range(retry):
        try:
            driver = _get_driver()
            driver.get(url)
            wait = WebDriverWait(driver, timeout)
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.giai-dac-biet")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.giai-tam")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='box-white']")),
                ))
            except Exception:
                print(f"[SELENIUM] Timeout chờ render: {draw_date}")
                time.sleep(2)
                continue
            time.sleep(1.0)
            html = driver.page_source
            if html and len(html) > 10000:
                print(f"[SELENIUM] OK ({len(html):,} chars): {draw_date}")
                return html
        except Exception as e:
            print(f"[SELENIUM] Lỗi lần {attempt+1}: {e}")
            global _driver
            try:
                if _driver:
                    _driver.quit()
            except Exception:
                pass
            _driver = None
        time.sleep(random.uniform(2, 4))
    return None


# ── Public API ────────────────────────────────────────────────────────────

def fetch_result_by_date(draw_date: date, province_slug: str = None) -> Optional[str]:
    """Lấy HTML kết quả theo ngày (dùng cho parser HTML cũ — chỉ gọi Selenium)."""
    return _fetch_selenium(draw_date)


def generate_date_range(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

