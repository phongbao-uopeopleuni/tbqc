# Phase 5.7a — Gallery Upload Contract Tests

> Type: `[test-only]`
> Scope: DB integration tests for `POST /api/upload-image` (album path).
>        Không thay đổi production code.

## Status

- Date: 2026-05-22
- Branch: `codex/phase-5-gallery-members`
- Runtime code changes: none
- Template/JS changes: none
- Mutation schema changes: none

## P0 Gate Evidence (trước khi tạo test)

| Check | Kết quả |
|---|---|
| Docker | ✅ Client+Server 29.4.3 |
| Backup parity drill | ✅ persons=1188, 20 tables, sample_non_null=True |
| `pytest -m db_integration` | ✅ 53 passed (Phase 5.6 baseline) |

## Tests Created

**File:** `tests/test_gallery_upload_contract.py` — 10 `@pytest.mark.db_integration` tests

### Error paths (7 tests)

| Test | Expected |
|---|---|
| `test_upload_wrong_password_returns_401` | 401, success=False |
| `test_upload_invalid_album_id_format_returns_400` | 400, success=False |
| `test_upload_album_not_found_returns_404` | 404, success=False |
| `test_upload_no_image_field_returns_400` | 400, success=False |
| `test_upload_invalid_extension_returns_400` | 400, success=False |
| `test_upload_fake_png_content_returns_400` | 400, success=False |
| `test_upload_no_album_no_auth_returns_403` | 403, success=False |

### Happy paths (3 tests)

| Test | Assertion |
|---|---|
| `test_upload_inserts_album_image_row` | INSERT album_images, count +1, body has success/album_id/url/filename |
| `test_upload_response_url_contains_album_path` | URL contains `album_{id}` |
| `test_upload_two_images_count_increases_by_two` | count +2 after 2 uploads |

## Key Patterns

### Minimal valid PNG

```python
def _make_minimal_png() -> io.BytesIO:
    from PIL import Image
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
```

Pillow-generated PNG passes `validate_image_payload` magic bytes check + Pillow verify.

### Filesystem isolation

```python
import services.gallery_service as gs
monkeypatch.setattr(gs, "BASE_DIR", str(tmp_path))
```

Redirects all `os.makedirs` and `file.save()` to pytest tmp_path — no real disk writes.

### Password bypass

```python
monkeypatch.setattr(gs, "verify_album_password", lambda pw: True)
```

Patched at usage site (import in `services.gallery_service`).

### MDL commit pattern

```python
def _count_images(cursor, album_id):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM album_images WHERE album_id = %s", (album_id,))
    result = cursor.fetchone()[0]
    _commit(cursor)  # release MDL trước khi handler DDL chạy
    return result
```

## Gate Evidence (sau khi tạo test)

| Gate | Command | Result |
|---|---|---|
| Test file | `pytest -x -v tests/test_gallery_upload_contract.py` | `10 passed in 27.04s` |
| Full regression | `pytest -x -q -m "not db_integration" --tb=no` | `384 passed, 3 skipped` |

## Seed IDs

- Albums: 1001–1012 (above Phase 5.5's 901–913)

## Next Step

Phase 5.7b: Members bulk update DB state contract tests
(`/api/members/bulk-update-branch`, `/api/members/bulk-update-sll`).
Note: test schema may not have `branch_name`/`branch_id` in `persons` — probe first.
