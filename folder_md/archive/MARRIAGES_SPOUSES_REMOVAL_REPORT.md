# Marriages Spouses Removal Report

## Summary
- Removed runtime dependency on legacy `marriages_spouses` table. APIs now avoid querying or updating the table and return safe placeholders where needed.
- SQL helper files that created/altered `marriages_spouses` are commented and marked deprecated to keep schema aligned with normalized `marriages`.
- Import scripts now skip legacy spouse import paths (legacy functions retained but no-op) to prevent failures.

## Changes by file
- `folder_py/app.py`
  - `/api/persons`: removed JOIN/aggregation on `marriages_spouses`; spouse field now defaults to `null`. Siblings and children remain intact.
  - Person detail flow: removed spouse queries; placeholders set with TODO to derive from normalized `marriages`.
  - Sync/update flows: removed writes/reads to `marriages_spouses`; added TODO note for future `marriages` integration.
  - `/api/members`: removed spouse query; placeholder + TODO.
- `folder_py/marriage_api.py`
  - All spouse endpoints now return `501` with TODO note to migrate to normalized `marriages` table (no DB calls to legacy table).
- `folder_sql/database_schema_in_laws.sql`
  - Commented legacy `marriages_spouses` alterations; marked deprecated.
- `folder_sql/database_schema_extended.sql`
  - Commented legacy `marriages_spouses` table creation and dependent view; marked deprecated with TODO to rebuild using `marriages`.
- `folder_sql/check_database_status.sql`
  - Replaced legacy table checks with a deprecated notice (schema uses `marriages`).
- `folder_py/import_final_csv_to_database.py` and `import_final_csv_to_database.py`
  - `import_marriages` now no-op with warning; spouse lookups/metrics referencing legacy table removed; added TODO to use normalized `marriages`.

## Confirmation
- `/api/persons` no longer references or joins `marriages_spouses`; SQL is valid against current schema.
- No active Python code writes/reads `marriages_spouses`; spouse features are temporarily disabled with clear TODOs to migrate to `marriages`.
- Schema files keep normalized design; no `CREATE TABLE marriages_spouses` is active.

## TODO (future)
- Reimplement spouse retrieval and persistence using normalized `marriages` table (husband_id / wife_id, dates, locations).
- Recreate spouse-related views/endpoints to read from `marriages`.
- Optional: add migration to map any legacy spouse text into normalized structure.

## Quick test checklist
- Hit `/api/health` (should stay OK).
- Hit `/api/persons` (should return data without SQL errors; `spouse` may be `null` for now).
- Hit `/api/members` and `/api/person/<id>` (no references to legacy table; spouse info placeholder).

