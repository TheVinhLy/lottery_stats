"""
Parse kết quả từ HTML của www.xosobinhduong.com.vn/kqxsmiennam

Cấu trúc thực tế (HTML rendered bởi Selenium):
  <div class="box-white">
    <div class="w-100">
      <table>
        <thead>
          <tr>
            <th> [ngày] </th>
            <th> <span>Tiền Giang</span> ... </th>   ← tên tỉnh
            <th> <span>Kiên Giang</span> ... </th>
            ...
          </tr>
        </thead>
        <tbody>
          <tr>  ← mỗi row = 1 loại giải
            <td class="text-center"> Giải tám ... </td>   ← nhãn giải
            <td> <span class="giai-tam">73</span> </td>
            <td> <span class="giai-tam">22</span> </td>
            ...
          </tr>
          ...
          <tr>
            <td> Giải đặc biệt ... </td>
            <td> <span class="giai-dac-biet">480644</span> </td>
            ...
          </tr>
        </tbody>
      </table>
    </div>
  </div>
"""

import re
from typing import Dict, List, Optional
from datetime import date

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[WARN] Cần: pip install beautifulsoup4 lxml")


# class span → prize_key trong DB
SPAN_CLASS_MAP = {
    "giai-dac-biet": "special_prize",
    "giai-nhat":     "prize_1",
    "giai-nhi":      "prize_2",
    "giai-ba":       "prize_3",
    "giai-tu":       "prize_4",
    "giai-nam":      "prize_5",
    "giai-sau":      "prize_6",
    "giai-bay":      "prize_7",
    "giai-tam":      "prize_8",
}

_PROVINCE_MAP = {
    # Tên đầy đủ
    "bình dương":        "Bình Dương",
    "tp. hồ chí minh":  "TP. Hồ Chí Minh",
    "tp hồ chí minh":   "TP. Hồ Chí Minh",
    "hồ chí minh":      "TP. Hồ Chí Minh",
    "đồng nai":         "Đồng Nai",
    "long an":          "Long An",
    "bình phước":       "Bình Phước",
    "tây ninh":         "Tây Ninh",
    "vũng tàu":         "Vũng Tàu",
    "bà rịa":           "Vũng Tàu",
    "an giang":         "An Giang",
    "bến tre":          "Bến Tre",
    "cần thơ":          "Cần Thơ",
    "đà lạt":           "Đà Lạt",
    "lâm đồng":         "Đà Lạt",
    "hậu giang":        "Hậu Giang",
    "kiên giang":       "Kiên Giang",
    "sóc trăng":        "Sóc Trăng",
    "tiền giang":       "Tiền Giang",
    "trà vinh":         "Trà Vinh",
    "vĩnh long":        "Vĩnh Long",
    "cà mau":           "Cà Mau",
    "bạc liêu":         "Bạc Liêu",
    "đắk lắk":          "Đắk Lắk",
    "bình thuận":       "Bình Thuận",
    "khánh hòa":        "Khánh Hòa",
    "ninh thuận":       "Ninh Thuận",
    "đồng tháp":        "Đồng Tháp",
    # Viết tắt (từ ảnh trang web)
    "tp. hcm":          "TP. Hồ Chí Minh",
    "tp.hcm":           "TP. Hồ Chí Minh",
    "tp hcm":           "TP. Hồ Chí Minh",
    "hcm":              "TP. Hồ Chí Minh",
    "l.an":             "Long An",
    "l. an":            "Long An",
    "b.phước":          "Bình Phước",
    "b. phước":         "Bình Phước",
    "b.phuoc":          "Bình Phước",
    "b.dương":          "Bình Dương",
    "b. dương":         "Bình Dương",
    "h.giang":          "Hậu Giang",
    "h. giang":         "Hậu Giang",
    "t.ninh":           "Tây Ninh",
    "t. ninh":          "Tây Ninh",
    "t.giang":          "Tiền Giang",
    "t. giang":         "Tiền Giang",
    "k.giang":          "Kiên Giang",
    "k. giang":         "Kiên Giang",
    "s.trăng":          "Sóc Trăng",
    "v.long":           "Vĩnh Long",
    "v.tàu":            "Vũng Tàu",
    "b.tre":            "Bến Tre",
    "t.vinh":           "Trà Vinh",
    "c.thơ":            "Cần Thơ",
    "c.mau":            "Cà Mau",
    "b.liêu":           "Bạc Liêu",
    "b.thuận":          "Bình Thuận",
    "k.hòa":            "Khánh Hòa",
    "n.thuận":          "Ninh Thuận",
    "đ.tháp":           "Đồng Tháp",
    "đ.nai":            "Đồng Nai",
    "đ.lạt":            "Đà Lạt",
    "a.giang":          "An Giang",
}


