"""
crawl_daily.py — Script chạy tự động bởi GitHub Actions mỗi ngày.
Crawl kết quả hôm qua (hoặc hôm nay) rồi lưu vào Supabase.

Chạy thủ công:
    python crawl_daily.py               # crawl hôm nay
    python crawl_daily.py --date 2026-05-01          # crawl ngày cụ thể
    python crawl_daily.py --days 7                   # crawl 7 ngày gần nhất
    python crawl_daily.py --date 2026-04-01 --days 30  # crawl 30 ngày từ ngày đó
"""

import sys
import os
import argparse
from datetime import date, timedelta

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser(description="Crawl dữ liệu xổ số miền Nam")
    parser.add_argument("--date",  type=str, default=None,
                        help="Ngày bắt đầu YYYY-MM-DD (mặc định: hôm nay)")
    parser.add_argument("--days",  type=int, default=1,
                        help="Số ngày cần crawl (mặc định: 1)")
    parser.add_argument("--mock",  action="store_true",
                        help="Chế độ demo (không cần internet)")
    args = parser.parse_args()

    # Xác định khoảng ngày
    if args.date:
        from datetime import datetime
        start = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        start = date.today()  # hôm nay

    end = start + timedelta(days=max(0, args.days - 1))

    print(f"[CRAWL] Bắt đầu: {start} → {end} | Mock={args.mock}")
    db_url = os.getenv("DATABASE_URL", "")
    print(f"[CRAWL] DATABASE_URL set: {bool(db_url)}")
    if db_url:
        # Cảnh báo nếu dùng direct connection thay vì pooler
        if "supabase.co:5432" in db_url or (":5432" in db_url and "pooler" not in db_url):
            print("[CRAWL] ⚠️  DATABASE_URL đang dùng direct connection (port 5432).")
            print("[CRAWL] ⚠️  GitHub Actions cần dùng Transaction Pooler (port 6543).")
            print("[CRAWL] ⚠️  Vào Supabase → Settings → Database → Transaction pooler → copy URI.")

    from database.db import Database
    from crawler.fetch import fetch_api_by_date, generate_date_range
    from crawler.parser import parse_api_response, generate_mock_data
    from database.models import PROVINCES

    try:
        db = Database()
    except Exception as e:
        print(f"[CRAWL] ❌ Không kết nối được database: {e}")
        print("[CRAWL] Kiểm tra DATABASE_URL — cần dùng Transaction Pooler URL (port 6543), không phải Direct Connection (port 5432).")
        sys.exit(1)
    all_dates = list(generate_date_range(start, end))
    total   = len(all_dates)
    saved   = 0
    skipped = 0
    errors  = 0

    for idx, cur_date in enumerate(all_dates, 1):
        date_str = cur_date.strftime("%Y-%m-%d")
        print(f"[{idx}/{total}] Đang xử lý: {date_str} ...", flush=True)

        try:
            if args.mock:
                for prov in list(PROVINCES.keys())[:3]:
                    rec = generate_mock_data(cur_date, prov)
                    if db.save_result(rec):
                        saved += 1
                    else:
                        skipped += 1
                print(f"  [DEMO] Đã tạo dữ liệu giả", flush=True)
            else:
                api_data = fetch_api_by_date(cur_date)
                if api_data:
                    records = parse_api_response(api_data, cur_date)
                    day_saved = 0
                    for rec in records:
                        if db.save_result(rec):
                            saved += 1
                            day_saved += 1
                        else:
                            skipped += 1
                    print(f"  ✅ Lưu {day_saved} tỉnh", flush=True)
                else:
                    print(f"  ⚠️  Không lấy được dữ liệu: {date_str}", flush=True)
                    errors += 1
        except Exception as e:
            print(f"  ❌ Lỗi: {e}", flush=True)
            errors += 1

    print(f"\n[CRAWL] Hoàn thành!")
    print(f"  Đã lưu mới:  {saved}")
    print(f"  Bỏ qua trùng: {skipped}")
    print(f"  Lỗi:         {errors}")

    total_in_db = db.get_record_count()
    print(f"  Tổng DB:     {total_in_db:,} bản ghi")

    # Thoát với exit code 1 nếu tất cả đều lỗi
    if errors == total and total > 0 and saved == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
