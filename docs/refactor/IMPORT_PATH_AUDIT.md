# Import Path Audit

> Liet ke tat ca import fallback `try: from folder_py.<mod> / except ImportError: from <mod>`.
> Muc tieu Phase 0c: chuan hoa ve 1 canonical path moi nhom (5 nhom PR `[fix]` rieng).

## Pattern can chuan hoa

```python
try:
    from folder_py.X import ...
except ImportError:
    from X import ...
```

Hoac voi `sys.path` hack:

```python
try:
    from folder_py.X import ...
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
    from X import ...
```

Risk R1: 1 trong 2 branch sai/move se duoc fallback im lang -> bug an.

## Evidence command (re-run de update)

```powershell
rg -n "except ImportError|from folder_py|sys\.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py blueprints folder_py
```

Output truoc Phase 0c: TBD (run + paste ket qua o Step 7)

## Nhom PR `[fix]` (theo plan §6)

### Nhom 1: db_config

| File | Line | Module bi fallback | Status |
|---|---|---|---|
| app.py | ~33 | folder_py.db_config | open |
| app.py | ~58 | folder_py.db_config | open |
| admin_routes.py | ~29 | folder_py.db_config | open |
| audit_log.py | ~41 | folder_py.db_config | open |
| marriage_api.py | ~11 | folder_py.db_config | open |
| db.py | ~7 | folder_py.db_config | open |
| auth.py | ~60 | folder_py.db_config | open |

**Action**: canonical = `folder_py.db_config`. Xoa branch `except ImportError`.

### Nhom 2: genealogy_tree

| File | Line | Module bi fallback | Status |
|---|---|---|---|
| app.py | ~487-501 | folder_py.genealogy_tree | open |

**Action**: canonical = `folder_py.genealogy_tree`. Xoa sys.path hack.

### Nhom 3: admin_routes

| File | Line | Module bi fallback | Status |
|---|---|---|---|
| app.py | ~164-170 | folder_py.admin_routes (khong ton tai) | open |

**Action**: canonical = `admin_routes` (root). Xoa folder_py fallback.

### Nhom 4: marriage_api

| File | Line | Module bi fallback | Status |
|---|---|---|---|
| app.py | ~190-197 | folder_py.marriage_api (khong ton tai) | open |

**Action**: canonical = `marriage_api` (root).

### Nhom 5: auth

| File | Line | Module bi fallback | Status |
|---|---|---|---|
| app.py | ~140-146 | folder_py.auth (khong ton tai) | open |

**Action**: canonical = `auth` (root).

## Quy tac PR cho moi nhom

1. **Mot nhom = mot PR `[fix]` rieng.** Khong gop.
2. Sau moi PR: `pytest -x tests/` pass + `python -c "import app"` smoke + url_map snapshot pass.
3. Commit message format: `[fix] phase-0c: normalize import nhom <N> (<module>)`
4. Truoc PR: `IMPORT_PATH_AUDIT.md` status = `open`. Sau PR: `closed (SHA xxxxxxx)`.

## Acceptable exceptions

Neu fallback co ly do thuc te (vd: optional dependency, conditional import), giu lai NHUNG ghi vao `IMPORT_PATH_AUDIT.md` muc duoi:

```
| File | Line | Module | Reason | Approval |
|---|---|---|---|---|
| (TBD) | (TBD) | (TBD) | (vd: optional cache lib) | (TBD) |
```

Hien tai: chua co fallback nao co ly do chap nhan duoc (tat ca la copy-paste defensive).

## Verification sau Phase 0c

```powershell
# Phai khong con hit nao trong cac file da xu ly
rg -n "except ImportError|from folder_py|sys\.path" app.py admin_routes.py audit_log.py marriage_api.py db.py auth.py
```

Neu hit > 0: ghi vao Acceptable exceptions hoac mo PR `[fix]` moi.
