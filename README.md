# 🎰 Thống Kê Xổ Số Miền Nam

Ứng dụng thống kê xổ số miền Nam — web app Streamlit chạy online, dữ liệu tự động cập nhật hàng ngày qua GitHub Actions, lưu trữ trên Supabase (PostgreSQL).

**Demo trực tiếp:** https://lotterystats.streamlit.app *(thay bằng URL Streamlit Cloud của bạn)*

---

## 📋 Mục Lục

1. [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
2. [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)
3. [Triển Khai Lần Đầu (Step-by-step)](#-triển-khai-lần-đầu-step-by-step)
4. [Cài Đặt Local](#-cài-đặt-local)
5. [Sử Dụng crawl_daily.py](#-sử-dụng-crawl_dailypy)
6. [GitHub Actions — Crawl Tự Động](#-github-actions--crawl-tự-động)
7. [Hướng Dẫn Sử Dụng App](#-hướng-dẫn-sử-dụng-app)
8. [Cơ Sở Dữ Liệu](#-cơ-sở-dữ-liệu)
9. [Xử Lý Sự Cố](#-xử-lý-sự-cố)
10. [Thư Viện & Nguồn Dữ Liệu](#-thư-viện--nguồn-dữ-liệu)

---

## 🏗 Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────┐
│                    NGƯỜI DÙNG (Browser)                  │
└────────────────────────┬────────────────────────────────┘
                         │  HTTPS
┌────────────────────────▼────────────────────────────────┐
│              Streamlit Cloud (streamlit_app.py)          │
│   - Hiển thị 10 tab thống kê                            │
│   - Kết nối Supabase để đọc dữ liệu                    │
└────────────────────────┬────────────────────────────────┘
                         │  DATABASE_URL (PostgreSQL)
┌────────────────────────▼────────────────────────────────┐
│                  Supabase (PostgreSQL)                   │
│   - Bảng: draw_results (toàn bộ kết quả xổ số)         │
└────────────────────────▲────────────────────────────────┘
                         │  INSERT hàng ngày
┌────────────────────────┴────────────────────────────────┐
│          GitHub Actions (.github/workflows/)             │
│   - Chạy 18:30 giờ VN mỗi ngày (11:30 UTC)            │
│   - Gọi crawl_daily.py → fetch JSON API → lưu DB       │
└─────────────────────────────────────────────────────────┘
```

**Luồng dữ liệu:**
`xosobinhduong.com.vn (JSON API)` → `crawler/fetch.py` → `crawler/parser.py` → `database/db.py` → `Supabase` → `streamlit_app.py`

---

## 📁 Cấu Trúc Thư Mục

```
lottery_stats/
├── streamlit_app.py         ← Web app chính (Streamlit, 10 tab)
├── crawl_daily.py           ← Script crawl cho GitHub Actions
├── main.py                  ← Entry point desktop (Tkinter, tùy chọn)
├── requirements.txt         ← Thư viện Python
├── .env                     ← Biến môi trường local (KHÔNG commit)
│
├── .github/
│   └── workflows/
│       └── daily_crawl.yml  ← GitHub Actions: crawl tự động hàng ngày
│
├── crawler/
│   ├── fetch.py             ← Gọi JSON API / Selenium dự phòng
│   ├── parser.py            ← Parse dữ liệu từ API JSON hoặc HTML
│   └── scheduler.py         ← Điều phối crawl đa luồng
│
├── database/
│   ├── db.py                ← CRUD + hàm thống kê (SQLite & PostgreSQL)
│   └── models.py            ← SQL schema, danh sách 23 tỉnh/thành
│
├── reports/
│   └── export_excel.py      ← Xuất báo cáo Excel
│
└── data/
    └── lottery.db           ← Database SQLite local (tự tạo, không commit)
```

---

## 🚀 Triển Khai Lần Đầu (Step-by-step)

### Bước 1 — Tạo tài khoản & project Supabase

1. Vào **https://supabase.com** → **Start your project** → đăng ký/đăng nhập
2. Nhấn **New project**, điền:
   - **Name**: `lottery-stats` (hoặc tên tuỳ ý)
   - **Database Password**: đặt mật khẩu mạnh, **lưu lại ngay**
   - **Region**: Southeast Asia (Singapore)
3. Chờ ~2 phút để project khởi tạo xong

4. Vào **SQL Editor** → **New query**, chạy lệnh tạo bảng:

```sql
CREATE TABLE IF NOT EXISTS draw_results (
    id            SERIAL PRIMARY KEY,
    draw_date     DATE        NOT NULL,
    province      TEXT        NOT NULL,
    special_prize TEXT,
    prize_1       TEXT,
    prize_2       TEXT,
    prize_3       TEXT,
    prize_4       TEXT,
    prize_5       TEXT,
    prize_6       TEXT,
    prize_7       TEXT,
    prize_8       TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (draw_date, province)
);

CREATE INDEX IF NOT EXISTS idx_draw_date     ON draw_results(draw_date);
CREATE INDEX IF NOT EXISTS idx_province      ON draw_results(province);
CREATE INDEX IF NOT EXISTS idx_date_province ON draw_results(draw_date, province);
```

5. Lấy **Transaction Pooler URL**:
   - Vào **Settings** → **Database** → mục **Connection string**
   - Chọn tab **Transaction pooler** (port **6543**)
   - Copy URI dạng:
     ```
     postgresql://postgres.xxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
     ```
   - Thay `[YOUR-PASSWORD]` bằng mật khẩu đã đặt ở bước 3
   - **Lưu URI này** — dùng cho bước 2 và bước 3

> ⚠️ **Quan trọng:** Phải dùng **Transaction Pooler (port 6543)**, KHÔNG dùng Direct Connection (port 5432) — GitHub Actions không kết nối được port 5432 do tường lửa.

---

### Bước 2 — Cấu hình GitHub Repository

1. Push code lên GitHub (nếu chưa có):
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```

2. Thêm **Secret** cho GitHub Actions:
   - Vào repo trên GitHub → **Settings** → **Secrets and variables** → **Actions**
   - Nhấn **New repository secret**
   - **Name**: `DATABASE_URL`
   - **Value**: URI Transaction Pooler đã copy ở Bước 1
   - Nhấn **Add secret**

3. Kiểm tra file `.github/workflows/daily_crawl.yml` đã có trong repo (tự động chạy lúc 18:30 VN mỗi ngày).

---

### Bước 3 — Triển khai lên Streamlit Cloud

1. Vào **https://share.streamlit.io** → **Sign in with GitHub**
2. Nhấn **New app**:
   - **Repository**: chọn repo của bạn
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
3. Nhấn **Advanced settings** → mục **Secrets**, thêm:
   ```toml
   DATABASE_URL = "postgresql://postgres.xxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
   ```
   *(Dùng cùng URI Transaction Pooler như bước 1)*
4. Nhấn **Deploy!** — chờ ~1-2 phút để app khởi động

---

### Bước 4 — Nạp dữ liệu lần đầu

Sau khi triển khai, cần crawl dữ liệu lịch sử. Có 2 cách:

**Cách A — Chạy thủ công trên GitHub Actions:**
- Vào repo → **Actions** → **Daily Lottery Crawl** → **Run workflow**
- Nhập `date`: `2026-01-01`, `days`: `150` (hoặc số ngày muốn lấy)
- Nhấn **Run workflow**

**Cách B — Chạy local rồi kết nối Supabase:**
```bash
# Tạo file .env với DATABASE_URL Transaction Pooler
# Sau đó crawl dữ liệu từ đầu năm
python crawl_daily.py --date 2026-01-01 --days 150
```

---

## 💻 Cài Đặt Local

### Yêu cầu
- Python 3.9+
- Git

### Các bước

```bash
# 1. Clone repo
git clone https://github.com/<username>/lottery_stats.git
cd lottery_stats

# 2. Tạo môi trường ảo
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# 3. Cài thư viện
pip install -r requirements.txt

# 4. (Tuỳ chọn) Tạo file .env để kết nối Supabase
# Tạo file .env với nội dung:
# DATABASE_URL=postgresql://postgres.xxxx:[PASSWORD]@...supabase.com:6543/postgres

# 5. Chạy web app
streamlit run streamlit_app.py
```

App mở tại `http://localhost:8501`.

> **Không có DATABASE_URL** → tự động dùng SQLite local tại `data/lottery.db`.

---

## ⚙️ Sử Dụng crawl_daily.py

Script crawl dữ liệu từ API và lưu vào database.

```bash
# Crawl hôm qua (mặc định)
python crawl_daily.py

# Crawl một ngày cụ thể
python crawl_daily.py --date 2026-05-28

# Crawl 7 ngày gần nhất (tính từ hôm qua)
python crawl_daily.py --days 7

# Crawl 30 ngày kể từ ngày chỉ định
python crawl_daily.py --date 2026-01-01 --days 30

# Chế độ demo (không cần internet)
python crawl_daily.py --mock
```

**Output mẫu:**
```
[CRAWL] Bắt đầu: 2026-05-28 → 2026-05-28 | Mock=False
[CRAWL] DATABASE_URL set: True
[1/1] Đang xử lý: 2026-05-28 ...
  ✅ Lưu: Bình Dương
  ✅ Lưu: TP. Hồ Chí Minh
  ...
[CRAWL] Hoàn thành: 8 lưu mới, 0 bỏ qua, 0 lỗi
```

---

## 🤖 GitHub Actions — Crawl Tự Động

File cấu hình: `.github/workflows/daily_crawl.yml`

### Lịch chạy
- **Tự động**: 18:30 giờ Việt Nam mỗi ngày (11:30 UTC)
- **Thủ công**: Vào **Actions** → **Daily Lottery Crawl** → **Run workflow**

### Tham số khi chạy thủ công

| Tham số | Mô tả | Ví dụ |
|---------|-------|-------|
| `date` | Ngày bắt đầu (YYYY-MM-DD) | `2026-01-01` |
| `days` | Số ngày cần crawl | `30` |

### Kiểm tra kết nối trước khi push

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from database.db import Database
db = Database()
print('Kết nối OK')
"
```

---

## 📖 Hướng Dẫn Sử Dụng App

### Tab 1 — 📥 Cập Nhật
1. Chọn **Từ ngày** và **Đến ngày**
2. Chọn **Tỉnh/Thành** (hoặc "Tất cả")
3. Tích **Chế độ Demo** nếu muốn test không cần internet
4. Nhấn **▶ CẬP NHẬT DỮ LIỆU** — nhấn **⏹ DỪNG** để dừng giữa chừng

### Tab 2 — 📋 Kết Quả
- Lọc theo khoảng ngày + tỉnh → nhấn **🔍 Xem**
- Xuất báo cáo: nhấn **📥 Xuất Excel**

### Tab 3 — 🎯 Lô 2 Số
- Tần suất 100 số lô tô (00–99)
- Biểu đồ nhiệt màu hot/cold
- **Lô Gan**: top số lâu không về (`Đang Gan` / `Siêu Gan` / `Tuyệt Chủng`)

### Tab 4 — 🎲 Lô 3 Số
- Tần suất 3 chữ số cuối, top nhiều & lô gan 3 số

### Tab 5 — 4️⃣ Lô 4 Số
- Tần suất 4 số cuối (giải 5, 6)

### Tab 6 — 5️⃣ Lô 5 Số
- Tần suất 5 số cuối (giải 1–4)

### Tab 7 — 🏆 Giải Đặc Biệt
- Thống kê 2 số cuối, 3 số cuối, chữ số đầu
- Lịch sử toàn bộ giải Đặc Biệt

### Tab 8 — 💡 Gợi Ý Số
- **Hot**: top số xuất hiện nhiều nhất
- **Cold / Gan**: top số lâu chưa về
- **Cầu**: số xuất hiện ≥ 3 kỳ liên tiếp trong 7 ngày gần nhất
- **Theo ĐB**: 2 số cuối giải ĐB các kỳ gần nhất

### Tab 9 — 🔄 Chu Kỳ
- Phân tích chu kỳ lặp lại trung bình của từng số

### Tab 10 — 📐 Đầu Đuôi
- Tần suất chữ số đầu (0–9) và chữ số đuôi (0–9)

---

## 🗄 Cơ Sở Dữ Liệu

### Schema bảng `draw_results`

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | SERIAL | Khoá chính tự tăng |
| `draw_date` | DATE | Ngày quay thưởng |
| `province` | TEXT | Tỉnh/thành (vd: "Bình Dương") |
| `special_prize` | TEXT | Giải Đặc Biệt (6 số) |
| `prize_1` – `prize_8` | TEXT | Giải Nhất đến Giải Tám |
| `created_at` | TIMESTAMPTZ | Thời điểm lưu |

**Ràng buộc**: `UNIQUE(draw_date, province)` — không lưu trùng.

### Biến môi trường

| Biến | Mô tả |
|------|-------|
| `DATABASE_URL` | URI PostgreSQL Transaction Pooler (port 6543). Không đặt → dùng SQLite local |

### 23 Tỉnh/Thành Miền Nam

Bình Dương · TP. Hồ Chí Minh · Đồng Nai · Long An · Bình Phước · Tây Ninh · Vũng Tàu ·
An Giang · Bến Tre · Cần Thơ · Đà Lạt · Hậu Giang · Kiên Giang · Sóc Trăng · Tiền Giang ·
Trà Vinh · Vĩnh Long · Cà Mau · Bạc Liêu · Đắk Lắk · Bình Thuận · Khánh Hòa · Ninh Thuận

---

## 🔧 Xử Lý Sự Cố

### ❌ GitHub Actions: `Network is unreachable` / `Connection refused`

**Nguyên nhân**: `DATABASE_URL` đang dùng Direct Connection (port 5432).

**Cách sửa**:
1. Vào Supabase → **Settings** → **Database** → **Connection string**
2. Chọn **Transaction pooler** → copy URI **(port 6543)**
3. GitHub repo → **Settings** → **Secrets** → cập nhật `DATABASE_URL`

### ❌ Streamlit Cloud: `psycopg2.OperationalError`

- **App settings** → **Secrets** → đảm bảo `DATABASE_URL` dùng port **6543**

### ❌ Không lấy được dữ liệu / bảng trống

```bash
python -c "
import requests, json
url = 'https://www.xosobinhduong.com.vn/get-lottery-mn'
r = requests.get(url, params={'mask':'getResultLoteryMn','lotdate':'2026-05-28','skip':'true','flagNumber':'-1'}, timeout=15)
print(r.status_code, json.dumps(r.json(), ensure_ascii=False)[:500])
"
```

### ❌ Lỗi import / thiếu thư viện

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### ❌ Reset dữ liệu local

```bash
del data\lottery.db        # Windows
rm data/lottery.db         # macOS/Linux
```

---

## 📦 Thư Viện & Nguồn Dữ Liệu

### Thư viện Python

| Thư viện | Mục đích |
|----------|----------|
| `streamlit` ≥1.35 | Web app framework |
| `plotly` ≥5.18 | Biểu đồ tương tác |
| `pandas` ≥2.0 | Xử lý & hiển thị dữ liệu |
| `requests` ≥2.28 | Gọi JSON API |
| `beautifulsoup4` + `lxml` | Parse HTML dự phòng |
| `psycopg2-binary` ≥2.9 | Kết nối PostgreSQL / Supabase |
| `openpyxl` ≥3.1 | Xuất báo cáo Excel |
| `python-dotenv` ≥1.0 | Đọc file `.env` |

### Nguồn dữ liệu

- **API JSON chính**:
  ```
  GET https://www.xosobinhduong.com.vn/get-lottery-mn
      ?mask=getResultLoteryMn&lotdate=YYYY-MM-DD&skip=true&flagNumber=-1
  ```
  Trả về JSON kết quả tất cả tỉnh trong ngày.

- **Selenium (dự phòng)**: Headless Chrome, chờ `span.giai-dac-biet`, chỉ dùng khi API không phản hồi.

---

*Cập nhật: tháng 5/2026*
