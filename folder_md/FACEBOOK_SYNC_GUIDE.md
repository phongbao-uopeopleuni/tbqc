# Hướng Dẫn Đồng Bộ Facebook Posts

## Tổng Quan

Module `facebook_sync.py` cho phép tự động lấy posts từ Facebook page và lưu vào database. Hệ thống sẽ:
- Lấy posts từ Facebook Graph API
- Download hình ảnh và lưu vào `static/images/facebook/`
- Tự động tạo/update activities trong database
- Hỗ trợ metadata và tracking Facebook post IDs

## Cấu Hình

### 1. Facebook Access Token

Để lấy posts từ Facebook, bạn cần Facebook Page Access Token:

**Cách 1: Sử dụng Environment Variables (Khuyến nghị)**

Thêm vào `tbqc_db.env` hoặc Railway environment variables:

```env
FB_PAGE_ID=PhongTuyBienQuanCong
FB_ACCESS_TOKEN=your_page_access_token_here
```

**Cách 2: Lấy Access Token từ Facebook**

1. Truy cập [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Chọn Page của bạn
3. Generate Page Access Token
4. Copy token và set vào environment variable

**Lưu ý**: 
- Access token có thể expire, cần refresh định kỳ
- Có thể sử dụng Long-lived Token (60 ngày) hoặc Permanent Token

### 2. Facebook Page ID

Page ID có thể là:
- Username: `PhongTuyBienQuanCong`
- Page ID số: `123456789012345`

## Sử Dụng

### 1. Sync Từ Admin Panel

1. Đăng nhập với tài khoản admin
2. Vào `/admin/activities`
3. Click nút "🔄 Đồng bộ từ Facebook"
4. Hệ thống sẽ tự động lấy 25 posts mới nhất

### 2. Sync Từ API

```bash
POST /api/activities/sync-facebook
Content-Type: application/json
Authorization: (admin login required)

{
  "limit": 25,
  "status": "published",
  "page_id": "PhongTuyBienQuanCong",
  "access_token": "optional_token_override"
}
```

### 3. Sync Từ Command Line

```bash
# Sync với default settings
python folder_py/facebook_sync.py

# Sync với custom settings
python folder_py/facebook_sync.py --limit 50 --status published --page-id PhongTuyBienQuanCong
```

## Database Schema

Module tự động thêm các columns vào bảng `activities`:

- `metadata` (TEXT): JSON metadata chứa Facebook post info
- `facebook_post_id` (VARCHAR(100)): Facebook post ID để tracking

## Cấu Trúc Metadata

```json
{
  "facebook_post_id": "123456789_987654321",
  "permalink_url": "https://facebook.com/PhongTuyBienQuanCong/posts/...",
  "image_urls": ["https://...", "https://..."],
  "has_images": true
}
```

## Image Storage

- Images được download vào: `static/images/facebook/`
- Filename format: `{md5_hash}.jpg`
- URL path: `/static/images/facebook/{filename}`
- Images đã download sẽ không download lại (check file exists)

## Auto Sync (Cron Job)

Để tự động sync định kỳ, có thể setup cron job:

```bash
# Sync mỗi 6 giờ
0 */6 * * * cd /path/to/tbqc && python folder_py/facebook_sync.py --limit 25
```

Hoặc sử dụng Railway Cron Jobs hoặc scheduled tasks.

## Troubleshooting

### Lỗi: "Không thể kết nối Facebook"

- Kiểm tra `FB_ACCESS_TOKEN` có đúng không
- Kiểm tra `FB_PAGE_ID` có đúng không
- Token có thể đã expire, cần refresh

### Lỗi: "Permission denied"

- Cần Page Access Token, không phải User Access Token
- Token cần có quyền `pages_read_engagement`

### Images không download

- Kiểm tra quyền ghi vào `static/images/facebook/`
- Kiểm tra disk space
- Kiểm tra network connection

### Posts không sync

- Kiểm tra database connection
- Kiểm tra logs trong console
- Verify Facebook page có posts không

## Limitations

1. **Rate Limiting**: Facebook API có rate limits, không nên sync quá thường xuyên
2. **Token Expiry**: Access tokens có thể expire, cần refresh
3. **Public Access**: Không có token chỉ lấy được limited data
4. **Image Size**: Large images có thể tốn thời gian download

## Best Practices

1. **Sync Frequency**: Khuyến nghị sync mỗi 6-12 giờ
2. **Limit**: Không sync quá nhiều posts một lần (max 100)
3. **Status**: Sync về "draft" trước, review rồi publish
4. **Backup**: Backup database trước khi sync lần đầu
5. **Monitoring**: Monitor logs để phát hiện lỗi sớm

## API Reference

### FacebookSync Class

```python
from folder_py.facebook_sync import FacebookSync

# Initialize
sync = FacebookSync(
    page_id="PhongTuyBienQuanCong",
    access_token="your_token"
)

# Sync posts
result = sync.sync(limit=25, status='published')
print(result)
```

### Methods

- `get_page_info()`: Lấy thông tin page
- `fetch_posts(limit)`: Lấy posts từ Facebook
- `process_post(post)`: Process một post
- `download_image(url)`: Download image
- `sync_to_database(posts, status)`: Sync vào database
- `sync(limit, status)`: Main sync function

---

**Last Updated**: 2025-12-13

