<<<<<<< ours
# Checklist kiá»ƒm thá»­ â€” Trang Gia pháº£ (`/genealogy`)

DÃ¹ng sau khi thay Ä‘á»•i `genealogy.html`, `family-tree-ui.js`, `multilevel-genealogy.js`, hoáº·c luá»“ng API cÃ¢y. ÄÃ¡nh dáº¥u tá»«ng má»¥c khi Ä‘Ã£ kiá»ƒm trÃªn **desktop** vÃ  **mobile** (hoáº·c DevTools responsive).

## 1. Táº£i trang & cá»•ng

- [ ] Má»Ÿ `/genealogy` â€” khÃ´ng lá»—i console nghiÃªm trá»ng.
- [ ] Náº¿u báº­t cá»•ng passphrase: nháº­p Ä‘Ãºng â†’ vÃ o ná»™i dung; sai â†’ thÃ´ng bÃ¡o lá»—i.

## 2. CÃ¢y & Ä‘á»“ng bá»™

- [ ] CÃ¢y hiá»ƒn thá»‹ sau khi táº£i (loading â†’ ná»™i dung).
- [ ] **Äá»“ng bá»™** â€” cÃ¢y lÃ m má»›i; **danh sÃ¡ch Ä‘a cáº¥p** cÃ¹ng cáº­p nháº­t.
- [ ] Äá»•i **Hiá»ƒn thá»‹ Ä‘áº¿n Ä‘á»i** â€” cÃ¢y vÃ  danh sÃ¡ch Ä‘a cáº¥p khá»›p Ä‘á»i.
- [ ] **Cáº­p nháº­t thÃ´ng tin** (náº¿u dÃ¹ng) â€” khÃ´ng lá»—i tráº¯ng mÃ n hÃ¬nh.

## 3. Cháº¿ Ä‘á»™ xem (Danh sÃ¡ch / Mindmap)

- [ ] **Danh sÃ¡ch** â€” section `#multilevelGenealogySection` **hiá»‡n**; danh sÃ¡ch cÃ³ cáº¥p (ul/li); cÃ¢y trong khung váº«n bÃ¬nh thÆ°á»ng.
- [ ] **Mindmap** â€” cáº§n ngÆ°á»i trá»ng tÃ¢m; sau khi chá»n â€” mindmap; section Ä‘a cáº¥p **áº©n**; quay láº¡i **Danh sÃ¡ch** â€” Ä‘a cáº¥p hiá»‡n láº¡i.

## 4. Danh sÃ¡ch Ä‘a cáº¥p (Multilevel)

- [ ] Tá»« Ä‘á»i 3 trá»Ÿ xuá»‘ng nhÃ¡nh cÃ³ thá»ƒ má»Ÿ/Ä‘Ã³ng (`<details>`).
- [ ] Báº¥m tÃªn (hoáº·c Enter/Space khi focus) â€” **ThÃ´ng tin chi tiáº¿t** táº£i Ä‘áº§y Ä‘á»§ (API), cÃ¢y highlight náº¿u cÃ³ `setSelectedPerson`.
- [ ] DÃ²ng family (náº¿u cÃ³ spouse id) â€” cÃ³ thá»ƒ báº¥m vÃ  má»Ÿ chi tiáº¿t.

## 5. Panel â€œThÃ´ng tin chi tiáº¿tâ€

- [ ] Chá»n ngÆ°á»i trÃªn cÃ¢y â€” panel chi tiáº¿t Ä‘Ãºng (tÃªn, Ä‘á»i, â€¦).
- [ ] **Desktop** â€” panel chiá»u cao há»£p lÃ½ + cuá»™n trong panel khi ná»™i dung dÃ i.
- [ ] **Mobile (â‰¤768px)** â€” panel khÃ´ng chiáº¿m gáº§n háº¿t mÃ n hÃ¬nh; ná»™i dung cuá»™n trong **`.tree-info-content`**.
- [ ] **Mobile** â€” cÃ¡c má»¥c dÃ i (Tiá»ƒu sá»­, Con, HÃ´n phá»‘i, â€¦) dáº¡ng **accordion** (thu gá»n).

## 6. TÃ¬m kiáº¿m & focus

- [ ] TÃ¬m theo tÃªn â€” káº¿t quáº£; chá»n má»™t ngÆ°á»i â€” cÃ¢y focus / highlight (theo logic hiá»‡n táº¡i).
- [ ] KhÃ´ng lá»—i khi khÃ´ng cÃ³ káº¿t quáº£.

## 7. ToÃ n mÃ n hÃ¬nh & PDF

- [ ] **ToÃ n mÃ n hÃ¬nh** cÃ¢y â€” panel chi tiáº¿t áº©n (theo CSS); `Esc` thoÃ¡t náº¿u cÃ³ gá»£i Ã½.
- [ ] **Xuáº¥t PDF** (náº¿u dÃ¹ng) â€” khÃ´ng crash; file táº£i vá».

