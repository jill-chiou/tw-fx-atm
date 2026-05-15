# 台灣外幣 ATM 地圖

互動式地圖，整合台灣各銀行外幣提款機位置與支援幣別，可依銀行篩選、偵測目前位置。

**Demo**：https://jill-chiou.github.io/tw-fx-atm

---

## 為什麼做這個

要出國領外幣前，要開六個分頁分別查各家銀行網站。政府（財金資訊公司 FISC）其實維護了一份完整的外幣 ATM 清單，但格式是 86 頁 PDF，無法搜尋、無法定位。這個專案把它變成可以用的地圖工具。

## 技術選型說明

| 工具 | 選用理由 |
|------|----------|
| **pdfplumber** | 針對表格擷取最可靠，不需要 Java 環境（tabula-py 需要），對中文 PDF 處理穩定 |
| **TGOS 批次地址比對** | 內政部官方地理資訊平台，針對台灣中文地址準確度優於 Nominatim/OpenStreetMap，無程式 API，上傳 CSV 等結果 |
| **requests + BeautifulSoup** | 爬取 17 家銀行官網取得各機台支援幣別，無需 Selenium |
| **SQLite** | 輕量資料管線，整合 FISC 位置與銀行幣別資料，方便月更維護 |
| **Leaflet.js** | 開源地圖套件，不需 API key，打包成靜態網站不需後端 |
| **GitHub Pages** | 靜態網站免費部署，朋友可直接透過 URL 使用，無需安裝任何東西 |

## 資料來源

- **ATM 位置**：財金資訊股份有限公司（FISC）「自動化服務機器業務提領外幣ATM位置查詢一覽」，2026/4/30 更新
- **Geocoding**：[內政地理資訊圖資雲整合服務平台 TGOS](https://www.tgos.tw/) 批次地址比對服務
- **幣別資料**：17 家銀行官網（台銀、土銀、合庫、一銀、彰銀、華南、兆豐、國泰、台新、新光、永豐、玉山、中信、富邦、遠東、星展、台北富邦）爬蟲擷取

## 專案結構

```
tw-fx-atm/
  data/
    raw/                    ← 原始 PDF（FISC 月更）
    processed/
      atm_data.csv          ← PDF 解析後的 CSV
      atm_geocoded.json     ← 加入經緯度後的 JSON
      atm_with_currencies.json  ← 最終輸出（前端資料來源）
      *_currencies.json     ← 各銀行幣別爬蟲結果（×17）
    atm.db                  ← SQLite（.gitignore，需本機產生）
  scripts/
    parse_pdf.py            ← PDF → CSV
    update_from_fisc.py     ← FISC 月更自動化流程
    geocode.py              ← CSV → JSON with lat/lng
    merge_currencies.py     ← FISC 位置 × 爬蟲幣別 → atm_with_currencies.json
    scrape_*.py (×17)       ← 各銀行幣別爬蟲
    db_init.py              ← 建立 SQLite schema
    db_import_locations.py  ← 匯入位置資料
    db_import_currencies.py ← 匯入幣別資料
    db_export.py            ← SQLite → atm_with_currencies.json
  docs/                     ← 規劃與技術文件（01–12）
  index.html                ← Leaflet.js 地圖前端
  README.md
```

### 本機產生 SQLite（首次或月更後）

```bash
python scripts/db_init.py
python scripts/db_import_locations.py
python scripts/db_import_currencies.py
python scripts/db_export.py
```

Windows 用 `python`（或 `py`）取代 `python3`。依賴套件：`pdfplumber`、`requests`、`beautifulsoup4`。

## 開發進度

- [x] Phase 0：技術選型與資料來源確認
- [x] Phase 1 MVP：PDF 解析 → TGOS Geocoding（1,960/1,962 筆）→ Leaflet 地圖 + 銀行篩選 → GitHub Pages
- [x] Phase 1.5：裝置定位 + 附近 ATM 面板（Geolocation API + Haversine 距離排序）
- [x] Phase 2：UI 改善（全螢幕地圖、懸浮頂欄、底部滑入面板、FAB 文字標籤、CJK 搜尋修正）
- [x] Phase 3：17 家銀行幣別爬蟲 + FISC 月更流程自動化 + SQLite 資料管線（1,971 筆位置，0 筆 null 幣別）
- [ ] F3：幣別篩選 UI（在篩選面板加幣別 checkbox，過濾地圖標記）
