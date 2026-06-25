#!/usr/bin/env python3
"""
Demo nâng cao: kết nối ứng dụng bên ngoài với Odoo bằng XML-RPC.

Cách chạy khi Odoo đang mở tại http://localhost:8069:
    python3 addons/quan_ly_khach_hang_van_ban/scripts/external_api_demo.py
"""

import argparse
import os
import xmlrpc.client
from datetime import datetime


URL = os.getenv("ODOO_URL", "http://localhost:8069")
DB = os.getenv("ODOO_DB", "admin")
USERNAME = os.getenv("ODOO_USERNAME", "admin")
PASSWORD = os.getenv("ODOO_PASSWORD", "")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Demo External API cho module Quản lý khách hàng và văn bản."
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Xóa các hồ sơ demo có mã khách hàng bắt đầu bằng KHAPI.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    if not PASSWORD:
        raise SystemExit(
            "Thiếu ODOO_PASSWORD. Ví dụ: "
            "ODOO_PASSWORD='mat_khau_odoo' python3 "
            "addons/quan_ly_khach_hang_van_ban/scripts/external_api_demo.py"
        )

    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        raise SystemExit("Không đăng nhập được. Kiểm tra database, user hoặc password.")

    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    if args.cleanup:
        demo_customer_ids = models.execute_kw(
            DB,
            uid,
            PASSWORD,
            "res.partner",
            "search",
            [[["ma_khach_hang", "=like", "KHAPI%"]]],
        )
        if demo_customer_ids:
            models.execute_kw(
                DB,
                uid,
                PASSWORD,
                "res.partner",
                "unlink",
                [demo_customer_ids],
            )
        print(f"Đã xóa {len(demo_customer_ids)} hồ sơ khách hàng demo KHAPI.")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    customer_ids = models.execute_kw(
        DB,
        uid,
        PASSWORD,
        "res.partner",
        "create",
        [[
            {
                "ma_khach_hang": "KHAPI%sDN" % timestamp,
                "name": "Công ty Demo External API",
                "is_khach_hang": True,
                "phan_loai_khach_hang": "doanh_nghiep",
                "muc_do_uu_tien": "cao",
                "trang_thai_cham_soc": "dang_cham_soc",
                "phone": "02499999999",
                "email": "demo-api@example.com",
                "linh_vuc_hoat_dong": "Chuyển đổi số",
                "nguon_khach_hang": "External API",
                "ghi_chu_ho_so": "Hồ sơ khách hàng doanh nghiệp được tạo từ ứng dụng bên ngoài Odoo.",
            },
            {
                "ma_khach_hang": "KHAPI%sCN" % timestamp,
                "name": "Nguyễn Văn An",
                "is_khach_hang": True,
                "phan_loai_khach_hang": "ca_nhan",
                "muc_do_uu_tien": "trung_binh",
                "trang_thai_cham_soc": "moi",
                "phone": "0987654321",
                "mobile": "0987654321",
                "email": "nguyenvanan.api@example.com",
                "street": "Số 12, đường Trần Phú",
                "city": "Đà Nẵng",
                "linh_vuc_hoat_dong": "Khách hàng cá nhân",
                "nguon_khach_hang": "External API - form đăng ký cá nhân",
                "ghi_chu_ho_so": "Hồ sơ khách hàng cá nhân được tạo từ ứng dụng bên ngoài Odoo.",
            },
        ]],
    )

    customers = models.execute_kw(
        DB,
        uid,
        PASSWORD,
        "res.partner",
        "search_read",
        [[["is_khach_hang", "=", True]]],
        {
            "fields": [
                "ma_khach_hang",
                "name",
                "phone",
                "email",
                "trang_thai_cham_soc",
                "tong_so_van_ban",
            ],
            "limit": 5,
            "order": "id desc",
        },
    )

    print(f"Đã tạo khách hàng ID: {customer_ids}")
    print("5 hồ sơ khách hàng mới nhất:")
    for customer in customers:
        print(
            "- {ma_khach_hang} | {name} | {phone} | {email} | "
            "{trang_thai_cham_soc} | {tong_so_van_ban} văn bản".format(**customer)
        )


if __name__ == "__main__":
    main()