def _normalize_province(raw: str) -> Optional[str]:
    import unicodedata
    key = re.sub(r'\s+', ' ', raw).strip().lower()

    if key in _PROVINCE_MAP:
        return _PROVINCE_MAP[key]

    for k, v in _PROVINCE_MAP.items():
        if k in key:
            return v

    # Fallback không dấu
    def no_accent(s):
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        ).lower()

    key_na = no_accent(key)
    for k, v in _PROVINCE_MAP.items():
        k_na = no_accent(k)
        if k_na in key_na or key_na in k_na:
            return v

    return None




def _empty(draw_date: date, province: str) -> Dict:
    return {
        "draw_date":     draw_date.strftime("%Y-%m-%d"),
        "province":      province,
        "special_prize": "",
        "prize_1": "", "prize_2": "", "prize_3": "",
        "prize_4": "", "prize_5": "", "prize_6": "",
        "prize_7": "", "prize_8": "",
        "all_numbers":   "",
    }


# ── Parser JSON API (primary) ─────────────────────────────────────────────

def parse_api_response(json_data: dict, draw_date: date) -> List[Dict]:
    """
    Parse dữ liệu từ JSON API endpoint /get-lottery-mn.
    Nhanh hơn và ổn định hơn parse HTML.
    """
    if not json_data:
        return []
    try:
        data = json_data.get("data", {})
        header = data.get("header", [])
        body   = data.get("body", [])

        if not header or not body:
            return []

        n = len(header)

        # Khởi tạo results
        results = []
        for h in header:
            province = _normalize_province(h.get("city_name", "")) or h.get("city_name", "?")
            results.append(_empty(draw_date, province))

        all_nums = [[] for _ in range(n)]

        for prize_row in body:
            code      = prize_row.get("code", "")
            prize_key = SPAN_CLASS_MAP.get(code)
            if not prize_key:
                continue
            col_data = prize_row.get("data", [])
            for col_idx, items in enumerate(col_data):
                if col_idx >= n:
                    break
                nums = [item["value"] for item in items if item.get("value")]
                if nums:
                    existing = results[col_idx][prize_key]
                    results[col_idx][prize_key] = (
                        existing + " " + " ".join(nums) if existing else " ".join(nums)
                    )
                    all_nums[col_idx].extend(nums)

        valid = []
        for col, res in enumerate(results):
            res["all_numbers"] = ", ".join(all_nums[col])
            if res["special_prize"] or len(all_nums[col]) >= 5:
                valid.append(res)

        return valid

    except Exception as e:
        print(f"[PARSER-API] Lỗi: {e}")
        return []


# ── Parser chính ──────────────────────────────────────────────────────────

