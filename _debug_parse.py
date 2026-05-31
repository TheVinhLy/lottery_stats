import sys
sys.path.insert(0, '.')
from crawler.fetch import fetch_api_by_date
from crawler.parser import parse_api_response, _normalize_province, SPAN_CLASS_MAP
from datetime import date

d = date(2026, 1, 5)
data = fetch_api_by_date(d)
results = parse_api_response(data, d)
print("Results count:", len(results))

header = data["data"]["header"]
body = data["data"]["body"]
print("header count:", len(header))
for h in header:
    orig = h.get("city_name", "")
    mapped = _normalize_province(orig)
    print(f"  province: {orig!r} -> {mapped!r}")

all_nums = [[] for _ in range(len(header))]
for prize_row in body:
    code = prize_row.get("code", "")
    prize_key = SPAN_CLASS_MAP.get(code)
    if not prize_key:
        print(f"  MISSING MAP: {code}")
        continue
    col_data = prize_row.get("data", [])
    for col_idx, items in enumerate(col_data):
        nums = [item["value"] for item in items if item.get("value")]
        all_nums[col_idx].extend(nums)

for i, nums in enumerate(all_nums):
    print(f"  col {i}: {len(nums)} numbers -> valid={bool(nums)}")
