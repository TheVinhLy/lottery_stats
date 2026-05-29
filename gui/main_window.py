"""
Giao diện chính - đầy đủ thống kê
"""
import sys, os, threading
from datetime import date, datetime, timedelta
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database
from database.models import PROVINCES
from crawler.scheduler import CrawlScheduler
from reports.export_excel import export_results

# ── Màu sắc ───────────────────────────────────────────────────────────────
C = {
    "bg":       "#0F1923",
    "panel":    "#1A2634",
    "card":     "#243447",
    "accent":   "#00D4FF",
    "orange":   "#FF6B35",
    "green":    "#2ECC71",
    "yellow":   "#F39C12",
    "red":      "#E74C3C",
    "purple":   "#9B59B6",
    "teal":     "#1ABC9C",
    "text":     "#E8F4FD",
    "muted":    "#8BA3BB",
    "border":   "#2C4056",
    "gold":     "#FFD700",
    "hot":      "#FF4757",
    "cold":     "#70A1FF",
}

PRIZE_LABELS = ["Tất cả", "Giải ĐB", "Giải 1", "Giải 2", "Giải 3",
                "Giải 4", "Giải 5", "Giải 6", "Giải 7", "Giải 8"]


# ── Widget helpers ─────────────────────────────────────────────────────────

def _lbl(parent, text, font_size=9, bold=False, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text,
                    font=("Segoe UI", font_size, "bold" if bold else "normal"),
                    fg=fg or C["text"], bg=bg or C["panel"], **kw)

def _btn(parent, text, cmd, bg=None, fg="white", padx=12, pady=6, **kw):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Segoe UI", 9, "bold"),
                     fg=fg, bg=bg or C["orange"],
                     activebackground=bg or C["orange"],
                     activeforeground=fg,
                     relief="flat", cursor="hand2",
                     padx=padx, pady=pady, **kw)

def _sep(parent, color=None):
    tk.Frame(parent, bg=color or C["border"], height=1).pack(fill="x", padx=12, pady=6)

def _combo(parent, var, values, width=16, **kw):
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly", font=("Segoe UI", 9), width=width, **kw)
    return cb

def _date_entry(parent, default_date: date, width=11):
    e = tk.Entry(parent, font=("Segoe UI", 9),
                 fg=C["text"], bg=C["card"],
                 insertbackground=C["accent"],
                 relief="flat", width=width)
    e.insert(0, default_date.strftime("%d/%m/%Y"))
    return e

def _tree(parent, cols, headings, widths, height=20, show="headings"):
    style = ttk.Style()
    style.configure("X.Treeview",
                    background=C["card"], foreground=C["text"],
                    fieldbackground=C["card"], rowheight=24,
                    font=("Segoe UI", 9))
    style.configure("X.Treeview.Heading",
                    background=C["panel"], foreground=C["accent"],
                    font=("Segoe UI", 9, "bold"))
    style.map("X.Treeview", background=[("selected", C["border"])])

    tv = ttk.Treeview(parent, columns=cols, show=show,
                      style="X.Treeview", height=height)
    for col, hd, w in zip(cols, headings, widths):
        tv.heading(col, text=hd)
        tv.column(col, width=w, anchor="center")
    return tv

