"""
Database - đầy đủ các hàm thống kê
Hỗ trợ SQLite (local) và PostgreSQL (Supabase production qua DATABASE_URL)
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from database.models import CREATE_TABLES_SQL, CREATE_TABLES_PG_SQL

# Load .env khi chạy local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _resolve_database_url() -> str:
    """
    Đọc DATABASE_URL theo thứ tự ưu tiên:
    1. Biến môi trường (local .env, GitHub Actions)
    2. st.secrets (Streamlit Cloud)
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL", "")
        if url:
            return url
    except Exception:
        pass
    return ""


class _PGConn:
    """
    Wrapper psycopg2 bắt chước interface của sqlite3.Connection,
    dùng DictCursor để rows hỗ trợ cả r[0] lẫn r['col'] giống sqlite3.Row.
    """
    def __init__(self, raw):
        self._raw = raw
        self._last_changes = 0

    def execute(self, sql: str, params=()):
        import psycopg2.extras
        sql = self._adapt(sql)
        cur = self._raw.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql, params)
        self._last_changes = max(0, cur.rowcount)
        return cur

    def executescript(self, sql: str):
        cur = self._raw.cursor()
        for stmt in sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)

    @property
    def total_changes(self) -> int:
        return self._last_changes

    def commit(self):   self._raw.commit()
    def rollback(self): self._raw.rollback()
    def close(self):    self._raw.close()

    @staticmethod
    def _adapt(sql: str) -> str:
        """Chuyển SQLite dialect → PostgreSQL dialect."""
        sql = sql.replace("?", "%s")
        # INSERT OR IGNORE xử lý riêng ở save_result
        return sql


