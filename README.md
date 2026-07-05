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
| **requests（+ BeautifulSoup）** | 取得 17 家銀行幣別資料：8 家官網可程式化擷取，8 家經官網調查後套用全行固定幣別，1 家人工記錄，無需 Selenium |
| **SQLite** | 輕量資料管線，整合 FISC 位置與銀行幣別資料，方便月更維護 |
| **Leaflet.js** | 開源地圖套件，不需 API key，打包成靜態網站不需後端 |
| **GitHub Pages** | 靜態網站免費部署，朋友可直接透過 URL 使用，無需安裝任何東西 |

## 資料來源

- **ATM 位置**：財金資訊股份有限公司（FISC）「自動化服務機器業務提領外幣ATM位置查詢一覽」，2026/5/31 更新
- **Geocoding**：[內政地理資訊圖資雲整合服務平台 TGOS](https://www.tgos.tw/) 批次地址比對服務
- **幣別資料**：17 家銀行（台銀、土銀、合庫、一銀、彰銀、華南、兆豐、國泰世華、台新、新光、永豐、玉山、中信、台北富邦、上海商銀、台灣企銀、元大）。其中 8 家由官網程式化擷取（國泰世華、玉山、華南、兆豐、永豐、新光、台新、一銀），8 家經官網調查確認全行幣別一致後直接套用（台銀、土銀、合庫、彰銀、中信、台北富邦、台灣企銀、元大），1 家人工記錄（上海商銀，僅 2 台）

## 專案結構

```
tw-fx-atm/
  data/
    raw/                    ← 原始 PDF（FISC 月更；.gitignore，本機保存）
    processed/
      atm_data.csv          ← PDF 解析後的 CSV（.gitignore，本機產生）
      atm_geocoded.json     ← 加入經緯度後的 JSON
      atm_with_currencies.json  ← 最終輸出（前端資料來源）
      *_currencies.json     ← 各銀行幣別結果（×17）
      sample_validation*.csv ← geocoding 抽樣驗證與人工核對紀錄
    atm.db                  ← SQLite（.gitignore，需本機產生）
  scripts/
    parse_pdf.py            ← PDF → CSV
    update_from_fisc.py     ← FISC 月更自動化流程
    geocode.py              ← CSV → JSON with lat/lng
    geocode_test.py         ← geocoding 小樣本測試
    export_for_tgos.py      ← 產生 TGOS 批次比對上傳檔
    import_tgos_result.py   ← 匯入 TGOS 比對結果
    validate_and_fix_geocoding.py ← 座標驗證修復 + 抽樣輸出
    review_sample_maps.py   ← 抽樣座標人工核對輔助工具
    merge_currencies.py     ← FISC 位置 × 銀行幣別 → atm_with_currencies.json
    scrape_*.py (×17)       ← 各銀行幣別取得（爬蟲／調查套用／手動）
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

## 資料品質與維護

### 月更流程

FISC 每月更新來源 PDF。`update_from_fisc.py` 一次完成：下載最新 PDF → pdfplumber 解析 → 與現有 `atm_data.csv` 做全欄位 diff。無差異就直接結束；有差異時更新 CSV 與 `atm_geocoded.json`——同「裝設地點」的新筆會繼承舊座標，真正的新點標記 `pending`，需再跑 `geocode.py` 補座標（前端會自動過濾無座標的點，不會顯示錯誤位置）。腳本最後輸出 diff report，列出每一筆新增與移除。之後重跑 `merge_currencies.py` 與 SQLite 四步即完成月更。

### Geocoding 驗證

初始批次 1,962 筆地址經 TGOS 批次比對，1,960 筆取得可用座標（99.9%，餘 2 筆地址無法比對）。「有座標」不等於「座標正確」，所以另有兩層驗證：

1. **程式檢查**（`validate_and_fix_geocoding.py`）：修復多重座標（含 `;` 的取第一值）、列出無座標筆、檢查座標是否落在台灣含離島的合理範圍（金門經度例外處理）。
2. **人工抽樣**（`review_sample_maps.py`）：隨機抽 30 筆逐一開 Google Maps 核對，判定標準是「點位落在分行／裝設場域附近即通過」。本輪結果 30/30 通過。依 rule of three，30 筆全過只能支持「整體錯誤率上界約 10%（95% 信心）」，不宣稱全數正確——取捨與統計討論詳見 `docs/06`。

### 爬蟲失敗時的行為（現狀與已知限制）

誠實現狀：**17 支 `scrape_*.py` 都沒有 try/except，也沒有失敗通知機制**。失敗時直接拋出例外中止（fail loud）。這在目前「每月人工執行、人工確認輸出筆數」的流程下可接受，原因是：

- 所有腳本都在**成功抓完後才寫出** `*_currencies.json`，中途失敗不會覆蓋上一版結果，`merge_currencies.py` 會沿用最後一次成功的資料（last known good）。
- 17 支中只有 8 支實際連網：7 支用 `requests`（均設 `timeout=20` 並檢查 `raise_for_status`），1 支（一銀）用 `urllib` 且**未設 timeout**，理論上可能無限等待。其餘 8 支為官網調查後套用全行固定幣別、1 支為人工記錄，不經網路。

已知限制：

- 銀行官網改版會讓對應爬蟲直接中斷，目前**沒有自動偵測或告警**，依賴月更時人工執行發現。
- 全行固定幣別的 8 家銀行，若個別機台幣別有差異，資料無法反映（來源本身即無機台級明細，詳見各腳本 docstring 的調查記錄）。
- 一銀官網僅說明 USD/JPY 全機台支援、CNY/HKD「部分機台」，故保守只標 USD/JPY，可能低估。

## 開發進度

- [x] Phase 0：技術選型與資料來源確認
- [x] Phase 1 MVP：PDF 解析 → TGOS Geocoding（1,960/1,962 筆）→ Leaflet 地圖 + 銀行篩選 → GitHub Pages
- [x] Phase 1.5：裝置定位 + 附近 ATM 面板（Geolocation API + Haversine 距離排序）
- [x] Phase 2：UI 改善（全螢幕地圖、懸浮頂欄、底部滑入面板、FAB 文字標籤、CJK 搜尋修正）
- [x] Phase 3：17 家銀行幣別覆蓋 + FISC 月更流程自動化 + SQLite 資料管線（2026/6 更新後 1,978 筆位置，0 筆 null 幣別）
- [x] F3：幣別篩選 UI（篩選面板幣別 chips，清單由資料動態產生，與銀行篩選 AND 疊加）
