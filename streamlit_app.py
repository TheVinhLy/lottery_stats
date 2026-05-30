"""
streamlit_app.py — Web version của Phần Mềm Thống Kê Xổ Số Miền Nam
Chạy local:  streamlit run streamlit_app.py
Deploy:      Streamlit Cloud (https://share.streamlit.io)
"""

import sys
import os
import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, datetime, timedelta

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database.db import Database
from database.models import PROVINCES
from reports.export_excel import export_results

# ══════════════════════════════════════════════════════════════════════════
# Cấu hình trang
# ══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Thống Kê Xổ Số Miền Nam",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Bảng màu tông Slate-Indigo (dịu mắt) ────────────────────────────────
# BG_PAGE   #1B1F2E   nền trang xanh đậm
# BG_PANEL  #232840   panel / sidebar
# BG_CARD   #2C3252   card / input
# ACCENT    #818CF8   indigo-400 (dịu hơn cyan)
# TEXT      #CBD5E1   xám xanh nhạt (không chói)
# MUTED     #64748B   chữ phụ
# BORDER    #374151   viền
# SUCCESS   #4ADE80→ #34D399  teal-green nhạt
# WARNING   #FB923C  cam nhạt
# GOLD      #FBBF24  vàng ấm

st.markdown("""
<style>
    /* ── Ẩn toolbar mặc định của Streamlit (che mất header app) ── */
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; visibility: hidden !important; }
    /* Ẩn nút Deploy và Share trên toolbar */
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    button[title="Deploy this app"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    /* Ẩn toàn bộ top-right action bar */
    .stAppToolbar { display: none !important; }
    [data-testid="stAppViewContainer"] > section:first-child > div[class*="toolbar"] { display: none !important; }
    div[class*="StatusWidget"] { display: none !important; }
    div[class*="viewerBadge"] { display: none !important; }
    /* Ẩn badge "Hosted with Streamlit" + "Created by" ở bottom */
    [data-testid="stBottom"] { display: none !important; }
    [data-testid="stBottomBlockContainer"] { display: none !important; }
    .st-emotion-cache-zq5wmm { display: none !important; }
    .viewerBadge_container__r5tak { display: none !important; }
    #stDecoration { display: none !important; }

    /* ── Nền & typography ── */
    .stApp { background-color: #1B1F2E; }
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    .main, .main > div, section[data-testid="stSidebar"] {
        background-color: #1B1F2E !important;
    }
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 0.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100% !important;
    }
    body, p, span, div, label {
        color: #CBD5E1 !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 1.05rem !important;
    }

    /* ── Header / title ── */
    h1, h2, h3, h4 { color: #E2E8F0 !important; font-weight: 700; }
    h2 { font-size: 1.4rem !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background-color: #232840;
        border-radius: 10px 10px 0 0;
        padding: 4px 6px 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px 8px 0 0;
        padding: 7px 18px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #94A3B8 !important;
        border: none;
        transition: background 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2C3252 !important;
        color: #C7D2FE !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3730A3 !important;
        color: #E0E7FF !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #1B1F2E;
        border-radius: 0 0 10px 10px;
        padding-top: 0.8rem;
    }

    /* ── Metric cards ── */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #232840 0%, #2C3252 100%);
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #818CF8 !important;
        font-size: 2.1rem !important;
        font-weight: 700;
    }
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.92rem !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #4338CA, #5B21B6) !important;
        color: #EDE9FE !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.4rem 1rem !important;
        box-shadow: 0 2px 6px rgba(67,56,202,0.4);
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4F46E5, #6D28D9) !important;
        box-shadow: 0 4px 12px rgba(79,70,229,0.5);
        transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        background: #2C3252 !important;
        color: #A5B4FC !important;
        box-shadow: none;
    }

    /* ── Inputs & Selectbox ── */
    .stTextInput input, .stDateInput input {
        background-color: #2C3252 !important;
        border: 1px solid #374151 !important;
        border-radius: 6px !important;
        color: #F1F5F9 !important;
        font-size: 1.05rem !important;
    }
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #2C3252 !important;
        border: 1px solid #374151 !important;
        border-radius: 6px !important;
        color: #F1F5F9 !important;
        font-size: 1.05rem !important;
    }
    /* Chữ hiển thị trong ô selectbox đã chọn */
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div {
        color: #F1F5F9 !important;
        font-size: 1.05rem !important;
    }
    /* ── Dropdown list khi mở ra ── */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        background-color: #2C3252 !important;
    }
    [data-baseweb="option"] {
        background-color: #2C3252 !important;
        color: #818CF8 !important;
        font-size: 1.05rem !important;
    }
    [data-baseweb="option"]:hover {
        background-color: #3D4A7A !important;
        color: #FFFFFF !important;
    }
    [aria-selected="true"][data-baseweb="option"] {
        background-color: #4338CA !important;
        color: #FFFFFF !important;
    }

    /* ── Date picker popup / calendar ── */
    [data-baseweb="calendar"] {
        background-color: #1B1F2E !important;
        border: 2px solid #4338CA !important;
        border-radius: 10px !important;
    }
    [data-baseweb="calendar"] * {
        background-color: #1B1F2E !important;
        color: #818CF8 !important;
    }
    /* Header tháng/năm */
    [data-baseweb="calendar"] [data-baseweb="select"] > div,
    [data-baseweb="calendar"] button {
        background-color: #2C3252 !important;
        color: #F1F5F9 !important;
        font-size: 1.0rem !important;
    }
    /* Ngày bình thường */
    [data-baseweb="calendar"] [role="gridcell"] > div,
    [data-baseweb="calendar"] [role="button"] {
        background-color: transparent !important;
        color: #F1F5F9 !important;
        font-size: 1.0rem !important;
    }
    /* Hover ngày */
    [data-baseweb="calendar"] [role="button"]:hover {
        background-color: #3D4A7A !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
    }
    /* Ngày đang chọn */
    [data-baseweb="calendar"] [aria-selected="true"] > div,
    [data-baseweb="calendar"] [data-selected="true"] > div {
        background-color: #4338CA !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
    }
    /* Ngày hôm nay */
    [data-baseweb="calendar"] [data-today="true"] > div {
        border: 2px solid #818CF8 !important;
        border-radius: 50% !important;
        background-color: #2C3252 !important;
    }
    /* Tên thứ */
    [data-baseweb="calendar"] [data-baseweb="day-label"],
    [data-baseweb="calendar"] [role="columnheader"] {
        color: #818CF8 !important;
        font-weight: 700 !important;
        background-color: #1B1F2E !important;
    }
    /* Nút prev/next tháng */
    [data-baseweb="calendar"] button[aria-label*="previous"],
    [data-baseweb="calendar"] button[aria-label*="next"],
    [data-baseweb="calendar"] button[aria-label*="Previous"],
    [data-baseweb="calendar"] button[aria-label*="Next"] {
        background-color: #3730A3 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    /* Popover wrapper nền — phải đặt trước calendar để không đè */
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] [data-baseweb="block"] {
        background-color: #1B1F2E !important;
        border: 2px solid #4338CA !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.7) !important;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #374151;
    }
    .stDataFrame thead th {
        background-color: #2C3252 !important;
        color: #A5B4FC !important;
        font-weight: 600;
        font-size: 1.1rem !important;
        border-bottom: 2px solid #4338CA !important;
    }
    /* Alternating rows: chẵn đậm, lẻ nhạt hơn */
    .stDataFrame tbody tr:nth-child(odd)  td { background-color: #1B1F2E !important; font-size: 1.1rem !important; }
    .stDataFrame tbody tr:nth-child(even) td { background-color: #232840 !important; font-size: 1.1rem !important; }
    .stDataFrame tbody tr:hover td { background-color: #2C3252 !important; }

    /* ── Căn nút hàng filter ngang hàng input ── */
    /* Ẩn label giả (dùng để đẩy nút xuống đúng vị trí) */
    label.btn-spacer-label { visibility: hidden; display: block;
        font-size: 0.875rem; margin-bottom: 0.25rem; }

    /* ── Info / Success / Warning boxes ── */
    .stInfo    { background-color: #1E293B !important; border-left: 4px solid #818CF8 !important; }
    .stSuccess { background-color: #14302A !important; border-left: 4px solid #34D399 !important; }
    .stWarning { background-color: #2D1F0E !important; border-left: 4px solid #FB923C !important; }
    .stError   { background-color: #2D0F14 !important; border-left: 4px solid #F87171 !important; }

    /* ── Caption / divider ── */
    .stCaption { color: #64748B !important; font-size: 0.88rem !important; }
    hr { border-color: #374151 !important; margin-top: 0.4rem !important; margin-bottom: 0.4rem !important; }

    /* ── Căn nút Phân Tích ngang hàng với input ── */
    div[data-testid="stVerticalBlock"] .stButton-align-label label {
        visibility: hidden;
    }

    /* ── Progress bar ── */
    .stProgress > div > div { background-color: #818CF8 !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1B1F2E; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4B5563; }
</style>
""", unsafe_allow_html=True)