class Database:
    def __init__(self, db_path: str = None):
        db_url = _resolve_database_url()
        self.use_pg = bool(db_url)
        if self.use_pg:
            self._pg_url = db_url
        else:
            if db_path is None:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, "data", "lottery.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Context manager — yield connection (SQLite hoặc PG wrapper), tự commit/rollback/close."""
        if self.use_pg:
            import psycopg2
            raw = psycopg2.connect(self._pg_url)
            conn = _PGConn(raw)
        else:
            raw = sqlite3.connect(self.db_path)
            raw.row_factory = sqlite3.Row
            conn = raw
        try:
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _init_db(self):
        if self.use_pg:
            import psycopg2
            raw = psycopg2.connect(self._pg_url)
            try:
                conn = _PGConn(raw)
                conn.executescript(CREATE_TABLES_PG_SQL)
                conn.commit()
            finally:
                raw.close()
        else:
            with sqlite3.connect(self.db_path) as raw:
                raw.executescript(CREATE_TABLES_SQL)
                raw.commit()

    # ── Lưu dữ liệu ──────────────────────────────────────────────────────

    def save_result(self, data: Dict) -> bool:
        if self.use_pg:
            sql = """INSERT INTO lottery_results
            (draw_date, province, special_prize, prize_1, prize_2, prize_3,
             prize_4, prize_5, prize_6, prize_7, prize_8, all_numbers)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (draw_date, province) DO NOTHING"""
        else:
            sql = """INSERT OR IGNORE INTO lottery_results
            (draw_date, province, special_prize, prize_1, prize_2, prize_3,
             prize_4, prize_5, prize_6, prize_7, prize_8, all_numbers)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
        try:
            with self._get_conn() as conn:
                conn.execute(sql, (
                    data.get("draw_date"), data.get("province"),
                    data.get("special_prize",""), data.get("prize_1",""),
                    data.get("prize_2",""),   data.get("prize_3",""),
                    data.get("prize_4",""),   data.get("prize_5",""),
                    data.get("prize_6",""),   data.get("prize_7",""),
                    data.get("prize_8",""),   data.get("all_numbers",""),
                ))
                conn.commit()
                return conn.total_changes > 0
        except Exception as e:
            print(f"[DB] Lỗi lưu: {e}")
            return False

    # ── Truy vấn cơ bản ──────────────────────────────────────────────────

    def get_results(self, start_date: str, end_date: str, province: str = None) -> List[Dict]:
        if province and province != "Tất cả":
            sql = "SELECT * FROM lottery_results WHERE draw_date BETWEEN ? AND ? AND province=? ORDER BY draw_date DESC"
            params = (start_date, end_date, province)
        else:
            sql = "SELECT * FROM lottery_results WHERE draw_date BETWEEN ? AND ? ORDER BY draw_date DESC"
            params = (start_date, end_date)
        with self._get_conn() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_record_count(self, province: str = None) -> int:
        if province and province != "Tất cả":
            sql, params = "SELECT COUNT(*) FROM lottery_results WHERE province=?", (province,)
        else:
            sql, params = "SELECT COUNT(*) FROM lottery_results", ()
        with self._get_conn() as conn:
            r = conn.execute(sql, params).fetchone()
            return r[0] if r else 0

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        with self._get_conn() as conn:
            r = conn.execute("SELECT MIN(draw_date), MAX(draw_date) FROM lottery_results").fetchone()
            return (r[0], r[1]) if r else (None, None)

    def check_exists(self, draw_date: str, province: str) -> bool:
        with self._get_conn() as conn:
            r = conn.execute("SELECT 1 FROM lottery_results WHERE draw_date=? AND province=?",
                             (draw_date, province)).fetchone()
            return r is not None

    def get_provinces_in_db(self) -> List[str]:
        with self._get_conn() as conn:
            return [r[0] for r in conn.execute(
                "SELECT DISTINCT province FROM lottery_results ORDER BY province").fetchall()]

    # ── Helper: trích số từ kết quả ──────────────────────────────────────

    def _extract_numbers(self, results: List[Dict], digits: int = 2) -> List[str]:
        """Trích tất cả số có đúng `digits` chữ số từ danh sách kết quả"""
        nums = []
        for r in results:
            raw = r.get("all_numbers", "")
            for tok in raw.split(","):
                tok = tok.strip()
                if tok and len(tok) >= digits:
                    # Lấy `digits` chữ số cuối
                    sub = tok[-digits:]
                    if sub.isdigit():
                        nums.append(sub)
        return nums

    def _extract_exact(self, results: List[Dict], digits: int) -> List[str]:
        """Trích số có ĐÚNG `digits` chữ số"""
        nums = []
        for r in results:
            raw = r.get("all_numbers", "")
            for tok in raw.split(","):
                tok = tok.strip()
                if len(tok) == digits and tok.isdigit():
                    nums.append(tok)
        return nums

    # ── Thống kê 2 số (lô tô) ────────────────────────────────────────────

    def get_number_frequency(self, start_date: str, end_date: str, province: str = None) -> Dict[str, int]:
        results = self.get_results(start_date, end_date, province)
        freq: Dict[str, int] = {}
        for n in self._extract_numbers(results, 2):
            freq[n] = freq.get(n, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    def get_head_tail_stats(self, start_date: str, end_date: str, province: str = None) -> Dict:
        results = self.get_results(start_date, end_date, province)
        head = {str(i): 0 for i in range(10)}
        tail = {str(i): 0 for i in range(10)}
        for n in self._extract_numbers(results, 2):
            head[n[0]] = head.get(n[0], 0) + 1
            tail[n[1]] = tail.get(n[1], 0) + 1
        return {"head": head, "tail": tail}

    def get_gan_numbers(self, reference_date: str, province: str = None, top_n: int = 30) -> List[Dict]:
        """Lô gan 2 số — lâu không xuất hiện"""
        if province and province != "Tất cả":
            sql = "SELECT * FROM lottery_results WHERE draw_date<=? AND province=? ORDER BY draw_date DESC LIMIT 200"
            params = (reference_date, province)
        else:
            sql = "SELECT * FROM lottery_results WHERE draw_date<=? ORDER BY draw_date DESC LIMIT 500"
            params = (reference_date,)
        with self._get_conn() as conn:
            results = [dict(r) for r in conn.execute(sql, params).fetchall()]

        last_seen: Dict[str, Tuple[str, int]] = {}
        for i, r in enumerate(results):
            for n in self._extract_numbers([r], 2):
                if n not in last_seen:
                    last_seen[n] = (r["draw_date"], i)

        gan = []
        for n in [f"{i:02d}" for i in range(100)]:
            if n in last_seen:
                d, idx = last_seen[n]
                gan.append({"number": n, "last_date": d, "days_absent": idx})
            else:
                gan.append({"number": n, "last_date": "Chưa xuất hiện", "days_absent": 9999})
        gan.sort(key=lambda x: x["days_absent"], reverse=True)
        return gan[:top_n]

    # ── Thống kê 3 số ─────────────────────────────────────────────────────

    def get_3digit_frequency(self, start_date: str, end_date: str, province: str = None) -> Dict[str, int]:
        """Tần suất 3 số cuối của tất cả giải"""
        results = self.get_results(start_date, end_date, province)
        freq: Dict[str, int] = {}
        for n in self._extract_numbers(results, 3):
            freq[n] = freq.get(n, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    def get_3digit_gan(self, reference_date: str, province: str = None, top_n: int = 30) -> List[Dict]:
        """Gan 3 số"""
        if province and province != "Tất cả":
            sql = "SELECT * FROM lottery_results WHERE draw_date<=? AND province=? ORDER BY draw_date DESC LIMIT 300"
            params = (reference_date, province)
        else:
            sql = "SELECT * FROM lottery_results WHERE draw_date<=? ORDER BY draw_date DESC LIMIT 600"
            params = (reference_date,)
        with self._get_conn() as conn:
            results = [dict(r) for r in conn.execute(sql, params).fetchall()]

        last_seen: Dict[str, Tuple[str, int]] = {}
        for i, r in enumerate(results):
            for n in self._extract_numbers([r], 3):
                if n not in last_seen:
                    last_seen[n] = (r["draw_date"], i)

        # Lấy top gan từ những số đã từng xuất hiện
        gan = []
        for n, (d, idx) in last_seen.items():
            gan.append({"number": n, "last_date": d, "days_absent": idx})
        gan.sort(key=lambda x: x["days_absent"], reverse=True)
        return gan[:top_n]

    # ── Thống kê 4 số ─────────────────────────────────────────────────────

    def get_4digit_frequency(self, start_date: str, end_date: str, province: str = None) -> Dict[str, int]:
        """Tần suất 4 số cuối — giải 5, 6"""
        results = self.get_results(start_date, end_date, province)
        freq: Dict[str, int] = {}
        for r in results:
            for field in ["prize_5", "prize_6"]:
                for tok in r.get(field, "").split():
                    tok = tok.strip()
                    if len(tok) == 4 and tok.isdigit():
                        freq[tok] = freq.get(tok, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    # ── Thống kê 5 số ─────────────────────────────────────────────────────

    def get_5digit_frequency(self, start_date: str, end_date: str, province: str = None) -> Dict[str, int]:
        """Tần suất 5 số — giải 1, 2, 3, 4"""
        results = self.get_results(start_date, end_date, province)
        freq: Dict[str, int] = {}
        for r in results:
            for field in ["prize_1", "prize_2", "prize_3", "prize_4"]:
                for tok in r.get(field, "").split():
                    tok = tok.strip()
                    if len(tok) == 5 and tok.isdigit():
                        freq[tok] = freq.get(tok, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    # ── Giải đặc biệt ─────────────────────────────────────────────────────

    def get_special_prize_stats(self, start_date: str, end_date: str, province: str = None) -> Dict:
        """Thống kê giải đặc biệt: 2 số cuối, 3 số cuối, đầu số"""
        results = self.get_results(start_date, end_date, province)
        last2: Dict[str, int] = {}
        last3: Dict[str, int] = {}
        first1: Dict[str, int] = {}
        all_specials = []

        for r in results:
            sp = r.get("special_prize", "").strip()
            if sp and sp.isdigit() and len(sp) >= 4:
                all_specials.append({"date": r["draw_date"], "province": r["province"], "number": sp})
                n2 = sp[-2:]
                n3 = sp[-3:]
                n1 = sp[0]
                last2[n2] = last2.get(n2, 0) + 1
                last3[n3] = last3.get(n3, 0) + 1
                first1[n1] = first1.get(n1, 0) + 1

        return {
            "last2":  dict(sorted(last2.items(),  key=lambda x: x[1], reverse=True)),
            "last3":  dict(sorted(last3.items(),  key=lambda x: x[1], reverse=True)),
            "first1": dict(sorted(first1.items(), key=lambda x: x[1], reverse=True)),
            "all":    all_specials,
        }

    # ── Gợi ý số ─────────────────────────────────────────────────────────

    def get_suggestions(self, reference_date: str, province: str = None) -> Dict:
        """
        Gợi ý số dựa trên nhiều tiêu chí:
        - Hot: xuất hiện nhiều trong 30 ngày gần nhất
        - Cold (Gan): lâu không xuất hiện → có thể sắp về
        - Cầu: xuất hiện liên tục nhiều kỳ liên tiếp
        - Theo đặc biệt: 2 số cuối giải ĐB kỳ trước
        """
        ref = datetime.strptime(reference_date, "%Y-%m-%d").date()
        d30_ago = (ref - timedelta(days=30)).strftime("%Y-%m-%d")
        d7_ago  = (ref - timedelta(days=7)).strftime("%Y-%m-%d")

        # Hot: top 10 trong 30 ngày
        freq_30 = self.get_number_frequency(d30_ago, reference_date, province)
        hot = [{"number": n, "count": c, "reason": f"Xuất hiện {c} lần/30 ngày"}
               for n, c in list(freq_30.items())[:10]]

        # Cold (gan): top 10 lâu nhất
        gan = self.get_gan_numbers(reference_date, province, top_n=10)
        cold = [{"number": g["number"], "last_date": g["last_date"],
                 "days_absent": g["days_absent"],
                 "reason": f"Vắng {g['days_absent']} kỳ"} for g in gan]

        # Cầu: số xuất hiện >= 3 kỳ liên tiếp trong 7 ngày
        freq_7 = self.get_number_frequency(d7_ago, reference_date, province)
        cau = [{"number": n, "count": c, "reason": f"Cầu {c} kỳ liên tiếp"}
               for n, c in freq_7.items() if c >= 3][:10]

        # Theo giải ĐB: lấy 2 số cuối của ĐB kỳ gần nhất
        if province and province != "Tất cả":
            sql = "SELECT special_prize, draw_date FROM lottery_results WHERE draw_date<=? AND province=? AND special_prize!='' ORDER BY draw_date DESC LIMIT 5"
            params = (reference_date, province)
        else:
            sql = "SELECT special_prize, draw_date, province FROM lottery_results WHERE draw_date<=? AND special_prize!='' ORDER BY draw_date DESC LIMIT 10"
            params = (reference_date,)
        with self._get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        theo_db = []
        for row in rows:
            sp = row[0].strip()
            if sp and len(sp) >= 2:
                n2 = sp[-2:]
                theo_db.append({
                    "number": n2,
                    "from_special": sp,
                    "date": row[1],
                    "reason": f"2 số cuối ĐB {sp} ngày {row[1]}"
                })

        return {"hot": hot, "cold": cold, "cau": cau, "theo_db": theo_db}

    # ── Thống kê theo kỳ / chu kỳ ────────────────────────────────────────

    def get_cycle_stats(self, number: str, province: str = None) -> Dict:
        """Phân tích chu kỳ xuất hiện của 1 số cụ thể"""
        if province and province != "Tất cả":
            sql = "SELECT draw_date FROM lottery_results WHERE province=? AND all_numbers LIKE ? ORDER BY draw_date"
            params = (province, f"%{number}%")
        else:
            sql = "SELECT draw_date FROM lottery_results WHERE all_numbers LIKE ? ORDER BY draw_date"
            params = (f"%{number}%",)

        with self._get_conn() as conn:
            rows = [r[0] for r in conn.execute(sql, params).fetchall()]

        # Lọc những ngày thực sự có số này (LIKE có thể false positive)
        confirmed = []
        with self._get_conn() as conn:
            for d in rows:
                r = conn.execute(
                    "SELECT all_numbers FROM lottery_results WHERE draw_date=?" +
                    (" AND province=?" if province and province != "Tất cả" else ""),
                    (d, province) if province and province != "Tất cả" else (d,)
                ).fetchone()
                if r:
                    nums = [n.strip() for n in r[0].split(",")]
                    if any(n[-2:] == number for n in nums if len(n) >= 2):
                        confirmed.append(d)

        if len(confirmed) < 2:
            return {"dates": confirmed, "avg_cycle": 0, "min_cycle": 0, "max_cycle": 0, "total": len(confirmed)}

        # Tính chu kỳ (khoảng cách giữa các lần xuất hiện, tính bằng ngày)
        cycles = []
        for i in range(1, len(confirmed)):
            d1 = datetime.strptime(confirmed[i-1], "%Y-%m-%d").date()
            d2 = datetime.strptime(confirmed[i],   "%Y-%m-%d").date()
            cycles.append((d2 - d1).days)

        return {
            "dates":     confirmed,
            "total":     len(confirmed),
            "avg_cycle": round(sum(cycles) / len(cycles), 1) if cycles else 0,
            "min_cycle": min(cycles) if cycles else 0,
            "max_cycle": max(cycles) if cycles else 0,
            "cycles":    cycles,
        }

    # ── Thống kê tổng hợp ────────────────────────────────────────────────

    def get_summary_stats(self, start_date: str, end_date: str, province: str = None) -> Dict:
        """Tổng hợp nhanh cho dashboard"""
        results = self.get_results(start_date, end_date, province)
        if not results:
            return {}

        freq = self.get_number_frequency(start_date, end_date, province)
        top5  = list(freq.items())[:5]
        bot5  = list(freq.items())[-5:]

        ht = self.get_head_tail_stats(start_date, end_date, province)
        top_head = max(ht["head"].items(), key=lambda x: x[1])
        top_tail = max(ht["tail"].items(), key=lambda x: x[1])

        sp_stats = self.get_special_prize_stats(start_date, end_date, province)
        top_db2  = list(sp_stats["last2"].items())[:3] if sp_stats["last2"] else []

        return {
            "total_records": len(results),
            "top5_numbers":  top5,
            "bot5_numbers":  bot5,
            "top_head":      top_head,
            "top_tail":      top_tail,
            "top_db_last2":  top_db2,
        }

    def get_top_numbers(self, start_date: str, end_date: str, province: str = None, top_n: int = 10) -> List[Dict]:
        freq = self.get_number_frequency(start_date, end_date, province)
        return [{"number": n, "count": c} for n, c in list(freq.items())[:top_n]]
