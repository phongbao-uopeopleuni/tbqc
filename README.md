# TBQC Gia Phả

Ứng dụng web quản lý và hiển thị gia phả (cây gia đình), kết nối giao diện HTML với cơ sở dữ liệu MySQL. Dự án sử dụng Flask, hỗ trợ trang quản trị, trang Thành viên, trang Tài liệu và bản đồ tìm kiếm mộ phần (Geoapify).

## Tổng quan

TBQC Gia Phả là website lưu trữ và trình bày thông tin gia phả dòng họ một cách trực quan, dễ tra cứu. Hệ thống cho phép xem cây gia phả, danh sách thành viên, quản lý tài liệu, theo dõi hoạt động và tìm kiếm thông tin mộ phần trên bản đồ.

## Mục tiêu

- **Lưu trữ gia phả số hóa:** Số hóa thông tin gia phả, giúp lưu trữ lâu dài và dễ dàng cập nhật.
- **Trình bày trực quan:** Hiển thị cây gia phả, mối quan hệ huyết thống, thông tin cá nhân một cách rõ ràng.
- **Tra cứu thuận tiện:** Cho phép thành viên tìm kiếm, lọc, xuất danh sách và quản lý dữ liệu.
- **Chia sẻ nội bộ:** Trang Thành viên, Tài liệu và Liên hệ giúp kết nối thông tin trong họ tộc.
- **Quản trị tập trung:** Giao diện admin để quản lý tài khoản, dữ liệu và theo dõi hoạt động hệ thống.

## Công nghệ

- **Backend:** Python 3, Flask
- **Database:** MySQL

## Cấu trúc thư mục

- `app.py` — Điểm vào ứng dụng
- `folder_py/` — Module phụ trợ (db_config, auth, ...)
- `blueprints/` — Flask blueprints: main, auth, activities, family_tree, persons, members_portal, gallery, admin
- `templates/` — Giao diện HTML (genealogy, members, admin, documents, index, ...)
- `static/` — CSS, JS, ảnh trang chủ

## Tính năng chính

- **Trang chủ:** Giới thiệu tổng quan, hình ảnh minh họa
- **Gia phả:** Cây gia phả tương tác, có bảo vệ bằng passphrase
- **Thành viên:** Danh sách thành viên, đăng nhập nội bộ, xuất Excel, tìm kiếm
- **Admin:** Đăng nhập, Dashboard, quản lý tài khoản, quản lý dữ liệu, nhật ký hoạt động
- **Liên hệ, Tài liệu**
