# INCIDENT LOG - TBQC

> **Muc dich:** Ghi lai su co, hotfix, rollback, va secret rotation co gia tri van hanh.  
> **Audience:** maintainers, operators, reviewers.  
> **Cap nhat lan cuoi:** 2026-05-27  
> **Canonical:** yes

File nay la noi ghi nhan su kien van hanh. Khong dung `docs/ai/memory/ai-project-memory.md` cho muc dich nay.

---

## Khi nao phai ghi vao file nay

Ghi mot entry moi khi co it nhat mot trong cac truong hop sau:

- su co production hoac staging dang active
- hotfix da triage hoac da ship
- rollback code hoac rollback database
- rotate secret vi nghi ngo hoac theo quy trinh
- DB change khan cap can giai trinh de maintainer sau co the lan theo

Khong ghi:

- bug nho chua thanh incident
- ghi chu brainstorming
- lich su refactor thong thuong

---

## Quy tac ghi

1. Ghi ngan, co the hanh dong duoc.
2. Khong ghi gia tri secret, password, token, passphrase, connection string day du.
3. Neu thay doi da ship va anh huong hanh vi release, cap nhat them `docs/releases/changelog.md`.
4. Neu day la chi tiet refactor workstream, cap nhat them `docs/refactor/`.

---

## Mau entry

```md
## YYYY-MM-DD - [P1|P2|P3|P4] Tieu de ngan

- Status: open | mitigated | fixed | monitoring
- Scope: production | staging | local
- Trigger: deploy | config | DB | secret rotation | external dependency | unknown
- Symptoms:
  - ...
- First detection:
  - ...
- Root cause:
  - ...
- Mitigation / fix:
  - ...
- Files or systems touched:
  - ...
- Verification:
  - ...
- Follow-up:
  - ...
```

---

## Entries

Them entry moi len tren cung.
