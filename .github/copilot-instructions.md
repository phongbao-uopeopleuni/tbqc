# TBQC Gia Pha — GitHub Copilot Instructions

## Project Overview
Flask web app for managing a Vietnamese royal family tree (Nguyen Phuoc Toc).
Backend: Python 3 + Flask. Database: MySQL. Deploy: Render/Railway.

## Project Structure
- `app.py` — Single entry point. Run from repo root: `python app.py`
- `blueprints/` — Flask blueprints: main, auth, activities, family_tree, persons, members_portal, gallery, admin
- `folder_py/` — Utility modules: db_config, genealogy_tree. NOT an entry point.
- `templates/` — Jinja2 HTML templates
- `static/` — CSS (`static/css/`), JS, images (`static/images/`)
- `scripts/` — Dev/ops utilities

## Critical Rules

### Never do these
- Never hardcode secrets, DB credentials, API keys, or passwords in source code.
- Never run `python app.py` from `folder_py/` — always from repo root.
- Never commit `.env`, `*.env`, `folder_sql/`, `tailieu/`, `backups/`, `*.sql`, `*.csv`.
- Never store plaintext passwords — use `bcrypt`.

### Environment Variables (`.env` or platform dashboard)
`SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`,
`MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD`, `GEOAPIFY_API_KEY`

### Database
- MySQL via `mysql-connector-python`.
- Import connection config: `from folder_py.db_config import get_db_config`
- Always use parameterized queries (`%s` placeholders) — no string formatting in SQL.

### Security Requirements
- Parameterized SQL queries only (prevent SQL injection).
- Jinja2 auto-escaping active — don't use `| safe` on user input.
- `bcrypt` for all password hashing.
- Rate limiting (`Flask-Limiter`) on auth/sensitive endpoints.
- CORS restricted to known origins.

### Code Style
- Python 3, PEP 8.
- Keep each blueprint focused on one feature area.
- Vietnamese comments/strings are acceptable throughout the codebase.
- Minimal changes — avoid refactoring beyond what is asked.

### Dependencies
flask, flask-cors, mysql-connector-python, bcrypt, flask-login, gunicorn,
requests, beautifulsoup4, lxml, Pillow, openai, anthropic, flask-wtf,
Flask-Limiter, Flask-Caching, python-dotenv, pandas, openpyxl

## Debugging Tips
- Health endpoint: `GET /api/health` — check `blueprints_registered` field.
- Startup log "OK: Da dang ky Flask Blueprints." = all blueprints loaded.
- 404 on `/genealogy`, `/members` after deploy = wrong working directory or Start Command.
