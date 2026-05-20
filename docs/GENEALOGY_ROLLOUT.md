<<<<<<< ours
# NÃ¢ng cáº¥p cÃ³ giai Ä‘oáº¡n â€” CÃ¢y gia pháº£ (`/genealogy`)

Pháº¡m vi: **chá»‰** trang Gia pháº£ vÃ  static JS liÃªn quan (`genealogy.html`, `family-tree-*.js`, `genealogy-lineage.js`, â€¦). KhÃ´ng Ä‘á»•i auth, members, admin trá»« khi cÃ³ má»¥c riÃªng.

| Giai Ä‘oáº¡n | Ná»™i dung | Gá»¡ / cá» |
|------------|----------|---------|
| **0** | Baseline + checklist regression | `GENEALOGY_QA_CHECKLIST.md` |
| **1** | Logic an toÃ n: cache thá»‘ng kÃª, bucket Ä‘á»i 0 vs chÆ°a gÃ¡n, tab Tháº¿ há»‡ 0 | KhÃ´ng cá» |
| **2** | PhÃ¢n nhÃ¡nh mÃ u theo Ä‘á»i 4+ (tÃ¹y chá»n) | `localStorage.genealogy_branch_mode` hoáº·c `window.GENEALOGY_BRANCH_MODE` = `legacy` (máº·c Ä‘á»‹nh) \| `gen4-detail` (khÃ´ng cÃ²n dropdown trÃªn trang; Ä‘áº·t báº±ng console hoáº·c script) |
| **3** | Debounce Ä‘á»•i filter Ä‘á»i (giáº£m gá»i API láº·p) | LuÃ´n báº­t (chá»‰ genealogy) |
| **4** | (Má»™t pháº§n) `nameToIdsMap` â€” má»i `person_id` trÃ¹ng tÃªn chuáº©n hÃ³a (phá»¥c vá»¥ tÃ¬m kiáº¿m / debug sau nÃ y) | `window.nameToIdsMap` sau `loadTreeData` |
| **5** | (Dá»± phÃ²ng) Layout D3 / API DB riÃªng | ChÆ°a triá»ƒn khai |

## ThÆ° viá»‡n ngoÃ i â€” Panzoom (khung cÃ¢y)