## 8. TÃ¡ch biá»‡t má»™ pháº§n

- [ ] TÃ¬m má»™ pháº§n / báº£n Ä‘á»“ â€” hoáº¡t Ä‘á»™ng Ä‘á»™c láº­p; khÃ´ng phá»¥ thuá»™c cháº¿ Ä‘á»™ danh sÃ¡ch Ä‘a cáº¥p.

## 9. Regression nhanh

- [ ] `GET /api/health` â€” tráº£ `ok` khi cÃ³ DB.
- [ ] Trang **ThÃ nh viÃªn** `/members` â€” khÃ´ng bá»‹ áº£nh hÆ°á»Ÿng bá»Ÿi thay Ä‘á»•i chá»‰ genealogy (náº¿u chá»‰ sá»­a JS/template gia pháº£).

## 10. NÃ¢ng cáº¥p cÃ³ giai Ä‘oáº¡n (rollout)

- [ ] Äá»c `GENEALOGY_ROLLOUT.md` â€” sau má»—i giai Ä‘oáº¡n cháº¡y láº¡i má»¥c 1â€“9 tÆ°Æ¡ng á»©ng.
- [ ] Tab **Tá»• tiÃªn (Äá»i 0)** (náº¿u cÃ³ dá»¯ liá»‡u Ä‘á»i 0) â€” báº£ng táº£i khi click; tab **Tháº¿ há»‡ 1** váº«n máº·c Ä‘á»‹nh má»Ÿ.
- [ ] **PhÃ¢n mÃ u nhÃ¡nh** (tÃ¹y chá»n, `localStorage.genealogy_branch_mode` / `window.GENEALOGY_BRANCH_MODE`) â€” `gen4-detail` vs `legacy`; Ä‘á»•i â†’ refresh cÃ¢y náº¿u cÃ³ gá»i `refreshTree`.

---

**Ghi chÃº PR/commit (máº«u):**  
*NÃ¢ng cáº¥p trang Gia pháº£: danh sÃ¡ch Ä‘a cáº¥p tÃ¡ch má»™ pháº§n, Ä‘á»“ng bá»™ vá»›i cÃ¢y; panel chi tiáº¿t responsive + accordion mobile; click danh sÃ¡ch má»Ÿ chi tiáº¿t API.*
=======
# Checklist kiá»ƒm thá»­ â€” Trang Gia pháº£ (`/genealogy`)

DÃ¹ng sau khi thay Ä‘á»•i `genealogy.html`, `family-tree-ui.js`, `multilevel-genealogy.js`, hoáº·c luá»“ng API cÃ¢y. ÄÃ¡nh dáº¥u tá»«ng má»¥c khi Ä‘Ã£ kiá»ƒm trÃªn **desktop** vÃ  **mobile** (hoáº·c DevTools responsive).

## 1. Táº£i trang & cá»•ng

- [ ] Má»Ÿ `/genealogy` â€” khÃ´ng lá»—i console nghiÃªm trá»ng.
- [ ] Náº¿u báº­t cá»•ng passphrase: nháº­p Ä‘Ãºng â†’ vÃ o ná»™i dung; sai â†’ thÃ´ng bÃ¡o lá»—i.

## 2. CÃ¢y & Ä‘á»“ng bá»™

- [ ] CÃ¢y hiá»ƒn thá»‹ sau khi táº£i (loading â†’ ná»™i dung).
- [ ] **Äá»“ng bá»™** â€” cÃ¢y lÃ m má»›i; **danh sÃ¡ch Ä‘a cáº¥p** cÃ¹ng cáº­p nháº­t.
- [ ] Äá»•i **Hiá»ƒn thá»‹ Ä‘áº¿n Ä‘á»i** â€” cÃ¢y vÃ  danh sÃ¡ch Ä‘a cáº¥p khá»›p Ä‘á»i.
- [ ] **Cáº­p nháº­t thÃ´ng tin** (náº¿u dÃ¹ng) â€” khÃ´ng lá»—i tráº¯ng mÃ n hÃ¬nh.

## 3. Cháº¿ Ä‘á»™ xem (Danh sÃ¡ch / Mindmap)

- [ ] **Danh sÃ¡ch** â€” section `#multilevelGenealogySection` **hiá»‡n**; danh sÃ¡ch cÃ³ cáº¥p (ul/li); cÃ¢y trong khung váº«n bÃ¬nh thÆ°á»ng.
- [ ] **Mindmap** â€” cáº§n ngÆ°á»i trá»ng tÃ¢m; sau khi chá»n â€” mindmap; section Ä‘a cáº¥p **áº©n**; quay láº¡i **Danh sÃ¡ch** â€” Ä‘a cáº¥p hiá»‡n láº¡i.