PROV_LIST = ["Tất cả"] + list(PROVINCES.keys())


def _sdf(df):
    """Màu xen kẽ dòng cho dataframe qua Pandas Styler."""
    def _alt(row):
        color = "#232840" if row.name % 2 == 0 else "#1B2035"
        return [f"background-color: {color}; color: #CBD5E1"] * len(row)
    return df.style.apply(_alt, axis=1)

# ══════════════════════════════════════════════════════════════════════════
# Khởi tạo Database (cache_resource: chỉ tạo 1 lần)
# ══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_db() -> Database:
    return Database()

db = get_db()

# ══════════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════════

col_h1, col_h2, col_h3 = st.columns([4, 3, 2])
with col_h1:
    st.markdown("## 🎯 Phần Mềm Thống Kê Xổ Số Miền Nam")
with col_h2:
    count = db.get_record_count()
    mn, mx = db.get_date_range()
    if mn:
        st.info(f"📊 **{count:,} bản ghi** &nbsp;|&nbsp; {mn} → {mx}", icon=None)
    else:
        st.info(f"📊 **{count:,} bản ghi** — Chưa có dữ liệu")
with col_h3:
    if st.button("🔄 Làm mới thống kê", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.markdown('<div style="margin-top:0.3rem"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# 10 Tabs
# ══════════════════════════════════════════════════════════════════════════

tabs = st.tabs([
    "📥 Cập Nhật", "📋 Kết Quả", "🎯 Lô 2 Số", "🎲 Lô 3 Số",
    "4️⃣ Lô 4 Số", "5️⃣ Lô 5 Số", "🏆 Giải ĐB",
    "💡 Gợi Ý Số", "🔄 Chu Kỳ", "📐 Đầu Đuôi",
])
(tab_update, tab_results, tab_lo2, tab_lo3, tab_lo4,
 tab_lo5, tab_special, tab_suggest, tab_cycle, tab_headtail) = tabs


# ══════════════════════════════════════════════════════════════════════════
# Tab 1 — Cập Nhật
# ══════════════════════════════════════════════════════════════════════════

with tab_update:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("⚙️ Cấu hình")
        upd_from = st.date_input("Từ ngày", value=date.today(), key="upd_from")
        upd_to   = st.date_input("Đến ngày", value=date.today(), key="upd_to")
        upd_prov = st.selectbox("Tỉnh/Thành", PROV_LIST, key="upd_prov")

        st.markdown("")
        btn_start = st.button("▶ CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True)

        if st.session_state.get("crawl_done"):
            s, sk = st.session_state["crawl_done"]
            st.success(f"✅ Đã lưu **{s}** bản ghi | Bỏ qua trùng: **{sk}**")

    with col_r:
        st.subheader("📋 Nhật ký")
        log_box = st.container(border=True)

        if btn_start:
            from crawler.fetch import fetch_api_by_date, generate_date_range
            from crawler.parser import parse_api_response

            all_dates = list(generate_date_range(upd_from, upd_to))
            total  = len(all_dates)
            saved  = skipped = 0
            filter_prov = None if upd_prov == "Tất cả" else upd_prov

            progress = st.progress(0.0, text="Đang chuẩn bị...")
            logs: list[str] = []

            def write_log(msg: str, level: str = ""):
                ts = datetime.now().strftime("%H:%M:%S")
                icon = {"ok": "✅", "err": "❌", "warn": "⚠️"}.get(level, "ℹ️")
                logs.append(f"`{ts}` {icon} {msg}")
                log_box.markdown("\n\n".join(logs[-30:]))  # giữ 30 dòng cuối

            write_log(f"Bắt đầu: {upd_from} → {upd_to} | Tỉnh: {upd_prov}")

            for idx, cur_date in enumerate(all_dates, 1):
                pct  = idx / total
                dstr = cur_date.strftime("%Y-%m-%d")
                progress.progress(pct, text=f"[{idx}/{total}] {dstr}")

                api_data = fetch_api_by_date(cur_date)
                if api_data:
                    records = parse_api_response(api_data, cur_date)
                    day_saved = 0
                    for rec in records:
                        if filter_prov and rec.get("province") != filter_prov:
                            continue
                        if db.save_result(rec):
                            saved += 1
                            day_saved += 1
                        else:
                            skipped += 1
                    write_log(f"[{idx}/{total}] {dstr} → lưu {day_saved} tỉnh", "ok")
                else:
                    write_log(f"[{idx}/{total}] Không có dữ liệu: {dstr}", "warn")

            progress.progress(1.0, text="Hoàn thành!")
            write_log(f"Xong! Đã lưu {saved} | Bỏ qua {skipped}", "ok")
            st.session_state["crawl_done"] = (saved, skipped)
            st.cache_resource.clear()
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# Tab 2 — Kết Quả
# ══════════════════════════════════════════════════════════════════════════

with tab_results:
    r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2, 2, 3, 1, 1])
    with r_c1: res_from = st.date_input("Từ", date.today(), key="res_from")
    with r_c2: res_to   = st.date_input("Đến", date.today(), key="res_to")
    with r_c3: res_prov = st.selectbox("Tỉnh", PROV_LIST, key="res_prov")
    with r_c4:
        st.markdown('<div style="padding-top:1.6rem"></div>', unsafe_allow_html=True)
        res_btn = st.button("🔍 Xem", key="res_btn", type="primary", use_container_width=True)
    with r_c5:
        st.markdown('<div style="padding-top:1.6rem"></div>', unsafe_allow_html=True)
        exp_btn = st.button("📊 Excel", key="res_exp", use_container_width=True)

    if res_btn or "res_data" not in st.session_state:
        rows = db.get_results(
            res_from.strftime("%Y-%m-%d"), res_to.strftime("%Y-%m-%d"), res_prov)
        st.session_state["res_data"] = rows

    rows = st.session_state.get("res_data", [])
    st.caption(f"**{len(rows):,} bản ghi**")

    if rows:
        df_res = pd.DataFrame(rows)[[
            "draw_date","province","special_prize","prize_1","prize_2",
            "prize_3","prize_4","prize_5","prize_6","prize_7","prize_8"]]
        df_res.columns = ["Ngày","Tỉnh","Đặc Biệt","Giải 1","Giải 2",
                          "Giải 3","Giải 4","Giải 5","Giải 6","Giải 7","Giải 8"]
        st.dataframe(_sdf(df_res), use_container_width=True, height=520)

        if exp_btn:
            buf = io.BytesIO()
            ss = res_from.strftime("%Y-%m-%d"); es = res_to.strftime("%Y-%m-%d")
            export_results(
                results=rows,
                freq_data=db.get_number_frequency(ss, es, res_prov),
                gan_data=db.get_gan_numbers(es, res_prov, 50),
                head_tail=db.get_head_tail_stats(ss, es, res_prov),
                output_path=buf, start_date=ss, end_date=es, province=res_prov)
            buf.seek(0)
            st.download_button(
                "⬇️ Tải file Excel",
                data=buf,
                file_name=f"XoSo_{ss}_{es}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Không có dữ liệu. Hãy chọn khoảng ngày rồi nhấn Xem.")


# ══════════════════════════════════════════════════════════════════════════
# Helpers dùng chung
# ══════════════════════════════════════════════════════════════════════════

def _filter_row(prefix: str, default_days: int = 90):
    """Thanh filter ngày + tỉnh dùng chung cho các tab thống kê."""
    c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
    with c1: d_from = st.date_input("Từ", date(2026, 1, 1), key=f"{prefix}_from")
    with c2: d_to   = st.date_input("Đến", date.today(), key=f"{prefix}_to")
    with c3: prov   = st.selectbox("Tỉnh", PROV_LIST, key=f"{prefix}_prov")
    with c4:
        st.markdown('<div style="padding-top:1.6rem"></div>', unsafe_allow_html=True)
        btn = st.button("📊 Phân Tích", key=f"{prefix}_btn", type="primary", use_container_width=True)
    return d_from, d_to, prov, btn


# Bảng màu Plotly dùng chung (tông Indigo-Teal, dịu mắt)
_PLOTLY_BG   = "#1B1F2E"
_PLOTLY_GRID = "#2C3252"
_PLOTLY_TEXT = "#94A3B8"

def _chart_layout(**extra):
    base = dict(
        plot_bgcolor=_PLOTLY_BG,
        paper_bgcolor=_PLOTLY_BG,
        font=dict(color=_PLOTLY_TEXT, family="Inter, Segoe UI, sans-serif", size=12),
        title_font=dict(color="#CBD5E1", size=13),
        xaxis=dict(gridcolor=_PLOTLY_GRID, linecolor=_PLOTLY_GRID,
                   tickfont=dict(color=_PLOTLY_TEXT)),
        yaxis=dict(gridcolor=_PLOTLY_GRID, linecolor=_PLOTLY_GRID,
                   tickfont=dict(color=_PLOTLY_TEXT)),
        margin=dict(t=44, b=12, l=12, r=12),
        coloraxis_showscale=False,
    )
    base.update(extra)
    return base


def _bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color_scale="Blues"):
    fig = px.bar(df, x=x, y=y, title=title,
                 color=y, color_continuous_scale=color_scale,
                 template="plotly_dark")
    fig.update_layout(**_chart_layout())
    return fig