def _scrolled_tree(parent, cols, headings, widths, height=20):
    frame = tk.Frame(parent, bg=C["bg"])
    frame.pack(fill="both", expand=True)
    tv = _tree(frame, cols, headings, widths, height)
    vsb = tk.Scrollbar(frame, orient="vertical", command=tv.yview)
    hsb = tk.Scrollbar(frame, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tv.pack(fill="both", expand=True)
    return tv

def _filter_bar(parent, with_province=True, with_date=True,
                default_from=None, default_to=None):
    """Thanh filter dùng chung — trả về dict các widget"""
    bar = tk.Frame(parent, bg=C["panel"])
    bar.pack(fill="x", padx=10, pady=(8, 2))
    widgets = {}

    if with_date:
        _lbl(bar, "Từ:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        e_from = _date_entry(bar, default_from or date.today() - timedelta(days=90))
        e_from.pack(side="left")
        widgets["from"] = e_from

        _lbl(bar, "Đến:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(6,2))
        e_to = _date_entry(bar, default_to or date.today())
        e_to.pack(side="left")
        widgets["to"] = e_to

    if with_province:
        _lbl(bar, "Tỉnh:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        var_prov = tk.StringVar(value="Tất cả")
        cb = _combo(bar, var_prov, ["Tất cả"] + list(PROVINCES.keys()), width=18)
        cb.pack(side="left", padx=2)
        widgets["province_var"] = var_prov
        widgets["province_cb"]  = cb

    return bar, widgets


def _parse_date(text: str) -> Optional[date]:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎯 Phần Mềm Thống Kê")
        self.geometry("1340x860")
        self.minsize(1100, 720)
        self.configure(bg=C["bg"])

        self.db = Database()
        self.scheduler = CrawlScheduler(self.db)
        self._crawl_running = False

        self._setup_notebook_style()
        self._build_header()
        self._build_tabs()
        self._refresh_header()

    # ── Style ─────────────────────────────────────────────────────────────

    def _setup_notebook_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("NB.TNotebook", background=C["bg"], borderwidth=0)
        s.configure("NB.TNotebook.Tab",
                    background=C["panel"], foreground=C["muted"],
                    padding=[14, 7], font=("Segoe UI", 9, "bold"))
        s.map("NB.TNotebook.Tab",
              background=[("selected", C["card"])],
              foreground=[("selected", C["accent"])])

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["panel"], height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎯  PHẦN MỀM THỐNG KÊ",
                 font=("Segoe UI", 15, "bold"),
                 fg=C["accent"], bg=C["panel"]).pack(side="left", padx=18, pady=10)

        self.lbl_status = tk.Label(hdr, text="● Sẵn sàng",
                                   font=("Segoe UI", 9), fg=C["green"], bg=C["panel"])
        self.lbl_status.pack(side="right", padx=16)
        self.lbl_db = tk.Label(hdr, text="",
                               font=("Segoe UI", 9), fg=C["muted"], bg=C["panel"])
        self.lbl_db.pack(side="right", padx=10)

    def _refresh_header(self):
        count = self.db.get_record_count()
        mn, mx = self.db.get_date_range()
        if mn:
            self.lbl_db.configure(text=f"DB: {count:,} bản ghi  ({mn} → {mx})")
        else:
            self.lbl_db.configure(text=f"DB: {count:,} bản ghi")

    # ── Tabs ──────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self.nb = ttk.Notebook(self, style="NB.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4,8))

        self._build_tab_update()
        self._build_tab_results()
        self._build_tab_lo2()
        self._build_tab_lo3()
        self._build_tab_lo4()
        self._build_tab_lo5()
        self._build_tab_special()
        self._build_tab_suggest()
        self._build_tab_cycle()
        self._build_tab_headtail()

    # ══════════════════════════════════════════════════════════════════════
    # Tab 1: Cập nhật
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_update(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  📥 Cập Nhật  ")

        left = tk.Frame(f, bg=C["panel"], width=300)
        left.pack(side="left", fill="y", padx=(10,4), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="CẤU HÌNH CẬP NHẬT",
                 font=("Segoe UI", 10, "bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(pady=(16,4), padx=14, anchor="w")
        _sep(left)

        _lbl(left, "Từ ngày:", bg=C["panel"], fg=C["muted"]).pack(padx=14, anchor="w", pady=(4,1))
        self.upd_from = _date_entry(left, date.today() - timedelta(days=30), width=18)
        self.upd_from.pack(padx=14, fill="x", pady=2)

        _lbl(left, "Đến ngày:", bg=C["panel"], fg=C["muted"]).pack(padx=14, anchor="w", pady=(4,1))
        self.upd_to = _date_entry(left, date.today(), width=18)
        self.upd_to.pack(padx=14, fill="x", pady=2)

        _lbl(left, "Tỉnh/Thành:", bg=C["panel"], fg=C["muted"]).pack(padx=14, anchor="w", pady=(4,1))
        self.upd_prov_var = tk.StringVar(value="Tất cả")
        cb = _combo(left, self.upd_prov_var, ["Tất cả"] + list(PROVINCES.keys()), width=22)
        cb.pack(padx=14, fill="x", pady=2)

        self.var_demo = tk.BooleanVar(value=False)
        tk.Checkbutton(left, text="🧪 Chế độ Demo (không cần internet)",
                       variable=self.var_demo,
                       font=("Segoe UI", 9), fg=C["muted"], bg=C["panel"],
                       activebackground=C["panel"], selectcolor=C["card"]
                       ).pack(padx=14, pady=8, anchor="w")

        _sep(left)

        self.btn_start = _btn(left, "▶  CẬP NHẬT DỮ LIỆU", self._start_crawl,
                              bg=C["orange"], pady=10)
        self.btn_start.pack(fill="x", padx=14, pady=(8,3))

        self.btn_stop = _btn(left, "⏹  DỪNG", self._stop_crawl,
                             bg=C["red"], pady=8, state="disabled")
        self.btn_stop.pack(fill="x", padx=14, pady=3)

        _btn(left, "🔄  Làm Mới", self._refresh_all,
             bg=C["card"], pady=8).pack(fill="x", padx=14, pady=3)

        _sep(left)
        _lbl(left, "TIẾN TRÌNH", bg=C["panel"], fg=C["muted"], font_size=8
             ).pack(padx=14, anchor="w", pady=(4,1))
        self.prog_var = tk.DoubleVar()
        ttk.Progressbar(left, variable=self.prog_var, maximum=100
                        ).pack(fill="x", padx=14, pady=3)
        self.lbl_prog = _lbl(left, "0 / 0", bg=C["panel"], fg=C["muted"], font_size=8)
        self.lbl_prog.pack(padx=14, anchor="w")

        # Log
        right = tk.Frame(f, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(4,10), pady=10)
        _lbl(right, "NHẬT KÝ", bg=C["bg"], fg=C["accent"], font_size=10, bold=True
             ).pack(anchor="w", pady=(4,3))

        log_frame = tk.Frame(right, bg=C["card"])
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, font=("Consolas", 9),
                           fg=C["text"], bg=C["card"],
                           insertbackground=C["accent"],
                           relief="flat", wrap="word", state="disabled")
        sb = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)
        self.log.tag_configure("ok",   foreground=C["green"])
        self.log.tag_configure("err",  foreground=C["red"])
        self.log.tag_configure("warn", foreground=C["yellow"])
        self._log(f"Khởi động: {datetime.now():%d/%m/%Y %H:%M:%S}")
        self._log(f"Database: {self.db.db_path}")
        self._log(f"Tổng bản ghi: {self.db.get_record_count():,}")

    def _log(self, msg, tag=""):
        def _w():
            self.log.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self.log.insert("end", f"[{ts}] {msg}\n", tag)
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, _w)

    def _start_crawl(self):
        if self._crawl_running: return
        s = _parse_date(self.upd_from.get())
        e = _parse_date(self.upd_to.get())
        if not s or not e:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ! Dùng dd/mm/yyyy")
            return
        if s > e:
            messagebox.showerror("Lỗi", "Từ ngày phải trước Đến ngày!")
            return
        self._crawl_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="● Đang cập nhật...", fg=C["yellow"])
        self._log(f"Bắt đầu: {s} → {e} | {self.upd_prov_var.get()}")
        self.scheduler.crawl_async(s, e, self.upd_prov_var.get(),
                                   on_progress=self._on_prog,
                                   on_done=self._on_done,
                                   on_error=self._on_err,
                                   use_mock=self.var_demo.get())

    def _stop_crawl(self):
        self.scheduler.stop()
        self._log("Đã dừng.", "warn")
        self._reset_crawl()

    def _on_prog(self, done, total, msg):
        pct = done/total*100 if total else 0
        tag = "ok" if "✓" in msg else ("warn" if "✗" in msg else "")
        def _u():
            self.prog_var.set(pct)
            self.lbl_prog.configure(text=f"{done} / {total}  ({pct:.0f}%)")
            self._log(msg, tag)
        self.after(0, _u)

    def _on_done(self, saved, skipped):
        def _u():
            self._log(f"✅ Hoàn tất! Mới: {saved}, Bỏ qua: {skipped}", "ok")
            self._reset_crawl()
            self._refresh_all()
            messagebox.showinfo("Hoàn Tất", f"✅ Cập nhật xong!\nMới: {saved}  |  Bỏ qua: {skipped}")
        self.after(0, _u)

    def _on_err(self, err):
        def _u():
            self._log(f"❌ Lỗi: {err}", "err")
            self._reset_crawl()
            messagebox.showerror("Lỗi", err)
        self.after(0, _u)

    def _reset_crawl(self):
        self._crawl_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="● Sẵn sàng", fg=C["green"])
        self.prog_var.set(0)

    def _refresh_all(self):
        self._refresh_header()

    # ══════════════════════════════════════════════════════════════════════
    # Tab 2: Kết quả
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_results(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  📋 Kết Quả  ")

        bar, w = _filter_bar(f)
        self.res_from = w["from"]; self.res_to = w["to"]
        self.res_prov = w["province_var"]
        _btn(bar, "🔍 Xem", self._load_results, bg=C["orange"]).pack(side="left", padx=6)
        _btn(bar, "📊 Xuất Excel", self._export_excel, bg=C["green"]).pack(side="right", padx=8)
        self.lbl_res_count = _lbl(bar, "", bg=C["panel"], fg=C["muted"])
        self.lbl_res_count.pack(side="right", padx=6)

        cols = ("date","prov","db","g1","g2","g3","g4","g5","g6","g7","g8")
        heads = ("Ngày","Tỉnh","Đặc Biệt","Giải 1","Giải 2","Giải 3","Giải 4","Giải 5","Giải 6","Giải 7","Giải 8")
        widths = (90,110,80,70,130,240,200,70,110,80,60)
        wrap = tk.Frame(f, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=10, pady=(2,8))
        self.res_tree = _tree(wrap, cols, heads, widths, height=28)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self.res_tree.yview)
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=self.res_tree.xview)
        self.res_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.res_tree.grid(row=0,column=0,sticky="nsew")
        vsb.grid(row=0,column=1,sticky="ns")
        hsb.grid(row=1,column=0,sticky="ew")
        wrap.grid_rowconfigure(0,weight=1); wrap.grid_columnconfigure(0,weight=1)
        self._load_results()

    def _load_results(self):
        s = _parse_date(self.res_from.get()); e = _parse_date(self.res_to.get())
        if not s or not e: return
        rows = self.db.get_results(s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"),
                                   self.res_prov.get())
        self.res_tree.delete(*self.res_tree.get_children())
        for r in rows:
            self.res_tree.insert("","end", values=(
                r["draw_date"], r["province"], r["special_prize"],
                r["prize_1"], r["prize_2"], r["prize_3"], r["prize_4"],
                r["prize_5"], r["prize_6"], r["prize_7"], r["prize_8"]))
        self.lbl_res_count.configure(text=f"{len(rows):,} bản ghi")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 3: Thống kê 2 số (lô tô)
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_lo2(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  🎯 Lô 2 Số  ")

        bar, w = _filter_bar(f)
        self.lo2_from = w["from"]; self.lo2_to = w["to"]
        self.lo2_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_lo2, bg=C["orange"]).pack(side="left", padx=6)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        content.columnconfigure(0, weight=2); content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # Bảng tần suất
        left = tk.Frame(content, bg=C["panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="TẦN SUẤT SỐ LÔ TÔ (00–99)",
                 font=("Segoe UI",10,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.lo2_tree = _scrolled_tree(left,
            ("rank","num","count","bar","pct"),
            ("#","Số","Lần XH","█ Biểu đồ","Tỷ lệ"),
            (35,55,65,220,60), height=26)

        # Panel bên phải: top/bottom
        right = tk.Frame(content, bg=C["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4,0))

        tk.Label(right, text="🔥 TOP 10 NÓNG NHẤT",
                 font=("Segoe UI",9,"bold"), fg=C["hot"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,2))
        self.lo2_hot = _scrolled_tree(right,
            ("num","count"),("Số","Lần"),(70,70), height=10)

        tk.Label(right, text="❄️ TOP 10 LẠNH NHẤT",
                 font=("Segoe UI",9,"bold"), fg=C["cold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(14,2))
        self.lo2_cold = _scrolled_tree(right,
            ("num","count"),("Số","Lần"),(70,70), height=10)

    def _load_lo2(self):
        s = _parse_date(self.lo2_from.get()); e = _parse_date(self.lo2_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.lo2_prov.get()
        freq = self.db.get_number_frequency(ss, es, prov)
        items = list(freq.items())
        if not items: return
        mx = items[0][1] or 1
        total = sum(v for _,v in items)

        self.lo2_tree.delete(*self.lo2_tree.get_children())
        for rank, (num, cnt) in enumerate(items, 1):
            bar = "█" * int(cnt/mx*28)
            pct = f"{cnt/total*100:.1f}%"
            self.lo2_tree.insert("","end", values=(rank,num,cnt,bar,pct))

        self.lo2_hot.delete(*self.lo2_hot.get_children())
        for num,cnt in items[:10]:
            self.lo2_hot.insert("","end", values=(num,cnt))

        self.lo2_cold.delete(*self.lo2_cold.get_children())
        # Thêm các số chưa xuất hiện
        all_nums = {f"{i:02d}" for i in range(100)}
        seen = {n for n,_ in items}
        zero = [(n,0) for n in sorted(all_nums - seen)]
        bottom = list(reversed(items[-10:])) + zero
        for num,cnt in bottom[:10]:
            self.lo2_cold.insert("","end", values=(num,cnt))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 4: Lô 3 số
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_lo3(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  🎲 Lô 3 Số  ")

        bar, w = _filter_bar(f)
        self.lo3_from = w["from"]; self.lo3_to = w["to"]
        self.lo3_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_lo3, bg=C["orange"]).pack(side="left", padx=6)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        content.columnconfigure(0, weight=2); content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=C["panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="TẦN SUẤT 3 SỐ CUỐI",
                 font=("Segoe UI",10,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.lo3_tree = _scrolled_tree(left,
            ("rank","num","count","bar"),
            ("#","3 Số","Lần","█ Biểu đồ"),
            (40,70,65,200), height=26)

        right = tk.Frame(content, bg=C["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        tk.Label(right, text="🔥 TOP 15 HAY XUẤT HIỆN",
                 font=("Segoe UI",9,"bold"), fg=C["hot"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,2))
        self.lo3_top = _scrolled_tree(right,
            ("num","count"),("3 Số","Lần"),(80,70), height=15)

        tk.Label(right, text="⏳ GAN 3 SỐ (lâu không về)",
                 font=("Segoe UI",9,"bold"), fg=C["cold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(12,2))
        self.lo3_gan = _scrolled_tree(right,
            ("num","last","days"),("3 Số","Lần cuối","Kỳ vắng"),(70,90,70), height=10)

    def _load_lo3(self):
        s = _parse_date(self.lo3_from.get()); e = _parse_date(self.lo3_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.lo3_prov.get()
        freq = self.db.get_3digit_frequency(ss, es, prov)
        items = list(freq.items())
        if not items: return
        mx = items[0][1] or 1

        self.lo3_tree.delete(*self.lo3_tree.get_children())
        for rank, (num, cnt) in enumerate(items[:100], 1):
            bar = "█" * int(cnt/mx*25)
            self.lo3_tree.insert("","end", values=(rank,num,cnt,bar))

        self.lo3_top.delete(*self.lo3_top.get_children())
        for num,cnt in items[:15]:
            self.lo3_top.insert("","end", values=(num,cnt))

        self.lo3_gan.delete(*self.lo3_gan.get_children())
        gan = self.db.get_3digit_gan(es, prov, top_n=15)
        for g in gan:
            self.lo3_gan.insert("","end", values=(
                g["number"], g["last_date"],
                g["days_absent"] if g["days_absent"]<9999 else "Chưa XH"))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 5: Lô 4 số
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_lo4(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  4️⃣ Lô 4 Số  ")

        bar, w = _filter_bar(f)
        self.lo4_from = w["from"]; self.lo4_to = w["to"]
        self.lo4_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_lo4, bg=C["orange"]).pack(side="left", padx=6)
        tk.Label(bar, text="(Giải 5, Giải 6 — 4 chữ số)",
                 font=("Segoe UI",8), fg=C["muted"], bg=C["panel"]).pack(side="left", padx=4)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        content.columnconfigure(0, weight=2); content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=C["panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="TẦN SUẤT 4 SỐ (Giải 5 & 6)",
                 font=("Segoe UI",10,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.lo4_tree = _scrolled_tree(left,
            ("rank","num","count","bar"),
            ("#","4 Số","Lần","█ Biểu đồ"),
            (40,80,65,200), height=26)

        right = tk.Frame(content, bg=C["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        tk.Label(right, text="🔥 TOP 20 SỐ 4 CHỮ SỐ",
                 font=("Segoe UI",9,"bold"), fg=C["hot"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,2))
        self.lo4_top = _scrolled_tree(right,
            ("num","count"),("4 Số","Lần"),(90,70), height=22)

    def _load_lo4(self):
        s = _parse_date(self.lo4_from.get()); e = _parse_date(self.lo4_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.lo4_prov.get()
        freq = self.db.get_4digit_frequency(ss, es, prov)
        items = list(freq.items())
        if not items: return
        mx = items[0][1] or 1

        self.lo4_tree.delete(*self.lo4_tree.get_children())
        for rank, (num, cnt) in enumerate(items[:100], 1):
            bar = "█" * int(cnt/mx*24)
            self.lo4_tree.insert("","end", values=(rank,num,cnt,bar))

        self.lo4_top.delete(*self.lo4_top.get_children())
        for num,cnt in items[:20]:
            self.lo4_top.insert("","end", values=(num,cnt))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 6: Lô 5 số
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_lo5(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  5️⃣ Lô 5 Số  ")

        bar, w = _filter_bar(f)
        self.lo5_from = w["from"]; self.lo5_to = w["to"]
        self.lo5_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_lo5, bg=C["orange"]).pack(side="left", padx=6)
        tk.Label(bar, text="(Giải 1, 2, 3, 4 — 5 chữ số)",
                 font=("Segoe UI",8), fg=C["muted"], bg=C["panel"]).pack(side="left", padx=4)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        content.columnconfigure(0, weight=2); content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=C["panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(left, text="TẦN SUẤT 5 SỐ (Giải 1–4)",
                 font=("Segoe UI",10,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.lo5_tree = _scrolled_tree(left,
            ("rank","num","count","bar"),
            ("#","5 Số","Lần","█ Biểu đồ"),
            (40,85,65,200), height=26)

        right = tk.Frame(content, bg=C["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        tk.Label(right, text="🔥 TOP 20 SỐ 5 CHỮ SỐ",
                 font=("Segoe UI",9,"bold"), fg=C["hot"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,2))
        self.lo5_top = _scrolled_tree(right,
            ("num","count"),("5 Số","Lần"),(100,70), height=22)

    def _load_lo5(self):
        s = _parse_date(self.lo5_from.get()); e = _parse_date(self.lo5_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.lo5_prov.get()
        freq = self.db.get_5digit_frequency(ss, es, prov)
        items = list(freq.items())
        if not items: return
        mx = items[0][1] or 1

        self.lo5_tree.delete(*self.lo5_tree.get_children())
        for rank, (num, cnt) in enumerate(items[:100], 1):
            bar = "█" * int(cnt/mx*24)
            self.lo5_tree.insert("","end", values=(rank,num,cnt,bar))

        self.lo5_top.delete(*self.lo5_top.get_children())
        for num,cnt in items[:20]:
            self.lo5_top.insert("","end", values=(num,cnt))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 7: Giải Đặc Biệt
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_special(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  🏆 Giải ĐB  ")

        bar, w = _filter_bar(f)
        self.sp_from = w["from"]; self.sp_to = w["to"]
        self.sp_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_special, bg=C["orange"]).pack(side="left", padx=6)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        content.columnconfigure(0,weight=1); content.columnconfigure(1,weight=1)
        content.columnconfigure(2,weight=2)
        content.rowconfigure(0,weight=1)

        # 2 số cuối ĐB
        c0 = tk.Frame(content, bg=C["panel"])
        c0.grid(row=0,column=0,sticky="nsew",padx=(0,3))
        tk.Label(c0, text="2 SỐ CUỐI GIẢI ĐB",
                 font=("Segoe UI",9,"bold"), fg=C["gold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sp_last2 = _scrolled_tree(c0,
            ("num","count"),("2 Cuối","Lần"),(80,70), height=24)

        # 3 số cuối ĐB
        c1 = tk.Frame(content, bg=C["panel"])
        c1.grid(row=0,column=1,sticky="nsew",padx=(3,3))
        tk.Label(c1, text="3 SỐ CUỐI GIẢI ĐB",
                 font=("Segoe UI",9,"bold"), fg=C["gold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sp_last3 = _scrolled_tree(c1,
            ("num","count"),("3 Cuối","Lần"),(80,70), height=24)

        # Lịch sử ĐB
        c2 = tk.Frame(content, bg=C["panel"])
        c2.grid(row=0,column=2,sticky="nsew",padx=(3,0))
        tk.Label(c2, text="LỊCH SỬ GIẢI ĐẶC BIỆT",
                 font=("Segoe UI",9,"bold"), fg=C["gold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sp_history = _scrolled_tree(c2,
            ("date","prov","num","l2","l3"),
            ("Ngày","Tỉnh","Giải ĐB","2 Cuối","3 Cuối"),
            (90,110,90,70,70), height=24)

    def _load_special(self):
        s = _parse_date(self.sp_from.get()); e = _parse_date(self.sp_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.sp_prov.get()
        data = self.db.get_special_prize_stats(ss, es, prov)

        self.sp_last2.delete(*self.sp_last2.get_children())
        for num,cnt in list(data["last2"].items())[:50]:
            self.sp_last2.insert("","end", values=(num,cnt))

        self.sp_last3.delete(*self.sp_last3.get_children())
        for num,cnt in list(data["last3"].items())[:50]:
            self.sp_last3.insert("","end", values=(num,cnt))

        self.sp_history.delete(*self.sp_history.get_children())
        for item in data["all"][:200]:
            sp = item["number"]
            self.sp_history.insert("","end", values=(
                item["date"], item["province"], sp,
                sp[-2:] if len(sp)>=2 else "",
                sp[-3:] if len(sp)>=3 else ""))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 8: Gợi ý số
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_suggest(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  💡 Gợi Ý Số  ")

        bar = tk.Frame(f, bg=C["panel"])
        bar.pack(fill="x", padx=10, pady=(8,2))
        _lbl(bar, "Tính đến ngày:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        self.sug_date = _date_entry(bar, date.today())
        self.sug_date.pack(side="left")
        _lbl(bar, "Tỉnh:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        self.sug_prov = tk.StringVar(value="Tất cả")
        _combo(bar, self.sug_prov, ["Tất cả"]+list(PROVINCES.keys()), width=18
               ).pack(side="left", padx=2)
        _btn(bar, "💡 Gợi Ý", self._load_suggest, bg=C["purple"]).pack(side="left", padx=8)

        info = tk.Label(f, text=(
            "🔥 Hot: xuất hiện nhiều nhất 30 ngày qua  │  "
            "❄️ Lạnh (Gan): lâu không về, có thể sắp xuất hiện  │  "
            "⚡ Cầu: xuất hiện ≥3 kỳ trong 7 ngày  │  "
            "🏆 Theo ĐB: 2 số cuối giải Đặc Biệt gần nhất"),
            font=("Segoe UI",8), fg=C["muted"], bg=C["bg"])
        info.pack(anchor="w", padx=12, pady=(2,0))

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(4,8))
        for i in range(4): content.columnconfigure(i, weight=1)
        content.rowconfigure(0, weight=1)

        # Hot
        c0 = tk.Frame(content, bg=C["panel"])
        c0.grid(row=0,column=0,sticky="nsew",padx=(0,3))
        tk.Label(c0, text="🔥 SỐ NÓNG (30 ngày)",
                 font=("Segoe UI",9,"bold"), fg=C["hot"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sug_hot = _scrolled_tree(c0,
            ("num","count","reason"),("Số","Lần","Ghi chú"),(60,55,140), height=22)

        # Cold/Gan
        c1 = tk.Frame(content, bg=C["panel"])
        c1.grid(row=0,column=1,sticky="nsew",padx=(3,3))
        tk.Label(c1, text="❄️ SỐ LẠNH / GAN",
                 font=("Segoe UI",9,"bold"), fg=C["cold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sug_cold = _scrolled_tree(c1,
            ("num","days","reason"),("Số","Kỳ vắng","Ghi chú"),(55,65,110), height=22)

        # Cầu
        c2 = tk.Frame(content, bg=C["panel"])
        c2.grid(row=0,column=2,sticky="nsew",padx=(3,3))
        tk.Label(c2, text="⚡ SỐ CẦU (7 ngày)",
                 font=("Segoe UI",9,"bold"), fg=C["yellow"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sug_cau = _scrolled_tree(c2,
            ("num","count","reason"),("Số","Kỳ","Ghi chú"),(55,55,130), height=22)

        # Theo ĐB
        c3 = tk.Frame(content, bg=C["panel"])
        c3.grid(row=0,column=3,sticky="nsew",padx=(3,0))
        tk.Label(c3, text="🏆 THEO GIẢI ĐB",
                 font=("Segoe UI",9,"bold"), fg=C["gold"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.sug_db = _scrolled_tree(c3,
            ("num","from_db","date"),("2 Cuối","Từ ĐB","Ngày"),(60,75,90), height=22)

    def _load_suggest(self):
        d = _parse_date(self.sug_date.get())
        if not d: return
        prov = self.sug_prov.get()
        data = self.db.get_suggestions(d.strftime("%Y-%m-%d"), prov)

        self.sug_hot.delete(*self.sug_hot.get_children())
        for item in data.get("hot",[]):
            self.sug_hot.insert("","end",values=(item["number"],item["count"],item["reason"]))

        self.sug_cold.delete(*self.sug_cold.get_children())
        for item in data.get("cold",[]):
            d_abs = item["days_absent"] if item["days_absent"]<9999 else "Chưa XH"
            self.sug_cold.insert("","end",values=(item["number"],d_abs,item["reason"]))

        self.sug_cau.delete(*self.sug_cau.get_children())
        for item in data.get("cau",[]):
            self.sug_cau.insert("","end",values=(item["number"],item["count"],item["reason"]))

        self.sug_db.delete(*self.sug_db.get_children())
        for item in data.get("theo_db",[]):
            self.sug_db.insert("","end",values=(item["number"],item["from_special"],item["date"]))

    # ══════════════════════════════════════════════════════════════════════
    # Tab 9: Chu kỳ số
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_cycle(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  🔄 Chu Kỳ  ")

        bar = tk.Frame(f, bg=C["panel"])
        bar.pack(fill="x", padx=10, pady=(8,2))
        _lbl(bar, "Nhập số (2 chữ số):", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        self.cyc_num = tk.Entry(bar, font=("Segoe UI",11,"bold"),
                                fg=C["gold"], bg=C["card"],
                                insertbackground=C["accent"],
                                relief="flat", width=6, justify="center")
        self.cyc_num.insert(0, "00")
        self.cyc_num.pack(side="left", padx=4)
        _lbl(bar, "Tỉnh:", bg=C["panel"], fg=C["muted"]).pack(side="left", padx=(8,2))
        self.cyc_prov = tk.StringVar(value="Tất cả")
        _combo(bar, self.cyc_prov, ["Tất cả"]+list(PROVINCES.keys()), width=18
               ).pack(side="left", padx=2)
        _btn(bar, "🔄 Phân Tích Chu Kỳ", self._load_cycle, bg=C["teal"]).pack(side="left", padx=8)

        # Summary cards
        self.cyc_summary = tk.Frame(f, bg=C["bg"])
        self.cyc_summary.pack(fill="x", padx=10, pady=(4,2))

        # History table
        bottom = tk.Frame(f, bg=C["bg"])
        bottom.pack(fill="both", expand=True, padx=10, pady=(2,8))
        bottom.columnconfigure(0,weight=1); bottom.columnconfigure(1,weight=1)
        bottom.rowconfigure(0,weight=1)

        left = tk.Frame(bottom, bg=C["panel"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,4))
        tk.Label(left, text="LỊCH SỬ XUẤT HIỆN",
                 font=("Segoe UI",9,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.cyc_history = _scrolled_tree(left,
            ("idx","date","gap"),
            ("#","Ngày xuất hiện","Cách kỳ trước (ngày)"),
            (40,110,150), height=22)

        right = tk.Frame(bottom, bg=C["panel"])
        right.grid(row=0,column=1,sticky="nsew",padx=(4,0))
        tk.Label(right, text="PHÂN TÍCH CHU KỲ",
                 font=("Segoe UI",9,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(8,3))
        self.cyc_info = tk.Text(right, font=("Segoe UI",10),
                                fg=C["text"], bg=C["card"],
                                relief="flat", wrap="word", state="disabled")
        self.cyc_info.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_cycle(self):
        num = self.cyc_num.get().strip().zfill(2)
        if not num.isdigit() or len(num) != 2:
            messagebox.showerror("Lỗi", "Nhập đúng 2 chữ số (VD: 07, 36, 99)")
            return
        prov = self.cyc_prov.get()
        data = self.db.get_cycle_stats(num, prov)

        # Clear summary
        for w in self.cyc_summary.winfo_children():
            w.destroy()

        # Hiện summary cards
        cards = [
            ("Tổng lần XH", str(data.get("total",0)), C["green"]),
            ("Chu kỳ TB",   f"{data.get('avg_cycle',0)} ngày", C["accent"]),
            ("Ngắn nhất",   f"{data.get('min_cycle',0)} ngày", C["yellow"]),
            ("Dài nhất",    f"{data.get('max_cycle',0)} ngày", C["red"]),
        ]
        for title, val, color in cards:
            card = tk.Frame(self.cyc_summary, bg=C["card"], padx=16, pady=8)
            card.pack(side="left", padx=6, pady=4)
            tk.Label(card, text=val, font=("Segoe UI",18,"bold"),
                     fg=color, bg=C["card"]).pack()
            tk.Label(card, text=title, font=("Segoe UI",8),
                     fg=C["muted"], bg=C["card"]).pack()

        # History
        dates  = data.get("dates", [])
        cycles = data.get("cycles", [])
        self.cyc_history.delete(*self.cyc_history.get_children())
        for i, d in enumerate(dates):
            gap = cycles[i-1] if i > 0 else "—"
            self.cyc_history.insert("","end", values=(i+1, d, gap))

        # Info text
        self.cyc_info.configure(state="normal")
        self.cyc_info.delete("1.0","end")
        if data["total"] == 0:
            self.cyc_info.insert("end", f"Số {num} chưa xuất hiện trong DB.\n")
        else:
            lines = [
                f"Số:           {num}",
                f"Tỉnh:         {prov}",
                f"Tổng lần XH:  {data['total']}",
                f"",
                f"Chu kỳ trung bình:  {data['avg_cycle']} ngày",
                f"Chu kỳ ngắn nhất:   {data['min_cycle']} ngày",
                f"Chu kỳ dài nhất:    {data['max_cycle']} ngày",
                f"",
                f"Lần đầu: {dates[0] if dates else '—'}",
                f"Lần cuối: {dates[-1] if dates else '—'}",
                f"",
                f"Nhận xét:",
            ]
            avg = data["avg_cycle"]
            if avg <= 7:
                lines.append("→ Số NÓNG, xuất hiện rất thường xuyên")
            elif avg <= 15:
                lines.append("→ Số BÌNH THƯỜNG, chu kỳ ổn định")
            elif avg <= 30:
                lines.append("→ Số ÍT GẶP, chu kỳ khá dài")
            else:
                lines.append("→ Số HIẾM, chu kỳ rất dài")

            if cycles:
                last_gap = cycles[-1]
                if last_gap > avg * 1.5:
                    lines.append(f"→ Kỳ vắng hiện tại ({last_gap} ngày) > TB → CÓ THỂ SẮP VỀ")
            self.cyc_info.insert("end", "\n".join(lines))
        self.cyc_info.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════
    # Tab 10: Đầu Đuôi
    # ══════════════════════════════════════════════════════════════════════

    def _build_tab_headtail(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  📐 Đầu Đuôi  ")

        bar, w = _filter_bar(f)
        self.ht_from = w["from"]; self.ht_to = w["to"]
        self.ht_prov = w["province_var"]
        _btn(bar, "📊 Phân Tích", self._load_headtail, bg=C["orange"]).pack(side="left", padx=6)

        content = tk.Frame(f, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(2,8))
        for i in range(3): content.columnconfigure(i, weight=1)
        content.rowconfigure(0, weight=1)

        # Đầu số
        c0 = tk.Frame(content, bg=C["panel"])
        c0.grid(row=0,column=0,sticky="nsew",padx=(0,4))
        tk.Label(c0, text="ĐẦU SỐ (chữ số đầu của lô)",
                 font=("Segoe UI",9,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.ht_head = _scrolled_tree(c0,
            ("digit","count","bar"),("Đầu","Lần","█"),(60,70,180), height=12)

        # Đuôi số
        c1 = tk.Frame(content, bg=C["panel"])
        c1.grid(row=0,column=1,sticky="nsew",padx=(4,4))
        tk.Label(c1, text="ĐUÔI SỐ (chữ số cuối của lô)",
                 font=("Segoe UI",9,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        self.ht_tail = _scrolled_tree(c1,
            ("digit","count","bar"),("Đuôi","Lần","█"),(60,70,180), height=12)

        # Ma trận đầu-đuôi
        c2 = tk.Frame(content, bg=C["panel"])
        c2.grid(row=0,column=2,sticky="nsew",padx=(4,0))
        tk.Label(c2, text="MA TRẬN ĐẦU × ĐUÔI (lần XH)",
                 font=("Segoe UI",9,"bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(anchor="w", padx=10, pady=(10,3))
        # Matrix dùng Text widget
        self.ht_matrix = tk.Text(c2, font=("Consolas",9),
                                 fg=C["text"], bg=C["card"],
                                 relief="flat", state="disabled")
        self.ht_matrix.pack(fill="both", expand=True, padx=8, pady=8)

    def _load_headtail(self):
        s = _parse_date(self.ht_from.get()); e = _parse_date(self.ht_to.get())
        if not s or not e: return
        ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        prov = self.ht_prov.get()

        ht = self.db.get_head_tail_stats(ss, es, prov)
        head = ht["head"]; tail = ht["tail"]
        mx_h = max(head.values()) or 1
        mx_t = max(tail.values()) or 1

        self.ht_head.delete(*self.ht_head.get_children())
        for i in range(10):
            cnt = head[str(i)]
            bar = "█" * int(cnt/mx_h*20)
            self.ht_head.insert("","end", values=(f"Đầu {i}", cnt, bar))

        self.ht_tail.delete(*self.ht_tail.get_children())
        for i in range(10):
            cnt = tail[str(i)]
            bar = "█" * int(cnt/mx_t*20)
            self.ht_tail.insert("","end", values=(f"Đuôi {i}", cnt, bar))

        # Ma trận: cần lấy tần suất từng cặp (đầu, đuôi)
        results = self.db.get_results(ss, es, prov)
        matrix = {(h,t): 0 for h in range(10) for t in range(10)}
        for r in results:
            for tok in r.get("all_numbers","").split(","):
                tok = tok.strip()
                if len(tok) >= 2:
                    lo = tok[-2:]
                    if lo.isdigit():
                        matrix[(int(lo[0]), int(lo[1]))] += 1

        self.ht_matrix.configure(state="normal")
        self.ht_matrix.delete("1.0","end")
        # Header
        line = "    " + "  ".join(f"[{t}]" for t in range(10))
        self.ht_matrix.insert("end", line + "\n")
        self.ht_matrix.insert("end", "    " + "─"*43 + "\n")
        for h in range(10):
            vals = [matrix[(h,t)] for t in range(10)]
            row_str = f" {h} │" + " ".join(f"{v:4d}" for v in vals)
            self.ht_matrix.insert("end", row_str + "\n")
        self.ht_matrix.insert("end", "\n(Hàng = Đầu số, Cột = Đuôi số)\n")
        self.ht_matrix.configure(state="disabled")

    # ── Export Excel ──────────────────────────────────────────────────────

    def _export_excel(self):
        s = _parse_date(self.res_from.get()); e = _parse_date(self.res_to.get())
        if not s or not e:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")],
            initialfile=f"XoSo_{s}_{e}.xlsx")
        if not path: return
        try:
            ss, es = s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
            prov = self.res_prov.get()
            export_results(
                results=self.db.get_results(ss,es,prov),
                freq_data=self.db.get_number_frequency(ss,es,prov),
                gan_data=self.db.get_gan_numbers(es,prov,50),
                head_tail=self.db.get_head_tail_stats(ss,es,prov),
                output_path=path, start_date=ss, end_date=es, province=prov)
            messagebox.showinfo("✅ Xong", f"Đã xuất:\n{path}")
        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex))


def run():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    run()
