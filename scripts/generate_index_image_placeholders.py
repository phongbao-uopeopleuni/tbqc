"""Tạo ảnh JPEG minh họa cho trang chủ khi chưa có file thật trong static/images/."""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# Ảnh minh họa Pillow ~11KB; ảnh thật thường ≥20KB — không ghi đè khi đã có file lớn hơn ngưỡng này
_MIN_REAL_BYTES = 15_000


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ):
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_jpg(path: str, size: tuple[int, int], lines: list[str], subtitle: str | None = None) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w, h = size
    img = Image.new("RGB", (w, h), color=(250, 235, 215))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=(139, 0, 0), width=4)
    f_title = _font(22 if w > 500 else 16)
    text = "\n".join(lines)
    if subtitle:
        text = text + "\n" + subtitle
    bbox = draw.multiline_textbbox((0, 0), text, font=f_title, spacing=8)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = (h - th) // 2
    draw.multiline_text((x, y), text, fill=(100, 20, 20), font=f_title, spacing=8)
    img.save(path, "JPEG", quality=88)


def main() -> None:
    root = os.path.join(os.path.dirname(__file__), "..", "static", "images")
    root = os.path.normpath(root)
    hero_path = os.path.join(root, "anh1", "anhhome.jpg")
    hero_spec: tuple[str, tuple[int, int], list[str], str | None] | None
    # Hero thường >80KB; tránh ghi đè ảnh bia đá thật
    if os.path.isfile(hero_path) and os.path.getsize(hero_path) > 80_000:
        print("Skip hero (anh1/anhhome.jpg already exists, real photo):", hero_path)
        hero_spec = None
    else:
        hero_spec = (
            hero_path,
            (920, 400),
            ["Ảnh minh họa — Hero"],
            "(Thay bằng ảnh thật: anhhome.jpg)",
        )
    # Tên file khớp README + templates/index.html (URL-safe, không khoảng trắng)
    specs: list[tuple[str, tuple[int, int], list[str], str | None]] = [
        (os.path.join(root, "1-vua-gia-long.jpg"), (680, 420), ["1. Vua Gia Long"], None),
        (os.path.join(root, "2-vua-minh-mang.jpg"), (680, 420), ["2. Vua Minh Mạng"], None),
        (os.path.join(root, "3-kim-sach-de-he-thi.jpg"), (680, 420), ["3. Kim sách Đế Hệ Thi"], None),
        (os.path.join(root, "4-kinh-thanh-hue.jpg"), (680, 420), ["4. Kinh thành Huế"], None),
        (os.path.join(root, "5-phu-tuy-bien.jpg"), (680, 420), ["5. Phủ Tuy Biên"], None),
        (os.path.join(root, "6-trong-nha-tho.jpg"), (680, 420), ["6. Trong nhà thờ"], None),
    ]
    if hero_spec is not None:
        specs.insert(0, hero_spec)
    for path, size, lines, sub in specs:
        if os.path.isfile(path) and os.path.getsize(path) > _MIN_REAL_BYTES:
            print("Skip (real photo exists):", path)
            continue
        make_jpg(path, size, lines, sub)
        print("Wrote", path)


if __name__ == "__main__":
    main()
