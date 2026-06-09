## static/images/ — cấu trúc thư mục

### Repo assets (hardcoded trong templates, KHÔNG migrate lên Volume)
- 1-vua-gia-long.jpg/.webp
- 2-vua-minh-mang.jpg/.webp
- 3-kim-sach-de-he-thi.jpg/.webp
- 4-kinh-thanh-hue.jpg/.webp
- 5-phu-tuy-bien.jpg/.webp
- 6-trong-nha-tho.jpg/.webp  ← cũng là DEFAULT_ACTIVITY_FALLBACK_URL

### Uploaded media (migrate lên Railway Volume /data/images/)
- activity_YYYYMMDD_HHMMSS_HASH.jpg  ← upload qua /api/upload-image, có DB ref
- anh1/                               ← gallery chính; gallery-001.jpg...gallery-120.jpg
                                        + anhhome.jpg/.webp (hero)
                                        + xuan-binh-ngo-2026.jpg
- don-dep-mo-gia-toc/                ← album dọn dẹp mộ; don-dep-001.jpg...don-dep-052.jpg
- _thumbs/                            ← auto-generated thumbnails
- album_*/                            ← albums tạo qua gallery UI (DB-managed)
- graves/                             ← ảnh mộ phần upload qua /api/grave/upload-image
- personal/                           ← ảnh cá nhân upload qua persons API

### Migration
- Script: python scripts/migrate_images_to_volume.py
- Env var Railway: RAILWAY_VOLUME_MOUNT_PATH=/data/images
- UI assets (1-6-*.jpg/.webp) KHÔNG được copy lên Volume (Flask fallback về static/)
