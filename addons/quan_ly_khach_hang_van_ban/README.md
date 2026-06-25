# Đề tài 4: Quản lý khách hàng + Quản lý văn bản

## Mục tiêu nghiệp vụ

Module này số hóa hồ sơ khách hàng bằng cách gom thông tin khách hàng, nhân viên phụ trách và toàn bộ văn bản liên quan vào cùng một nơi. Người dùng có thể mở hồ sơ khách hàng để xem nhanh hợp đồng, báo giá, tài liệu pháp lý, văn bản đến và văn bản đi.

## Các module kết hợp

- `nhan_su`: cung cấp danh sách nhân viên phụ trách khách hàng và xử lý hồ sơ.
- `quan_ly_van_ban`: cung cấp nghiệp vụ văn bản đến, văn bản đi, loại văn bản.
- `quan_ly_khach_hang_van_ban`: mở rộng hồ sơ khách hàng và gắn văn bản vào khách hàng.

## Luồng demo đề xuất

1. Tạo một nhân viên trong `QLNS / Quản lý nhân viên`.
2. Vào `QLNS / Đề tài 4 / Hồ sơ khách hàng`, tạo khách hàng mới và chọn nhân viên phụ trách.
3. Trong tab `Văn bản đi`, tạo báo giá hoặc hợp đồng gửi khách hàng.
4. Trong tab `Văn bản đến`, tạo tài liệu pháp lý hoặc phản hồi từ khách hàng.
5. Quay lại danh sách khách hàng để xem tổng số văn bản và lọc theo nhân viên phụ trách/trạng thái chăm sóc.

## Điểm cải tiến so với module gốc

- Có mã khách hàng tự sinh theo sequence `KH00001`.
- Có hồ sơ khách hàng tập trung thay vì chỉ lưu văn bản rời rạc.
- Có nhóm hồ sơ: hợp đồng, báo giá, pháp lý, biên bản làm việc.
- Có ngày hiệu lực, ngày hết hạn, trạng thái xử lý và tệp đính kèm.
- Liên kết nhân viên phụ trách từ module nhân sự để đáp ứng yêu cầu kết hợp với `Quản lý nhân sự`.

## Yêu cầu nâng cao đã thực hiện

### 1. Tích hợp AI hỗ trợ phân tích hồ sơ

Module có chức năng `Phân tích AI` trong form `Hồ sơ khách hàng`.

Cách demo:

1. Vào `QLNS / Đề tài 4 / Hồ sơ khách hàng`.
2. Mở một khách hàng đã có văn bản đến/văn bản đi.
3. Bấm nút `Phân tích AI`.
4. Xem tab `Phân tích AI`.

AI nội bộ sẽ tự sinh:

- Tóm tắt trạng thái hồ sơ khách hàng.
- Cảnh báo văn bản đã hết hạn hoặc sắp hết hạn trong 30 ngày.
- Cảnh báo văn bản chưa có tệp đính kèm.
- Gợi ý hành động tiếp theo cho nhân viên phụ trách.

Chức năng này không phụ thuộc API key bên ngoài, phù hợp để demo ổn định khi chấm bài.

### 2. Kết nối ứng dụng bên ngoài bằng External API

Module có demo kết nối Odoo với ứng dụng bên ngoài bằng XML-RPC theo tài liệu External API của Odoo 15.

Chạy khi Odoo đang mở tại `http://localhost:8069`:

```bash
ODOO_PASSWORD='mat_khau_odoo_cua_ban' python3 addons/quan_ly_khach_hang_van_ban/scripts/external_api_demo.py
```

Script sẽ:

- Đăng nhập vào database `admin`.
- Tạo một hồ sơ khách hàng mẫu từ bên ngoài Odoo.
- Đọc lại 5 hồ sơ khách hàng mới nhất để kiểm tra dữ liệu.

## Nguồn tham khảo

- Kho học phần FIT-DNU/Business-Internship.
- Tài liệu Odoo 15 về model, view, action và sequence.
- Tài liệu Odoo 15 External API: `https://www.odoo.com/documentation/15.0/developer/reference/external_api.html`
