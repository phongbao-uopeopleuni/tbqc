# Incident Templates

> Dung file nay lam khuon khi can ghi incident hoac rollback trong refactor.

## File naming

`YYYY-MM-DD-short-desc.md`

Vi du: `2026-05-21-phase-1-admin-login-rollback.md`

## Template

```markdown
# Incident YYYY-MM-DD: <short-desc>

## Timeline
- HH:MM Deploy SHA xxxxxxx
- HH:MM Symptom phat hien: ...
- HH:MM Revert quyet dinh
- HH:MM Revert deploy SHA yyyyyyy live
- HH:MM Smoke pass, service on dinh

## Symptom quan sat
- ...

## SHA truoc / sau revert
- Pre: xxxxxxx (broken)
- Post: yyyyyyy (= SHA truoc deploy)

## Root cause (sau khi tim ra)
- ...

## Fix (ke hoach re-attempt PR)
- ...

## Prevention (cap nhat plan/test de tranh tai phat)
- ...

## Evidence files
- Railway log dump: logs/incident-<date>.txt
- /api/health response truoc/sau: ...
- Baseline compare output: ...
```
