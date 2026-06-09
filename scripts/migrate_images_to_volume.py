#!/usr/bin/env python3
"""
Migrate uploaded media từ static/images/ lên Railway Volume.

Chạy một lần trên Railway console sau khi volume đã được mount:
    python scripts/migrate_images_to_volume.py

Idempotent: bỏ qua file đã tồn tại trên volume.
Repo assets (6 ảnh UI trang chủ) KHÔNG được copy — giữ trong repo
để Flask fallback khi volume chưa có.

Rollback: revert bằng cách unset RAILWAY_VOLUME_MOUNT_PATH trên Railway
dashboard → Flask sẽ serve từ static/images/ như cũ.
"""
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_IMAGES = REPO_ROOT / "static" / "images"

# Ảnh UI trang chủ — hardcoded trong templates/index.html, giữ trong repo
REPO_ASSETS = frozenset({
    "1-vua-gia-long.jpg",
    "1-vua-gia-long.webp",
    "2-vua-minh-mang.jpg",
    "2-vua-minh-mang.webp",
    "3-kim-sach-de-he-thi.jpg",
    "3-kim-sach-de-he-thi.webp",
    "4-kinh-thanh-hue.jpg",
    "4-kinh-thanh-hue.webp",
    "5-phu-tuy-bien.jpg",
    "5-phu-tuy-bien.webp",
    "6-trong-nha-tho.jpg",
    "6-trong-nha-tho.webp",
    "README.txt",
})


def main():
    volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
    if not volume_path:
        print("ERROR: RAILWAY_VOLUME_MOUNT_PATH chưa được set.", file=sys.stderr)
        print("       Set env var này trên Railway trước khi chạy script.", file=sys.stderr)
        sys.exit(1)

    volume = Path(volume_path)
    if not volume.exists():
        print(f"ERROR: Volume path không tồn tại: {volume}", file=sys.stderr)
        sys.exit(1)

    if not STATIC_IMAGES.exists():
        print(f"ERROR: Source path không tồn tại: {STATIC_IMAGES}", file=sys.stderr)
        sys.exit(1)

    print(f"Source : {STATIC_IMAGES}")
    print(f"Target : {volume}")
    print()

    copied = skipped_exists = skipped_asset = errors = 0

    for src in sorted(STATIC_IMAGES.rglob("*")):
        if not src.is_file():
            continue

        rel = src.relative_to(STATIC_IMAGES)

        # Bỏ qua repo assets (chỉ kiểm tra top-level)
        if len(rel.parts) == 1 and rel.name in REPO_ASSETS:
            skipped_asset += 1
            continue

        dst = volume / rel

        if dst.exists():
            skipped_exists += 1
            continue

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  COPY  {rel}")
            copied += 1
        except OSError as e:
            print(f"  ERROR {rel}: {e}", file=sys.stderr)
            errors += 1

    print()
    print(f"Xong: {copied} copied | {skipped_exists} đã có trên volume | "
          f"{skipped_asset} repo assets bỏ qua | {errors} lỗi")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
