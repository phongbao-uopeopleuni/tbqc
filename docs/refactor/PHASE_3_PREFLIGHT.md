# Phase 3 Pre-flight — App Bootstrap Shrink

**Ngay:** 2026-05-22  
**Branch hien tai:** `codex/phase-2-service-refactor` (chua merge)  
**Branch Phase 3 se tao:** `codex/phase-3-bootstrap-shrink` (tu master sau khi Phase 2 merge)  
**Tham khao plan:** `docs/Pre-refactor May 20, 2026.md §9`

---

## Muc tieu

Giam `app.py` tu **1846 lines** xuong con ~200–300 lines (bootstrap/wiring thuan).  
Khong doi runtime contract: URL, method, payload, template name, DOM id/class.

---

## Frozen contracts (KHONG duoc thay doi trong tat ca Phase 3 sub-steps)

| Contract | File / Command | Gia tri hien tai |
|---|---|---|
| Route count | `python -c "import app; print(len(list(app.app.url_map.iter_rules())))"` | **117 routes** |
| Blueprint list | `tests/fixtures/bootstrap/bootstrap_snapshot.json` | 9 blueprints (activities, admin, auth, family_tree, gallery, main, members_portal, persons) |
| Before-request hooks | bootstrap_snapshot.json | csrf_protect, _check_request_limit, _page_view_before_request |
| After-request hooks | bootstrap_snapshot.json | cors_after_request, __inject_headers, _add_security_headers, _sanitize_response, _update_remember_cookie |
| Error handler codes | bootstrap_snapshot.json | 403, 404, 429, 500 |
| url_map_ordered | `tests/fixtures/url_map/url_map_ordered.txt` | Frozen (test_url_map_contract.py) |

---

## Snapshot bat buoc truoc moi sub-step

Chay het 4 lenh nay truoc khi bat dau bat ky 3.x nao:

```bash
# 1. Compile check
python -m compileall app.py -q

# 2. Contract gate nhanh
pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_p0_contract.py

# 3. Bootstrap smoke
python -c "import app; print(len(list(app.app.url_map.iter_rules())), 'routes')"

# 4. Full regression (truoc khi commit)
pytest -x -q -m "not db_integration"
# Expected: 382 passed, 3 skipped, 13 deselected
```

---

## Phase 3 Sub-steps — Scope chi tiet

### Phase 3.1 — security/members_gate.py

**Muc tieu file:** `security/members_gate.py` (tao moi)  
**Lines trong app.py:** 251–483 (~232 lines)  
**Risk tier:** Medium — co module-level side effect `FIXED_MEMBERS_PASSWORDS`

**Ham can move:**

| Ham | Lines | Ghi chu |
|---|---|---|
| `_load_fixed_members_passwords()` | 257–265 | Pure function |
| `_BCRYPT_HASH_PREFIXES` | 268 | Constant |
| `_is_bcrypt_hash()` | 271–273 | Pure function |
| `_verify_fixed_member_password()` | 276–299 | Security-critical |
| `FIXED_MEMBERS_PASSWORDS` | 302 | Module-level side effect — xem chu y |
| `MEMBERS_GATE_ACCOUNTS` | 306 | Module-level — phu thuoc FIXED_MEMBERS_PASSWORDS |
| `sync_members_gate_accounts_from_db()` | 421–440 | DB call |
| `validate_tbqc_gate()` | 442–471 | Core auth logic |

**Chu y quan trong (Risk R11):**

- `FIXED_MEMBERS_PASSWORDS = _load_fixed_members_passwords()` la **import-time side effect** — phai duoc goi khi `security/members_gate.py` duoc import.
- `app.py` phai import `FIXED_MEMBERS_PASSWORDS`, `MEMBERS_GATE_ACCOUNTS`, `validate_tbqc_gate`, `sync_members_gate_accounts_from_db` tu `security.members_gate`.
- App start log phai identical truoc/sau (test `test_members_gate_fixed_accounts.py`).
- `_BCRYPT_HASH_PREFIXES` va `_is_bcrypt_hash` chi dung noi bo → khong can facade.
- `validate_tbqc_gate` va `sync_members_gate_accounts_from_db` co external caller trong `app.py` → phai co facade.

**External callers (grep ket qua):**

```
app.py: validate_tbqc_gate(username, password)
app.py: sync_members_gate_accounts_from_db()
blueprints/members_portal.py: (import validate_tbqc_gate inline)
```

