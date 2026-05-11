# 待辦事項

## 進行中 / 待做

### 資料穩定性
- [x] index.html 加上無座標資料過濾，避免 `lat: null` / `lng: null` 造成前端錯誤

### UI 改善
- [x] 手機版 RWD 排版：改為全螢幕地圖 + 浮動搜尋列 + bottom sheet
- [x] 篩選器 UI 整理：銀行多選移到 bottom sheet，不再橫向右滑
- [x] 地圖 popup 資訊排版優化：改為圓角 popup，銀行色點輔助識別
- [x] 整體配色 / 字體調整：改為柔和藍綠主色、冷灰背景、白色浮動面板
- [x] 參考開源地圖專案與設計網站，整理可借用的 marker、搜尋、篩選、底部面板設計
- [ ] UI polish QA：檢查搜尋無結果、全消銀行、點擊列表打開 popup、手機高度與安全區

### 幣別篩選（資料蒐集難度高，與位置驗證合併進行）
- [x] 調查各家銀行幣別資訊的資料格式（網頁 / PDF / API）
- [x] 決定要支援哪幾家主要銀行
- [ ] 新光銀行幣別爬蟲 POC（靜態 HTML，最佳第一步）
- [ ] 兆豐銀行幣別爬蟲 POC（大型銀行，幣別資訊透明）
- [ ] 爬取 / 解析各家幣別資料，同步驗證位置正確性，合併進 atm_geocoded.json
- [ ] 前端加幣別篩選 UI

---

## 已完成

- [x] PDF 解析 → atm_data.csv（1,962 筆）
- [x] TGOS 批次地址比對 → atm_geocoded.json（1,952/1,962 筆，98.5%）
- [x] Leaflet 地圖 + 銀行篩選 UI
- [x] GitHub Pages 部署（https://jill-chiou.github.io/tw-fx-atm）
- [x] 裝置定位（Geolocation API）+ 附近 ATM 面板（Haversine 距離排序）
- [x] Geocoding 抽樣驗證：30 筆 Google Maps 人工核對全數通過
- [x] 自動範圍檢查：過濾座標不在台灣範圍內的異常筆（lat 21.9~25.3, lng 119.3~122.1）
- [x] 地圖 UI 第二版：搜尋列、圓形 marker、bottom sheet、銀行篩選面板
- [x] 前端搜尋：支援銀行、裝設地點、地址，以及「高雄三民」這類 2 字分組查詢
- [x] 銀行資料來源 inventory：盤點各銀行幣別資料格式與爬取優先順序
