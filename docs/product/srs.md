# SRS â€” Äáº·c táº£ yÃªu cáº§u pháº§n má»m há»‡ thá»‘ng Gia pháº£ TBQC

> **Software Requirements Specification** cho dá»± Ã¡n `tbqc` (Flask + MySQL).
> PhiÃªn báº£n: 1.0 â€” Cáº­p nháº­t: 2026-04-21.
> TÃ i liá»‡u nÃ y tuÃ¢n theo khung IEEE-830 vÃ  Ã¡p dá»¥ng cÃ¡c nguyÃªn táº¯c Requirements Engineering: Elicitation, Analysis, Specification, Validation & Verification, Use Case Modeling.

---

## Má»¥c lá»¥c

1. [Giá»›i thiá»‡u](#1-giá»›i-thiá»‡u)
2. [MÃ´ táº£ chung](#2-mÃ´-táº£-chung)
3. [Ká»¹ thuáº­t thu tháº­p yÃªu cáº§u (Elicitation)](#3-ká»¹-thuáº­t-thu-tháº­p-yÃªu-cáº§u-elicitation)
4. [YÃªu cáº§u chá»©c nÄƒng (Functional Requirements)](#4-yÃªu-cáº§u-chá»©c-nÄƒng-functional-requirements)
5. [YÃªu cáº§u phi chá»©c nÄƒng (Non-Functional Requirements)](#5-yÃªu-cáº§u-phi-chá»©c-nÄƒng-non-functional-requirements)
6. [Use Case Modeling & UML](#6-use-case-modeling--uml)
7. [MÃ´ hÃ¬nh dá»¯ liá»‡u](#7-mÃ´-hÃ¬nh-dá»¯-liá»‡u)
8. [Kiáº¿n trÃºc triá»ƒn khai & váº­n hÃ nh](#8-kiáº¿n-trÃºc-triá»ƒn-khai--váº­n-hÃ nh)
9. [Validation & Verification](#9-validation--verification)
10. [Ma tráº­n truy váº¿t yÃªu cáº§u (Traceability Matrix)](#10-ma-tráº­n-truy-váº¿t-yÃªu-cáº§u-traceability-matrix)
11. [Phá»¥ lá»¥c](#11-phá»¥-lá»¥c)

---

## 1. Giá»›i thiá»‡u

### 1.1. Má»¥c Ä‘Ã­ch

TÃ i liá»‡u nÃ y Ä‘áº·c táº£ chi tiáº¿t cÃ¡c yÃªu cáº§u chá»©c nÄƒng, phi chá»©c nÄƒng, vÃ  quy táº¯c váº­n hÃ nh cá»§a **há»‡ thá»‘ng Gia pháº£ TBQC** â€” má»™t á»©ng dá»¥ng web phá»¥c vá»¥ quáº£n lÃ½, tra cá»©u vÃ  chia sáº» thÃ´ng tin dÃ²ng há», bao gá»“m cÃ¢y gia pháº£ tÆ°Æ¡ng tÃ¡c, cá»•ng thÃ nh viÃªn, quáº£n trá»‹, tÃ i liá»‡u, hoáº¡t Ä‘á»™ng vÃ  báº£n Ä‘á»“ má»™ pháº§n.

TÃ i liá»‡u hÆ°á»›ng Ä‘áº¿n:

- **Developer / Maintainer** â€” lÃ m cÄƒn cá»© thiáº¿t káº¿, hiá»‡n thá»±c vÃ  kiá»ƒm thá»­.
- **QA / Tester** â€” lÃ m cÄƒn cá»© xÃ¢y dá»±ng test case vÃ  ká»‹ch báº£n nghiá»‡m thu.
- **Admin / Ban gia pháº£** â€” hiá»ƒu luá»“ng nghiá»‡p vá»¥ Ä‘á»ƒ váº­n hÃ nh Ä‘Ãºng quy trÃ¬nh.
- **Stakeholder** (trÆ°á»Ÿng tá»™c, thÃ nh viÃªn dÃ²ng há») â€” xÃ¡c nháº­n há»‡ thá»‘ng Ä‘Ã¡p á»©ng nhu cáº§u.

### 1.2. Pháº¡m vi

Há»‡ thá»‘ng **tbqc** (Tá»™c BÃ¹i Quang ChÃ­nh â€” vÃ­ dá»¥) cung cáº¥p:

- CÃ¢y gia pháº£ tÆ°Æ¡ng tÃ¡c nhiá»u Ä‘á»i, Ä‘a cháº¿ Ä‘á»™ xem (cÃ¢y, danh sÃ¡ch Ä‘a cáº¥p, mindmap).
- Cá»•ng Ä‘Äƒng nháº­p thÃ nh viÃªn (passphrase) vá»›i quyá»n xem, xuáº¥t Excel, Ä‘á» xuáº¥t chá»‰nh sá»­a.
- Báº£ng quáº£n trá»‹ cho admin: CRUD ngÆ°á»i, duyá»‡t yÃªu cáº§u sá»­a, backup DB, Ä‘á»“ng bá»™ tÃ i khoáº£n.
- Module má»™ pháº§n vá»›i báº£n Ä‘á»“ (Geoapify) vÃ  áº£nh.
- Module hoáº¡t Ä‘á»™ng/tin tá»©c vÃ  quáº£n lÃ½ tÃ i liá»‡u.

### 1.3. Thuáº­t ngá»¯ vÃ  viáº¿t táº¯t

| Thuáº­t ngá»¯ | Ã nghÄ©a |
|-----------|---------|
| SRS | Software Requirements Specification |
| FR | Functional Requirement â€” yÃªu cáº§u chá»©c nÄƒng |
| NFR | Non-Functional Requirement â€” yÃªu cáº§u phi chá»©c nÄƒng |
| UC | Use Case |
| V&V | Validation & Verification |
| RBAC | Role-Based Access Control â€” phÃ¢n quyá»n theo vai trÃ² |
| PII | Personally Identifiable Information â€” thÃ´ng tin Ä‘á»‹nh danh cÃ¡ nhÃ¢n |
| Person | Má»™t cÃ¡ nhÃ¢n trong gia pháº£ (báº£ng `persons`) |
| Generation | Äá»i (tháº¿ há»‡), cá»™t `generation_level` |
| Branch | NhÃ¡nh cá»§a dÃ²ng há» (báº£ng `branches`) |
| Passphrase | Chuá»—i bÃ­ máº­t dÃ¹ng Ä‘á»ƒ vÃ o cá»•ng members/genealogy |

### 1.4. TÃ i liá»‡u tham chiáº¿u

- `docs/operations/runbook.md` â€” HÆ°á»›ng dáº«n developer, cáº¥u hÃ¬nh, deploy.
- `CLAUDE.md` â€” Quy Æ°á»›c phÃ¡t triá»ƒn.
- `docs/qa/genealogy-qa-checklist.md` â€” Checklist kiá»ƒm thá»­ há»“i quy.
- `docs/product/rollout/genealogy-rollout.md` â€” Káº¿ hoáº¡ch triá»ƒn khai theo giai Ä‘oáº¡n.
- `folder_sql/reset_schema_tbqc.sql` â€” Schema dá»¯ liá»‡u chuáº©n.
- `.env.example` â€” Máº«u biáº¿n mÃ´i trÆ°á»ng.

---

## 2. MÃ´ táº£ chung

### 2.1. Bá»‘i cáº£nh sáº£n pháº©m

TrÆ°á»›c khi sá»‘ hÃ³a, thÃ´ng tin dÃ²ng há» Ä‘Æ°á»£c lÆ°u trong sá»• giáº¥y vÃ  file Excel rá»i ráº¡c, gÃ¢y khÃ³ khÄƒn khi tra cá»©u tá»• tiÃªn/háº­u duá»‡, cáº­p nháº­t thÃ nh viÃªn má»›i, quáº£n lÃ½ má»™ pháº§n, vÃ  báº£o toÃ n dá»¯ liá»‡u qua thá»i gian. Há»‡ thá»‘ng Gia pháº£ TBQC thay tháº¿ cÃ¡c nguá»“n rá»i ráº¡c Ä‘Ã³ báº±ng má»™t ná»n táº£ng web táº­p trung, truy cáº­p Ä‘Æ°á»£c qua internet, cÃ³ phÃ¢n quyá»n, cÃ³ audit log vÃ  cÃ³ cÆ¡ cháº¿ backup.

### 2.2. CÃ¡c nhÃ³m ngÆ°á»i dÃ¹ng (Actors)

| Actor | MÃ´ táº£ | CÃ¡ch truy cáº­p |
|-------|-------|---------------|
| **Guest** (KhÃ¡ch) | ChÆ°a Ä‘Äƒng nháº­p | Xem trang chá»§, hoáº¡t Ä‘á»™ng, tÃ i liá»‡u cÃ´ng khai |
| **Member** (ThÃ nh viÃªn) | NgÆ°á»i trong dÃ²ng há», cÃ³ passphrase | Cá»•ng `/members`, cÃ¢y gia pháº£ Ä‘áº§y Ä‘á»§, xuáº¥t Excel, gá»­i yÃªu cáº§u sá»­a |
| **Editor** (Cá»™ng tÃ¡c) | Member Ä‘Æ°á»£c cáº¥p quyá»n Ä‘Äƒng bÃ i | ÄÄƒng hoáº¡t Ä‘á»™ng/tin tá»©c qua `/editor` |
| **Admin** | Quáº£n trá»‹ há»‡ thá»‘ng | ToÃ n bá»™ `/admin/*`, CRUD, backup, duyá»‡t yÃªu cáº§u |
| **System/Cron** | TÃ¡c vá»¥ ná»n | Backup Ä‘á»‹nh ká»³, cache refresh |

### 2.3. Giáº£ Ä‘á»‹nh vÃ  rÃ ng buá»™c

- MySQL 8.x, Python 3.11+.
- Triá»ƒn khai trÃªn ná»n táº£ng há»— trá»£ biáº¿n mÃ´i trÆ°á»ng vÃ  volume persistent (Railway, VPS, â€¦).
- Dá»¯ liá»‡u gia pháº£ lÃ  **PII** â€” khÃ´ng Ä‘Æ°á»£c cÃ´ng khai toÃ n bá»™ khi chÆ°a xÃ¡c thá»±c.
- NgÃ´n ngá»¯ chÃ­nh: tiáº¿ng Viá»‡t (UTF-8, `utf8mb4_unicode_ci`).
- Há»‡ thá»‘ng sá»­ dá»¥ng má»™t database MySQL duy nháº¥t; khÃ´ng cÃ³ sharding trong giai Ä‘oáº¡n hiá»‡n táº¡i.

---

## 3. Ká»¹ thuáº­t thu tháº­p yÃªu cáº§u (Elicitation)

CÃ¡c ká»¹ thuáº­t Ä‘Ã£ Ä‘Æ°á»£c Ã¡p dá»¥ng Ä‘á»ƒ láº­p ra báº£n SRS nÃ y:

| Ká»¹ thuáº­t | Stakeholder | Káº¿t quáº£ Ä‘áº§u ra |
|---|---|---|
| **Interview** 1-1 | TrÆ°á»Ÿng tá»™c | Quy táº¯c Ä‘á»i/nhÃ¡nh, quy táº¯c hÃ´n nhÃ¢n (cÃ³ nhiá»u vá»£/chá»“ng), quyá»n xem nháº¡y cáº£m |
| **Document analysis** | Ban gia pháº£ | 3 CSV gá»‘c (`person.csv`, `father_mother.csv`, `spouse_sibling_children.csv`) â†’ schema `persons`, `relationships`, `marriages` |
| **Workshop** | Ban gia pháº£ + Dev | Thá»‘ng nháº¥t cháº¿ Ä‘á»™ xem (cÃ¢y/danh sÃ¡ch/mindmap), phÃ¢n loáº¡i nhÃ¡nh |
| **Observation** | ThÃ nh viÃªn cao tuá»•i | CÃ¡ch Ä‘á»c gia pháº£ truyá»n thá»‘ng â†’ chá»©c nÄƒng xem theo **Ä‘á»i** (`/api/generations`) |
| **Prototyping** | TrÆ°á»Ÿng tá»™c | áº¢nh `tree-default-view.png`, `tree-zoomed.png` Ä‘á»ƒ duyá»‡t phá»‘i cáº£nh |
| **Questionnaire** | ThÃ nh viÃªn | Nhu cáº§u tÃ¬m kiáº¿m, xuáº¥t Excel, cáº­p nháº­t thÃ´ng tin cÃ¡ nhÃ¢n |
| **Brainstorming** | Dev | Module má»™ pháº§n + Geoapify, module hoáº¡t Ä‘á»™ng, audit log |
| **Reverse engineering** | Dev | File Excel cÅ©, quyá»ƒn gia pháº£ giáº¥y â†’ sinh schema vÃ  quy táº¯c import |

**NguyÃªn táº¯c:** Má»i yÃªu cáº§u Ä‘Æ°á»£c liá»‡t kÃª trong tÃ i liá»‡u nÃ y pháº£i truy ngÆ°á»£c Ä‘Æ°á»£c vá» Ã­t nháº¥t má»™t nguá»“n elicitation á»Ÿ báº£ng trÃªn.

---

## 4. YÃªu cáº§u chá»©c nÄƒng (Functional Requirements)

YÃªu cáº§u chá»©c nÄƒng Ä‘Æ°á»£c Ä‘Ã¡nh mÃ£ `FR-<Module>-<Sá»‘>`. Má»—i FR cÃ³ **ID, mÃ´ táº£, actor, input, output, tiÃªu chÃ­ cháº¥p nháº­n**.

### 4.1. Module `main` â€” Trang cÃ´ng khai

| ID | MÃ´ táº£ | Actor | Endpoint / Nguá»“n | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-MAIN-01 | Hiá»ƒn thá»‹ trang chá»§ vá»›i giá»›i thiá»‡u dÃ²ng há» | Guest | `GET /` | Trang load < 2s; khÃ´ng yÃªu cáº§u Ä‘Äƒng nháº­p |
| FR-MAIN-02 | Hiá»ƒn thá»‹ trang Gia pháº£ vá»›i cá»•ng passphrase | Guest | `GET /genealogy` | Hiá»‡n form passphrase náº¿u chÆ°a cÃ³ session há»£p lá»‡ |
| FR-MAIN-03 | XÃ¡c thá»±c passphrase Ä‘á»ƒ má»Ÿ ná»™i dung gia pháº£ | Guest | `POST /api/genealogy/verify-passphrase` | Tráº£ `200 {ok: true}` náº¿u passphrase khá»›p `GENEALOGY_PASSPHRASES`; `401` náº¿u sai; rate-limit â‰¥ 5 láº§n sai trong 5 phÃºt |
| FR-MAIN-04 | Trang liÃªn há»‡ | Guest | `GET /contact` | Hiá»‡n form/thÃ´ng tin liÃªn há»‡ |
| FR-MAIN-05 | Trang tÃ i liá»‡u | Guest | `GET /documents` | Liá»‡t kÃª tÃ i liá»‡u cÃ´ng khai |

### 4.2. Module `auth` â€” XÃ¡c thá»±c

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-AUTH-01 | ÄÄƒng nháº­p báº±ng username + password | Admin/Editor | `POST /api/login` | So khá»›p `password_hash` báº£ng `users`; tráº£ cookie session |
| FR-AUTH-02 | ÄÄƒng xuáº¥t | Logged-in user | `POST /api/logout` | Há»§y session; chuyá»ƒn vá» `/` |
| FR-AUTH-03 | Láº¥y thÃ´ng tin ngÆ°á»i dÃ¹ng hiá»‡n táº¡i | Logged-in user | `GET /api/current-user` | Tráº£ `{username, role, full_name}` hoáº·c `401` |
| FR-AUTH-04 | Trang login UI | Guest | `GET /login`, `GET /admin/login-page` | Hiá»ƒn thá»‹ form |

### 4.3. Module `family_tree` â€” CÃ¢y gia pháº£

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-TREE-01 | Láº¥y toÃ n bá»™ dá»¯ liá»‡u cÃ¢y gia pháº£ | Member | `GET /api/family-tree` | JSON chá»©a táº¥t cáº£ person + quan há»‡ cha-máº¹-con |
| FR-TREE-02 | Láº¥y danh sÃ¡ch quan há»‡ cha-máº¹-con | Member | `GET /api/relationships` | Má»—i báº£n ghi cÃ³ `parent_id`, `child_id`, `relation_type` |
| FR-TREE-03 | Láº¥y danh sÃ¡ch con cá»§a má»™t ngÆ°á»i | Member | `GET /api/children/<parent_id>` | Chá»‰ tráº£ `child_id` cÃ³ `parent_id` match |
| FR-TREE-04 | Äá»“ng bá»™ láº¡i cÃ¢y tá»« dá»¯ liá»‡u nguá»“n | Admin | `POST /api/genealogy/sync` | Ghi audit log; cache invalidate |
| FR-TREE-05 | Xem cÃ¢y dáº¡ng thu gá»n/Ä‘áº§y Ä‘á»§ | Member | `GET /api/tree` | Tham sá»‘ Ä‘á»i tÃ¹y chá»n; tráº£ cáº¥u trÃºc lá»“ng |
| FR-TREE-06 | Liá»‡t kÃª tá»• tiÃªn cá»§a má»™t ngÆ°á»i | Member | `GET /api/ancestors/<id>` | Truy váº¿t ngÆ°á»£c `relationships` Ä‘áº¿n Ä‘á»i 1 |
| FR-TREE-07 | Liá»‡t kÃª háº­u duá»‡ cá»§a má»™t ngÆ°á»i | Member | `GET /api/descendants/<id>` | Truy váº¿t xuÃ´i Ä‘áº¿n lÃ¡ |
| FR-TREE-08 | Liá»‡t kÃª cÃ¡c Ä‘á»i (generations) | Member | `GET /api/generations` | Tráº£ sá»‘ Ä‘á»i, mÃ´ táº£, Ä‘áº¿m ngÆ°á»i má»—i Ä‘á»i |

### 4.4. Module `persons` â€” Há»“ sÆ¡ cÃ¡ nhÃ¢n

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-PERSON-01 | Danh sÃ¡ch táº¥t cáº£ ngÆ°á»i | Member | `GET /api/persons` | PhÃ¢n trang náº¿u > 500 báº£n ghi |
| FR-PERSON-02 | Chi tiáº¿t 1 ngÆ°á»i | Member | `GET /api/person/<id>` | Bao gá»“m cha/máº¹, vá»£/chá»“ng, con, má»™ pháº§n |
| FR-PERSON-03 | TÃ¬m kiáº¿m theo tÃªn/nÄƒm sinh | Member | `GET /api/search?q=` | Há»— trá»£ tiáº¿ng Viá»‡t cÃ³ dáº¥u/khÃ´ng dáº¥u; giá»›i háº¡n 50 káº¿t quáº£ |
| FR-PERSON-04 | Táº¡o person má»›i | Admin | `POST /api/persons` | Validate báº¯t buá»™c `full_name`; sinh `person_id` theo quy táº¯c `P-<gen>-<seq>` |
| FR-PERSON-05 | Sá»­a person | Admin | `PUT /api/person/<id>` | Ghi `updated_at`; ghi audit log |
| FR-PERSON-06 | XoÃ¡ person | Admin | `DELETE /api/person/<id>` | Cascade xoÃ¡ `relationships`, `marriages`; cáº£nh bÃ¡o náº¿u cÃ²n háº­u duá»‡ |
| FR-PERSON-07 | XoÃ¡ hÃ ng loáº¡t | Admin | `DELETE /api/persons/batch` | YÃªu cáº§u xÃ¡c nháº­n 2 bÆ°á»›c; audit log |
| FR-PERSON-08 | Gá»­i yÃªu cáº§u sá»­a thÃ´ng tin | Member/Guest | `POST /api/edit-requests` | Ghi vÃ o `edit_requests` vá»›i `status='pending'` |

### 4.5. Module `members_portal` â€” Cá»•ng thÃ nh viÃªn

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-MEM-01 | Trang cá»•ng thÃ nh viÃªn | Member | `GET /members` | Check session passphrase; náº¿u khÃ´ng cÃ³ â†’ form nháº­p |
| FR-MEM-02 | XÃ¡c thá»±c passphrase vÃ o cá»•ng | Guest | `POST /members/verify` | So vá»›i `MEMBERS_PASSWORD` hoáº·c `MEMBERS_FIXED_ACCOUNTS` |
| FR-MEM-03 | Danh sÃ¡ch thÃ nh viÃªn JSON (cÃ³ cache) | Member | `GET /api/members` | Cache tá»‘i thiá»ƒu 60s; invalidate khi admin sá»­a person |
| FR-MEM-04 | Xuáº¥t Excel danh sÃ¡ch thÃ nh viÃªn | Member | `GET /members/export/excel` | File `.xlsx` â‰¥ 1MB há»£p lá»‡; cÃ³ cá»™t Ä‘áº§y Ä‘á»§ |
| FR-MEM-05 | Cáº­p nháº­t nhÃ¡nh hÃ ng loáº¡t | Admin | `POST /api/members/bulk-update-branch` | Validate danh sÃ¡ch `person_id`; ghi audit |

### 4.6. Module `activities` â€” Hoáº¡t Ä‘á»™ng / Tin tá»©c

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-ACT-01 | Danh sÃ¡ch hoáº¡t Ä‘á»™ng | Guest | `GET /activities` | Chá»‰ hiá»‡n `status='published'`; phÃ¢n trang |
| FR-ACT-02 | Chi tiáº¿t hoáº¡t Ä‘á»™ng | Guest | `GET /activities/<id>` | 404 náº¿u `draft` vÃ  guest |
| FR-ACT-03 | TrÃ¬nh soáº¡n tháº£o | Editor | `GET /editor` | Check quyá»n Ä‘Äƒng |
| FR-ACT-04 | Kiá»ƒm tra quyá»n Ä‘Äƒng | Editor | `GET /api/activities/can-post` | Tráº£ `{can_post: bool, reason}` |
| FR-ACT-05 | Má»Ÿ quyá»n báº±ng máº­t kháº©u session | Editor | `POST /api/activities/post-login` | So vá»›i máº­t kháº©u cáº¥u hÃ¬nh |
| FR-ACT-06 | CRUD hoáº¡t Ä‘á»™ng | Editor/Admin | `GET/POST /api/activities`, `GET/PUT/DELETE /api/activities/<id>` | Kiá»ƒm quyá»n; audit log vá»›i thao tÃ¡c ghi |

### 4.7. Module `gallery` â€” áº¢nh vÃ  Má»™ pháº§n

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-GAL-01 | Láº¥y API key Geoapify an toÃ n | Member | `GET /api/geoapify-key` | Chá»‰ tráº£ khi cÃ³ session há»£p lá»‡ |
| FR-GAL-02 | Cáº­p nháº­t vá»‹ trÃ­ má»™ | Admin | `POST /api/grave/update-location` | LÆ°u vÃ o cá»™t `grave_location`; validate lat/lng |
| FR-GAL-03 | Upload áº£nh má»™ | Admin | `POST /api/grave/upload-image` | Accept jpg/png â‰¤ 10MB; lÆ°u vÃ o volume; path vÃ o `grave_image` |
| FR-GAL-04 | XoÃ¡ áº£nh má»™ | Admin | Tuá»³ endpoint cáº¥u hÃ¬nh | YÃªu cáº§u `GRAVE_IMAGE_DELETE_PASSWORD` |
| FR-GAL-05 | Phá»¥c vá»¥ áº£nh tÄ©nh | All | `GET /static/images/<path>`, `GET /images/<path>` | Cache-Control phÃ¹ há»£p; cháº·n directory traversal |
| FR-GAL-06 | CRUD album | Admin/Editor | `GET/POST /api/albums`, â€¦ | Máº­t kháº©u album (`ALBUM_PASSWORD`) náº¿u cáº¥u hÃ¬nh |

### 4.8. Module `admin` â€” Quáº£n trá»‹

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-ADM-01 | Äá»“ng bá»™ tÃ i khoáº£n tá»« env | Admin | `POST /api/admin/sync-tbqc-accounts` | Upsert `users` theo `MEMBERS_FIXED_ACCOUNTS` |
| FR-ADM-02 | Quáº£n lÃ½ users | Admin | `GET/POST /api/admin/users` | Táº¡o/sá»­a; lÆ°u `password_hash`; khÃ´ng lÆ°u plaintext |
| FR-ADM-03 | Backup DB thá»§ cÃ´ng | Admin | `POST /api/admin/backup` | Sinh file `.sql.gz` vÃ o `BACKUP_DIR`; Ä‘áº·t máº­t kháº©u báº±ng `BACKUP_PASSWORD` |
| FR-ADM-04 | Liá»‡t kÃª backup | Admin | `GET /api/admin/backups` | Danh sÃ¡ch file + kÃ­ch thÆ°á»›c + timestamp |
| FR-ADM-05 | Táº£i backup | Admin | `GET /api/admin/backup/<filename>` | Cháº·n path traversal; audit log |
| FR-ADM-06 | Duyá»‡t yÃªu cáº§u sá»­a | Admin | Cáº­p nháº­t `edit_requests.status` | `approved â†’ processed` khi Ã¡p dá»¥ng thay Ä‘á»•i |
| FR-ADM-07 | Trang dashboard | Admin | `GET /admin/dashboard` | Thá»‘ng kÃª tá»•ng quan (sá»‘ ngÆ°á»i, sá»‘ nhÃ¡nh, sá»‘ yÃªu cáº§u pending) |

### 4.9. Module `audit_log` â€” Nháº­t kÃ½

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-LOG-01 | Ghi nháº­t kÃ½ má»i thao tÃ¡c ghi dá»¯ liá»‡u | System | Ná»™i bá»™ (`audit_log.py`) | Má»—i action ghi: `user_id`, `action`, `target`, `timestamp`, `ip`, `details` |
| FR-LOG-02 | Xem nháº­t kÃ½ | Admin | `GET /admin/activity-logs` | Lá»c theo user/thá»i gian/loáº¡i hÃ nh Ä‘á»™ng |

### 4.10. Module `health` â€” Váº­n hÃ nh

| ID | MÃ´ táº£ | Actor | Endpoint | TiÃªu chÃ­ cháº¥p nháº­n |
|---|---|---|---|---|
| FR-HEALTH-01 | Kiá»ƒm tra sá»©c khoáº» há»‡ thá»‘ng | System | `GET /api/health` | Tráº£ `{status: ok, db: ok}`; 503 náº¿u DB fail |
| FR-HEALTH-02 | Thá»‘ng kÃª há»‡ thá»‘ng | Admin | `GET /api/stats` | Tá»•ng person, tá»•ng user, uptime |

---

## 5. YÃªu cáº§u phi chá»©c nÄƒng (Non-Functional Requirements)

MÃ£: `NFR-<Loáº¡i>-<Sá»‘>`. Má»—i NFR pháº£i **Ä‘o Ä‘Æ°á»£c**.

### 5.1. Performance

| ID | YÃªu cáº§u | NgÆ°á»¡ng Ä‘o |
|---|---|---|
| NFR-PERF-01 | Thá»i gian táº£i trang `/genealogy` láº§n Ä‘áº§u | p95 < 2.5s vá»›i máº¡ng 4G |
| NFR-PERF-02 | Thá»i gian pháº£n há»“i `/api/family-tree` | p95 < 800ms vá»›i 2000 person |
| NFR-PERF-03 | Thá»i gian pháº£n há»“i `/api/search` | p95 < 500ms |
| NFR-PERF-04 | Thá»i gian xuáº¥t Excel `/members/export/excel` | < 5s vá»›i 5000 báº£n ghi |
| NFR-PERF-05 | Cache `/api/members` | TTL â‰¥ 60s; invalidate < 5s sau thay Ä‘á»•i |

### 5.2. Scalability

| ID | YÃªu cáº§u | NgÆ°á»¡ng |
|---|---|---|
| NFR-SCALE-01 | Táº£i Ä‘á»“ng thá»i | â‰¥ 100 user concurrent khÃ´ng lá»—i 5xx |
| NFR-SCALE-02 | TÄƒng ngang | CÃ³ thá»ƒ cháº¡y nhiá»u worker Gunicorn khÃ´ng race condition |
| NFR-SCALE-03 | Dung lÆ°á»£ng dá»¯ liá»‡u | Há»— trá»£ â‰¥ 20,000 person khÃ´ng giáº£m hiá»‡u nÄƒng > 20% |

### 5.3. Security

| ID | YÃªu cáº§u | Minh chá»©ng |
|---|---|---|
| NFR-SEC-01 | KhÃ´ng hard-code secret | Táº¥t cáº£ secret Ä‘á»c tá»« `.env` / biáº¿n mÃ´i trÆ°á»ng |
| NFR-SEC-02 | Máº­t kháº©u lÆ°u dáº¡ng hash | Bcrypt/Argon2 trong cá»™t `password_hash` |
| NFR-SEC-03 | HTTPS end-to-end | Reverse proxy / CDN báº¯t buá»™c HTTPS trÃªn production |
| NFR-SEC-04 | CSRF | `flask-wtf` báº­t token cho form |
| NFR-SEC-05 | Rate limiting | `flask-limiter`: login â‰¤ 10/phÃºt/IP; passphrase â‰¤ 5/5 phÃºt/IP |
| NFR-SEC-06 | Cookie báº£o máº­t | `Secure`, `HttpOnly`, `SameSite=Lax` trÃªn production |
| NFR-SEC-07 | RBAC | Member â‰  Editor â‰  Admin; kiá»ƒm tra server-side, khÃ´ng tin client |
| NFR-SEC-08 | Cháº·n path traversal | áº¢nh/backup normalize path; whitelist thÆ° má»¥c |
| NFR-SEC-09 | KhÃ´ng log secret | Log khÃ´ng chá»©a password, passphrase, token |
| NFR-SEC-10 | Audit log báº¥t biáº¿n | `audit_logs` chá»‰ INSERT, khÃ´ng UPDATE/DELETE tá»« UI |

### 5.4. Reliability & Availability

| ID | YÃªu cáº§u | NgÆ°á»¡ng |
|---|---|---|
| NFR-REL-01 | Uptime | â‰¥ 99.5% / thÃ¡ng (trá»« báº£o trÃ¬ cÃ³ thÃ´ng bÃ¡o) |
| NFR-REL-02 | Health check | `/api/health` pháº£i pháº£n há»“i < 1s |
| NFR-REL-03 | Recovery Time Objective (RTO) | Phá»¥c há»“i sau sá»± cá»‘ DB â‰¤ 2h tá»« backup gáº§n nháº¥t |
| NFR-REL-04 | Recovery Point Objective (RPO) | Máº¥t tá»‘i Ä‘a 24h dá»¯ liá»‡u (backup háº±ng ngÃ y) |
| NFR-REL-05 | Gunicorn tá»± khá»Ÿi Ä‘á»™ng láº¡i | `--max-requests 1000 --max-requests-jitter 50` |

### 5.5. Usability

| ID | YÃªu cáº§u | NgÆ°á»¡ng |
|---|---|---|
| NFR-USE-01 | Responsive | Hoáº¡t Ä‘á»™ng tá»‘t trÃªn mÃ n â‰¥ 360px |
| NFR-USE-02 | Accordion mobile | Má»¥c dÃ i trong panel chi tiáº¿t gáº­p Ä‘Æ°á»£c (â‰¤ 768px) |
| NFR-USE-03 | Tiáº¿ng Viá»‡t cÃ³ dáº¥u | Hiá»ƒn thá»‹ Ä‘Ãºng font; tÃ¬m kiáº¿m bá» dáº¥u váº«n ra káº¿t quáº£ |
| NFR-USE-04 | Accessibility | TÃªn nÃºt cÃ³ `aria-label`; focusable báº±ng Tab/Enter |

### 5.6. Maintainability

| ID | YÃªu cáº§u | Minh chá»©ng |
|---|---|---|
| NFR-MAIN-01 | Cáº¥u trÃºc blueprint | Má»—i module má»™t file; khÃ´ng import vÃ²ng |
| NFR-MAIN-02 | Test coverage | â‰¥ 50% cho module `family_tree`, `persons`, `members_portal` |
| NFR-MAIN-03 | Lint frontend | `npm run lint` pass trÃªn CI |
| NFR-MAIN-04 | TÃ i liá»‡u | Má»—i endpoint cÃ³ mÃ´ táº£ trong README hoáº·c docstring |

### 5.7. Portability

| ID | YÃªu cáº§u | Minh chá»©ng |
|---|---|---|
| NFR-PORT-01 | KhÃ´ng phá»¥ thuá»™c OS | Cháº¡y Ä‘Æ°á»£c Linux, Windows (dev) |
| NFR-PORT-02 | KhÃ´ng phá»¥ thuá»™c háº¡ táº§ng cá»¥ thá»ƒ | Cháº¡y Railway, VPS, local vá»›i cÃ¹ng code |
| NFR-PORT-03 | MySQL alias | Äá»c Ä‘Æ°á»£c cáº£ `DB_*` láº«n `MYSQL*` env |

### 5.8. Compliance & Privacy

| ID | YÃªu cáº§u | Minh chá»©ng |
|---|---|---|
| NFR-PRIV-01 | PII báº£o vá»‡ | Dá»¯ liá»‡u Ä‘áº§y Ä‘á»§ chá»‰ lá»™ sau khi xÃ¡c thá»±c member |
| NFR-PRIV-02 | XoÃ¡ theo yÃªu cáº§u | ThÃ nh viÃªn cÃ³ thá»ƒ yÃªu cáº§u áº©n/xoÃ¡ qua `edit_requests` |
| NFR-PRIV-03 | KhÃ´ng commit dá»¯ liá»‡u tháº­t | Repo khÃ´ng chá»©a dump DB tháº­t |

---

## 6. Use Case Modeling & UML

### 6.1. SÆ¡ Ä‘á»“ Use Case tá»•ng thá»ƒ

```mermaid
flowchart LR
    Guest((Guest))
    Member((Member))
    Editor((Editor))
    Admin((Admin))

    subgraph Há»‡_thá»‘ng_Gia_pháº£_TBQC
        UC01[UC-01: Xem cÃ¢y gia pháº£]
        UC02[UC-02: TÃ¬m kiáº¿m ngÆ°á»i]
        UC03[UC-03: Xem tá»• tiÃªn / háº­u duá»‡]
        UC04[UC-04: ÄÄƒng nháº­p passphrase]
        UC05[UC-05: Xuáº¥t Excel thÃ nh viÃªn]
        UC06[UC-06: Gá»­i yÃªu cáº§u sá»­a]
        UC07[UC-07: Xem má»™ pháº§n trÃªn báº£n Ä‘á»“]
        UC08[UC-08: CRUD Person]
        UC09[UC-09: Duyá»‡t yÃªu cáº§u sá»­a]
        UC10[UC-10: Backup DB]
        UC11[UC-11: Äá»“ng bá»™ tÃ i khoáº£n]
        UC12[UC-12: Cáº­p nháº­t vá»‹ trÃ­ & áº£nh má»™]
        UC13[UC-13: ÄÄƒng hoáº¡t Ä‘á»™ng/tin tá»©c]
        UC14[UC-14: ÄÄƒng nháº­p admin]
        UC15[UC-15: Xem nháº­t kÃ½ thao tÃ¡c]
    end

    Guest --> UC01
    Guest --> UC02
    Guest --> UC07
    Guest --> UC06
    Member --> UC04
    Member --> UC03
    Member --> UC05
    Member --> UC06
    Editor --> UC13
    Admin --> UC14
    Admin --> UC08
    Admin --> UC09
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC15

    UC05 -. Â«includeÂ» .-> UC04
    UC06 -. Â«includeÂ» .-> UC04
    UC08 -. Â«includeÂ» .-> UC14
    UC12 -. Â«extendÂ» .-> UC07
```

### 6.2. Äáº·c táº£ Use Case chi tiáº¿t

> Template chuáº©n cho má»—i Use Case (cÃ³ thá»ƒ copy cho cÃ¡c UC khÃ¡c).

#### UC-01 â€” Xem cÃ¢y gia pháº£

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-01 |
| **TÃªn** | Xem cÃ¢y gia pháº£ tÆ°Æ¡ng tÃ¡c |
| **Actor chÃ­nh** | Member |
| **Actor phá»¥** | Guest (cháº¿ Ä‘á»™ háº¡n cháº¿) |
| **Má»¥c Ä‘Ã­ch** | Cho phÃ©p ngÆ°á»i dÃ¹ng xem cáº¥u trÃºc dÃ²ng há» qua nhiá»u Ä‘á»i |
| **Pre-condition** | Guest Ä‘Ã£ nháº­p Ä‘Ãºng passphrase (náº¿u báº­t cá»•ng) |
| **Trigger** | Truy cáº­p `/genealogy` |
| **Main flow** | 1. User má»Ÿ `/genealogy` <br> 2. FE gá»i `GET /api/family-tree` <br> 3. Server truy váº¥n `persons` + `relationships` + `marriages` <br> 4. Server tráº£ JSON lá»“ng nhau <br> 5. FE render cÃ¢y SVG + panel chi tiáº¿t <br> 6. User click node â†’ FE hiá»ƒn thá»‹ thÃ´ng tin chi tiáº¿t |
| **Alt flow 2a** | Náº¿u cache cÃ²n háº¡n â†’ tráº£ tá»« cache |
| **Exception 3a** | DB timeout â†’ tráº£ 503, FE hiá»‡n thÃ´ng bÃ¡o retry |
| **Post-condition** | CÃ¢y hiá»ƒn thá»‹ Ä‘áº§y Ä‘á»§, cÃ³ thá»ƒ zoom/pan |
| **FR liÃªn quan** | FR-TREE-01, FR-TREE-02, FR-MAIN-03 |
| **NFR liÃªn quan** | NFR-PERF-01, NFR-PERF-02, NFR-USE-01 |

#### UC-05 â€” Xuáº¥t Excel danh sÃ¡ch thÃ nh viÃªn

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-05 |
| **TÃªn** | Export members to Excel |
| **Actor chÃ­nh** | Member |
| **Pre-condition** | ÄÃ£ Ä‘Äƒng nháº­p cá»•ng `/members` báº±ng passphrase |
| **Trigger** | Báº¥m nÃºt "Xuáº¥t Excel" |
| **Main flow** | 1. Member báº¥m nÃºt <br> 2. FE gá»i `GET /members/export/excel` <br> 3. Server kiá»ƒm session <br> 4. Server truy váº¥n `persons` + `marriages` + `branches` <br> 5. Sinh file `.xlsx` báº±ng `openpyxl` <br> 6. Ghi `audit_log` hÃ nh Ä‘á»™ng export <br> 7. Tráº£ file vá»›i header `Content-Disposition: attachment` |
| **Alt flow 3a** | Session háº¿t háº¡n â†’ `401` â†’ FE redirect `/members` |
| **Exception 4a** | DB lá»—i â†’ `503`, thÃ´ng bÃ¡o ngÆ°á»i dÃ¹ng |
| **Exception 5a** | Thiáº¿u thÆ° viá»‡n `openpyxl` â†’ `500` + log lá»—i |
| **Post-condition** | File `.xlsx` táº£i vá»; báº£n ghi audit Ä‘Æ°á»£c táº¡o |
| **FR liÃªn quan** | FR-MEM-04, FR-LOG-01 |
| **NFR liÃªn quan** | NFR-PERF-04, NFR-SEC-07 |

#### UC-06 â€” Gá»­i yÃªu cáº§u chá»‰nh sá»­a

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-06 |
| **TÃªn** | Submit edit request |
| **Actor chÃ­nh** | Member hoáº·c Guest |
| **Pre-condition** | Biáº¿t `person_id` hoáº·c tÃªn ngÆ°á»i cáº§n sá»­a |
| **Main flow** | 1. User má»Ÿ form "Äá» xuáº¥t sá»­a" trÃªn trang chi tiáº¿t ngÆ°á»i <br> 2. Nháº­p ná»™i dung + liÃªn há»‡ (náº¿u guest) <br> 3. FE gá»i `POST /api/edit-requests` <br> 4. Server validate `person_id` tá»“n táº¡i <br> 5. Server INSERT `edit_requests` vá»›i `status='pending'` <br> 6. Tráº£ `{ok: true, request_id}` <br> 7. Admin nháº­n thÃ´ng bÃ¡o (náº¿u báº­t email) |
| **Alt flow 4a** | Náº¿u `person_id` khÃ´ng tá»“n táº¡i nhÆ°ng cÃ³ `person_name` â†’ lÆ°u dáº¡ng backup |
| **Exception 5a** | DB lá»—i â†’ `500`; FE hiá»‡n thÃ´ng bÃ¡o |
| **Post-condition** | Báº£n ghi `edit_requests` Ä‘Æ°á»£c táº¡o, chá» admin duyá»‡t |
| **FR liÃªn quan** | FR-PERSON-08 |

#### UC-08 â€” CRUD Person (Admin)

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-08 |
| **TÃªn** | Quáº£n lÃ½ há»“ sÆ¡ Person |
| **Actor chÃ­nh** | Admin |
| **Pre-condition** | Admin Ä‘Ã£ Ä‘Äƒng nháº­p `/admin/login` |
| **Main flow (Create)** | 1. Admin má»Ÿ form "ThÃªm ngÆ°á»i" <br> 2. Nháº­p: `full_name`, `gender`, `generation_level`, `father_mother_id`, â€¦ <br> 3. FE `POST /api/persons` <br> 4. Server validate báº¯t buá»™c <br> 5. Server sinh `person_id` theo pattern `P-<gen>-<seq>` <br> 6. INSERT `persons`; náº¿u cÃ³ `father_mother_id` â†’ INSERT `relationships` <br> 7. Ghi audit log <br> 8. Cache invalidate |
| **Alt flow 4a** | Náº¿u thiáº¿u `full_name` â†’ `400 {error: "full_name required"}` |
| **Alt flow (Update)** | `PUT /api/person/<id>`: chá»‰ cáº­p nháº­t trÆ°á»ng cÃ³ máº·t trong body |
| **Alt flow (Delete)** | `DELETE /api/person/<id>`: cáº£nh bÃ¡o náº¿u cÃ³ háº­u duá»‡; cascade xoÃ¡ `relationships`, `marriages` |
| **Post-condition** | DB cáº­p nháº­t; audit log ghi; cÃ¢y refresh Ä‘á»“ng bá»™ |
| **FR liÃªn quan** | FR-PERSON-04, FR-PERSON-05, FR-PERSON-06, FR-LOG-01 |
| **NFR liÃªn quan** | NFR-SEC-07, NFR-SEC-10 |

#### UC-09 â€” Duyá»‡t yÃªu cáº§u sá»­a

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-09 |
| **Main flow** | 1. Admin má»Ÿ `/admin/requests` <br> 2. Tháº¥y danh sÃ¡ch `status='pending'` <br> 3. Chá»n má»™t yÃªu cáº§u â†’ xem chi tiáº¿t <br> 4. Báº¥m "Duyá»‡t" hoáº·c "Tá»« chá»‘i" <br> 5. Náº¿u duyá»‡t: admin tá»± Ã¡p dá»¥ng thay Ä‘á»•i qua UC-08; sau Ä‘Ã³ cáº­p nháº­t `status='processed'`, `processed_at=NOW()`, `processed_by=admin.id` <br> 6. Náº¿u tá»« chá»‘i: `status='rejected'`, `rejection_reason=...` |

#### UC-10 â€” Backup Database

| Má»¥c | Ná»™i dung |
|-----|----------|
| **ID** | UC-10 |
| **Trigger** | (Thá»§ cÃ´ng) Admin báº¥m "Backup"; (Tá»± Ä‘á»™ng) Cron hoáº·c script ná»n |
| **Main flow** | 1. `POST /api/admin/backup` <br> 2. Server gá»i `mysqldump` hoáº·c lib tÆ°Æ¡ng Ä‘Æ°Æ¡ng <br> 3. LÆ°u file `.sql.gz` vÃ o `BACKUP_DIR` (trÃªn volume) <br> 4. (Tuá»³ chá»n) MÃ£ hoÃ¡ báº±ng `BACKUP_PASSWORD` <br> 5. Ghi audit log <br> 6. Tráº£ `{filename, size, created_at}` |
| **Post-condition** | File backup náº±m trÃªn volume; liá»‡t kÃª Ä‘Æ°á»£c qua `GET /api/admin/backups` |

### 6.3. Sequence Diagram â€” UC-05 (Export Excel)

```mermaid
sequenceDiagram
    actor M as Member
    participant B as Browser
    participant F as Flask (members_portal)
    participant DB as MySQL
    participant FS as Filesystem
    participant L as audit_log

    M->>B: Click "Xuáº¥t Excel"
    B->>F: GET /members/export/excel (cookie)
    F->>F: require_member_session()
    alt Session há»£p lá»‡
        F->>DB: SELECT persons JOIN marriages JOIN branches
        DB-->>F: rows
        F->>FS: openpyxl.Workbook â†’ save buffer
        F->>L: INSERT audit_log (action='export_excel')
        F-->>B: 200 + .xlsx (Content-Disposition: attachment)
        B-->>M: Táº£i file vá» mÃ¡y
    else Session háº¿t háº¡n
        F-->>B: 401 Unauthorized
        B->>B: Redirect /members
    end
```

### 6.4. Activity Diagram â€” Luá»“ng yÃªu cáº§u sá»­a

```mermaid
flowchart TD
    Start([Start]) --> A[User má»Ÿ chi tiáº¿t person]
    A --> B[Báº¥m 'Äá» xuáº¥t sá»­a']
    B --> C[Äiá»n ná»™i dung + liÃªn há»‡]
    C --> D{Validate}
    D -- KhÃ´ng há»£p lá»‡ --> C
    D -- Há»£p lá»‡ --> E[POST /api/edit-requests]
    E --> F[(edit_requests<br/>status=pending)]
    F --> G[Admin má»Ÿ /admin/requests]
    G --> H{Quyáº¿t Ä‘á»‹nh}
    H -- Duyá»‡t --> I[Admin Ã¡p dá»¥ng thay Ä‘á»•i<br/>UC-08 Update Person]
    I --> J[status=processed<br/>processed_at, processed_by]
    H -- Tá»« chá»‘i --> K[status=rejected<br/>rejection_reason]
    J --> End([End])
    K --> End
```

### 6.5. State Machine â€” VÃ²ng Ä‘á»i Edit Request

```mermaid
stateDiagram-v2
    [*] --> Pending: POST /api/edit-requests
    Pending --> Approved: Admin duyá»‡t
    Pending --> Rejected: Admin tá»« chá»‘i (kÃ¨m lÃ½ do)
    Approved --> Processed: ÄÃ£ Ã¡p dá»¥ng vÃ o persons
    Rejected --> [*]
    Processed --> [*]
```

### 6.6. Class Diagram â€” Miá»n dá»¯ liá»‡u chÃ­nh

```mermaid
classDiagram
    class Person {
        +string person_id  %% P-<gen>-<seq>
        +string full_name
        +string alias
        +string gender
        +string status
        +int generation_level
        +date birth_date_solar
        +string birth_date_lunar
        +date death_date_solar
        +string home_town
        +string grave_info
        +string grave_location
        +string grave_image
        +string father_mother_id
    }
    class Relationship {
        +int id
        +string parent_id
        +string child_id
        +enum relation_type  %% father, mother, in_law, ...
    }
    class Marriage {
        +int id
        +string person_id
        +string spouse_person_id
        +string status  %% Äang káº¿t hÃ´n, ÄÃ£ ly dá»‹, ...
        +string note
    }
    class EditRequest {
        +int request_id
        +int person_id
        +int user_id
        +string content
        +enum status  %% pending/approved/rejected/processed
        +datetime processed_at
        +int processed_by
    }
    class User {
        +int user_id
        +string username
        +string password_hash
        +enum role  %% admin/user
        +bool is_active
    }
    class Activity {
        +int activity_id
        +string title
        +text content
        +enum status  %% published/draft
    }
    class AuditLog {
        +int id
        +int user_id
        +string action
        +string target
        +datetime created_at
        +string ip
        +json details
    }

    Person "1" -- "0..*" Relationship : parent
    Person "1" -- "0..*" Relationship : child
    Person "1" -- "0..*" Marriage
    Person "1" -- "0..*" EditRequest : target
    User "1" -- "0..*" EditRequest : submitted
    User "1" -- "0..*" EditRequest : processed
    User "1" -- "0..*" AuditLog : actor
```

### 6.7. Component Diagram â€” Kiáº¿n trÃºc triá»ƒn khai

```mermaid
flowchart TB
    Browser[Browser<br/>HTML/JS/SVG tree]
    subgraph App["Flask app (Gunicorn)"]
        direction TB
        MAIN[main_bp]
        AUTH[auth_bp]
        TREE[family_tree_bp]
        PERS[persons_bp]
        MEM[members_portal_bp]
        ACT[activities_bp]
        GAL[gallery_bp]
        ADM[admin_bp]
        LEG[admin_routes.py<br/>legacy]
        MAR[marriage_api.py]
        LOG[audit_log.py]
    end
    MySQL[(MySQL<br/>persons, relationships,<br/>marriages, users,<br/>edit_requests, audit_logs)]
    Vol[(Volume<br/>BACKUP_DIR,<br/>static/images/grave)]
    Geo[Geoapify API]

    Browser -- HTTPS --> App
    App -- SQL --> MySQL
    App -- Read/Write --> Vol
    App -- HTTPS --> Geo
```

---

## 7. MÃ´ hÃ¬nh dá»¯ liá»‡u

### 7.1. Báº£ng chÃ­nh (theo `folder_sql/reset_schema_tbqc.sql`)

| Báº£ng | Má»¥c Ä‘Ã­ch | KhÃ³a chÃ­nh | Ghi chÃº |
|------|----------|-----------|---------|
| `persons` | LÆ°u má»—i cÃ¡ nhÃ¢n | `person_id VARCHAR(50)` | Äá»‹nh dáº¡ng `P-<gen>-<seq>` |
| `relationships` | Cha-máº¹ â†’ con | `id` auto | FK cascade |
| `marriages` | HÃ´n nhÃ¢n (nhiá»u vá»£/chá»“ng) | `id` auto | Unique pair |
| `edit_requests` | YÃªu cáº§u sá»­a | `request_id` | `status` enum |
| `users` | TÃ i khoáº£n Ä‘Äƒng nháº­p | `user_id` | `password_hash` báº¯t buá»™c |
| `activities` | Tin tá»©c/hoáº¡t Ä‘á»™ng | `activity_id` | `status` draft/published |
| `branches` | NhÃ¡nh dÃ²ng há» | `branch_id` | `branch_name` unique |
| `generations` | Äá»i | `generation_id` | `generation_number` unique |
| `locations` | Äá»‹a Ä‘iá»ƒm | `location_id` | Unique `(name,type)` |
| `birth_records` / `death_records` | Sá»± kiá»‡n sinh/máº¥t chi tiáº¿t | auto | FK `person_id` |
| `audit_logs` | Nháº­t kÃ½ | auto | INSERT-only |

### 7.2. Quy táº¯c nghiá»‡p vá»¥ (Business Rules)

- **BR-01** â€” Má»™t `person_id` lÃ  duy nháº¥t toÃ n há»‡ thá»‘ng, khÃ´ng tÃ¡i sá»­ dá»¥ng.
- **BR-02** â€” `generation_level` pháº£i lÃ  sá»‘ nguyÃªn â‰¥ 1 (Ä‘á»i 1 lÃ  cao nháº¥t).
- **BR-03** â€” Má»™t `Person` cÃ³ thá»ƒ cÃ³ nhiá»u báº£n ghi `Marriage` vá»›i `status` khÃ¡c nhau.
- **BR-04** â€” `Relationship` chá»‰ cÃ³ `relation_type âˆˆ {father, mother, in_law, child_in_law, other}`.
- **BR-05** â€” XoÃ¡ `Person` sáº½ cascade xoÃ¡ `Relationship`, `Marriage` liÃªn quan (do FK `ON DELETE CASCADE`).
- **BR-06** â€” `edit_requests.status` tuÃ¢n theo mÃ¡y tráº¡ng thÃ¡i UC-06: chá»‰ `pending â†’ approved/rejected`, `approved â†’ processed`.
- **BR-07** â€” Máº­t kháº©u ngÆ°á»i dÃ¹ng **khÃ´ng bao giá»** lÆ°u plaintext.
- **BR-08** â€” Audit log ghi **má»i** thao tÃ¡c thay Ä‘á»•i `persons`, `relationships`, `marriages`, `edit_requests`, `users`, `activities`, `backups`.

---

## 8. Kiáº¿n trÃºc triá»ƒn khai & váº­n hÃ nh

### 8.1. Stack cÃ´ng nghá»‡

| Layer | CÃ´ng nghá»‡ |
|-------|-----------|
| Backend | Python 3.11+, Flask, flask-login, flask-limiter, flask-wtf, Flask-Caching, flask-cors |
| DB | MySQL 8.x (mysql-connector-python) |
| WSGI | Gunicorn (preload, 1 worker Ã— 4 threads, timeout 120s) |
| Frontend | Jinja2 template, Vanilla JS, SVG cho cÃ¢y, CSS responsive |
| Map | Geoapify API (key qua env) |
| Háº¡ táº§ng | Railway / VPS + Volume persistent |

### 8.2. Cáº¥u hÃ¬nh mÃ´i trÆ°á»ng (`.env`)

| NhÃ³m | Biáº¿n | Báº¯t buá»™c? | Má»¥c Ä‘Ã­ch |
|------|------|-----------|----------|
| DB | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | âœ… | Káº¿t ná»‘i MySQL |
| DB alias | `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` | âŒ | TÆ°Æ¡ng thÃ­ch Railway |
| Session | `SECRET_KEY` | âœ… (prod) | KÃ½ session |
| Cá»•ng | `MEMBERS_PASSWORD`, `GENEALOGY_PASSPHRASES` | âœ… | Báº£o vá»‡ cá»•ng member/genealogy |
| Admin | `ADMIN_PASSWORD`, `MEMBERS_FIXED_ACCOUNTS` | âœ… | TÃ i khoáº£n admin seed |
| Album/Má»™ | `ALBUM_PASSWORD`, `GRAVE_IMAGE_DELETE_PASSWORD` | âŒ | Tuá»³ chá»n |
| Backup | `BACKUP_DIR`, `BACKUP_PASSWORD` | âœ… (prod) | ThÆ° má»¥c + máº­t kháº©u backup |
| Map | `GEOAPIFY_API_KEY` | âŒ | Báº£n Ä‘á»“ má»™ pháº§n |
| Social | `FB_PAGE_ID`, `FB_ACCESS_TOKEN` | âŒ | NhÃºng Facebook (náº¿u báº­t) |
| Cookie | `COOKIE_DOMAIN`, `CORS_ALLOWED_ORIGINS` | âŒ | Äa subdomain |
| Volume | `RAILWAY_VOLUME_MOUNT_PATH` | âŒ | Mount áº£nh/backup |

### 8.3. Thá»© tá»± Ä‘Äƒng kÃ½ route (trÃ¡nh trÃ¹ng)

1. `register_blueprints(app)` â€” `main â†’ auth â†’ activities â†’ family_tree â†’ persons â†’ members_portal â†’ gallery â†’ admin`.
2. `register_admin_routes(app)` â€” legacy `/admin/*`.
3. `register_marriage_routes(app)`.
4. Route khai trá»±c tiáº¿p trong `app.py`.
5. `add_url_rule(...)` cuá»‘i `app.py`.

> **Quy táº¯c:** khi trÃ¹ng URL, **handler Ä‘Äƒng kÃ½ sau tháº¯ng**. Pháº£i kiá»ƒm tra báº±ng `scripts/list_routes.py` sau má»—i láº§n thÃªm route.

### 8.4. Quy trÃ¬nh khá»Ÿi cháº¡y (Runbook)

#### Local dev
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # sá»­a giÃ¡ trá»‹ tháº­t
python app.py
curl http://127.0.0.1:5000/api/health
```

#### Production (Gunicorn)
```text
web: gunicorn app:app \
     --bind 0.0.0.0:8080 \
     --workers 1 --threads 4 \
     --timeout 120 --preload \
     --max-requests 1000 --max-requests-jitter 50
```

### 8.5. Quy trÃ¬nh backup & khÃ´i phá»¥c

| BÆ°á»›c | Thao tÃ¡c | TiÃªu chÃ­ xÃ¡c nháº­n |
|------|---------|-------------------|
| Backup thá»§ cÃ´ng | `POST /api/admin/backup` hoáº·c `scripts/backup_database.py` | File `.sql.gz` trong `BACKUP_DIR`, kÃ­ch thÆ°á»›c > 0 |
| Backup tá»± Ä‘á»™ng | Cron daily 02:00 | Log ghi thÃ nh cÃ´ng; file má»›i trong `BACKUP_DIR` |
| Liá»‡t kÃª | `GET /api/admin/backups` | Tráº£ list vá»›i size + timestamp |
| Táº£i vá» | `GET /api/admin/backup/<filename>` | File táº£i Ä‘Ãºng; path traversal bá»‹ cháº·n |
| KhÃ´i phá»¥c | Káº¿t ná»‘i MySQL vÃ  `mysql < backup.sql` | `SELECT COUNT(*) FROM persons` khá»›p sá»‘ cÅ© |

### 8.6. Quy trÃ¬nh váº­n hÃ nh thÆ°á»ng ngÃ y (Operational Playbook)

| TÃ¬nh huá»‘ng | HÃ nh Ä‘á»™ng |
|-----------|-----------|
| **Deploy má»›i** | Merge PR â†’ CI lint pass â†’ deploy Railway â†’ `curl /api/health` â†’ cháº¡y QA checklist |
| **ThÃªm person** | Admin â†’ `/admin/persons` â†’ Táº¡o â†’ kiá»ƒm tra cÃ¢y qua `/genealogy` |
| **Duyá»‡t yÃªu cáº§u sá»­a** | Admin â†’ `/admin/requests` â†’ duyá»‡t â†’ UC-08 â†’ set `processed` |
| **Backup trÆ°á»›c thay Ä‘á»•i lá»›n** | UC-10 trÆ°á»›c khi cháº¡y `drop_old_tables.sql` hoáº·c migration |
| **BÃ¡o lá»—i tá»« thÃ nh viÃªn** | Check `audit_logs`, `application.log`; reproduce trÃªn staging |
| **Sá»± cá»‘ DB** | `GET /api/health` â†’ kiá»ƒm env `DB_*` â†’ restart service â†’ náº¿u máº¥t data, khÃ´i phá»¥c tá»« `BACKUP_DIR` |
| **áº¢nh máº¥t sau redeploy** | Kiá»ƒm tra `RAILWAY_VOLUME_MOUNT_PATH`; gáº¯n láº¡i volume |

### 8.7. GiÃ¡m sÃ¡t vÃ  log

- **Health check:** monitor ngoáº¡i (UptimeRobot, BetterStack) gá»i `/api/health` má»—i 60s.
- **Log á»©ng dá»¥ng:** `logs/` + stdout gunicorn â†’ táº­p trung qua ná»n táº£ng.
- **Audit log nghiá»‡p vá»¥:** báº£ng `audit_logs` (MySQL) â€” query báº±ng `/admin/activity-logs`.
- **Alert:** khi `/api/health` fail 3 láº§n liÃªn tiáº¿p â†’ thÃ´ng bÃ¡o admin qua Slack/email.

### 8.8. Checklist báº£o máº­t trÆ°á»›c khi phÃ¡t hÃ nh

- [ ] `SECRET_KEY` ngáº«u nhiÃªn, â‰¥ 32 kÃ½ tá»±.
- [ ] KhÃ´ng cÃ²n giÃ¡ trá»‹ `changeme`/`default`/`123` trong báº¥t ká»³ secret nÃ o.
- [ ] HTTPS báº­t á»Ÿ edge (reverse proxy / CDN).
- [ ] `COOKIE_DOMAIN` khá»›p apex + www; cookie `Secure; HttpOnly`.
- [ ] `flask-limiter` báº­t cho `/api/login`, `/api/genealogy/verify-passphrase`, `/members/verify`.
- [ ] `.env` khÃ´ng náº±m trong git history.
- [ ] `BACKUP_DIR` trÃªn volume persistent.
- [ ] `GENEALOGY_PASSPHRASES`, `MEMBERS_PASSWORD`, `ADMIN_PASSWORD` Ä‘Ã£ rotate sau dev.

---

## 9. Validation & Verification

### 9.1. Verification (xÃ¢y Ä‘Ãºng tÃ i liá»‡u)

| Ká»¹ thuáº­t | Thá»±c hiá»‡n | Táº§n suáº¥t |
|---------|-----------|---------|
| **Requirements review** | Team Ä‘á»c SRS, check CLEAR (Complete, Consistent, Unambiguous, Verifiable, Feasible, Traceable) | Má»—i láº§n cáº­p nháº­t SRS |
| **Code review** | PR báº¯t buá»™c 1 reviewer; check map vá» FR/NFR trong mÃ´ táº£ | Má»—i PR |
| **Static analysis** | `npm run lint`, pytest, pre-commit | CI má»—i push |
| **Unit test** | `pytest tests/` cho `family_tree`, `persons`, `members_portal` | CI |
| **Route audit** | `scripts/list_routes.py`, `scripts/check_blueprint_routes.py` | TrÆ°á»›c release |

### 9.2. Validation (xÃ¢y Ä‘Ãºng cÃ¡i user cáº§n)

| Ká»¹ thuáº­t | Thá»±c hiá»‡n | Táº§n suáº¥t |
|---------|-----------|---------|
| **Prototype review** | ÄÆ°a áº£nh UI cho trÆ°á»Ÿng tá»™c duyá»‡t | Má»—i tÃ­nh nÄƒng UI má»›i |
| **UAT** | Ban gia pháº£ dÃ¹ng staging 1 tuáº§n, kÃ½ nháº­n theo `GENEALOGY_QA_CHECKLIST.md` | Má»—i release lá»›n |
| **Beta members** | 5-10 thÃ nh viÃªn dÃ¹ng thá»±c táº¿, feedback qua `edit_requests` | Rolling |
| **Usage metrics** | Theo dÃµi sá»‘ lÆ°á»£t xem cÃ¢y, export Excel, edit request â†’ xÃ¡c nháº­n tÃ­nh nÄƒng Ä‘Æ°á»£c dÃ¹ng | HÃ ng thÃ¡ng |

### 9.3. TiÃªu chÃ­ cháº¥p nháº­n (Acceptance) cho release

- [ ] ToÃ n bá»™ QA checklist `GENEALOGY_QA_CHECKLIST.md` pass.
- [ ] Unit test pass 100% trÃªn `main`.
- [ ] KhÃ´ng cÃ³ NFR-SEC bá»‹ vi pháº¡m (scan secret, dependency audit).
- [ ] `/api/health` ok trÃªn mÃ´i trÆ°á»ng staging â‰¥ 24h.
- [ ] TrÆ°á»Ÿng tá»™c hoáº·c ngÆ°á»i Ä‘Æ°á»£c uá»· quyá»n kÃ½ nháº­n UAT.

---

## 10. Ma tráº­n truy váº¿t yÃªu cáº§u (Traceability Matrix)

| Req ID | MÃ´ táº£ ngáº¯n | Use Case | Endpoint chÃ­nh | File code | Test |
|--------|-----------|----------|----------------|-----------|------|
| FR-MAIN-03 | XÃ¡c thá»±c passphrase gia pháº£ | UC-04 | `POST /api/genealogy/verify-passphrase` | `blueprints/main.py` | `tests/test_genealogy_auth.py` |
| FR-AUTH-01 | ÄÄƒng nháº­p user/pass | UC-14 | `POST /api/login` | `blueprints/auth.py`, `auth.py` | `tests/test_auth.py` |
| FR-TREE-01 | Dá»¯ liá»‡u cÃ¢y | UC-01 | `GET /api/family-tree` | `blueprints/family_tree.py`, `app.py` | `tests/test_tree.py` |
| FR-TREE-06 | Tá»• tiÃªn | UC-03 | `GET /api/ancestors/<id>` | `app.py` | `tests/test_ancestors.py` |
| FR-PERSON-03 | TÃ¬m kiáº¿m | UC-02 | `GET /api/search` | `blueprints/persons.py` | `tests/test_search.py` |
| FR-PERSON-04 | Táº¡o person | UC-08 | `POST /api/persons` | `blueprints/persons.py`, `app.py` | `tests/test_persons_crud.py` |
| FR-PERSON-08 | Gá»­i yÃªu cáº§u sá»­a | UC-06 | `POST /api/edit-requests` | `blueprints/persons.py` | `tests/test_edit_requests.py` |
| FR-MEM-04 | Xuáº¥t Excel | UC-05 | `GET /members/export/excel` | `blueprints/members_portal.py` | `tests/test_export.py` |
| FR-GAL-02 | Cáº­p nháº­t vá»‹ trÃ­ má»™ | UC-12 | `POST /api/grave/update-location` | `blueprints/gallery.py`, `app.py` | `tests/test_grave.py` |
| FR-ADM-03 | Backup DB | UC-10 | `POST /api/admin/backup` | `admin_routes.py` | `tests/test_backup.py` |
| FR-ADM-06 | Duyá»‡t yÃªu cáº§u | UC-09 | `/admin/requests` | `admin_routes.py` | `tests/test_admin_requests.py` |
| FR-LOG-01 | Ghi audit | (XuyÃªn suá»‘t) | Ná»™i bá»™ | `audit_log.py` | `tests/test_audit.py` |
| FR-HEALTH-01 | Health check | â€” | `GET /api/health` | `app.py` | `tests/test_health.py` |
| NFR-PERF-02 | `/api/family-tree` < 800ms | UC-01 | â€” | index SQL, cache | `tests/perf/test_tree_perf.py` |
| NFR-SEC-05 | Rate limit | UC-04, UC-14 | â€” | `flask-limiter` config | `tests/test_rate_limit.py` |

> **Quy táº¯c:** Má»—i FR/NFR **pháº£i** cÃ³ hÃ ng á»Ÿ báº£ng nÃ y. Khi thÃªm yÃªu cáº§u má»›i, thÃªm hÃ ng tÆ°Æ¡ng á»©ng. Khi xoÃ¡ test, kiá»ƒm tra xem cÃ³ hÃ ng nÃ o máº¥t truy váº¿t khÃ´ng.

---

## 11. Phá»¥ lá»¥c

### 11.1. Ná»£ ká»¹ thuáº­t (Technical Debt)

- `/api/activities/can-post` Ä‘á»‹nh nghÄ©a á»Ÿ hai nÆ¡i (blueprint `activities` + `admin_routes`). Cáº§n thá»‘ng nháº¥t.
- `/api/tree`, `/api/generations` cÃ³ thá»ƒ trÃ¹ng giá»¯a blueprint vÃ  `add_url_rule` trong `app.py`.
- `app.py` lá»›n (~113KB) â€” cáº§n refactor dáº§n theo blueprint.
- Má»™t sá»‘ báº£ng phá»¥ (`birth_records`, `death_records`, `personal_details`) chÆ°a Ä‘Æ°á»£c dÃ¹ng Ä‘áº§y Ä‘á»§ trong UI.

### 11.2. Lá»‹ch sá»­ phiÃªn báº£n

| Version | NgÃ y | Thay Ä‘á»•i | NgÆ°á»i |
|---------|------|----------|-------|
| 1.0 | 2026-04-21 | Báº£n Ä‘áº§u tiÃªn â€” Ã¡p dá»¥ng Requirements Engineering vÃ o dá»± Ã¡n | â€” |

### 11.3. CÃ¡c tÃ i liá»‡u sá»‘ng cÃ¹ng SRS

- `GENEALOGY_QA_CHECKLIST.md` â€” Checklist nghiá»‡m thu.
- `GENEALOGY_ROLLOUT.md` â€” Káº¿ hoáº¡ch rollout.
- `DEBUGGER.md` â€” HÆ°á»›ng dáº«n debug.
- `README.md` â€” HÆ°á»›ng dáº«n setup + route tÃ³m táº¯t.

### 11.4. Quy trÃ¬nh cáº­p nháº­t SRS

1. Táº¡o branch `srs/<chá»§-Ä‘á»>`.
2. Cáº­p nháº­t file `docs/product/srs.md` + báº£ng truy váº¿t.
3. PR, yÃªu cáº§u Ã­t nháº¥t 1 reviewer á»Ÿ ban gia pháº£ + 1 dev.
4. Sau khi merge, cáº­p nháº­t version á»Ÿ má»¥c 11.2.
5. Náº¿u cÃ³ FR/NFR má»›i, báº¯t buá»™c thÃªm **test tÆ°Æ¡ng á»©ng** trÆ°á»›c khi Ä‘Ã³ng issue.

---

*Háº¿t tÃ i liá»‡u SRS v1.0.*
