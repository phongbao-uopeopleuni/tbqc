# Hướng dẫn Setup Railway Volume cho Lưu trữ Ảnh

## 📋 Tổng quan

Railway Volume giúp lưu trữ persistent files (như ảnh) mà không bị mất khi redeploy. Đây là giải pháp tốt nhất cho việc lưu trữ ảnh đính kèm trong bài đăng.

## 🚀 Các bước Setup

### Bước 1: Tạo Volume Service trong Railway

1. **Vào Railway Dashboard**
   - Truy cập [railway.app](https://railway.app)
   - Chọn project của bạn

2. **Thêm Volume Service**
   - Click **"+ New"** hoặc **"Add Service"**
   - Chọn **"Volume"** từ danh sách template
   - Đặt tên: `images-volume` (hoặc tên bạn muốn)
   - Click **"Add"**

3. **Cấu hình Volume**
   - Railway sẽ tự động tạo volume
   - Ghi nhớ **Volume Name** (ví dụ: `images-volume`)

### Bước 2: Mount Volume vào Web Service

1. **Vào Web Service Settings**
   - Click vào **Web Service** của bạn
   - Vào tab **"Settings"** hoặc **"Variables"**

2. **Mount Volume**
   - Scroll xuống phần **"Volumes"** hoặc **"Mounts"**
   - Click **"Add Volume Mount"** hoặc **"Mount"**
   - Chọn volume: `images-volume` (hoặc tên bạn đã tạo)
   - **Mount Path**: `/app/static/images`
   - Click **"Save"** hoặc **"Apply"**

### Bước 3: Cấu hình Environment Variable (Optional)

Nếu Railway tự động tạo biến môi trường cho volume path, bạn có thể sử dụng:

```env
RAILWAY_VOLUME_MOUNT_PATH=/app/static/images
```

**Lưu ý**: Code đã được cập nhật để tự động detect volume path, nên bước này là optional.

### Bước 4: Deploy và Test

1. **Commit và Push code**
   ```bash
   git add .
   git commit -m "Add Railway Volume support for images"
   git push origin master
   ```

2. **Railway sẽ tự động deploy**
   - Chờ deployment hoàn tất
   - Check logs để đảm bảo không có lỗi

3. **Test Upload Ảnh**
   - Vào trang admin: `/admin/activities`
   - Tạo hoặc chỉnh sửa bài đăng
   - Upload ảnh và kiểm tra xem ảnh có được lưu không
   - Xem bài đăng ở `/activities/<id>` để đảm bảo ảnh hiển thị đúng

## 🔍 Kiểm tra Volume đã Mount chưa

### Cách 1: Kiểm tra trong Railway Dashboard
- Vào Web Service → Settings → Volumes
- Xem danh sách volumes đã mount

### Cách 2: Kiểm tra trong Logs
- Vào Web Service → Logs
- Tìm log về volume mount (nếu có)

### Cách 3: Test trong Code
Code đã được cập nhật để tự động detect volume path:
- Nếu có `RAILWAY_VOLUME_MOUNT_PATH` và path tồn tại → dùng volume
- Nếu không → dùng `static/images` mặc định

## 📁 Cấu trúc Thư mục

Sau khi mount volume, cấu trúc sẽ như sau:

```
/app/                          # Root của container
├── app.py                     # Flask app
├── static/
│   └── images/                # ← Volume được mount vào đây
│       ├── activity_xxx.jpg
│       └── activity_yyy.jpg
└── ...
```

## ⚠️ Lưu ý Quan trọng

1. **Backup Volume**
   - Railway Volume có thể được backup
   - Vào Volume service → Settings → Backup để tạo snapshot

2. **Ảnh cũ không tự động migrate**
   - Ảnh đã upload trước khi mount volume vẫn ở trong container filesystem
   - Cần manually copy ảnh cũ vào volume (nếu cần)

3. **Volume Size**
   - Railway Volume có giới hạn dung lượng (tùy plan)
   - Kiểm tra usage trong Volume settings

4. **Redeploy không mất ảnh**
   - Sau khi mount volume, ảnh sẽ được lưu persistent
   - Redeploy sẽ không làm mất ảnh

## 🔧 Troubleshooting

### Vấn đề: Ảnh không hiển thị sau khi mount volume

**Giải pháp:**
1. Kiểm tra volume đã mount đúng chưa
2. Kiểm tra permissions của volume path
3. Kiểm tra logs để xem có lỗi gì không
4. Đảm bảo code đã được deploy với version mới nhất

### Vấn đề: Không thể upload ảnh

**Giải pháp:**
1. Kiểm tra Web Service có quyền write vào volume không
2. Kiểm tra volume path trong environment variables
3. Xem logs để tìm lỗi cụ thể

### Vấn đề: Volume không mount

**Giải pháp:**
1. Đảm bảo đã tạo Volume service trước
2. Kiểm tra mount path có đúng không (`/app/static/images`)
3. Redeploy Web Service sau khi mount volume

## 📚 Tài liệu Tham khảo

- [Railway Volume Documentation](https://docs.railway.app/storage/volumes)
- [Railway Mounting Volumes](https://docs.railway.app/storage/volumes#mounting-volumes)

## ✅ Checklist Setup

- [ ] Đã tạo Volume service trong Railway
- [ ] Đã mount volume vào Web Service tại `/app/static/images`
- [ ] Đã commit và push code mới nhất
- [ ] Đã test upload ảnh thành công
- [ ] Đã test hiển thị ảnh trong bài đăng
- [ ] Đã verify ảnh không bị mất sau khi redeploy

---

**Lưu ý**: Sau khi setup xong, tất cả ảnh mới upload sẽ được lưu vào Railway Volume và sẽ không bị mất khi redeploy.