def parse_lottery_page(html: str, draw_date: date) -> List[Dict]:
    if not html or not BS4_AVAILABLE:
        return []

    soup = BeautifulSoup(html, "lxml")

    # Tìm table kết quả trong div.box-white
    box = soup.find("div", class_="box-white")
    if not box:
        print("[PARSER] Không tìm thấy div.box-white")
        return []

    table = box.find("table")
    if not table:
        print("[PARSER] Không tìm thấy <table> trong box-white")
        return []

    # ── Bước 1: Tên tỉnh từ <thead> ──────────────────────────────────────
    # Cấu trúc: <th> <span class="">Tiền Giang</span> ... </th>
    # Cột đầu tiên là ngày → bỏ qua
    province_names: List[str] = []
    thead = table.find("thead")
    if thead:
        header_row = thead.find("tr")
        if header_row:
            ths = header_row.find_all("th")
            for th in ths[1:]:   # bỏ cột 0 (ngày)
                # span đầu tiên không có class cụ thể = tên tỉnh
                spans = th.find_all("span")
                for sp in spans:
                    cls = sp.get("class") or []
                    # span tên tỉnh thường không có class hoặc class rỗng
                    if not cls or cls == [""]:
                        name = _normalize_province(sp.get_text(strip=True))
                        if name:
                            province_names.append(name)
                            break
                else:
                    # Fallback: lấy text div đầu tiên trong th
                    div = th.find("div", class_="text-center")
                    if div:
                        name = _normalize_province(div.get_text(" ", strip=True))
                        if name:
                            province_names.append(name)

    if not province_names:
        print("[PARSER] Không nhận diện được tên tỉnh trong thead")
        return []

    n = len(province_names)
    print(f"[PARSER] {draw_date} — {n} tỉnh: {province_names}")

    # ── Bước 2: Dữ liệu giải từ <tbody> ──────────────────────────────────
    # Mỗi <tr> = 1 loại giải
    # <td> đầu = nhãn giải, các <td> tiếp = cột tỉnh
    # Trong mỗi td tỉnh có các <span class="giai-*"> chứa số

    results = [_empty(draw_date, pname) for pname in province_names]
    all_nums = [[] for _ in range(n)]

    tbody = table.find("tbody")
    if not tbody:
        print("[PARSER] Không tìm thấy tbody")
        return []

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # Xác định loại giải từ td đầu tiên
        label_td = tds[0]
        prize_key = None
        # Tìm span có class giai-* trong TOÀN bộ row → xác định prize_key
        for td in tds[1:]:
            for sp in td.find_all("span"):
                for cls in (sp.get("class") or []):
                    if cls in SPAN_CLASS_MAP:
                        prize_key = SPAN_CLASS_MAP[cls]
                        break
                if prize_key:
                    break
            if prize_key:
                break

        if not prize_key:
            continue

        # Thu thập số từ mỗi cột tỉnh
        for col_idx, td in enumerate(tds[1:n+1]):
            nums = []
            for sp in td.find_all("span"):
                for cls in (sp.get("class") or []):
                    if cls in SPAN_CLASS_MAP:
                        val = sp.get_text(strip=True)
                        if val:
                            nums.append(val)

            if nums:
                existing = results[col_idx][prize_key]
                if existing:
                    results[col_idx][prize_key] = existing + " " + " ".join(nums)
                else:
                    results[col_idx][prize_key] = " ".join(nums)
                all_nums[col_idx].extend(nums)

    # ── Bước 3: all_numbers và lọc ───────────────────────────────────────
    valid = []
    for col, data in enumerate(results):
        data["all_numbers"] = ", ".join(all_nums[col])
        if data["special_prize"] or len(all_nums[col]) >= 5:
            valid.append(data)

    return valid


# ── API tương thích ngược ────────────────────────────────────────────────

def parse_lottery_html(html: str, draw_date: date, province: str) -> Optional[Dict]:
    results = parse_lottery_page(html, draw_date)
    if not results:
        return None
    if province and province != "Tất cả":
        for r in results:
            if r["province"] == province:
                return r
    return results[0]


# ── Dữ liệu demo ─────────────────────────────────────────────────────────

def generate_mock_data(draw_date: date, province: str) -> Dict:
    import random
    def rn(d): return str(random.randint(10**(d-1), 10**d-1))
    prizes = {
        "special_prize": rn(6),
        "prize_1": rn(5),
        "prize_2": f"{rn(5)} {rn(5)}",
        "prize_3": " ".join(rn(5) for _ in range(6)),
        "prize_4": " ".join(rn(5) for _ in range(7)),
        "prize_5": rn(4),
        "prize_6": " ".join(rn(4) for _ in range(3)),
        "prize_7": rn(3),
        "prize_8": rn(2),
    }
    all_nums = []
    for v in prizes.values():
        all_nums.extend(v.split())
    return {"draw_date": draw_date.strftime("%Y-%m-%d"), "province": province,
            **prizes, "all_numbers": ", ".join(all_nums)}