# ══════════════════════════════════════════════════════════════════════════
# Tab 3 — Lô 2 Số
# ══════════════════════════════════════════════════════════════════════════

with tab_lo2:
    lo2_from, lo2_to, lo2_prov, lo2_btn = _filter_row("lo2")

    if lo2_btn:
        with st.spinner("Đang tính tần suất..."):
            freq = db.get_number_frequency(
                lo2_from.strftime("%Y-%m-%d"), lo2_to.strftime("%Y-%m-%d"), lo2_prov)
        st.session_state["lo2_freq"] = freq

    freq = st.session_state.get("lo2_freq")
    if freq is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê lô 2 số.")
    else:
        items = list(freq.items())
        total_cnt = sum(v for _, v in items)
        df_lo2 = pd.DataFrame(items, columns=["Số", "Lần XH"])
        df_lo2["Tỷ lệ %"] = (df_lo2["Lần XH"] / total_cnt * 100).round(2)
        df_lo2["Rank"] = range(1, len(df_lo2) + 1)

        col_chart, col_right = st.columns([3, 1])
        with col_chart:
            # Biểu đồ sắp xếp theo số 00-99
            df_plot = df_lo2.sort_values("Số")
            # Thêm các số 0 lần nếu thiếu
            all_nums = {f"{i:02d}" for i in range(100)}
            missing  = all_nums - set(df_plot["Số"])
            if missing:
                miss_df  = pd.DataFrame({"Số": sorted(missing), "Lần XH": 0, "Tỷ lệ %": 0.0, "Rank": 0})
                df_plot  = pd.concat([df_plot, miss_df]).sort_values("Số").reset_index(drop=True)

            fig = _bar_chart(df_plot, "Số", "Lần XH", "Tần suất lô 2 số (00–99)")
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"Tổng {total_cnt:,} lượt xuất hiện | {len(items)} số khác nhau")
            st.dataframe(_sdf(df_lo2[["Rank","Số","Lần XH","Tỷ lệ %"]].reset_index(drop=True)),
                         use_container_width=True, height=300)

        with col_right:
            st.markdown("### 🔥 Top 10 Nóng nhất")
            hot_df = df_lo2.head(10)[["Số","Lần XH"]]
            st.dataframe(_sdf(hot_df), use_container_width=True, hide_index=True)

            st.markdown("### ❄️ Top 10 Lạnh nhất")
            # Đưa các số chưa xuất hiện lên đầu
            seen_set = set(df_lo2["Số"])
            zero_nums = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in seen_set]
            cold_rows = [{"Số": n, "Lần XH": 0} for n in zero_nums[:10]]
            cold_df   = pd.DataFrame(df_lo2.tail(10)[["Số","Lần XH"]].values.tolist(),
                                     columns=["Số","Lần XH"])
            if cold_rows:
                cold_df = pd.DataFrame(cold_rows)
            st.dataframe(_sdf(cold_df), use_container_width=True, hide_index=True)

            # Lô Gan
            st.markdown("### ⏳ Lô Gan (lâu không về)")
            gan = db.get_gan_numbers(lo2_to.strftime("%Y-%m-%d"), lo2_prov, top_n=20)
            gan_df = pd.DataFrame(gan)[["number","last_date","days_absent"]]
            gan_df.columns = ["Số","Lần cuối","Kỳ vắng"]
            gan_df["Kỳ vắng"] = gan_df["Kỳ vắng"].apply(lambda x: "Chưa XH" if x >= 9999 else x)
            st.dataframe(_sdf(gan_df), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 4 — Lô 3 Số
# ══════════════════════════════════════════════════════════════════════════

with tab_lo3:
    lo3_from, lo3_to, lo3_prov, lo3_btn = _filter_row("lo3")

    if lo3_btn:
        with st.spinner("Đang tính tần suất 3 số..."):
            freq3 = db.get_3digit_frequency(
                lo3_from.strftime("%Y-%m-%d"), lo3_to.strftime("%Y-%m-%d"), lo3_prov)
            gan3  = db.get_3digit_gan(lo3_to.strftime("%Y-%m-%d"), lo3_prov, top_n=30)
        st.session_state["lo3_freq"] = freq3
        st.session_state["lo3_gan"]  = gan3

    freq3 = st.session_state.get("lo3_freq")
    if freq3 is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê lô 3 số.")
    else:
        items3 = list(freq3.items())
        df_lo3 = pd.DataFrame(items3, columns=["3 Số","Lần XH"])

        col_l3, col_r3 = st.columns([3, 1])
        with col_l3:
            df_top100 = df_lo3.head(100)
            fig3 = _bar_chart(df_top100, "3 Số", "Lần XH", "Top 100 tần suất 3 số cuối")
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(_sdf(df_lo3.head(100)), use_container_width=True, height=280, hide_index=True)

        with col_r3:
            st.markdown("### 🔥 Top 15 hay gặp")
            st.dataframe(_sdf(df_lo3.head(15)), use_container_width=True, hide_index=True)

            st.markdown("### ⏳ Lô Gan 3 số")
            gan3 = st.session_state.get("lo3_gan", [])
            if gan3:
                df_g3 = pd.DataFrame(gan3)[["number","last_date","days_absent"]]
                df_g3.columns = ["3 Số","Lần cuối","Kỳ vắng"]
                df_g3["Kỳ vắng"] = df_g3["Kỳ vắng"].apply(lambda x: "Chưa XH" if x >= 9999 else x)
                st.dataframe(_sdf(df_g3), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 5 — Lô 4 Số
# ══════════════════════════════════════════════════════════════════════════

with tab_lo4:
    lo4_from, lo4_to, lo4_prov, lo4_btn = _filter_row("lo4")
    st.caption("*(Tập trung Giải 5 & Giải 6 — 4 chữ số)*")

    if lo4_btn:
        with st.spinner("Đang tính tần suất 4 số..."):
            freq4 = db.get_4digit_frequency(
                lo4_from.strftime("%Y-%m-%d"), lo4_to.strftime("%Y-%m-%d"), lo4_prov)
        st.session_state["lo4_freq"] = freq4

    freq4 = st.session_state.get("lo4_freq")
    if freq4 is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê lô 4 số.")
    else:
        items4 = list(freq4.items())
        df_lo4 = pd.DataFrame(items4, columns=["4 Số","Lần XH"])

        col_l4, col_r4 = st.columns([3, 1])
        with col_l4:
            fig4 = _bar_chart(df_lo4.head(60), "4 Số", "Lần XH", "Top 60 tần suất 4 số")
            st.plotly_chart(fig4, use_container_width=True)
            st.dataframe(_sdf(df_lo4.head(100)), use_container_width=True, height=280, hide_index=True)
        with col_r4:
            st.markdown("### 🔥 Top 20 hay gặp")
            st.dataframe(_sdf(df_lo4.head(20)), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 6 — Lô 5 Số
# ══════════════════════════════════════════════════════════════════════════

with tab_lo5:
    lo5_from, lo5_to, lo5_prov, lo5_btn = _filter_row("lo5")
    st.caption("*(Tập trung Giải 1, 2, 3, 4 — 5 chữ số)*")

    if lo5_btn:
        with st.spinner("Đang tính tần suất 5 số..."):
            freq5 = db.get_5digit_frequency(
                lo5_from.strftime("%Y-%m-%d"), lo5_to.strftime("%Y-%m-%d"), lo5_prov)
        st.session_state["lo5_freq"] = freq5

    freq5 = st.session_state.get("lo5_freq")
    if freq5 is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê lô 5 số.")
    else:
        items5 = list(freq5.items())
        df_lo5 = pd.DataFrame(items5, columns=["5 Số","Lần XH"])

        col_l5, col_r5 = st.columns([3, 1])
        with col_l5:
            fig5 = _bar_chart(df_lo5.head(60), "5 Số", "Lần XH", "Top 60 tần suất 5 số")
            st.plotly_chart(fig5, use_container_width=True)
            st.dataframe(_sdf(df_lo5.head(100)), use_container_width=True, height=280, hide_index=True)
        with col_r5:
            st.markdown("### 🔥 Top 20 hay gặp")
            st.dataframe(_sdf(df_lo5.head(20)), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 7 — Giải Đặc Biệt
# ══════════════════════════════════════════════════════════════════════════

with tab_special:
    sp_from, sp_to, sp_prov, sp_btn = _filter_row("sp")

    if sp_btn:
        with st.spinner("Đang tải thống kê giải ĐB..."):
            sp_data = db.get_special_prize_stats(
                sp_from.strftime("%Y-%m-%d"), sp_to.strftime("%Y-%m-%d"), sp_prov)
        st.session_state["sp_data"] = sp_data

    sp_data = st.session_state.get("sp_data")
    if sp_data is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê giải Đặc Biệt.")
    else:
        col_a, col_b, col_c = st.columns([1, 1, 2])

        with col_a:
            st.markdown("### 🏅 2 Số Cuối Giải ĐB")
            df_l2 = pd.DataFrame(list(sp_data["last2"].items())[:50],
                                 columns=["2 Cuối","Lần XH"])
            fig_l2 = _bar_chart(df_l2, "2 Cuối", "Lần XH", "2 số cuối ĐB", "Purp")
            st.plotly_chart(fig_l2, use_container_width=True)
            st.dataframe(_sdf(df_l2), use_container_width=True, height=250, hide_index=True)

        with col_b:
            st.markdown("### 🏅 3 Số Cuối Giải ĐB")
            df_l3 = pd.DataFrame(list(sp_data["last3"].items())[:50],
                                 columns=["3 Cuối","Lần XH"])
            fig_l3 = _bar_chart(df_l3, "3 Cuối", "Lần XH", "3 số cuối ĐB", "Teal")
            st.plotly_chart(fig_l3, use_container_width=True)
            st.dataframe(_sdf(df_l3), use_container_width=True, height=250, hide_index=True)

        with col_c:
            st.markdown("### 📜 Lịch sử Giải Đặc Biệt")
            hist = sp_data.get("all", [])
            if hist:
                df_hist = pd.DataFrame(hist)
                df_hist["2 Cuối"] = df_hist["number"].str[-2:]
                df_hist["3 Cuối"] = df_hist["number"].str[-3:]
                df_hist = df_hist[["date","province","number","2 Cuối","3 Cuối"]]
                df_hist.columns = ["Ngày","Tỉnh","Giải ĐB","2 Cuối","3 Cuối"]
                st.dataframe(_sdf(df_hist), use_container_width=True, height=560, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 8 — Gợi Ý Số
# ══════════════════════════════════════════════════════════════════════════

with tab_suggest:
    sug_c1, sug_c2, sug_c3 = st.columns([2, 3, 1])
    with sug_c1:
        sug_date = st.date_input("Tính đến ngày", value=date.today(), key="sug_date")
    with sug_c2:
        sug_prov = st.selectbox("Tỉnh", PROV_LIST, key="sug_prov")
    with sug_c3:
        st.markdown('<div style="padding-top:1.6rem"></div>', unsafe_allow_html=True)
        sug_btn = st.button("💡 Gợi Ý", key="sug_btn", type="primary", use_container_width=True)

    st.caption(
        "🔥 **Hot**: xuất hiện nhiều 30 ngày qua &nbsp;|&nbsp; "
        "❄️ **Lạnh/Gan**: lâu không về &nbsp;|&nbsp; "
        "⚡ **Cầu**: ≥3 kỳ trong 7 ngày &nbsp;|&nbsp; "
        "🏆 **Theo ĐB**: 2 số cuối giải Đặc Biệt gần nhất"
    )

    if sug_btn:
        with st.spinner("Đang tính gợi ý..."):
            sug_data = db.get_suggestions(sug_date.strftime("%Y-%m-%d"), sug_prov)
        st.session_state["sug_data"] = sug_data

    sug_data = st.session_state.get("sug_data")
    if sug_data is None:
        st.info("👆 Nhấn **Gợi Ý** để xem đề xuất số.")
    else:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        with col_s1:
            st.markdown("### 🔥 Số Nóng")
            hot = sug_data.get("hot", [])
            if hot:
                df_hot = pd.DataFrame(hot)[["number","count","reason"]]
                df_hot.columns = ["Số","Lần/30 ngày","Ghi chú"]
                st.dataframe(_sdf(df_hot), use_container_width=True, hide_index=True)

        with col_s2:
            st.markdown("### ❄️ Số Lạnh / Gan")
            cold = sug_data.get("cold", [])
            if cold:
                df_cold = pd.DataFrame(cold)
                df_cold["days_absent"] = df_cold["days_absent"].apply(
                    lambda x: "Chưa XH" if x >= 9999 else x)
                df_cold = df_cold[["number","days_absent","reason"]]
                df_cold.columns = ["Số","Kỳ vắng","Ghi chú"]
                st.dataframe(_sdf(df_cold), use_container_width=True, hide_index=True)

        with col_s3:
            st.markdown("### ⚡ Số Cầu (7 ngày)")
            cau = sug_data.get("cau", [])
            if cau:
                df_cau = pd.DataFrame(cau)[["number","count","reason"]]
                df_cau.columns = ["Số","Kỳ liên tiếp","Ghi chú"]
                st.dataframe(_sdf(df_cau), use_container_width=True, hide_index=True)
            else:
                st.caption("Không có số cầu (chưa có số nào xuất hiện ≥3 kỳ)")

        with col_s4:
            st.markdown("### 🏆 Theo Giải ĐB")
            theo_db = sug_data.get("theo_db", [])
            if theo_db:
                df_tdb = pd.DataFrame(theo_db)[["number","from_special","date"]]
                df_tdb.columns = ["2 Cuối","Từ ĐB","Ngày"]
                st.dataframe(_sdf(df_tdb), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# Tab 9 — Chu Kỳ
# ══════════════════════════════════════════════════════════════════════════

with tab_cycle:
    cy_c1, cy_c2, cy_c3 = st.columns([1, 3, 1])
    with cy_c1:
        cyc_num = st.text_input("Nhập số (2 chữ số)", value="07", max_chars=2, key="cyc_num")
    with cy_c2:
        cyc_prov = st.selectbox("Tỉnh", PROV_LIST, key="cyc_prov")
    with cy_c3:
        st.markdown('<div style="padding-top:1.6rem"></div>', unsafe_allow_html=True)
        cyc_btn = st.button("🔄 Phân Tích", key="cyc_btn", type="primary", use_container_width=True)

    if cyc_btn:
        num_clean = cyc_num.strip().zfill(2)
        if not num_clean.isdigit() or len(num_clean) != 2:
            st.error("Nhập đúng 2 chữ số (VD: 07, 36, 99)")
        else:
            with st.spinner(f"Đang phân tích chu kỳ số {num_clean}..."):
                cyc_data = db.get_cycle_stats(num_clean, cyc_prov)
            st.session_state["cyc_data"] = cyc_data
            st.session_state["cyc_num_shown"] = num_clean

    cyc_data = st.session_state.get("cyc_data")
    if cyc_data is None:
        st.info("👆 Nhập số và nhấn **Phân Tích** để xem chu kỳ.")
    else:
        num_shown = st.session_state.get("cyc_num_shown", "??")

        # Summary cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng lần XH",     str(cyc_data.get("total", 0)))
        m2.metric("Chu kỳ TB",       f"{cyc_data.get('avg_cycle', 0)} ngày")
        m3.metric("Ngắn nhất",       f"{cyc_data.get('min_cycle', 0)} ngày")
        m4.metric("Dài nhất",        f"{cyc_data.get('max_cycle', 0)} ngày")

        col_cy1, col_cy2 = st.columns([2, 1])
        with col_cy1:
            dates  = cyc_data.get("dates", [])
            cycles = cyc_data.get("cycles", [])
            if dates:
                hist_rows = []
                for i, d in enumerate(dates):
                    gap = cycles[i-1] if i > 0 else None
                    hist_rows.append({"#": i+1, "Ngày XH": d,
                                      "Cách kỳ trước (ngày)": gap if gap is not None else "—"})
                df_cyc = pd.DataFrame(hist_rows)
                st.dataframe(_sdf(df_cyc), use_container_width=True, height=440, hide_index=True)

                # Timeline chart
                if cycles:
                    fig_cy = go.Figure()
                    fig_cy.add_trace(go.Scatter(
                        x=list(range(1, len(cycles)+1)), y=cycles,
                        mode="lines+markers",
                        line=dict(color="#818CF8", width=2),
                        marker=dict(size=6),
                        name="Khoảng cách (ngày)"))
                    avg = cyc_data.get("avg_cycle", 0)
                    fig_cy.add_hline(y=avg, line_dash="dash", line_color="#FBBF24",
                                     annotation_text=f"TB: {avg} ngày")
                    fig_cy.update_layout(
                        title=f"Chu kỳ xuất hiện số {num_shown}",
                        **_chart_layout())
                    st.plotly_chart(fig_cy, use_container_width=True)

        with col_cy2:
            st.markdown("### 📊 Nhận xét")
            if cyc_data["total"] == 0:
                st.warning(f"Số **{num_shown}** chưa xuất hiện trong DB.")
            else:
                avg = cyc_data.get("avg_cycle", 0)
                if avg <= 7:
                    verdict = "🔥 Số **NÓNG**, xuất hiện rất thường xuyên"
                elif avg <= 15:
                    verdict = "✅ Số **BÌNH THƯỜNG**, chu kỳ ổn định"
                elif avg <= 30:
                    verdict = "🌙 Số **ÍT GẶP**, chu kỳ khá dài"
                else:
                    verdict = "❄️ Số **HIẾM**, chu kỳ rất dài"
                st.markdown(verdict)

                if cycles:
                    last_gap = cycles[-1]
                    if last_gap > avg * 1.5:
                        st.success(f"⚡ Kỳ vắng hiện tại ({last_gap} ngày) > TB → **Có thể sắp về!**")
                    else:
                        st.info(f"Kỳ vắng hiện tại: {last_gap} ngày")

                if dates:
                    st.markdown(f"- Lần đầu: **{dates[0]}**")
                    st.markdown(f"- Lần cuối: **{dates[-1]}**")


# ══════════════════════════════════════════════════════════════════════════
# Tab 10 — Đầu Đuôi
# ══════════════════════════════════════════════════════════════════════════

with tab_headtail:
    ht_from, ht_to, ht_prov, ht_btn = _filter_row("ht")

    if ht_btn:
        with st.spinner("Đang tính đầu đuôi..."):
            ht_data   = db.get_head_tail_stats(
                ht_from.strftime("%Y-%m-%d"), ht_to.strftime("%Y-%m-%d"), ht_prov)
            ht_results = db.get_results(
                ht_from.strftime("%Y-%m-%d"), ht_to.strftime("%Y-%m-%d"), ht_prov)
        st.session_state["ht_data"]    = ht_data
        st.session_state["ht_results"] = ht_results

    ht_data = st.session_state.get("ht_data")
    if ht_data is None:
        st.info("👆 Nhấn **Phân Tích** để xem thống kê đầu đuôi.")
    else:
        head = ht_data["head"]
        tail = ht_data["tail"]

        col_h, col_t, col_m = st.columns([1, 1, 2])

        with col_h:
            st.markdown("### 🔢 Đầu số (chữ số đầu)")
            df_head = pd.DataFrame([
                {"Đầu": f"Đầu {i}", "Lần XH": head[str(i)]} for i in range(10)
            ])
            fig_head = px.bar(df_head, x="Đầu", y="Lần XH",
                              color="Lần XH", color_continuous_scale="Blues",
                              template="plotly_dark", title="Phân bố đầu số")
            fig_head.update_layout(**_chart_layout())
            st.plotly_chart(fig_head, use_container_width=True)
            st.dataframe(_sdf(df_head), use_container_width=True, hide_index=True)

        with col_t:
            st.markdown("### 🔢 Đuôi số (chữ số cuối)")
            df_tail = pd.DataFrame([
                {"Đuôi": f"Đuôi {i}", "Lần XH": tail[str(i)]} for i in range(10)
            ])
            fig_tail = px.bar(df_tail, x="Đuôi", y="Lần XH",
                              color="Lần XH", color_continuous_scale="Teal",
                              template="plotly_dark", title="Phân bố đuôi số")
            fig_tail.update_layout(**_chart_layout())
            st.plotly_chart(fig_tail, use_container_width=True)
            st.dataframe(_sdf(df_tail), use_container_width=True, hide_index=True)

        with col_m:
            st.markdown("### 🔲 Ma trận Đầu × Đuôi")
            results = st.session_state.get("ht_results", [])
            matrix = {(h, t): 0 for h in range(10) for t in range(10)}
            for r in results:
                for tok in r.get("all_numbers", "").split(","):
                    tok = tok.strip()
                    if len(tok) >= 2:
                        lo = tok[-2:]
                        if lo.isdigit():
                            matrix[(int(lo[0]), int(lo[1]))] += 1

            mat_data = [[matrix[(h, t)] for t in range(10)] for h in range(10)]
            df_mat = pd.DataFrame(mat_data,
                                  index=[f"Đầu {h}" for h in range(10)],
                                  columns=[f"Đuôi {t}" for t in range(10)])

            fig_mat = px.imshow(df_mat,
                                labels=dict(x="Đuôi số", y="Đầu số", color="Lần XH"),
                                color_continuous_scale="Blues",
                                title="Ma trận Đầu × Đuôi (lần xuất hiện)",
                                template="plotly_dark",
                                aspect="auto")
            fig_mat.update_layout(**_chart_layout(coloraxis_showscale=True))
            st.plotly_chart(fig_mat, use_container_width=True)
            st.dataframe(df_mat, use_container_width=True)