## 4. Danh sÃ¡ch Ä‘a cáº¥p (Multilevel)

- [ ] Tá»« Ä‘á»i 3 trá»Ÿ xuá»‘ng nhÃ¡nh cÃ³ thá»ƒ má»Ÿ/Ä‘Ã³ng (`<details>`).
- [ ] Báº¥m tÃªn (hoáº·c Enter/Space khi focus) â€” **ThÃ´ng tin chi tiáº¿t** táº£i Ä‘áº§y Ä‘á»§ (API), cÃ¢y highlight náº¿u cÃ³ `setSelectedPerson`.
- [ ] DÃ²ng family (náº¿u cÃ³ spouse id) â€” cÃ³ thá»ƒ báº¥m vÃ  má»Ÿ chi tiáº¿t.

## 5. Panel â€œThÃ´ng tin chi tiáº¿tâ€

- [ ] Chá»n ngÆ°á»i trÃªn cÃ¢y â€” panel chi tiáº¿t Ä‘Ãºng (tÃªn, Ä‘á»i, â€¦).
- [ ] **Desktop** â€” panel chiá»u cao há»£p lÃ½ + cuá»™n trong panel khi ná»™i dung dÃ i.
- [ ] **Mobile (â‰¤768px)** â€” panel khÃ´ng chiáº¿m gáº§n háº¿t mÃ n hÃ¬nh; ná»™i dung cuá»™n trong **`.tree-info-content`**.
- [ ] **Mobile** â€” cÃ¡c má»¥c dÃ i (Tiá»ƒu sá»­, Con, HÃ´n phá»‘i, â€¦) dáº¡ng **accordion** (thu gá»n).

## 6. TÃ¬m kiáº¿m & focus

- [ ] TÃ¬m theo tÃªn â€” káº¿t quáº£; chá»n má»™t ngÆ°á»i â€” cÃ¢y focus / highlight (theo logic hiá»‡n táº¡i).
- [ ] KhÃ´ng lá»—i khi khÃ´ng cÃ³ káº¿t quáº£.

## 7. ToÃ n mÃ n hÃ¬nh & PDF

- [ ] **ToÃ n mÃ n hÃ¬nh** cÃ¢y â€” panel chi tiáº¿t áº©n (theo CSS); `Esc` thoÃ¡t náº¿u cÃ³ gá»£i Ã½.
- [ ] **Xuáº¥t PDF** (náº¿u dÃ¹ng) â€” khÃ´ng crash; file táº£i vá».

## 8. TÃ¡ch biá»‡t má»™ pháº§n

- [ ] TÃ¬m má»™ pháº§n / báº£n Ä‘á»“ â€” hoáº¡t Ä‘á»™ng Ä‘á»™c láº­p; khÃ´ng phá»¥ thuá»™c cháº¿ Ä‘á»™ danh sÃ¡ch Ä‘a cáº¥p.

## 9. Regression nhanh

- [ ] `GET /api/health` â€” tráº£ `ok` khi cÃ³ DB.
- [ ] Trang **ThÃ nh viÃªn** `/members` â€” khÃ´ng bá»‹ áº£nh hÆ°á»Ÿng bá»Ÿi thay Ä‘á»•i chá»‰ genealogy (náº¿u chá»‰ sá»­a JS/template gia pháº£).

## 10. NÃ¢ng cáº¥p cÃ³ giai Ä‘oáº¡n (rollout)

- [ ] Äá»c `GENEALOGY_ROLLOUT.md` â€” sau má»—i giai Ä‘oáº¡n cháº¡y láº¡i má»¥c 1â€“9 tÆ°Æ¡ng á»©ng.
- [ ] Tab **Tá»• tiÃªn (Äá»i 0)** (náº¿u cÃ³ dá»¯ liá»‡u Ä‘á»i 0) â€” báº£ng táº£i khi click; tab **Tháº¿ há»‡ 1** váº«n máº·c Ä‘á»‹nh má»Ÿ.
- [ ] **PhÃ¢n mÃ u nhÃ¡nh** (tÃ¹y chá»n, `localStorage.genealogy_branch_mode` / `window.GENEALOGY_BRANCH_MODE`) â€” `gen4-detail` vs `legacy`; Ä‘á»•i â†’ refresh cÃ¢y náº¿u cÃ³ gá»i `refreshTree`.

---

**Ghi chÃº PR/commit (máº«u):**  
*NÃ¢ng cáº¥p trang Gia pháº£: danh sÃ¡ch Ä‘a cáº¥p tÃ¡ch má»™ pháº§n, Ä‘á»“ng bá»™ vá»›i cÃ¢y; panel chi tiáº¿t responsive + accordion mobile; click danh sÃ¡ch má»Ÿ chi tiáº¿t API.*
>>>>>>> theirs

