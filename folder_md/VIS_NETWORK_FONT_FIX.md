# Sửa lỗi vis-network font.bold

## ✅ Đã sửa

**File:** `templates/index.html` (dòng 3944-3951)

**Vấn đề:**
- vis-network không chấp nhận `bold: true` (boolean)
- Gây cảnh báo "Invalid type received for bold"

**Giải pháp:**
- Đã bỏ `bold: true` khỏi font options
- Font vẫn hiển thị đẹp với size và face đã định nghĩa

**Code trước:**
```javascript
font: { 
  size: 16,
  face: 'Arial, sans-serif',
  bold: true,  // ❌ Không hợp lệ
  color: '#333'
}
```

**Code sau:**
```javascript
font: { 
  size: 16,
  face: 'Arial, sans-serif',
  color: '#333'
  // ✅ Đã bỏ bold: true
}
```

## 📝 Lưu ý

Nếu muốn font đậm, có thể:
1. Dùng CSS để style nodes
2. Hoặc dùng chuỗi font-weight trong CSS thay vì trong vis-network options

## ✅ Kết quả

- ✅ Không còn cảnh báo "Invalid type received for bold"
- ✅ Tree vẫn render đúng
- ✅ Font hiển thị bình thường

