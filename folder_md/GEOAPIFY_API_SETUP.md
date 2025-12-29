# 🗺️ Hướng dẫn cấu hình Geoapify API Key

## Tổng quan

Geoapify API được sử dụng để hiển thị bản đồ và geocoding cho tính năng "Tìm kiếm mộ phần" trên trang `/genealogy`.

**⚠️ LƯU Ý:** API key này **KHÔNG được commit lên Git**. Chỉ lưu ở local (`tbqc_db.env`) hoặc environment variables trên server production.

---

## Đăng ký API Key miễn phí

1. Truy cập: https://www.geoapify.com/
2. Đăng ký tài khoản miễn phí (không cần thẻ tín dụng)
3. Vào Dashboard → API Keys
4. Copy API key của bạn

**Giới hạn miễn phí:** 3,000 requests/ngày

---

## Cấu hình Local Development

### Cách 1: Sử dụng file `tbqc_db.env` (Khuyến nghị)

1. Mở file `tbqc_db.env` (nếu chưa có, copy từ `tbqc_db.env.example`)
2. Thêm dòng:
   ```env
   GEOAPIFY_API_KEY=your_api_key_here
   ```
3. Thay `your_api_key_here` bằng API key thực tế của bạn
4. Restart server

### Cách 2: Sử dụng Environment Variables

**Windows PowerShell:**
```powershell
$env:GEOAPIFY_API_KEY = "your_api_key_here"
```

**Windows Command Prompt:**
```cmd
set GEOAPIFY_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GEOAPIFY_API_KEY=your_api_key_here
```

---

## Cấu hình Production (Railway/Render)

### Railway.app

1. Vào Railway Dashboard: https://railway.app
2. Chọn project của bạn
3. Click vào Web Service (không phải Database)
4. Vào tab **Variables**
5. Click **+ New Variable**
6. Thêm:
   - **Key**: `GEOAPIFY_API_KEY`
   - **Value**: `your_api_key_here` (thay bằng API key thực tế)
7. Railway sẽ tự động redeploy

### Render.com

1. Vào Render Dashboard: https://render.com
2. Chọn Web Service của bạn
3. Vào tab **Environment**
4. Click **Add Environment Variable**
5. Thêm:
   - **Key**: `GEOAPIFY_API_KEY`
   - **Value**: `your_api_key_here` (thay bằng API key thực tế)
6. Click **Save Changes**
7. Render sẽ tự động redeploy

### Platform khác

Tìm phần **Environment Variables** trong dashboard và thêm:
- **Key**: `GEOAPIFY_API_KEY`
- **Value**: API key của bạn

---

## Kiểm tra cấu hình

### Local

1. Restart server sau khi set environment variable
2. Mở trang `/genealogy`
3. Mở Console (F12) và kiểm tra log:
   ```
   GEOAPIFY_API_KEY check: { hasApiKey: true, ... }
   ```
4. Thử tính năng "Tìm kiếm mộ phần"

### Production

1. Kiểm tra logs trên platform:
   - Railway: Tab **Deployments** → Click vào deployment mới nhất → Xem logs
   - Render: Tab **Logs**
2. Tìm log:
   ```
   Geoapify API key loaded: 0a6bd517f...
   ```
   (Không nên thấy warning "GEOAPIFY_API_KEY chưa được cấu hình")

---

## Troubleshooting

### Vấn đề: Trang `/genealogy` hiển thị trắng

**Nguyên nhân có thể:**
1. API key chưa được set trên production
2. JavaScript error khi load trang
3. CSS không load được

**Giải pháp:**
1. Set `GEOAPIFY_API_KEY` trong environment variables trên production
2. Kiểm tra Console (F12) để xem có JavaScript error không
3. Kiểm tra Network tab để xem có file nào không load được không

### Vấn đề: Bản đồ không hiển thị

**Nguyên nhân:**
- API key không đúng hoặc đã hết hạn
- Đã vượt quá giới hạn 3,000 requests/ngày

**Giải pháp:**
1. Kiểm tra API key trong Geoapify Dashboard
2. Kiểm tra usage trong Geoapify Dashboard
3. Đợi đến ngày hôm sau để reset limit (nếu dùng free tier)

### Vấn đề: "Geoapify API key chưa được cấu hình" hiển thị

**Nguyên nhân:**
- API key chưa được set trong environment variables hoặc `tbqc_db.env`

**Giải pháp:**
1. Kiểm tra file `tbqc_db.env` có API key không (local)
2. Kiểm tra environment variables trên production platform
3. Restart/redeploy server sau khi set environment variable

---

## Security Checklist

- ✅ Không hardcode API key trong code
- ✅ API key được lấy từ environment variable
- ✅ `tbqc_db.env` đã được thêm vào `.gitignore`
- ✅ API key không xuất hiện trong Git history
- ✅ Environment variables được set riêng cho production

---

## Lưu ý

- **Local:** API key được load từ `tbqc_db.env` (file này không được commit)
- **Production:** API key chỉ được load từ environment variables
- Trang `/genealogy` vẫn hiển thị được ngay cả khi không có API key, chỉ phần bản đồ mộ phần sẽ không hoạt động

---

**Last Updated**: 2025-12-29