**Pre-flight rieng Phase 3.1:**

```bash
grep -rn "validate_tbqc_gate\|sync_members_gate_accounts_from_db\|FIXED_MEMBERS_PASSWORDS\|MEMBERS_GATE_ACCOUNTS" . --include="*.py" | grep -v __pycache__
```

**Gate sau Phase 3.1:**

```bash
pytest -x -q tests/test_members_gate_fixed_accounts.py tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_p0_contract.py
pytest -x -q -m "not db_integration"
```

---

### Phase 3.2 — services/external_posts_service.py

**Muc tieu file:** `services/external_posts_service.py` (tao moi)  
**Lines trong app.py:** 341–420 (helpers), 316 (cache dict), 1515–1588 (route handlers)  
**Risk tier:** Low — external HTTP + cache, khong lien quan DB mutation

**Ham can move:**

| Ham / bien | Lines | Ghi chu |
|---|---|---|
| `external_posts_cache` | 316 | Module-level dict — phai song cung module |
| `NPT_COUNCIL_RSS_URL` | 354 | Constant |
| `_npt_post_is_new()` | 357–368 | Pure function |
| `_fetch_npt_council_rss()` | 371–418 | External HTTP (requests, BeautifulSoup) |
| `_external_posts_mutation_authorized()` | 341–352 | Auth helper |
| `get_external_posts()` | 1515–1548 | Route handler — giu inline hoac tach |
| `clear_external_posts_cache()` | 1549–1558 | Route handler |
| `refresh_external_posts()` | 1559–1586 | Route handler |

**Chu y:** Route handlers (`get_external_posts`, `clear/refresh`) co the giu inline trong `app.py` neu chi co 10–20 lines, chi move business logic xuong service.

**Gate sau Phase 3.2:**

```bash
pytest -x -q tests/test_api_routes.py -k "external_posts or rss" tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py
pytest -x -q -m "not db_integration"
```

---

### Phase 3.3 — services/genealogy_sync.py

**Muc tieu file:** `services/genealogy_sync.py` (tao moi)  
**Lines trong app.py:** 484–768 (~284 lines)  
**Risk tier:** Medium-High — DB mutation (INSERT/UPDATE persons, relationships, marriages)

**Ham can move:**

| Ham | Lines | Ghi chu |
|---|---|---|
| `sync_genealogy_from_members()` | 484–718 | ~234 lines, DB write — MUTATION |
| `_collect_person_ids_from_tree_node()` | 720–730 | Pure recursive helper |
| `_fetch_marriage_pairs_in_scope()` | 733–766 | Read-only DB query |

**Chu y:**

- `sync_genealogy_from_members` la **P0 mutation** (INSERT/UPDATE vao 3 bang). Neu ap dung P0 gate nghiem ngat, can: audit snapshot + before/after fixture + unauthorized test truoc khi move.
- Tuy nhien, plan §9.3.3 gop vao Phase 3 (khong phan vao Phase 5), nen co the accept risk nay voi contract test bao ve.
- `_collect_person_ids_from_tree_node` va `_fetch_marriage_pairs_in_scope` la helpers cho `get_tree()` (Phase 3.4) — phai move truoc hoac cung luc.

**Gate sau Phase 3.3:**

```bash
pytest -x -q tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_p0_contract.py
pytest -x -q -m "not db_integration"
```

---

### Phase 3.4 — family tree routes (NANG NHAT)

**Lines trong app.py:** 769–1730 (~961 lines)  
**Risk tier:** HIGH — logic genealogy phuc tap, 3 route handlers lon

**Ham can move / xem xet:**

| Ham | Lines so luong | Ghi chu |
|---|---|---|
| `get_tree()` | 769–911 (~142 lines) | Route `/api/tree` |
| `get_ancestors()` | 912–1206 (~295 lines!) | Route `/api/ancestors/<id>` |
| `get_descendants()` | 1207–1245 (~38 lines) | Route `/api/descendants/<id>` |
| `get_stats()` | 1246–1269 (~23 lines) | Route `/api/stats` |
| `api_admin_users()` | 1270–1320 (~50 lines) | Admin API |
| `api_admin_user_detail()` | 1321–1395 (~74 lines) | Admin API |
| `verify_password_api()` | 1396–1423 (~27 lines) | Admin API |
| `api_admin_code_graph_rescan()` | 1424–1456 (~32 lines) | Admin API |
| `api_health()` | 1457–1514 (~57 lines) | Health check — sensitive |
| `api_member_stats()` | 1587–1731 (~144 lines) | Members stats |
| `_health_detail_authorized()` | 319–325 | Helper cho api_health |
| `_public_health_payload()` | 328–338 | Helper cho api_health |

