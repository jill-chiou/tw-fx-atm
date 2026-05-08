# 待辦事項

## 進行中 / 待做

### UI 改善
- [ ] 手機版 RWD 排版
- [ ] 篩選器 UI 整理（目前銀行太多，擠成一排）
- [ ] 地圖 popup 資訊排版優化
- [ ] 整體配色 / 字體調整

### 資料品質驗證
- [ ] 自動範圍檢查：過濾座標不在台灣範圍內的異常筆（lat 21.9~25.3, lng 119.3~122.1）
- [ ] 抽樣 Google Maps 比對：隨機抽 30 筆，用店名 + 位置確認現場是否真有 ATM

### 幣別篩選（資料蒐集難度高，與位置驗證合併進行）
- [ ] 調查各家銀行幣別資訊的資料格式（網頁 / PDF / API）
- [ ] 決定要支援哪幾家主要銀行
- [ ] 爬取 / 解析各家幣別資料，同步驗證位置正確性，合併進 atm_geocoded.json
- [ ] 前端加幣別篩選 UI

---

## 已完成

- [x] PDF 解析 → atm_data.csv（1,962 筆）
- [x] TGOS 批次地址比對 → atm_geocoded.json（1,952/1,962 筆，98.5%）
- [x] Leaflet 地圖 + 銀行篩選 UI
- [x] GitHub Pages 部署（https://jill-chiou.github.io/tw-fx-atm）
- [x] 裝置定位（Geolocation API）+ 附近 ATM 面板（Haversine 距離排序）
