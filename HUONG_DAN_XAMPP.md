# HƯỚNG DẪN XAMPP (NGẮN GỌN)

## BƯỚC 1: TẢI VÀ CÀI XAMPP

1. Tải: https://www.apachefriends.org/download.html
2. Cài đặt: Next → Next → Finish
3. Xong!

## BƯỚC 2: KHỞI ĐỘNG MYSQL

1. Mở **XAMPP Control Panel**
2. Tìm **MySQL** → Click nút **Start**
3. Chờ đến khi nút chuyển thành **Stop** (màu xanh)
4. Xong!

## BƯỚC 3: KẾT NỐI TRONG INTELLIJ

1. `Alt + 1` → Click `+` → `MySQL`
2. Điền:
   - **User**: `root`
   - **Password**: (để trống - không điền gì)
   - **Database**: (để trống)
3. Test Connection → ✅ OK
4. OK

## XONG!

Sau đó chạy `setup_database.sql` với connection root này.

