# Schema Change Checklist

Last updated: 2026-06-14 (PR-B2)  
Audience: maintainer, operator  
Purpose: quy trình bắt buộc cho mọi thay đổi schema DB trên production.

## 1. Nguyên tắc

- Mọi schema change đều phải qua `scripts/migrate.py`, không ALTER thủ công trên prod.
- Mỗi ALTER phải idempotent (`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`).
- `MODIFY COLUMN` (ví dụ: widening enum) được dùng nhưng phải note rõ là idempotent khi target state đã đúng.
- Không mix schema change với feature code trong cùng một PR nếu cả hai có độ rủi ro cao.
- Migration phải chạy với `DB_MIGRATOR_USER`, không dùng runtime `DB_USER`.

## 2. Trước khi code

- [ ] Xác định bảng nào bị ảnh hưởng.
- [ ] Kiểm tra bảng đó có bao nhiêu rows trên prod (estimate lock time).
- [ ] Xác nhận ALTER là online (InnoDB instant ADD COLUMN nếu không đổi default nullable).
- [ ] Kiểm tra `reset_schema_tbqc.sql` có phản ánh đúng không — nếu chưa, cập nhật trong cùng PR.
- [ ] Kiểm tra `ensure_*_table()` trong migrate.py có nhất quán với ALTER không.

## 3. Viết migration

- [ ] Thêm ALTER vào `scripts/migrate.py::run_migrations()` với comment rõ fix/phase.
- [ ] Đảm bảo idempotent: chạy hai lần không lỗi.
- [ ] Chạy `python scripts/check_migration_state.py --strict` trên DB local/staging trước.

## 4. Trước khi deploy lên production

- [ ] Backup prod DB (xem `docs/operations/backup-restore-drill.md`).
- [ ] Chạy `python scripts/check_migration_state.py` trên prod để xác nhận trạng thái.
- [ ] Confirm deploy window: không overlap với deploy khác cùng ngày.
- [ ] Thông báo nếu có người dùng đang active (migration lock ngắn nhưng nên cẩn thận).

## 5. Chạy migration trên production

```bash
# Cần các env vars: DB_HOST, DB_PORT, DB_NAME, DB_MIGRATOR_USER, DB_MIGRATOR_PASSWORD
python scripts/migrate.py
```

Expected output: `Migrations done.`

Nếu lỗi: không commit, không chạy tiếp — xem rollback §7.

## 6. Sau khi migrate

- [ ] Chạy lại `python scripts/check_migration_state.py` — confirm tất cả columns present.
- [ ] Chạy smoke: `python scripts/smoke_prod.py`.
- [ ] Kiểm tra Railway logs: không có lỗi DB mới.
- [ ] Update `docs/operations/release-gate.md` §5 divergences table (đánh dấu Applied).

## 7. Rollback

Migration này (thêm columns + widen enum) **không có rollback tự động**. Nếu app lỗi sau migration:

1. **Xác định lỗi** — check Railway logs trước khi rollback.
2. **App rollback** (nếu code mới gây lỗi): Railway → Settings → Deployments → Rollback to previous. Columns vẫn còn nhưng code cũ chạy được vì guards `SHOW COLUMNS` vẫn hoạt động.
3. **Column rollback** (hiếm, chỉ nếu column gây corruption): `ALTER TABLE users DROP COLUMN <col>` — chỉ làm khi chắc chắn và có backup.

## 8. Thêm migration mới trong tương lai

1. Thêm ALTER vào `run_migrations()` với comment `# <Phase/Fix> — <mô tả>`.
2. Cập nhật `ensure_*_table()` nếu đây là table mới.
3. Cập nhật `reset_schema_tbqc.sql` để fresh bootstrap khớp.
4. Thêm entry vào `REQUIRED_COLUMNS` trong `scripts/check_migration_state.py`.
5. Chạy checklist này từ đầu.
