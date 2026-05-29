#!/usr/bin/env python3
"""
Ứng dụng Thống Kê Miền Nam
Entry point chính
"""

import sys
import os

# Đảm bảo import đúng package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Kiểm tra và thông báo các thư viện cần thiết"""
    required = []
    optional = []

    # Kiểm tra requests
    try:
        import requests
    except ImportError:
        required.append("requests")

    # Kiểm tra beautifulsoup4
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        required.append("beautifulsoup4")

    # Kiểm tra lxml
    try:
        import lxml
    except ImportError:
        optional.append("lxml (khuyến nghị cho parser nhanh hơn)")

    # Kiểm tra openpyxl
    try:
        import openpyxl
    except ImportError:
        optional.append("openpyxl (cần để xuất Excel)")

    # Kiểm tra customtkinter
    try:
        import customtkinter
    except ImportError:
        optional.append("customtkinter (giao diện đẹp hơn)")

    if required:
        print("=" * 60)
        print("⚠️  THIẾU THƯ VIỆN BẮT BUỘC:")
        for pkg in required:
            print(f"   pip install {pkg}")
        print()
        print("Chạy lệnh sau để cài tất cả:")
        print("   pip install -r requirements.txt")
        print("=" * 60)
        
        # Vẫn tiếp tục chạy nếu chỉ thiếu requests/bs4 (dùng demo mode)
        print("\n⚡ Bạn vẫn có thể dùng chế độ Demo (không cần internet)")
        print("   Bật tùy chọn 'Chế độ Demo' trong Tab Cập Nhật Dữ Liệu\n")

    if optional:
        print("📦 Thư viện tùy chọn chưa cài:")
        for pkg in optional:
            print(f"   - {pkg}")
        print()


def main():
    print("=" * 60)
    print("   🎰 PHẦN MỀM THỐNG KÊ MIỀN NAM")
    print("   Phiên bản 1.0.0")
    print("=" * 60)

    check_dependencies()

    try:
        from gui.main_window import run
        print("[MAIN] Khởi động giao diện...")
        run()
    except ImportError as e:
        print(f"[ERROR] Không thể tải giao diện: {e}")
        print("Hãy đảm bảo bạn đang chạy từ thư mục gốc của dự án.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Lỗi không xác định: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
