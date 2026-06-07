## HÆ°á»›ng dáº«n cho Debugger (khÃ´ng commit máº­t kháº©u)

Dá»± Ã¡n nÃ y **khÃ´ng lÆ°u** username/password/server tháº­t trong Git. Táº¥t cáº£ thÃ´ng tin nháº¡y cáº£m Ä‘Æ°á»£c náº¡p tá»« **biáº¿n mÃ´i trÆ°á»ng** hoáº·c file local (vÃ­ dá»¥ `.env`, `tbqc_db.env`) vá»‘n Ä‘Ã£ Ä‘Æ°á»£c `.gitignore`.

Má»¥c tiÃªu cá»§a tÃ i liá»‡u nÃ y lÃ  giÃºp debugger Ä‘á»c code vÃ  hiá»ƒu â€œsecret Ä‘i vÃ o há»‡ thá»‘ng nhÆ° tháº¿ nÃ oâ€ mÃ  khÃ´ng cáº§n tháº¥y giÃ¡ trá»‹ tháº­t.

### 1) CÃ¡c nhÃ³m cáº¥u hÃ¬nh chÃ­nh

- **Káº¿t ná»‘i Database**
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - Code láº¥y tá»« env (hoáº·c biáº¿n tÆ°Æ¡ng Ä‘Æ°Æ¡ng `MYSQL*` tÃ¹y ná»n táº£ng).

- **Flask session/cookie**
  - `SECRET_KEY` (báº¯t buá»™c trÃªn production)
  - `COOKIE_DOMAIN` (production, dÃ¹ng chung cho domain vÃ  www)

- **Auth/Password ná»™i bá»™**
  - `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD`
  - `ALBUM_PASSWORD` (tuá»³ chá»n)
  - `GRAVE_IMAGE_DELETE_PASSWORD` (tuá»³ chá»n)
  - `MEMBERS_FIXED_ACCOUNTS` (tuá»³ chá»n): danh sÃ¡ch user/pass cá»‘ Ä‘á»‹nh cho cá»•ng Members
    - Format: `user1:pass1,user2:pass2`

- **Passphrase má»Ÿ trang Gia pháº£**
  - `GENEALOGY_PASSPHRASES` (phÃ¢n cÃ¡ch báº±ng dáº¥u pháº©y)
    - VÃ­ dá»¥: `phrase1,phrase2,phrase3`

### 2) Äiá»ƒm vÃ o (entrypoint)

- Cháº¡y á»©ng dá»¥ng tá»« `app.py` (thÆ° má»¥c gá»‘c repo). Blueprints Ä‘Æ°á»£c Ä‘Äƒng kÃ½ tá»« Ä‘Ã¢y.

### 3) Luá»“ng báº£o vá»‡ trang Gia pháº£ (passphrase)

- Frontend (`templates/genealogy.html`) gá»i API:
  - `POST /api/genealogy/verify-passphrase` vá»›i JSON `{ "passphrase": "..." }`
- Backend (`blueprints/main.py`) kiá»ƒm tra passphrase dá»±a trÃªn env `GENEALOGY_PASSPHRASES`.

### 4) Gá»£i Ã½ cÃ¡ch set env khi debug

- Táº¡o file `.env` local dá»±a trÃªn `.env.example` vÃ  Ä‘iá»n giÃ¡ trá»‹ tháº­t.
- Hoáº·c cáº¥u hÃ¬nh â€œEnvironment variablesâ€ ngay trong IDE/debugger profile (khuyáº¿n nghá»‹ náº¿u khÃ´ng muá»‘n táº¡o file).


