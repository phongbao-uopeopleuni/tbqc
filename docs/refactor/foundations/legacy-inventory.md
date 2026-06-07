# Legacy Inventory

> Danh sach file/folder legacy: khong dung routine, co the chua xoa, mark "DANGER" hoac "archived".

## folder_sql/ — Migration scripts

**Vi tri**: `D:\tbqc\folder_sql\`

| File | Loai | Status | Ghi chu |
|---|---|---|---|
| `reset_schema_tbqc.sql` | bootstrap | OK dung trong test | Core schema persons/relationships/marriages |
| `create_users_table.sql` | bootstrap | OK | Bang users + permissions |
| `create_activity_logs_table.sql` | bootstrap | OK | Bat buoc cho audit gate |
| `create_edit_requests_table.sql` | bootstrap | OK | Bang edit_requests |
| `add_alias_column.sql` | migration | OK incremental | Cot phu |
| `add_grave_image_column.sql` | migration | OK | |
| `add_grave_location_column.sql` | migration | OK | |
| `add_member_profile_fields.sql` | migration | OK | |
| `add_occupation_column.sql` | migration | OK | |
| `add_performance_indexes.sql` | migration | OK | Indexes |
| `create_users_table_only.sql` | duplicate? | **DANGER** | Verify vs create_users_table.sql |
| `check_and_migrate.sql` | check | unknown | |
| `check_database_status.sql` | check | unknown | |
| `drop_old_tables.sql` | **DESTRUCTIVE** | **DANGER** | KHONG chay routine, chi setup lan dau |
| `reset_database_complete.sql` | **DESTRUCTIVE** | **DANGER** | KHONG chay routine |
| `reset_tbqc_tables.sql` | **DESTRUCTIVE** | **DANGER** | KHONG chay routine |
| `update_views_procedures_tbqc.sql` | views/procs | unknown | |
| `update_views_with_csv_id.sql` | views/procs | unknown | |
| `archive/` | folder | archived | Da archived |

**Rule**: 3 file DESTRUCTIVE chi chay khi setup local DB lan dau hoac drill restore. KHONG chay tren production.

## scripts/ — Extract / verify scripts

| File | Risk | Ghi chu |
|---|---|---|
| `scripts/extract_admin_templates.py` | **DANGER** | Co the ghi de admin_templates.py neu chay nham. Cham co dry-run flag truoc khi dung. |
| `scripts/extract_templates.py` | **DANGER** | Tuong tu. |
| `scripts/fix_index_js.py` | low | Patch index.js |
| `scripts/generate_index_image_placeholders.py` | low | One-time generator |
| `scripts/code-graph/scan.mjs` | OK | Code-graph scanner, da regenerate o commit e1317e7 |
| `scripts/verify-*.py` | OK | Verify scripts, read-only |
| `scripts/check_blueprint_routes.py` | OK | Useful cho Phase 0a inventory |
| `scripts/check_outdated_deps.py` | OK | |
| `scripts/list_routes.py` | OK | Useful cho ROUTE_INVENTORY.md |
| `scripts/run_pre_upgrade.py` | OK | Pre-upgrade gate |
| `scripts/branch_report_*.xlsx` | data | Output of `branch_report_p5_p8.py` |
| `scripts/Template_updatetbqc.xlsx` | data | Excel template |
| `scripts/cleanup_unused_files.py` | unknown | Verify behavior truoc khi chay |
| `scripts/sync_tbqc_accounts.py` | OK | Sync admin accounts |
| `scripts/TEST_API_ENDPOINTS.ps1` | OK | Manual smoke |
| `scripts/setup-local-env.ps1` | OK | Local dev setup |

**Action**: 2 file DANGER (`extract_*_templates.py`) — khuyen nghi move sang `scripts/legacy/` hoac them `--dry-run` mac dinh trong Phase 0a.

## Legacy assets

| File | Status | Ghi chu |
|---|---|---|
| `docs/assets/tree-default-view.png` | moved | Moved tu repo root 2026-05-21 |
| `docs/assets/tree-zoomed.png` | moved | Moved tu repo root 2026-05-21 |
| `static/images/anh1/*.jpg` cu | da xoa 3 file | Commit 8b0e8fd |
| `static/data/code-graph.json` | active | Da regenerate commit e1317e7, ~94k dong |

## folder_py/ — KHONG legacy

Mac du ten goi y "legacy", `folder_py/` la **canonical** cho:
- `folder_py/db_config.py` — DB config single source
- `folder_py/genealogy_tree.py` — tree algorithm

Phase 0c se xoa dual-path `try: from folder_py.X / except: from X`, chot canonical = `folder_py.X`.
