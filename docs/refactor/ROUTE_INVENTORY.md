# Route Inventory

> Day du route runtime cua tbqc. Cot Risk Tier va Domain de input cho Phase 1/2/3.

## Format

| Cot | Y nghia |
|---|---|
| URL | Route rule |
| Method | GET/POST/PUT/DELETE |
| Endpoint | Flask endpoint name (input cho `url_for`) |
| Handler | Function name |
| File:Line | Vi tri code |
| Pattern | `@app.route` \| `register` \| `blueprint` |
| Domain | Phase 1 domain group |
| Risk | P0 \| P1 \| P2 |
| Auth | `none` \| `login_required` \| `admin_required` \| `permission_required:<name>` |
| Audit | Y \| N (co goi `log_*` khong) |
| HasTest | Y \| N \| partial |

## Risk tier

```
P0 = auth, admin, session/token/password, DB write, file write/delete,
     backup create/restore, bulk update/export sensitive data
P1 = read API co contract ro, admin read/write read-back,
     route du lieu quan trong nhung blast radius vua
P2 = health, static-ish, debug/internal, utility low-risk
```

## TODO: fill table (Step 3)

Lay danh sach tu:

```powershell
python scripts/list_routes.py > docs/refactor/_routes_raw.txt
```

Sau do nhom theo file (app.py / admin_routes.py / blueprints/* / marriage_api.py) va dien risk tier.

## App.py routes (@app.route) — count: ~18

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/stats | GET | TBD | TBD | app.py:1263 | @app.route | infra | TBD | TBD | TBD | TBD |
| /api/admin/users | GET,POST | TBD | TBD | app.py:1287 | @app.route | admin_users | P0 | admin_required | Y | TBD |
| /api/admin/users/<int:user_id> | GET,PUT,DELETE | TBD | TBD | app.py:1338 | @app.route | admin_users | P0 | admin_required | Y | TBD |
| /api/admin/verify-password | POST | TBD | TBD | app.py:1413 | @app.route | admin_auth | P0 | admin_required | TBD | TBD |
| /api/admin/activity-logs | GET | TBD | TBD | app.py:1434 | @app.route | admin_logs | P1 | admin_required | TBD | TBD |
| /api/admin/reset-logs | POST | TBD | TBD | app.py:1534 | @app.route | admin_logs | P0 | admin_required | Y | TBD |
| /api/admin/code-graph/rescan | POST | TBD | TBD | app.py:1584 | @app.route | admin_dashboard | P1 | admin_required | TBD | TBD |
| /api/admin/backup | POST | TBD | TBD | app.py:1614 | @app.route | admin_backup_create | P0 | admin_required | Y | TBD |
| /api/admin/backups | GET | TBD | TBD | app.py:1619 | @app.route | admin_backup_read | P0 | admin_required | TBD | TBD |
| /api/admin/backup/<filename> | GET | TBD | TBD | app.py:1624 | @app.route | admin_backup_read | P0 | admin_required | TBD | TBD |
| /api/health | GET | TBD | TBD | app.py:1629 | @app.route | infra | P2 | none | N | Y |
| /api/external-posts | GET | TBD | TBD | app.py:1687 | @app.route | infra | P2 | none | N | TBD |
| /api/external-posts/clear-cache | POST | TBD | TBD | app.py:1721 | @app.route | infra | P1 | token | N | TBD |
| /api/external-posts/refresh | GET,POST | TBD | TBD | app.py:1731 | @app.route | infra | P1 | token | N | TBD |
| /api/stats/members | GET | TBD | TBD | app.py:1759 | @app.route | members | P1 | TBD | N | TBD |

## admin_routes.py routes (register pattern) — count: ~30

Source: `register_admin_routes(app)` in admin_routes.py.

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /admin/login | GET,POST | admin_login | admin_login | admin_routes.py:49 | register | admin_login_logout | P0 | none | Y | partial |
| /admin/logout | GET | admin_logout | admin_logout | admin_routes.py:171 | register | admin_login_logout | P0 | login_required | Y | TBD |
| /admin/dashboard | GET | admin_dashboard | admin_dashboard | admin_routes.py:178 | register | admin_dashboard | P1 | admin_required | TBD | TBD |
| ... (TODO: fill 27 routes con lai) | | | | | | | | | | |

## blueprints/* routes — count: ~47

Tach theo blueprint file.

### blueprints/main.py (5 routes)

| URL | Method | Endpoint | Handler | File:Line | Domain | Risk |
|---|---|---|---|---|---|---|
| / | GET | TBD | TBD | blueprints/main.py:13 | public | P1 |
| /api/genealogy/verify-passphrase | POST | TBD | TBD | blueprints/main.py:22 | members_gate | P0 |
| /genealogy | GET | TBD | TBD | blueprints/main.py:38 | public | P1 |
| /contact | GET | TBD | TBD | blueprints/main.py:49 | public | P2 |
| /documents | GET | TBD | TBD | blueprints/main.py:58 | public | P2 |
| /privacy | GET | TBD | TBD | blueprints/main.py:67 | public | P2 |

### blueprints/auth.py (5 routes)

### blueprints/activities.py (7 routes)

### blueprints/family_tree.py (8 routes)

### blueprints/persons.py (10 routes)

### blueprints/members_portal.py (8 routes)

### blueprints/gallery.py (16 routes)

### blueprints/admin.py (1 route)

## marriage_api.py routes — count: TBD

Source: `register_marriage_routes(app)` in marriage_api.py.

## Total: ~95 routes (TBD verify by `scripts/list_routes.py`)

## Gap / chua xac dinh

- Endpoint name chua dien cho hau het — fill o Step 3
- Auth/Audit/HasTest cot chua dien — fill o Step 3
- Domain assignment cho cac blueprint route — fill o Step 3
