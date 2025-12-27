# Cập Nhật Hệ Thống Blog Hoạt Động

## Tổng Quan

Đã chuyển đổi hệ thống từ **sync tự động từ Facebook** sang **blog tự quản lý** với admin đăng bài trực tiếp.

## Thay Đổi Chính

### ✅ Đã Xóa
- ❌ Facebook sync functionality
- ❌ API endpoint `/api/activities/sync-facebook`
- ❌ Nút "Đồng bộ từ Facebook" trong admin panel
- ❌ Dependencies không cần thiết cho Facebook API

### ✅ Đã Thêm/Cải Thiện

#### 1. **Image Upload Feature**
- ✅ API endpoint `/api/upload-image` (admin only)
- ✅ Upload ảnh từ máy tính
- ✅ Validate file type và size (max 5MB)
- ✅ Lưu vào `static/images/activities/`
- ✅ Preview ảnh trước khi lưu

#### 2. **Admin Interface Improvements**
- ✅ Nút "📷 Upload" để upload ảnh dễ dàng
- ✅ Preview ảnh sau khi upload
- ✅ Form validation và error handling tốt hơn
- ✅ UI/UX cải thiện

#### 3. **Blog Public Interface**
- ✅ Layout blog đẹp hơn với card design
- ✅ Responsive design cho mobile
- ✅ Typography cải thiện
- ✅ Date formatting đẹp hơn
- ✅ Related posts section
- ✅ Better image display

## Cách Sử Dụng

### Cho Admin: Đăng Bài

1. **Đăng nhập** với tài khoản admin
2. Vào **`/admin/activities`**
3. **Điền thông tin bài viết**:
   - Tiêu đề (bắt buộc)
   - Tóm tắt (tùy chọn)
   - Nội dung (bắt buộc)
   - Ảnh đại diện: Có thể:
     - Nhập URL ảnh
     - Hoặc click "📷 Upload" để upload từ máy tính
4. **Chọn trạng thái**:
   - "Nháp": Lưu để chỉnh sửa sau
   - "Đã đăng": Hiển thị công khai ngay
5. **Lưu bài viết**

### Cho Người Dùng: Xem Blog

1. Vào **`/activities`**
2. Xem danh sách bài viết (chỉ posts có status "published")
3. Click vào bài viết để xem chi tiết
4. Xem related posts ở cuối trang

## API Endpoints

### Upload Image
```
POST /api/upload-image
Authorization: Admin login required
Content-Type: multipart/form-data

Body:
  image: (file)

Response:
{
  "success": true,
  "url": "/static/images/activities/activity_20251213_120000_abc123.jpg",
  "filename": "activity_20251213_120000_abc123.jpg"
}
```

### Create Activity
```
POST /api/activities
Authorization: Admin login required
Content-Type: application/json

Body:
{
  "title": "Tiêu đề bài viết",
  "summary": "Tóm tắt...",
  "content": "Nội dung đầy đủ...",
  "thumbnail": "/static/images/activities/...",
  "status": "published" | "draft"
}
```

### Get Activities (Public)
```
GET /api/activities?status=published&limit=20
No authentication required

Response:
[
  {
    "id": 1,
    "title": "...",
    "summary": "...",
    "content": "...",
    "thumbnail": "...",
    "status": "published",
    "created_at": "2025-12-13T10:00:00"
  }
]
```

## File Structure

```
tbqc/
├── app.py                          # Main app với upload endpoint
├── admin_activities.html           # Admin interface (đã cải thiện)
├── activities.html                 # Blog public (đã cải thiện)
├── static/
│   └── images/
│       └── activities/             # Uploaded images
│           └── activity_*.jpg
```

## Database Schema

Bảng `activities` giữ nguyên:
- `activity_id`: Primary key
- `title`: Tiêu đề
- `summary`: Tóm tắt
- `content`: Nội dung
- `status`: 'published' | 'draft'
- `thumbnail`: URL ảnh đại diện
- `created_at`: Ngày tạo
- `updated_at`: Ngày cập nhật

**Lưu ý**: Columns `metadata` và `facebook_post_id` vẫn còn trong database nhưng không còn sử dụng.

## Best Practices

1. **Image Upload**:
   - Sử dụng ảnh có kích thước hợp lý (< 5MB)
   - Format: JPG, PNG, GIF, WebP
   - Khuyến nghị: Resize ảnh trước khi upload để tối ưu

2. **Content**:
   - Viết tóm tắt ngắn gọn (150-300 ký tự)
   - Format nội dung với line breaks để dễ đọc
   - Thêm ảnh đại diện để bài viết đẹp hơn

3. **Status Management**:
   - Lưu "Nháp" để chỉnh sửa sau
   - Chỉ "Đăng bài" khi đã hoàn thiện

## Troubleshooting

### Lỗi upload ảnh
- Kiểm tra file size (< 5MB)
- Kiểm tra file type (chỉ ảnh)
- Kiểm tra quyền ghi vào `static/images/activities/`

### Bài viết không hiển thị
- Kiểm tra status phải là "published"
- Kiểm tra API response
- Xem console logs

### Ảnh không hiển thị
- Kiểm tra URL ảnh có đúng không
- Kiểm tra file có tồn tại trong `static/images/activities/`
- Kiểm tra quyền đọc file

---

**Updated**: 2025-12-13  
**Status**: ✅ Ready to use

