# 🚀 Quick Start - UI Setup

## ✅ Đã Hoàn Thành

Tất cả các sửa đổi đã được thực hiện để UI chạy hoàn chỉnh.

## 📋 Các Thay Đổi Chính

### 1. Flask Configuration
- ✅ `static_folder='static'`
- ✅ `template_folder='templates'`
- ✅ `static_url_path='/static'`

### 2. Routes
- ✅ `GET /` → `render_template('index.html')`
- ✅ `GET /login` → `render_template('login.html')`
- ✅ `GET /members` → `render_template('members.html')`

### 3. Static Files
- ✅ JS files: `/static/js/*.js`
- ✅ Images: `/static/images/*.jpg`
- ✅ Legacy routes kept for compatibility

### 4. Template Paths
- ✅ Scripts: `/static/js/family-tree-core.js`
- ✅ Images: `/static/images/vua-minh-mang.jpg`

## 🎯 Cách Chạy

### Bước 1: Khởi động Server
```powershell
python app.py
```

### Bước 2: Mở Browser
```
http://127.0.0.1:5000/
```

### Bước 3: Kiểm Tra
1. **Trang chủ hiển thị** ✅
2. **Tree visualization load** ✅
3. **Search hoạt động** ✅
4. **Click node hiển thị info** ✅
5. **Không có 404 errors** ✅

## 🔍 Kiểm Tra Console

Mở Browser DevTools (F12) và kiểm tra:
- ✅ Không có lỗi 404 cho JS files
- ✅ Không có lỗi 404 cho images
- ✅ API calls thành công (200 OK)
- ✅ Tree renders correctly

## 📝 Test API Endpoints

Trong Browser Console:
```javascript
// Test tree API
fetch('/api/tree?max_gen=5').then(r => r.json()).then(console.log)

// Test search API
fetch('/api/search?q=Minh').then(r => r.json()).then(console.log)

// Test ancestors API
fetch('/api/ancestors/1').then(r => r.json()).then(console.log)
```

## ✅ Expected Results

Sau khi chạy `python app.py`:

1. **Server starts** → `Running on http://127.0.0.1:5000`
2. **Open browser** → `http://127.0.0.1:5000/`
3. **Page loads** → Index.html renders
4. **Tree displays** → Interactive genealogy tree
5. **Search works** → Can search and focus on person
6. **Click node** → Shows person info panel

## 🎉 Done!

UI đã sẵn sàng và hoạt động đầy đủ!

