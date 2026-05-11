# 待辦事項

## 待做

### UI
- [ ] UI polish QA：搜尋無結果、全消銀行、點擊列表打開 popup、手機高度與安全區

### 幣別功能
- [ ] Mac 補 push：skbank / cathaybk / ctbc / esunbank / hncb / sinopac 的 `*_currencies.json`（目前只有 megabank + taishin 在 git）
- [ ] 前端顯示幣別覆蓋狀態（無幣別資訊的機台加「幣別資訊不完整」灰色提示）

### 維運
- [ ] 月更腳本驗證：`scripts/update_from_fisc.py` 確認 CCR 排程正常（首次自動執行 2026/06/01）
- [ ] 兆豐「新店分行」、中信「全家\_葵爾特店」：待 FISC 下次更新後確認是否出現

---

## 已完成

### 資料建置
- [x] PDF 解析 → atm_data.csv（1,962 筆）
- [x] TGOS 批次地址比對 → atm_geocoded.json（1,952/1,962 筆，98.5%）
- [x] Geocoding 抽樣驗證：30 筆 Google Maps 人工核對全數通過
- [x] 自動範圍檢查：過濾座標不在台灣範圍內的異常筆
- [x] index.html 加上無座標資料過濾（`lat: null` / `lng: null`）

### 前端
- [x] Leaflet 地圖 + 銀行篩選 UI
- [x] GitHub Pages 部署（https://jill-chiou.github.io/tw-fx-atm）
- [x] 裝置定位（Geolocation API）+ 附近 ATM 面板（Haversine 距離排序）
- [x] 地圖 UI 第二版：搜尋列、圓形 marker、bottom sheet、銀行篩選面板
- [x] 前端搜尋：支援銀行、裝設地點、地址，以及「高雄三民」這類 2 字分組查詢
- [x] 手機版 RWD 排版：全螢幕地圖 + 浮動搜尋列 + bottom sheet
- [x] 篩選器 UI 整理：銀行多選移到 bottom sheet
- [x] 地圖 popup 排版優化：圓角 popup，銀行色點輔助識別
- [x] 整體配色 / 字體調整：柔和藍綠主色、冷灰背景、白色浮動面板
- [x] 前端幣別篩選 UI（AND 邏輯；幣別 null 預設顯示）

### 幣別資料
- [x] 銀行資料來源 inventory：盤點各銀行幣別格式與爬取優先順序
- [x] 新光銀行爬蟲（18 筆，靜態 HTML）
- [x] 兆豐銀行爬蟲（118 筆，JSON API）
- [x] 國泰世華爬蟲（172 筆，JSON API）
- [x] 中信銀行（167 筆，bot 保護→直接套用 FISC，USD/JPY/CNY）
- [x] 玉山銀行爬蟲（143 筆，HTML 內嵌 JSON）
- [x] 華南銀行爬蟲（46 筆，XML）
- [x] 永豐銀行爬蟲（95 筆，JSON API 逐縣市/逐幣別）
- [x] 台新銀行爬蟲（1,011 筆，**機台層級**，GetCustomATM.jsp）→ FISC 1026/1026 全覆蓋
- [x] Merge 腳本：含空 branch guard、fallback 邏輯、分行精確配對統計
- [x] 地址交叉驗證：7 家銀行官網地址 vs FISC，0 筆真正不符
