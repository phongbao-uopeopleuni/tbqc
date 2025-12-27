# Format Hiển Thị Chuỗi Phả Hệ Theo Dòng Cha

## ✅ Format Chuẩn (Đã Xác Nhận)

### Cấu Trúc Mỗi Đời

Mỗi đời được hiển thị trong một card với **2 dòng**:

#### Dòng 1: Thông tin đời và tên tổ tiên
```
Đời X – Tên tổ tiên
```

**Lưu ý quan trọng:**
- ❌ **KHÔNG** hiển thị tên bố trong ngoặc đơn
- ✅ Chỉ hiển thị: "Đời X – Tên tổ tiên"
- Ví dụ: "Đời 1 – Vua Minh Mạng" (KHÔNG có "(Gia Long)")

#### Dòng 2: Thông tin cha mẹ
```
Con của Ông ... và Bà ...
```

**Các trường hợp:**
- Có đủ cha và mẹ: `Con của Ông [tên cha] và Bà [tên mẹ]`
- Chỉ có cha: `Con của Ông [tên cha] và Bà Chưa có thông tin`
- Chỉ có mẹ: `Con của Ông Chưa có thông tin và Bà [tên mẹ]`
- Không có cả hai: `Con của Ông Chưa có thông tin và Bà Chưa có thông tin`

## 📋 Ví Dụ Hiển Thị

```
Đời 1 – Vua Minh Mạng
Con của Ông Gia Long và Bà Thuận Thiên Hoàng hậu

Đời 2 – TBQC Miên Sủng
Con của Ông Minh Mạng và Bà Tiệp dư Nguyễn Thị Viên

Đời 3 – Kỳ Ngoại Hầu Hường Phiêu
Con của Ông TBQC Miên Sủng và Bà Chưa có thông tin

Đời 4 – Ưng Lương Thái Thường Tự Khanh
Con của Ông Kỳ Ngoại Hầu Hường Phiêu và Bà Trần Thị Vung

Đời 5 – Bửu Lộc
Con của Ông Ưng Lương Thái Thường Tự Khanh và Bà Lê Thị Cam

Đời 6 – Vĩnh Phước
Con của Ông Bửu Lộc và Bà Nguyễn Thị Chín

Đời 7 – Bảo Phong
Con của Ông Vĩnh Phước và Bà Trương Thị Thanh Tâm
```

## 🔧 Code Implementation

### Frontend (templates/index.html)

Function `generatePersonCard()`:

```javascript
function generatePersonCard(p, gen, isFullWidth = true) {
  const name = p.full_name || 'Không rõ tên';
  const fatherName = normalizeParentName(p.father_name, true) || p.father_name || '';
  const motherName = normalizeParentName(p.mother_name, false) || p.mother_name || '';
  
  // Dòng 1: Chỉ hiển thị "Đời X – Tên tổ tiên" (KHÔNG có tên bố)
  const titleLine = `Đời ${gen} – ${escapeHtml(name)}`;
  
  // Dòng 2: "Con của Ông ... và Bà ..."
  let parentInfo = '';
  if (fatherName && motherName) {
    parentInfo = `Con của Ông ${escapeHtml(fatherName)} và Bà ${escapeHtml(motherName)}`;
  } else if (fatherName) {
    parentInfo = `Con của Ông ${escapeHtml(fatherName)} và Bà Chưa có thông tin`;
  } else if (motherName) {
    parentInfo = `Con của Ông Chưa có thông tin và Bà ${escapeHtml(motherName)}`;
  } else {
    parentInfo = 'Con của Ông Chưa có thông tin và Bà Chưa có thông tin';
  }
  
  // ... render HTML
}
```

## ⚠️ Lưu Ý Quan Trọng

1. **KHÔNG BAO GIỜ** thêm tên bố vào dòng 1 trong ngoặc đơn
2. **LUÔN** hiển thị thông tin cha mẹ ở dòng 2 riêng biệt
3. **LUÔN** sử dụng "Chưa có thông tin" khi thiếu dữ liệu (không để trống)
4. **CHỈ** hiển thị theo dòng cha (Nam), không hiển thị vợ/chồng (Nữ)

## 🎨 Styling

- **Badge đời:** Màu sắc khác nhau cho mỗi đời (đỏ, cam, vàng, xanh lá, xanh dương, tím, tím đậm)
- **Dòng 1:** Font lớn, đậm, màu đỏ đậm (#7b1a1a)
- **Dòng 2:** Font nhỏ hơn, màu xám đậm (#333)
- **Card:** Nền beige nhạt, viền vàng, bo góc, có shadow

## ✅ Checklist Khi Sửa Code

- [ ] Dòng 1: Chỉ có "Đời X – Tên tổ tiên" (KHÔNG có tên bố)
- [ ] Dòng 2: "Con của Ông ... và Bà ..."
- [ ] Xử lý null/undefined: Hiển thị "Chưa có thông tin"
- [ ] Chỉ hiển thị Nam (cha), không hiển thị Nữ (vợ/chồng)
- [ ] Sắp xếp theo generation_level tăng dần (từ xa đến gần)

## 📝 Lịch Sử Thay Đổi

- **2025-12-11:** Xác nhận format cuối cùng - bỏ tên bố khỏi dòng 1
- **2025-12-11:** Thêm filter gender = 'Nam' để loại bỏ vợ/chồng
- **2025-12-11:** Cải thiện API để trả về đầy đủ thông tin cha mẹ

