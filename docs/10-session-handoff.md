# Session 交接文件

> 建立日期：2026-05-09
> 用途：記錄本 session 完成的工作與下一步待辦，方便下次 session 快速接手。

---

## 本 Session 完成的事

### 1. 幣別爬蟲（7 家銀行）

| 銀行 | 腳本 | 輸出 | 幣別 | 備註 |
|------|------|------|------|------|
| 臺灣新光商業銀行 | `scripts/scrape_skbank.py` | `skbank_currencies.json` | USD/JPY/CNY/HKD | 靜態 HTML，requests + BS4 |
| 兆豐國際商業銀行 | `scripts/scrape_megabank.py` | `megabank_currencies.json` | USD/JPY/EUR/CNY/HKD | 內部 JSON API，無需 Playwright |
| 國泰世華商業銀行 | `scripts/scrape_cathaybk.py` | `cathaybk_currencies.json` | USD/JPY | 內部 JSON API，無需 Playwright |
| 中國信託商業銀行 | `scripts/scrape_ctbc.py` | `ctbc_currencies.json` | USD/JPY/CNY | 官網有 bot 保護，Chrome 調查後確認統一幣別，直接套用 FISC |
| 玉山商業銀行 | `scripts/scrape_esunbank.py` | `esunbank_currencies.json` | USD/JPY/CNY/HKD | 外幣 ATM 頁面內嵌 `info` / `dic` |
| 華南商業銀行 | `scripts/scrape_hncb.py` | `hncb_currencies.json` | USD/JPY/CNY/HKD | 官網 `/hncb/XML/ATM.xml` SOAP/XML |
| 永豐商業銀行 | `scripts/scrape_sinopac.py` | `sinopac_currencies.json` | USD/JPY/CNY/HKD | 內部 JSON API；逐縣市、逐幣別查詢。2026-05-10 重跑成功，95 筆，merge 新增 73 筆 |

### 2. Merge 腳本

- **`scripts/merge_currencies.py`**：將各銀行爬蟲結果 merge 進 `atm_geocoded.json`，產出 `data/processed/atm_with_currencies.json`
- 目前覆蓋：**719 / 1,960 筆（36%）**（已併入玉山、華南、永豐）

```
134  玉山
171  國泰世華
167  中信
109  兆豐
 73  永豐
 46  華南
 17  新光
---
719  合計
```

### 3. 前端幣別篩選

- `index.html` 改讀 `atm_with_currencies.json`
- 篩選 sheet 加入幣別 chip（USD/JPY/CNY/EUR/HKD）
- 邏輯：**AND**（選多種幣別 → 要同時具備才顯示）
- 幣別 null（尚未爬取的銀行）預設仍顯示

### 4. 地址交叉驗證

- 所有已爬銀行均做「官網地址 vs FISC 地址」驗證
- 結論：**0 筆真正地址不符**，差異全為格式問題（`-1號` vs `之1號`、段別漢字/數字、含不含行政區名）
- 驗證方法與坑記錄在 `docs/08-currency-merge.md`

### 5. 文件更新

| 檔案 | 新增內容 |
|------|---------|
| `docs/07-bank-data-inventory.md` | 各銀行狀態更新、覆蓋率試算表（從 09 併入）|
| `docs/08-currency-merge.md` | 四家銀行的 merge 記錄、地址驗證方法與坑 |
| `docs/06-ui-and-data-research-plan.md` | Step 6、7、8 標記完成 |

---

## 待辦事項

### 優先（依覆蓋率排序）

| # | 銀行 | FISC 台數 | 累積覆蓋率 | 已知情況 | 建議做法 |
|---|------|---------|---------|---------|---------|
| 1 | 永豐商業銀行 | 91 | 36% | ✅ 完成（2026-05-10）：95 筆，merge 新增 73 筆 | — |
| 2 | 台新國際商業銀行 | 1,026 | 89% | **官網完全無幣別資訊** | 另立專案追查；可試 Network tab 找 API |

### 其他

- [ ] 將 `atm_with_currencies.json` 的幣別覆蓋狀態反映在前端（例如：「幣別資訊不完整」的提示）
- [ ] 月更腳本 `scripts/update_from_fisc.py`：驗證 CCR 排程是否正確運作（首次自動執行是 2026/06/01）
- [ ] 兆豐「新店分行」和中信「全家\_葵爾特店」：待 FISC 下次更新後確認是否出現

---

## 關鍵技術筆記

### 各銀行 API 特性

| 銀行 | API 特性 | 能否外部呼叫 |
|------|---------|------------|
| 新光 | 靜態 HTML | ✓ requests |
| 兆豐 | JSON API，需 Referer header | ✓ requests |
| 國泰世華 | JSON API，需 Referer header | ✓ requests |
| 玉山 | HTML 內嵌 JSON (`info` / `dic`) | ✓ requests |
| 華南 | XML (`/hncb/XML/ATM.xml`) | ✓ requests |
| 永豐 | JSON API，需逐縣市/逐幣別查詢 | ✓ requests |
| 中信 | PerimeterX bot 保護 + session token | ✗ 需瀏覽器 |

### 中信 CTBC 特殊發現

- Angular scope 的 `checkForeignCurrency()` 對任何 ATM 永遠回傳 true
- 分頁無法透過 `rqData` 控制（page 參數不生效）
- 幣別篩選是純前端 UI，所有外幣 ATM 統一 USD/JPY/CNY

### 地址驗證函數設計

正規化順序：`臺→台` → 移除行政區詞 → 統一段別（一→1）→ 移除園區前綴 → `A-B → A之B`
比對方式：任一 FISC 條目吻合即通過（同分行可能有多台機器）

---

## 目前產出檔案狀態

```
data/processed/
├── atm_geocoded.json          # FISC 位置資料（1,960 筆，0 pending）
├── atm_with_currencies.json   # merge 後含幣別（646 筆有幣別，1,314 筆 null）
├── skbank_currencies.json     # 新光（18 筆）
├── megabank_currencies.json   # 兆豐（118 筆）
├── cathaybk_currencies.json   # 國泰世華（172 筆）
├── ctbc_currencies.json       # 中信（167 筆，FISC 直接套用）
├── esunbank_currencies.json   # 玉山（143 筆）
└── hncb_currencies.json       # 華南（46 筆）

scripts/
├── scrape_skbank.py
├── scrape_megabank.py
├── scrape_cathaybk.py
├── scrape_ctbc.py
├── scrape_esunbank.py
├── scrape_hncb.py
├── scrape_sinopac.py          # 已完成，待有網路權限時重跑
├── merge_currencies.py        # 每爬完一家，重跑此腳本即可更新
└── update_from_fisc.py        # 月更腳本（CCR 自動執行）
```
