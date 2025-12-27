# Tính Năng Blog Tự Động Từ Facebook

## Tổng Quan

Đã tạo hệ thống blog tự động lấy nội dung từ Facebook page [PhongTuyBienQuanCong](https://www.facebook.com/PhongTuyBienQuanCong). Hệ thống sẽ tự động:
- ✅ Lấy posts từ Facebook Graph API
- ✅ Download hình ảnh và lưu vào server
- ✅ Tạo/update activities trong database
- ✅ Hiển thị dạng blog với carousel và layout đẹp

## Files Đã Tạo

### 1. Core Module
- **`folder_py/facebook_sync.py`**: Module chính để sync Facebook posts
  - Class `FacebookSync` với các methods:
    - `fetch_posts()`: Lấy posts từ Facebook API
    - `download_image()`: Download và lưu images
    - `process_post()`: Process post thành format database
    - `sync_to_database()`: Sync vào database
    - `sync()`: Main sync function

### 2. API Endpoints
- **`POST /api/activities/sync-facebook`**: API endpoint để trigger sync (admin only)
  - Request body: `{limit, status, page_id?, access_token?}`
  - Response: `{success, message, stats}`

### 3. Database Updates
- Đã cập nhật bảng `activities` với:
  - `metadata` (TEXT): JSON metadata từ Facebook
  - `facebook_post_id` (VARCHAR(100)): Tracking Facebook post ID
  - Index trên `facebook_post_id` để tối ưu query

### 4. Admin Interface
- Đã thêm nút "🔄 Đồng bộ từ Facebook" vào `/admin/activities`
- Click để sync posts tự động

### 5. Scripts
- **`sync_facebook.bat`**: Windows batch script
- **`sync_facebook.ps1`**: PowerShell script
- Có thể chạy từ command line

### 6. Documentation
- **`folder_md/FACEBOOK_SYNC_GUIDE.md`**: Hướng dẫn chi tiết

## Cách Sử Dụng

### Bước 1: Cấu Hình Facebook Access Token

Thêm vào `tbqc_db.env` hoặc Railway environment variables:

```env
FB_PAGE_ID=PhongTuyBienQuanCong
FB_ACCESS_TOKEN=your_page_access_token_here
```

**Lấy Access Token:**
1. Truy cập [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Chọn Page của bạn
3. Generate Page Access Token
4. Copy token vào environment variable

### Bước 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies mới:
- `requests==2.31.0`: Để gọi Facebook API và download images
- `Pillow==10.1.0`: Xử lý images (optional, cho future features)

### Bước 3: Sync Facebook Posts

**Cách 1: Từ Admin Panel (Khuyến nghị)**
1. Đăng nhập với tài khoản admin
2. Vào `/admin/activities`
3. Click nút "🔄 Đồng bộ từ Facebook"
4. Đợi sync hoàn tất

**Cách 2: Từ Command Line**
```bash
# Windows
sync_facebook.bat

# PowerShell
.\sync_facebook.ps1

# Python trực tiếp
python folder_py/facebook_sync.py --limit 25 --status published
```

**Cách 3: Từ API**
```bash
POST /api/activities/sync-facebook
Content-Type: application/json
Authorization: (admin login required)

{
  "limit": 25,
  "status": "published"
}
```

### Bước 4: Xem Kết Quả

- Posts sẽ xuất hiện tại `/activities`
- Images được lưu tại `static/images/facebook/`
- Posts có status "published" sẽ hiển thị công khai

## Tính Năng

### 1. Auto Sync
- Tự động lấy posts mới nhất từ Facebook
- Download images và lưu vào server
- Tạo activities với đầy đủ metadata

### 2. Smart Processing
- Tự động tạo title từ nội dung post
- Extract summary (300 ký tự đầu)
- Download và optimize images
- Track Facebook post ID để tránh duplicate

### 3. Blog Interface
- Carousel hiển thị posts có hình ảnh
- Grid layout cho danh sách posts
- Detail page với related posts
- Responsive design

### 4. Admin Management
- Sync button trong admin panel
- Real-time sync status
- Auto update existing posts
- Draft/Published status control

## Cấu Trúc Dữ Liệu

### Activity với Facebook Metadata

```json
{
  "id": 1,
  "title": "Tiêu đề post",
  "summary": "Tóm tắt...",
  "content": "Nội dung đầy đủ...",
  "thumbnail": "/static/images/facebook/abc123.jpg",
  "status": "published",
  "metadata": {
    "facebook_post_id": "123456789_987654321",
    "permalink_url": "https://facebook.com/...",
    "image_urls": ["https://..."],
    "has_images": true
  },
  "created_at": "2025-12-13T10:00:00"
}
```

## Auto Sync (Cron Job)

Để tự động sync định kỳ, setup cron job:

```bash
# Sync mỗi 6 giờ
0 */6 * * * cd /path/to/tbqc && python folder_py/facebook_sync.py --limit 25
```

Hoặc sử dụng Railway Scheduled Tasks.

## Troubleshooting

### Lỗi: "FB_ACCESS_TOKEN không được set"
- Kiểm tra environment variables
- Đảm bảo token đã được set đúng

### Lỗi: "Không thể kết nối Facebook"
- Token có thể đã expire
- Kiểm tra Page ID có đúng không
- Kiểm tra network connection

### Images không download
- Kiểm tra quyền ghi vào `static/images/facebook/`
- Kiểm tra disk space
- Kiểm tra logs

### Posts không sync
- Kiểm tra database connection
- Kiểm tra Facebook page có posts không
- Xem logs trong console

## Best Practices

1. **Sync Frequency**: Khuyến nghị sync mỗi 6-12 giờ
2. **Limit**: Không sync quá nhiều posts một lần (max 100)
3. **Status**: Sync về "draft" trước, review rồi publish
4. **Backup**: Backup database trước khi sync lần đầu
5. **Monitoring**: Monitor logs để phát hiện lỗi sớm

## Next Steps

Có thể mở rộng thêm:
- [ ] Auto sync với cron job
- [ ] Email notification khi có posts mới
- [ ] Image optimization (resize, compress)
- [ ] Support video posts
- [ ] Support multiple Facebook pages
- [ ] Analytics và statistics

---

**Created**: 2025-12-13  
**Status**: ✅ Ready to use

