# 待辦事項

## 進行中 / 待做

### UI 改善
- [ ] 手機版 RWD 排版
- [ ] 篩選器 UI 整理（目前銀行太多，擠成一排）
- [ ] 地圖 popup 資訊排版優化
- [ ] 整體配色 / 字體調整

### 裝置位置 + 距離功能
- [ ] 使用 Geolocation API 取得使用者位置
- [ ] Haversine 公式計算與各 ATM 的距離
- [ ] 畫面下方顯示「最近的 N 家」列表
- [ ] 地圖自動移至使用者位置並標示

### 幣別篩選（資料蒐集難度高）
- [ ] 調查各家銀行幣別資訊的資料格式（網頁 / PDF / API）
- [ ] 決定要支援哪幾家主要銀行
- [ ] 爬取 / 解析各家幣別資料，合併進 atm_geocoded.json
- [ ] 前端加幣別篩選 UI

---

## 已完成

- [x] PDF 解析 → atm_data.csv（1,962 筆）
- [x] Geocoding → atm_geocoded.json（1,939 筆，98.8%）
- [x] Leaflet 地圖 + 銀行篩選 UI
- [x] GitHub Pages 部署（https://intomoonlight.github.io/tw-fx-atm）
