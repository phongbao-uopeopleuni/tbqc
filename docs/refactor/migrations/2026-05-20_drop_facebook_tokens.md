# Migration: drop bảng `facebook_tokens` (unused)

**Ngày áp dụng:** 2026-05-20
**Applied by:** Phong Bao (local Python script, Railway DB)
**Rows lost:** 0 (bảng rỗng tại thời điểm drop)

## Lý do

Không có code Python/JS nào đọc hoặc ghi bảng này. App dùng `FB_PAGE_ID` + `FB_ACCESS_TOKEN` từ env var thay thế. Verified: grep toàn bộ `*.py *.js *.html` — 0 reference.

## Forward migration

```sql
DROP TABLE IF EXISTS facebook_tokens;
```

## Rollback (chạy nếu cần khôi phục)

```sql
CREATE TABLE `facebook_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `token_type` enum('user','page','app') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'page',
  `access_token` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `page_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT 'PhongTuyBienQuanCong',
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `idx_page_id` (`page_id`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Cách áp dụng (đã dùng)

```python
from folder_py.db_config import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS facebook_tokens')
conn.commit()
cur.close()
conn.close()
```