- **[@panzoom/panzoom](https://github.com/timmywil/panzoom)** táº£i qua jsDelivr trong `genealogy.html`; `static/js/family-tree-panzoom.js` gáº¯n vÃ o `.tree` sau má»—i láº§n váº½.
- Há»— trá»£: zoom báº±ng lÄƒn chuá»™t trÃªn vÃ¹ng cÃ¢y, pinch trÃªn mobile, pan (kÃ©o ná»n) mÆ°á»£t hÆ¡n; Ã´ ngÆ°á»i / gia Ä‘Ã¬nh / connector dÃ¹ng lá»›p `panzoom-exclude` Ä‘á»ƒ khÃ´ng bá»‹ kÃ©o nháº§m.
- Náº¿u CDN lá»—i vÃ  `typeof Panzoom === 'undefined'`, code quay vá» cÃ¡ch cÅ©: `transform` + kÃ©o tay (`setupPanOnTreeContainer`).

## Kiá»ƒm thá»­ sau má»—i giai Ä‘oáº¡n

Cháº¡y checklist trong `GENEALOGY_QA_CHECKLIST.md` (desktop + mobile).

## Cháº¿ Ä‘á»™ nhÃ¡nh (Giai Ä‘oáº¡n 2)

- **`legacy`**: Giá»¯ hÃ nh vi cÅ© (phÃ¢n mÃ u tá»« con cá»§a Ä‘á»i 2).
- **`gen4-detail`**: Sau bÆ°á»›c trÃªn, tÃ¡ch thÃªm mÃ u theo tá»«ng nhÃ¡nh **Ä‘á»i 4** (con cá»§a nÃºt gia Ä‘Ã¬nh Ä‘á»i 3).

Báº­t thá»­ trong console trang Gia pháº£:

```js
localStorage.setItem('genealogy_branch_mode', 'gen4-detail');
location.reload();
```

Táº¯t:

```js
localStorage.removeItem('genealogy_branch_mode');
// hoáº·c
localStorage.setItem('genealogy_branch_mode', 'legacy');
location.reload();
```
=======
# NÃ¢ng cáº¥p cÃ³ giai Ä‘oáº¡n â€” CÃ¢y gia pháº£ (`/genealogy`)

Pháº¡m vi: **chá»‰** trang Gia pháº£ vÃ  static JS liÃªn quan (`genealogy.html`, `family-tree-*.js`, `genealogy-lineage.js`, â€¦). KhÃ´ng Ä‘á»•i auth, members, admin trá»« khi cÃ³ má»¥c riÃªng.

| Giai Ä‘oáº¡n | Ná»™i dung | Gá»¡ / cá» |
|------------|----------|---------|
| **0** | Baseline + checklist regression | `GENEALOGY_QA_CHECKLIST.md` |
| **1** | Logic an toÃ n: cache thá»‘ng kÃª, bucket Ä‘á»i 0 vs chÆ°a gÃ¡n, tab Tháº¿ há»‡ 0 | KhÃ´ng cá» |
| **2** | PhÃ¢n nhÃ¡nh mÃ u theo Ä‘á»i 4+ (tÃ¹y chá»n) | `localStorage.genealogy_branch_mode` hoáº·c `window.GENEALOGY_BRANCH_MODE` = `legacy` (máº·c Ä‘á»‹nh) \| `gen4-detail` (khÃ´ng cÃ²n dropdown trÃªn trang; Ä‘áº·t báº±ng console hoáº·c script) |
| **3** | Debounce Ä‘á»•i filter Ä‘á»i (giáº£m gá»i API láº·p) | LuÃ´n báº­t (chá»‰ genealogy) |
| **4** | (Má»™t pháº§n) `nameToIdsMap` â€” má»i `person_id` trÃ¹ng tÃªn chuáº©n hÃ³a (phá»¥c vá»¥ tÃ¬m kiáº¿m / debug sau nÃ y) | `window.nameToIdsMap` sau `loadTreeData` |
| **5** | (Dá»± phÃ²ng) Layout D3 / API DB riÃªng | ChÆ°a triá»ƒn khai |

## ThÆ° viá»‡n ngoÃ i â€” Panzoom (khung cÃ¢y)

- **[@panzoom/panzoom](https://github.com/timmywil/panzoom)** táº£i qua jsDelivr trong `genealogy.html`; `static/js/family-tree-panzoom.js` gáº¯n vÃ o `.tree` sau má»—i láº§n váº½.
- Há»— trá»£: zoom báº±ng lÄƒn chuá»™t trÃªn vÃ¹ng cÃ¢y, pinch trÃªn mobile, pan (kÃ©o ná»n) mÆ°á»£t hÆ¡n; Ã´ ngÆ°á»i / gia Ä‘Ã¬nh / connector dÃ¹ng lá»›p `panzoom-exclude` Ä‘á»ƒ khÃ´ng bá»‹ kÃ©o nháº§m.
- Náº¿u CDN lá»—i vÃ  `typeof Panzoom === 'undefined'`, code quay vá» cÃ¡ch cÅ©: `transform` + kÃ©o tay (`setupPanOnTreeContainer`).

## Kiá»ƒm thá»­ sau má»—i giai Ä‘oáº¡n

Cháº¡y checklist trong `GENEALOGY_QA_CHECKLIST.md` (desktop + mobile).

## Cháº¿ Ä‘á»™ nhÃ¡nh (Giai Ä‘oáº¡n 2)

- **`legacy`**: Giá»¯ hÃ nh vi cÅ© (phÃ¢n mÃ u tá»« con cá»§a Ä‘á»i 2).
- **`gen4-detail`**: Sau bÆ°á»›c trÃªn, tÃ¡ch thÃªm mÃ u theo tá»«ng nhÃ¡nh **Ä‘á»i 4** (con cá»§a nÃºt gia Ä‘Ã¬nh Ä‘á»i 3).

Báº­t thá»­ trong console trang Gia pháº£:

```js
localStorage.setItem('genealogy_branch_mode', 'gen4-detail');
location.reload();
```

Táº¯t:

```js
localStorage.removeItem('genealogy_branch_mode');
// hoáº·c
localStorage.setItem('genealogy_branch_mode', 'legacy');
location.reload();
```
>>>>>>> theirs

