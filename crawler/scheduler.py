"""
Điều phối crawl dữ liệu.

Logic mới:
  - Mỗi ngày chỉ cần 1 request → parse ra nhiều tỉnh cùng lúc
  - Nếu chọn tỉnh cụ thể → lọc sau khi parse
"""

import threading
import time
from datetime import date
from typing import Callable, List, Optional

from crawler.fetch import fetch_api_by_date, fetch_result_by_date, generate_date_range
from crawler.parser import parse_api_response, parse_lottery_page, generate_mock_data
from database.db import Database
from database.models import PROVINCES


class CrawlScheduler:
    def __init__(self, db: Database):
        self.db = db
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def crawl_async(
        self,
        start_date: date,
        end_date: date,
        province_name: str,
        on_progress: Callable[[int, int, str], None] = None,
        on_done: Callable[[int, int], None] = None,
        on_error: Callable[[str], None] = None,
        use_mock: bool = False,
    ):
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            args=(start_date, end_date, province_name,
                  on_progress, on_done, on_error, use_mock),
            daemon=True,
        )
        self._thread.start()

    def _worker(self, start_date, end_date, province_name,
                on_progress, on_done, on_error, use_mock):
        try:
            all_dates = list(generate_date_range(start_date, end_date))
            total   = len(all_dates)
            saved   = 0
            skipped = 0

            # Danh sách tỉnh cần lọc (None = lấy tất cả)
            filter_province = None if province_name == "Tất cả" else province_name

            for idx, current_date in enumerate(all_dates, 1):
                if self._stop_event.is_set():
                    break

                date_str = current_date.strftime("%Y-%m-%d")

                # ── Chế độ Demo ───────────────────────────────────────────
                if use_mock:
                    provinces_to_fake = (
                        [province_name] if filter_province
                        else list(PROVINCES.keys())[:3]
                    )
                    day_saved = 0
                    for prov in provinces_to_fake:
                        mock = generate_mock_data(current_date, prov)
                        if self.db.save_result(mock):
                            day_saved += 1
                        else:
                            skipped += 1
                    saved += day_saved
                    msg = f"[DEMO] {date_str}  →  lưu {day_saved} tỉnh"
                    if on_progress:
                        on_progress(idx, total, msg)
                    continue

                # ── Online: API trực tiếp (nhanh, không cần Selenium) ────
                results = []

                # Bước 1: thử JSON API
                json_data = fetch_api_by_date(current_date)
                if json_data:
                    results = parse_api_response(json_data, current_date)

                # Bước 2: nếu API thất bại → fallback Selenium + parse HTML
                if not results:
                    print(f"[SCHEDULER] API thất bại, thử Selenium: {date_str}")
                    html = fetch_result_by_date(current_date)
                    if html:
                        results = parse_lottery_page(html, current_date)

                if not results:
                    msg = f"✗ Không parse được dữ liệu: {date_str}"
                    if on_progress:
                        on_progress(idx, total, msg)
                    time.sleep(1)
                    continue

                # Lọc theo tỉnh nếu cần
                if filter_province:
                    results = [r for r in results if r["province"] == filter_province]

                day_saved   = 0
                day_skipped = 0
                prov_names  = []
                for r in results:
                    if self.db.save_result(r):
                        day_saved += 1
                        prov_names.append(r["province"])
                    else:
                        day_skipped += 1

                saved   += day_saved
                skipped += day_skipped

                status = "✓" if day_saved else "↩"
                prov_str = ", ".join(prov_names) if prov_names else f"bỏ qua {day_skipped}"
                msg = f"{status} {date_str}  →  {day_saved} tỉnh mới  [{prov_str}]"
                if on_progress:
                    on_progress(idx, total, msg)

                time.sleep(0.8)   # delay lịch sự, tránh bị ban IP

            if on_done:
                on_done(saved, skipped)

        except Exception as e:
            if on_error:
                on_error(str(e))
            print(f"[SCHEDULER] Lỗi: {e}")
