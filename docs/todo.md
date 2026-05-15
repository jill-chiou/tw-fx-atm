# 待辦事項

## 當前計畫（依序進行）

### 階段一：前端修正

- [x] **F1** — 移除 stale null 邏輯：`redraw()` 的 `|| data.currencies === null` 已無效，現在 100% 有幣別資料
- [x] **F2a** — sheet list 幣別同步：`updateSheetList()` 未套用幣別篩選，地圖與列表可能不一致（搜尋、附近、計數三條路徑都要修）
- [x] **F2b** — 點列表後收起 bottom sheet：避免 popup 被 sheet 遮住
- [x] **F2c** — 手機安全區：`#bottom-sheet` 補 `padding-bottom: env(safe-area-inset-bottom)` 避免 iPhone 主頁指示條遮住最後一列

### 階段二：架構升級

- [x] **A1** — SQLite pipeline：設計 schema（`atm_locations` / `bank_currencies` / `source_log`），改寫 merge 腳本（2026-05-13 完成，詳見 `docs/12-sqlite-pipeline-plan.md`）
  - FISC 1,949 筆 + Gap B 22 筆 = 1,971 筆；幣別 3,637 筆（精確 1,908 台、fallback 41 台）；驗證通過

---

## 維運（等時間 / 等 FISC 更新）

- [ ] 月更腳本驗證：`scripts/update_from_fisc.py` 確認 CCR 排程正常（首次自動執行 2026/06/01）
- [ ] 兆豐「新店分行」、中信「全家\_葵爾特店」：待 FISC 下次更新後確認是否出現

---

## 已完成

### 幣別資料（全 17 家，2026-05-11 完成）
- [x] 新光銀行（17 筆命中，靜態 HTML，USD/JPY/CNY/HKD 逐台）
- [x] 兆豐銀行（114 筆，JSON API，USD/JPY/EUR/CNY/HKD）
- [x] 國泰世華（171 筆，JSON API，USD/JPY）
- [x] 中國信託（167 筆，bot 保護→直接套用 FISC，USD/JPY/CNY）
- [x] 玉山銀行（136 筆，HTML 內嵌 JSON）
- [x] 華南銀行（46 筆，XML）
- [x] 永豐銀行（74 筆命中，JSON API 逐縣市/逐幣別）
- [x] 台新銀行（1,026 筆，機台層級，GetCustomATM.jsp）
- [x] 臺灣銀行（44 筆，直接套用 FISC，USD/HKD/JPY/CNY）
- [x] 第一商業銀行（42 筆，REST API，保守 USD/JPY）
- [x] 台北富邦（39 筆，直接套用 FISC，USD/JPY）
- [x] 上海商業儲蓄銀行（2 筆，手動記錄，逐台幣別：USD/JPY/HKD/CNY + USD/JPY）
- [x] 合作金庫（15 筆，直接套用 FISC，保守 USD/JPY）
- [x] 臺灣土地銀行（12 筆，直接套用 FISC，保守 USD/JPY）
- [x] 元大商業銀行（7 筆，直接套用 FISC，保守 USD/JPY）
- [x] 臺灣中小企業銀行（6 筆，直接套用 FISC，保守 USD/JPY）
- [x] 彰化商業銀行（1 筆，直接套用 FISC，保守 USD/JPY）
- [x] Gap A/B 分析與 merge 修正：100% 覆蓋率（詳見 `docs/11-gap-analysis-and-merge-fixes.md`）
- [x] **覆蓋率：1,971 / 1,971（100%）**

### 資料建置
- [x] PDF 解析 → atm_data.csv（1,962 筆）
- [x] TGOS 批次地址比對 → atm_geocoded.json（1,952/1,962 筆，98.5%）
- [x] Geocoding 抽樣驗證：30 筆 Google Maps 人工核對全數通過
- [x] 自動範圍檢查：過濾座標不在台灣範圍內的異常筆
- [x] Merge 腳本：含空 branch guard、fallback 邏輯、分行精確配對統計
- [x] 地址交叉驗證：7 家銀行官網地址 vs FISC，0 筆真正不符

### 前端
- [x] Leaflet 地圖 + 銀行篩選 UI
- [x] GitHub Pages 部署
- [x] 裝置定位（Geolocation API）+ 附近 ATM 面板（Haversine 距離排序）
- [x] 地圖 UI 第二版：搜尋列、圓形 marker、bottom sheet、銀行篩選面板
- [x] 前端搜尋（銀行/地點/地址，2 字 bigram AND）
- [x] 手機版 RWD 排版
- [x] 前端幣別篩選 UI（AND 邏輯；幣別 null 預設顯示）
