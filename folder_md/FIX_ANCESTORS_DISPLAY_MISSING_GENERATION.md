# Sửa lỗi thiếu đời trong hiển thị "Tổ tiên"

## 🎯 Vấn đề

Trong phần "Cây Gia Phả Tương Tác", khi tìm ông "Ưng Lương Thái Thường Tự Khanh" (P-4-23), phần "Tổ tiên" trong sidebar "Thông tin chi tiết" chỉ hiển thị:
- Đời 1: Vua Minh Mạng
- Đời 2: TBQC Miên Sủng

**Thiếu đời 3:** Kỳ Ngoại Hầu Hường Phiêu (P-3-12)

## 🔍 Nguyên nhân

**File:** `templates/index.html` (dòng 4261-4280)

Logic cũ dùng `slice(0, -1)` để loại bỏ phần tử cuối cùng (người hiện tại), nhưng:
1. Nếu `ancestors_chain` không được sắp xếp đúng, phần tử cuối có thể không phải người hiện tại
2. Logic này có thể loại bỏ nhầm một tổ tiên nếu thứ tự không đúng

## ✅ Giải pháp

**File:** `templates/index.html` (dòng 4260-4280)

**Thay đổi:**
1. **Thay `slice(0, -1)` bằng filter dựa trên `person_id`**
   - So sánh `person_id` của mỗi phần tử với `person_id` của người hiện tại
   - Chỉ loại bỏ nếu `person_id` khớp, không phải dựa vào vị trí

2. **Đảm bảo hiển thị đầy đủ**
   - Filter tất cả ancestors, không bỏ sót
   - Sắp xếp theo `generation_level` tăng dần

3. **Cải thiện hiển thị generation**
   - Hỗ trợ cả `generation_number` và `generation_level`
   - Hiển thị đầy đủ thông tin đời

**Code mới:**
```javascript
// Ancestors
if (ancestors.ancestors_chain && ancestors.ancestors_chain.length > 0) {
  // Filter: loại bỏ người hiện tại (dựa trên person_id) thay vì slice(0, -1)
  // Đảm bảo không bỏ sót bất kỳ tổ tiên nào
  const currentPersonId = String(person.person_id || '').trim();
  const ancestorsOnly = ancestors.ancestors_chain.filter(p => {
    const pId = String(p.person_id || '').trim();
    return pId !== currentPersonId;
  });
  
  // Sắp xếp tổ tiên theo đời tăng dần (đời 1 → đời 2 → ... → đời n)
  const sortedAncestors = ancestorsOnly.sort((a, b) => {
    const genA = a.generation_number || a.generation_level || 999;
    const genB = b.generation_number || b.generation_level || 999;
    return genA - genB;
  });
  
  if (sortedAncestors.length > 0) {
    html += `
      <div style="margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
        <h5 style="color: #8B0000; margin-bottom: 10px; font-size: 16px;">Tổ tiên</h5>
        <div style="font-size: 14px; line-height: 1.8;">
          ${sortedAncestors.map(p => 
            `<div>${escapeHtml(p.full_name)} ${p.generation_number ? `(Đời ${p.generation_number})` : (p.generation_level ? `(Đời ${p.generation_level})` : '')}</div>`
          ).join('')}
        </div>
      </div>
    `;
  }
}
```

## 🧪 Test

### Bước 1: Khởi động server

```powershell
python app.py
```

### Bước 2: Test API (tùy chọn)

```powershell
python test_ancestors_api.py
```

**Kết quả mong đợi:**
- API trả về đầy đủ ancestors chain: P-1-1, P-2-3, P-3-12, P-4-23

### Bước 3: Test frontend

1. Mở `http://localhost:5000`
2. Tìm kiếm "Ưng Lương" hoặc "P-4-23"
3. Click vào node "Ưng Lương Thái Thường Tự Khanh"
4. Kiểm tra sidebar "Thông tin chi tiết" → phần "Tổ tiên"

**Kết quả mong đợi:**
- ✅ Đời 1: Vua Minh Mạng
- ✅ Đời 2: TBQC Miên Sủng
- ✅ Đời 3: Kỳ Ngoại Hầu Hường Phiêu (đã được thêm vào)

## ✅ Kết quả

- ✅ Hiển thị đầy đủ tất cả các đời tổ tiên
- ✅ Không bỏ sót bất kỳ tổ tiên nào
- ✅ Sắp xếp đúng theo đời tăng dần
- ✅ Chỉ loại bỏ người hiện tại (dựa trên `person_id`, không phải vị trí)

## 📋 Lưu ý

- **Chỉ sửa frontend:** Không thay đổi logic backend hoặc API
- **Tương thích ngược:** Logic mới vẫn hoạt động với dữ liệu cũ
- **Hiệu suất:** Filter và sort không ảnh hưởng đáng kể đến hiệu suất

---

**Đã sửa xong! Phần "Tổ tiên" giờ hiển thị đầy đủ tất cả các đời. 🚀**

