# CLAUDE.md

Hướng dẫn hành vi khi code trong repo **tbqc** (Flask, Jinja, static JS/CSS, pytest). Nội dung dưới đây kết hợp [Karpathy-inspired guidelines](https://github.com/forrestchang/andrej-karpathy-skills) với bối cảnh project.

## Project (tbqc)

- Giữ pattern hiện có: blueprints, services, `utils/`, templates, `tests/` với `pytest`.
- Trước khi đổi hành vi: xem test liên quan trong `tests/`; ưu tiên thêm/sửa test khi sửa bug hoặc logic quan trọng.
- Không commit secret; tham chiếu `.env.example` và các script kiểm tra trong `scripts/`.

### Frontend lint (static/js/**)

- Dev-only: `package.json` + `eslint.config.js` + `.prettierrc.json` chỉ dùng cho local/CI, không ship runtime.
- Câu lệnh thường dùng:
  - `npm run lint` — ESLint strict (fail nếu có lỗi bug: `no-redeclare`, `no-dupe-*`, `no-unreachable`, `no-undef`…).
  - `npm run lint:fix` — sửa tự động phần fixable.
  - `npm run format:check` / `npm run format:write` — Prettier.
- CI: `.github/workflows/lint-js.yml` chạy khi PR/push đụng `static/js/**` hoặc config. ESLint strict; Prettier informational (`continue-on-error: true`).
- Khi thêm global mới (biến/hàm dùng chéo file hoặc từ inline `<script>` trong template), khai báo vào `globals` trong `eslint.config.js` để `no-undef` không báo false positive.

---

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
