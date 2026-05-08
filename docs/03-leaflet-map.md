# Step 03 — 前端地圖：Leaflet.js

> 這份文件記錄 `index.html` 的設計思路、每段程式碼的概念，以及為什麼不需要後端。

---

## 為什麼不需要後端？

**一般需要後端的情況**：資料在伺服器的資料庫，每次查詢都要瀏覽器 → 後端 → 資料庫 → 後端 → 瀏覽器跑一圈。

**本專案的情況**：`atm_geocoded.json` 是靜態檔案，只有 1,962 筆（約 500KB）。頁面載入時一次全部讀進瀏覽器記憶體，之後所有篩選都是 JavaScript 在記憶體裡過濾陣列，不需要再問任何人。

需要後端的條件：資料量太大、需要保護資料、需要寫入、或資料即時在變。這個專案三個都不符合。

---

## 整體架構

```
index.html
  │
  ├── <link> Leaflet CSS（CDN）
  ├── <script> Leaflet JS（CDN）
  │
  ├── <header> 標題 + 顯示筆數
  ├── <div id="filter-bar"> 銀行篩選 checkbox
  ├── <div id="map"> 地圖容器
  │
  └── <script>
        1. 初始化地圖
        2. fetch() 載入 JSON
        3. 為每個座標建立 marker
        4. 動態產生篩選 UI
        5. 監聽 checkbox → 更新 marker 顯示
```

---

## Leaflet.js 基礎

### 引入方式

不需要安裝，直接從 CDN 引入：

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

CDN（Content Delivery Network）= 別人幫你放在網路上的檔案，直接引用就好。

### 初始化地圖

```javascript
const map = L.map("map").setView([23.97, 120.97], 8);
```

- `L.map("map")` → 把 id 為 `map` 的 `<div>` 變成地圖容器
- `.setView([緯度, 經度], 縮放等級)` → 台灣中心點，縮放 8 剛好看到全島

### 加底圖

```javascript
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '© OpenStreetMap',
  maxZoom: 19,
}).addTo(map);
```

Leaflet 的底圖是由一片片「磁磚圖片」拼起來的。`{s}` = 子域名（分散伺服器負載），`{z}/{x}/{y}` = 縮放等級和磁磚座標，Leaflet 會自動計算和請求正確的圖片。

### 加圖釘

```javascript
L.marker([lat, lng]).addTo(map);
```

一行就能在地圖上畫一個圖釘。

### Popup（點擊彈出資訊）

```javascript
marker.bindPopup(`<strong>臺灣銀行</strong><br>台北市中正區重慶南路一段120號`);
```

`bindPopup()` 傳入 HTML 字串，點擊圖釘就會顯示。

---

## 自訂圖釘顏色

Leaflet 預設圖釘是藍色，全部一樣顏色無法區分銀行。用 `L.divIcon` 可以放任意 HTML/SVG 當圖釘：

```javascript
function makeIcon(color) {
  const svg = `<svg ...><path fill="${color}" .../></svg>`;
  return L.divIcon({
    html: svg,
    iconSize: [24, 36],
    iconAnchor: [12, 36],    // 圖釘底端對齊座標點
    popupAnchor: [0, -36],   // popup 從圖釘頂端往上彈出
  });
}
```

`iconAnchor` = 圖片哪個像素對應到地圖座標。圖釘高 36px，底端是 `[12, 36]`（x=中間，y=最底）。

---

## fetch() 載入 JSON

```javascript
fetch("data/processed/atm_geocoded.json")
  .then(r => r.json())
  .then(data => {
    // data 是一個 JavaScript 陣列，每個元素是一筆 ATM 資料
  });
```

`fetch()` 是瀏覽器內建的 HTTP 請求函式，回傳 Promise（非同步）。`.then()` 是「等完成後做」的寫法。

**為什麼不能直接用 `file://` 開 HTML？**
瀏覽器的安全機制（CORS）不允許 `file://` 頁面用 `fetch()` 讀本機檔案。要用 HTTP server：

```bash
python3 -m http.server 8000
# 然後開 http://localhost:8000
```

GitHub Pages 上就不需要，因為那是真正的 HTTP。

---

## 動態產生篩選 UI

```javascript
banksOrdered.forEach(bank => {
  const label = document.createElement("label");
  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.checked = true;
  cb.addEventListener("change", () => {
    if (cb.checked) activeSet.add(bank);
    else            activeSet.delete(bank);
    redrawMarkers();
  });
  label.appendChild(cb);
  label.appendChild(document.createTextNode(bank));
  bar.appendChild(label);
});
```

**`document.createElement`**：用 JavaScript 動態建立 HTML 元素，不需要在 HTML 裡寫死。因為銀行清單是從資料來的，不能硬寫。

**`addEventListener("change", ...)`**：監聽 checkbox 狀態改變事件，改變時更新 `activeSet`（一個 `Set`，存目前勾選的銀行名稱）並重繪地圖。

---

## marker 的顯示/隱藏

```javascript
function redrawMarkers() {
  allMarkers.forEach(({ marker, bank }) => {
    if (activeSet.has(bank)) {
      if (!map.hasLayer(marker)) marker.addTo(map);
    } else {
      if (map.hasLayer(marker)) map.removeLayer(marker);
    }
  });
}
```

**不是刪掉再重建**，而是把 marker 加入地圖或從地圖移除。marker 物件一直存在記憶體裡，只是顯示/隱藏。這樣比每次重建快很多。

---

## 資料清洗：#N/A 問題

原始資料中有 61 筆 `銀行名稱` 是 `#N/A`（代號 012，Excel 計算錯誤留下的），有些是空字串。

```javascript
function displayBank(record) {
  const name = record["銀行名稱"];
  if (!name || name === "#N/A") return `代號 ${record["代號"]}`;
  return name;
}
```

顯示為「代號 012」，座標還是用，不浪費這筆資料。

---

## 本機測試 vs GitHub Pages

| | 本機 | GitHub Pages |
|---|---|---|
| 啟動方式 | `python3 -m http.server 8000` | push 到 main 後自動 |
| 網址 | `http://localhost:8000` | `https://xxx.github.io/tw-fx-atm` |
| fetch() | 需要 HTTP server 才能用 | 直接可用 |
| 手機測試 | 同 WiFi 下用電腦 IP | 任何網路都可以 |

---

## 成果

| 項目 | 數值 |
|------|------|
| 顯示筆數 | 1,913 筆（有座標的全部顯示）|
| 銀行數 | 18 間 |
| 篩選方式 | checkbox + 全選/全消 |
| 不需要後端 | 是 |
| 輸出 | `index.html` |

---

## 下一步

1. `git add index.html && git commit && git push`
2. GitHub Repo → Settings → Pages → Branch: main / root → Save
3. 等約 1 分鐘 → `https://jill-chiou.github.io/tw-fx-atm` 上線

---

## 本步驟學到的概念

- **Leaflet.js**：輕量地圖套件，CDN 引入，不需安裝
- **Tile Layer**：底圖由磁磚圖片拼成，Leaflet 自動管理
- **L.divIcon**：用 SVG/HTML 自訂圖釘外觀
- **fetch() + Promise**：非同步載入 JSON 資料
- **CORS / file:// 限制**：為什麼本機要起 HTTP server
- **動態 DOM 操作**：`createElement` + `addEventListener` 產生 UI
- **Set**：用來儲存「目前勾選的銀行」，查詢是否存在是 O(1)
- **marker.addTo / removeLayer**：顯示/隱藏比刪除重建快
