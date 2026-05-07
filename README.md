# 台灣外幣 ATM 地圖

互動式地圖，整合台灣各銀行外幣提款機位置，可依銀行篩選、偵測目前位置。

**Demo**：（上線後補）

---

## 為什麼做這個

要出國領外幣前，要開六個分頁分別查各家銀行網站。政府（財金資訊公司 FISC）其實維護了一份完整的外幣 ATM 清單，但格式是 86 頁 PDF，無法搜尋、無法定位。這個專案把它變成可以用的地圖工具。

## 技術選型說明

| 工具 | 選用理由 |
|------|----------|
| **pdfplumber** | 針對表格擷取最可靠，不需要 Java 環境（tabula-py 需要），對中文 PDF 處理穩定 |
| **NLSC Geocoding API** | 國土測繪中心免費政府 API，針對台灣中文地址準確度優於 Nominatim/OpenStreetMap |
| **Leaflet.js** | 開源地圖套件，不需 API key，打包成靜態網站不需後端 |
| **GitHub Pages** | 靜態網站免費部署，朋友可直接透過 URL 使用，無需安裝任何東西 |

## 資料來源

- **ATM 位置**：財金資訊股份有限公司（FISC）「自動化服務機器業務提領外幣ATM位置查詢一覽」，2026/3/31 更新
- **Geocoding**：[國土測繪中心地址定位服務](https://www.nlsc.gov.tw/)

## 專案結構

```
tw-fx-atm/
  data/
    raw/          ← 原始 PDF
    processed/    ← 解析後的 CSV / 含經緯度的 JSON
  scripts/
    parse_pdf.py  ← PDF → CSV
    geocode.py    ← CSV + NLSC API → JSON with lat/lng
  index.html      ← Leaflet.js 地圖前端
  README.md
```

## 開發進度

- [x] Phase 0：技術選型與資料來源確認
- [ ] Phase 1 MVP：PDF 解析 → Geocoding → Leaflet 地圖 + 銀行篩選 → GitHub Pages
- [ ] Phase 2：爬取各銀行網站補充幣別資料（USD / JPY / EUR 等）