**Chu y:**

- `get_ancestors` (295 lines) la route handler lon nhat — candidate cho `services/genealogy_tree_service.py` hoac `blueprints/family_tree.py`.
- `api_health` co security logic rieng (`_health_detail_authorized`) — can test rieng.
- Admin API routes (1270–1456) co the di vao `admin/api_routes.py` hoac tach rieng.
- **Khong nen lam het Phase 3.4 trong 1 PR** — chia nho theo domain:
  - 3.4a: genealogy read routes (`get_tree`, `get_ancestors`, `get_descendants`, `get_stats`)
  - 3.4b: admin API routes (`api_admin_users`, `api_admin_user_detail`, `verify_password_api`, `api_admin_code_graph_rescan`)
  - 3.4c: health + member stats (`api_health`, `api_member_stats`)

**Gate sau tung sub-step 3.4:**

```bash
pytest -x -q tests/test_api_routes.py tests/test_url_map_contract.py tests/test_bootstrap_snapshot.py tests/test_endpoint_names.py tests/test_p0_contract.py
pytest -x -q -m "not db_integration"
```

---

### Phase 3.5 — Error handlers

**Lines trong app.py:** 1732–1808 (~76 lines)  
**Risk tier:** Low  
**Muc tieu file:** `app_errors.py` hoac giu inline (nho, khong can thiet phai move)

**Ham:**

```python
@app.errorhandler(500) def internal_error(error): ...   # 1732
@app.errorhandler(404) def not_found(error): ...        # 1754
@app.errorhandler(403) def forbidden(error): ...        # 1794
@app.errorhandler(429) def ratelimit_handler(e): ...    # 1802
```

**Khuyen nghi:** Cac error handler nay ngan, co the giu inline trong `app.py` thay vi tach ra. Chi tach neu co nhu cau tai su dung hoac test rieng.

**Gate sau Phase 3.5:**

```bash
pytest -x -q tests/test_bootstrap_snapshot.py tests/test_url_map_contract.py
# Kiem tra error_handler_codes van la [403, 404, 429, 500]
pytest -x -q -m "not db_integration"
```

---

### Phase 3.6 — Bootstrap wiring

**Sau khi move het:** `app.py` chi con:
- `import` blocks
- `load_env()`, `app = Flask(...)`, extensions init
- `register_blueprints(app)`, `register_admin_routes(app)`, `register_marriage_routes(app)` 
- `if __name__ == '__main__': app.run(...)`

**Ket qua mong doi:** app.py ~200–300 lines (tu 1846 lines ban dau).

---

## Thu tu thuc hien khuyen nghi

```
Phase 3.1 → security/members_gate.py       (an toan, side-effect ro rang)
Phase 3.2 → external_posts_service.py      (doc lap, HTTP only)
Phase 3.5 → error handlers                 (nho, co the lam truoc 3.3 neu muon nhanh)
Phase 3.3 → genealogy_sync.py              (medium risk — mutation)
Phase 3.4a → genealogy read routes         (lon, can split PR)
Phase 3.4b → admin API routes
Phase 3.4c → health + member stats
Phase 3.6 → final cleanup
```

---

## Pre-flight checklist truoc khi tao branch Phase 3

- [ ] Phase 2 branch da merge vao master
- [ ] `git checkout master && git pull` tren machine
- [ ] `git checkout -b codex/phase-3-bootstrap-shrink`
- [ ] Chay full baseline: `pytest -x -q -m "not db_integration"` → 382 passed
- [ ] Xac nhan app.py la 1846 lines (nen la it hon sau khi merge Phase 2 van giu nguyen — Phase 2 khong sua app.py nhieu)
- [ ] `grep -rn "validate_tbqc_gate\|sync_members_gate\|FIXED_MEMBERS_PASSWORDS\|MEMBERS_GATE_ACCOUNTS" . --include="*.py" | grep -v __pycache__` → ghi lai ket qua cho Phase 3.1 scope
