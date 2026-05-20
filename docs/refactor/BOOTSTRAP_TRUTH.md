# Bootstrap Truth (frozen)

> Production runtime hien tai. **Khong duoc doi trong refactor**.

## Production runtime (verified 2026-05-20)

- **Platform**: Railway
- **Entry**: Procfile (`gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50`)
- **Module entry**: `app.py` tai repo root, bien module-level `app`
- **Verified bang**: `curl -fsS https://www.phongtuybienquancong.info/api/health` -> HTTP 200, 333ms
- **Evidence**: Response header `x-railway-edge`, body `{"server":"ok","database":"connected","blueprints_registered":true,"stats":{"persons_count":1188,"relationships_count":1611}}`
- **render.yaml**: Render fallback, startCommand da align voi Procfile tu commit `4365b79`

## Persistence

- `instance/secret_key`: file local, persistent qua restart, dam bao session continuity. Khong duoc xoa/doi vi tri.
- `.db_resolved.json`: file cache cross-process tu `folder_py/db_config.py`. KHONG commit. Test conftest phai xoa fixture nay.

## Frozen rules trong refactor

1. KHONG doi sang `create_app()` factory.
2. KHONG doi entry command tren Procfile.
3. KHONG doi vi tri `instance/secret_key`.
4. render.yaml chi la Render fallback, phai khop Procfile.
5. Thu tu init trong app.py: `Config.init_app(app)` -> `init_extensions(app)` -> error hardening -> `init_login_manager(app)` -> `register_blueprints(app)` -> `register_admin_routes(app)` -> `register_marriage_routes(app)` -> `register_page_views(app)`. Khong doi thu tu.

## Local dev env (tu pre-flight 2026-05-20)

- Python: **3.13.5** (newer than Railway likely 3.11.x)
- Node: **24.12.0** (newer than Railway LTS 18.x)
- pytest baseline: **232 passed, 3 skipped** (test_api_routes 2 skip optional, test_mysql_auth chmod-Windows skip)
- npm run lint baseline: **0 errors, 71 warnings** (all `no-unused-vars`)

## TODO trong Phase 0a

- [ ] Verify Railway image Python version chinh xac (Railway dashboard hoac `python --version` trong build log)
- [ ] Verify Railway image Node version (neu Railway build front-end)
- [ ] Verify Railway log retention (free vs paid plan: 3 hoac 30 ngay)
- [ ] Verify Railway healthcheck path = `/api/health` (Railway dashboard)

## Re-validate khi nao

- Sau khi doi infra (Railway plan, gunicorn version, Python version)
- Sau khi doi entrypoint co chu dich (PR `[chore]` rieng)
