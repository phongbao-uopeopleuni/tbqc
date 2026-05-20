# Frozen File Policy

> Cac file/URL khong duoc move/rename/delete trong giai doan refactor. Vi pham = block PR.

## Frozen files (core)

```
app.py
admin_routes.py
admin_templates.py
marriage_api.py
extensions.py
config.py
auth.py
audit_log.py
db.py
folder_py/db_config.py
folder_py/genealogy_tree.py
blueprints/__init__.py
Procfile
render.yaml
instance/secret_key
tests/conftest.py
```

Quy tac: Phase 1+ co the **noi dung** cua file frozen (tach code ra module moi), nhung **vi tri** + **ten** file phai giu nguyen. File cu tro thanh facade re-export.

## Frozen public URL

Doi tac ngoai (browser, crawler, CDN, self-call) da cache hoac hardcode cac path nay:

```
/                              # Trang chu + SEO
/api/health                    # Railway healthcheck (doi shape = restart loop)
/api/members                   # Self-call tu /api/genealogy/sync (app.py L520)
/api/persons                   # Public read
/api/family-tree               # Public read
/api/tree                      # Public read
/api/grave-search              # Gallery search
/api/geoapify-key              # Map widget
/family-tree-core.js           # Template /genealogy load truc tiep
/family-tree-ui.js             # Template /genealogy load truc tiep
/genealogy-lineage.js          # Template / load truc tiep
/static/images/<path>          # Anh hien tren index + crawler social
/images/<path>                 # Alias /static/images
/static/js/*                   # Tat ca JS template reference truc tiep
```

Doi URL = PR `[chore]` rieng voi:
1. 301 redirect tu URL cu
2. Thong bao 24h truoc maintenance
3. Update tat ca template reference trong cung PR

## Rebase + conflict policy

- Refactor branch rebase master moi tuan.
- KHONG merge master vao refactor branch (gay merge commit).
- Neu feature PR cham domain dang refactor: cho refactor PR merge xong, feature owner rebase.
- Hot-fix production luon uu tien hon refactor; refactor branch tu rebase sau hotfix.
- Refactor owner xu ly conflict frozen file; khong nguoi khac tu y unfreeze.

## Initial frozen domain (Phase 1 thu tu)

```
1. admin_login_logout       (P0-auth)
2. admin_dashboard          (P1-read)
3. admin_logs               (P1/P0)
4. admin_data_management    (P1-read)
5. admin_requests           (P0-mutation)
6. admin_users              (P0-mutation+audit)
7. admin_csv                (P0-filesystem)
8. admin_members            (P0-mutation+audit)
9. admin_backup_read        (P0-sensitive)
10. admin_backup_create     (P0-filesystem+audit)
```

Trong Phase 1, mot luc CHI mot domain duoc unfreeze. Cac domain con lai van frozen.

## .gitignore enforcement

```
instance/secret_key
.db_resolved.json
.env
tbqc_db.env
*.pyc
__pycache__/
.pytest_cache/
```

Verify: `Get-Content .gitignore` truoc khi mo PR Phase 0a.
