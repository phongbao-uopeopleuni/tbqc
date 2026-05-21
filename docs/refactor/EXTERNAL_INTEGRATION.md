# External Integration Inventory

> Inventory cac integration vuot ra ngoai process Flask. Muc tieu: khong vo tinh doi contract khi refactor.

## Status

- **Updated:** 2026-05-21
- **Scope:** code inventory + user-confirmed production sign-off cho Phase 0d
- **Operational sign-off:** user xac nhan production hien tai khong co cron, webhook, consumer, hoac external caller dac biet nao ngoai inventory ben duoi

## Outbound calls confirmed tu code

| Type | Source | Target | Current contract | Evidence |
|---|---|---|---|---|
| RSS fetch | `GET /api/external-posts`, `GET /api/external-posts-live` | `https://nguyenphuoctoc.info/rss/hoat-dong-hoi-dong-npt-vn/` | Read-only HTTP GET, timeout 30s, custom User-Agent `PhongTuyBienQuanCong/1.0` | `app.py` `NPT_COUNCIL_RSS_URL`, `_fetch_npt_council_rss()` |
| Self-call sync source | `POST /api/genealogy/sync` | `https://www.phongtuybienquancong.info/api/members` | Read-only HTTP GET, timeout 60s, JSON contract phai la list hoac `{success,data}` | `app.py` `sync_genealogy_from_members()` |

## Browser/client-facing integrations

| Type | Entry point | External dependency | Current contract | Evidence |
|---|---|---|---|---|
| Map key bootstrap | `GET /api/geoapify-key` | `api.geoapify.com` duoc browser goi sau khi nhan key | Server chi phat hanh API key; front-end map contract khong duoc doi path | `blueprints/gallery.py:get_geoapify_api_key` |
| Social/SEO crawler | `/`, `/static/images/<path>`, `/images/<path>` | Facebook, Zalo, search crawler cache URL public | Public URL contract frozen; neu doi phai co PR `[chore]` + redirect | `FROZEN_FILE_POLICY.md`, plan §21.4 |

## Platform integrations

| Type | Producer | Target | Current contract | Evidence |
|---|---|---|---|---|
| Healthcheck | Railway | `GET /api/health` | Path va JSON shape la runtime contract | `BOOTSTRAP_TRUTH.md`, `FROZEN_FILE_POLICY.md` |
| Deployment logs / metrics | Railway | service stdout/stderr + HTTP logs | Dung cho incident forensics; retention da verify la `Hobby / 7 days` | `BOOTSTRAP_TRUTH.md` |

## Verification outcome

1. Workspace plan/log retention da verify tren Railway dashboard: `Hobby`, `7-Day Log History`.
2. User da xac nhan production hien tai khong co webhook, cron, consumer, hoac external integration nao khac ngoai inventory code-level trong file nay.
3. Access-log crawler user-agent chi tiet chua duoc snapshot trong repo, nhung khong phat hien them runtime contract nao can freeze ngoai danh sach hien tai.

## Refactor rules

1. KHONG doi path public da freeze trong `FROZEN_FILE_POLICY.md`.
2. KHONG doi shape `/api/health`.
3. KHONG doi JSON shape cua `/api/members` neu chua co PR `[chore]` rieng, vi `/api/genealogy/sync` dang phu thuoc.
4. Neu them integration moi, cap nhat file nay trong cung PR.
