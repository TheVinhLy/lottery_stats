"""
Database models cho ứng dụng thống kê
Hỗ trợ SQLite (local) và PostgreSQL (Supabase production)
"""

# ── SQLite schema ────────────────────────────────────────────────
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS lottery_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date TEXT NOT NULL,
    province TEXT NOT NULL,
    special_prize TEXT,
    prize_1 TEXT,
    prize_2 TEXT,
    prize_3 TEXT,
    prize_4 TEXT,
    prize_5 TEXT,
    prize_6 TEXT,
    prize_7 TEXT,
    prize_8 TEXT,
    all_numbers TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(draw_date, province)
);

CREATE TABLE IF NOT EXISTS number_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    province TEXT NOT NULL,
    date_range_start TEXT,
    date_range_end TEXT,
    frequency INTEGER DEFAULT 0,
    last_appeared TEXT,
    days_absent INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_draw_date ON lottery_results(draw_date);
CREATE INDEX IF NOT EXISTS idx_province ON lottery_results(province);
CREATE INDEX IF NOT EXISTS idx_draw_date_province ON lottery_results(draw_date, province);
"""

# ── PostgreSQL schema (Supabase) ─────────────────────────────────
CREATE_TABLES_PG_SQL = """
CREATE TABLE IF NOT EXISTS lottery_results (
    id SERIAL PRIMARY KEY,
    draw_date TEXT NOT NULL,
    province TEXT NOT NULL,
    special_prize TEXT,
    prize_1 TEXT,
    prize_2 TEXT,
    prize_3 TEXT,
    prize_4 TEXT,
    prize_5 TEXT,
    prize_6 TEXT,
    prize_7 TEXT,
    prize_8 TEXT,
    all_numbers TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(draw_date, province)
);

CREATE TABLE IF NOT EXISTS number_stats (
    id SERIAL PRIMARY KEY,
    number TEXT NOT NULL,
    province TEXT NOT NULL,
    date_range_start TEXT,
    date_range_end TEXT,
    frequency INTEGER DEFAULT 0,
    last_appeared TEXT,
    days_absent INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_draw_date ON lottery_results(draw_date);
CREATE INDEX IF NOT EXISTS idx_province ON lottery_results(province);
CREATE INDEX IF NOT EXISTS idx_draw_date_province ON lottery_results(draw_date, province);
"""

PROVINCES = {
    "Bình Dương": "binh-duong",
    "TP. Hồ Chí Minh": "tp-ho-chi-minh",
    "Đồng Nai": "dong-nai",
    "Long An": "long-an",
    "Bình Phước": "binh-phuoc",
    "Tây Ninh": "tay-ninh",
    "Vũng Tàu": "vung-tau",
    "An Giang": "an-giang",
    "Bến Tre": "ben-tre",
    "Cần Thơ": "can-tho",
    "Đà Lạt": "da-lat",
    "Hậu Giang": "hau-giang",
    "Kiên Giang": "kien-giang",
    "Sóc Trăng": "soc-trang",
    "Tiền Giang": "tien-giang",
    "Trà Vinh": "tra-vinh",
    "Vĩnh Long": "vinh-long",
    "Cà Mau": "ca-mau",
    "Bạc Liêu": "bac-lieu",
    "Đắk Lắk": "dak-lak",
    "Bình Thuận": "binh-thuan",
    "Khánh Hòa": "khanh-hoa",
    "Ninh Thuận": "ninh-thuan",
}
