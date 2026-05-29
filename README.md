# 🎰 Phần Mềm Thống Kê Xổ Số Miền Nam

Ứng dụng desktop Python để thu thập, cập nhật và thống kê dữ liệu xổ số miền Nam từ website xosobinhduong.com.vn.

---

## 📁 Cấu Trúc Thư Mục

```
lottery_stats/
├── main.py                  ← Chạy file này
├── requirements.txt         ← Danh sách thư viện
│
├── gui/
│   └── main_window.py       ← Giao diện chính (Tkinter, 10 tab)
│
├── crawler/
│   ├── fetch.py             ← Gọi JSON API / Selenium dự phòng
│   ├── parser.py            ← Parse kết quả từ API hoặc HTML
│   └── scheduler.py         ← Điều phối crawl đa luồng
│
├── database/
│   ├── db.py                ← CRUD + toàn bộ hàm thống kê SQLite
│   └── models.py            ← SQL schema & danh sách 23 tỉnh/thành
│
├── reports/
│   └── export_excel.py      ← Xuất báo cáo Excel
│
└── data/
    └── lottery.db           ← Database SQLite (tự tạo khi chạy lần đầu)
```

---

## 🚀 Cài Đặt & Chạy

### 1. Cài Python 3.8+
Tải từ https://python.org

### 2. Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
```

### 3. Cài thư viện
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng
```bash
python main.py
```

---

## 📖 Hướng Dẫn Sử Dụng

Ứng dụng có **10 tab** chính:

### Tab 1 — 📥 Cập Nhật
1. Nhập **Từ ngày** và **Đến ngày** (định dạng dd/mm/yyyy)
2. Chọn **Tỉnh/Thành** (hoặc "Tất cả" để lấy toàn miền Nam)
3. Tích **Chế độ Demo** nếu không có internet (sinh dữ liệu ngẫu nhiên để test)
4. Nhấn **▶ CẬP NHẬT DỮ LIỆU** — có thể dừng giữa chừng bằng **⏹ DỪNG**
5. Theo dõi tiến trình và nhật ký bên phải

### Tab 2 — 📋 Kết Quả
- Lọc theo khoảng ngày và tỉnh
- Xem bảng kết quả đầy đủ tất cả giải
- Nhấn **Xuất Excel** để lưu báo cáo

### Tab 3 — 🎯 Lô 2 Số
- Tần suất xuất hiện 100 số lô tô (00–99)
- Bảng thống kê + biểu đồ cột màu nhiệt (hot/cold)
- Lô gan 2 số: số lâu không về, phân loại mức độ khan hiếm

### Tab 4 — 🎲 Lô 3 Số
- Tần suất 3 chữ số cuối của tất cả giải
- Top số xuất hiện nhiều nhất và lô gan 3 số

### Tab 5 — 4️⃣ Lô 4 Số
- Tần suất 4 số cuối (tập trung giải 5, giải 6)

### Tab 6 — 5️⃣ Lô 5 Số
- Tần suất 5 số cuối (tập trung giải 1–4)

### Tab 7 — 🏆 Giải Đặc Biệt
- Thống kê giải ĐB: 2 số cuối, 3 số cuối, chữ số đầu
- Danh sách lịch sử toàn bộ giải ĐB

### Tab 8 — 💡 Gợi Ý Số
- **Hot**: top số xuất hiện nhiều trong 30 ngày gần nhất
- **Cold/Gan**: top số lâu chưa về (có thể sắp quay lại)
- **Cầu**: số xuất hiện ≥ 3 kỳ liên tiếp trong 7 ngày gần nhất
- **Theo ĐB**: 2 số cuối giải ĐB của các kỳ gần nhất

### Tab 9 — 🔄 Chu Kỳ
- Phân tích chu kỳ lặp lại của các số

### Tab 10 — 📐 Đầu Đuôi
- Thống kê chữ số đầu (0–9) và chữ số đuôi (0–9) từ tất cả số lô

---

## ⚙️ Yêu Cầu Hệ Thống
- Python 3.8 trở lên
- Windows 10/11 (khuyến nghị), macOS, hoặc Linux
- Kết nối internet (để cập nhật dữ liệu thực)
- RAM: 256MB trở lên

## 📦 Thư Viện Sử Dụng
| Thư viện | Mục đích |
|----------|----------|
| `requests` | Gọi JSON API lấy kết quả xổ số |
| `beautifulsoup4` + `lxml` | Parse HTML dự phòng |
| `sqlite3` | Database local (built-in Python) |
| `tkinter` | Giao diện (built-in Python) |
| `openpyxl` | Xuất báo cáo Excel |
| `pandas` | Xử lý dữ liệu nâng cao (tùy chọn) |
| `selenium` | Dự phòng khi API bị chặn (tùy chọn) |

---

## 🌐 Nguồn Dữ Liệu

- **API chính**: `https://www.xosobinhduong.com.vn/get-lottery-mn`  
  Trả về JSON trực tiếp, không cần trình duyệt.
- **Dự phòng**: Selenium headless (Chrome) render trang HTML rồi parse kết quả.
- Mỗi ngày chỉ cần 1 request → parse ra kết quả của nhiều tỉnh cùng lúc.

## 🗺️ Danh Sách Tỉnh/Thành (23 tỉnh)

Bình Dương, TP. Hồ Chí Minh, Đồng Nai, Long An, Bình Phước, Tây Ninh, Vũng Tàu,
An Giang, Bến Tre, Cần Thơ, Đà Lạt, Hậu Giang, Kiên Giang, Sóc Trăng, Tiền Giang,
Trà Vinh, Vĩnh Long, Cà Mau, Bạc Liêu, Đắk Lắk, Bình Thuận, Khánh Hòa, Ninh Thuận.

---

## 🔧 Xử Lý Sự Cố

### Website bị chặn / không lấy được dữ liệu
- Dùng **Chế độ Demo** để test các chức năng thống kê
- Cài thêm `selenium` + Chrome để dùng chế độ dự phòng
- Kiểm tra kết nối internet

### Lỗi import
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Dữ liệu bị lỗi / muốn reset
- Xóa file `data/lottery.db` để bắt đầu lại từ đầu

---

## 📝 Ghi Chú
- Dữ liệu lưu trong `data/lottery.db` (SQLite, tự tạo)
- Không lưu bản ghi trùng (tự động bỏ qua nhờ ràng buộc `UNIQUE(draw_date, province)`)
- Có thể backup bằng cách copy file `.db`
- Header ứng dụng hiển thị tổng số bản ghi và khoảng ngày trong DB
