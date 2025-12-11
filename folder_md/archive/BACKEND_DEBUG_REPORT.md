# Backend Debug Report (siblings & spouses cleanup)

## Scope
- Remove runtime dependency on deprecated tables `sibling_relationships` and `marriages_spouses`.
- Stabilize key endpoints: `/api/health`, `/api/persons`, `/api/person/<id>`, `/api/members`.
- Keep JSON shape; spouses may be `null` temporarily with TODO to use `marriages`.

## Files changed
- `folder_py/app.py`
  - `/api/persons`: removed legacy joins; siblings derived from `relationships`; spouse set to `None` with TODO.
  - `/api/person/<id>`: fixed undefined `father_name`/`mother_name`; siblings via `relationships`; spouse placeholder; no legacy tables queried.
  - `/api/members`: keeps siblings via `relationships`; spouse placeholder; no legacy tables.
  - Added `run_smoke_tests()` helper using Flask test client.
- `folder_py/marriage_api.py`
  - All spouse endpoints return HTTP 501 with TODO; no DB calls to `marriages_spouses`.
- `folder_sql/database_schema_in_laws.sql`
  - Commented sibling/marriages_spouses DDL sections as deprecated.
- `folder_sql/database_schema_extended.sql`
  - Commented legacy `marriages_spouses` table + view; marked deprecated.
- `folder_sql/check_database_status.sql`
  - Replaced marriages_spouses check with deprecated notice.
- `folder_py/import_final_csv_to_database.py` / `import_final_csv_to_database.py`
  - Legacy spouse import now no-op with warning; no queries to `marriages_spouses`; sibling count derived from `relationships`.

## Query refactors
- Siblings: now computed via `relationships` (shared `father_id` or `mother_id`), no `sibling_relationships` table.
- Spouses: legacy table removed from all runtime queries; current responses set `spouse` to `None` with TODO to use normalized `marriages`.

## TODOs (future)
- Implement spouse derivation using `marriages` (husband_id/wife_id, dates/locations).
- Rebuild spouse-related views/endpoints on top of `marriages`.

## Quick sanity commands
```bash
curl -s http://localhost:5000/api/health
curl -s http://localhost:5000/api/persons | head
curl -s http://localhost:5000/api/person/1   # replace 1 with a real person_id
```

## Checklist
- [x] No active code/SQL depends on `sibling_relationships` or `marriages_spouses`.
- [x] `/api/health` runs.
- [x] `/api/persons` returns JSON list without SQL errors.
- [x] `/api/person/<id>` no NameError/SQL errors.
- [x] Siblings derived from `relationships`.
- [x] Spouse no longer depends on deprecated table (currently `None`, TODO to use `marriages`).

