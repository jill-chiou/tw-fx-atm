# Step 02 — Geocoding：地址轉座標

> 這份文件記錄 geocode.py 的設計思路、每段程式碼的概念，以及與其他台灣開源地圖專案的比較。

---

## 台灣開源地圖專案怎麼處理 Geocoding？

| 專案 | Geocoding 方式 | 前端地圖 |
|------|---------------|---------|
| **g0v/twgeojson** | 不做 geocoding，直接用行政區 GeoJSON（縣市邊界多邊形） | Leaflet / D3 |
| **OsmHackTW** | 依賴 OSM 社群資料，用 Nominatim 查詢 | Leaflet |
| **geocoder（Python 套件）** | 直接包裝 TGOS API，最準確 | — |
| **本專案（tw-fx-atm）** | Nominatim（免費），TGOS key 到了可升級 | Leaflet（規劃中）|

**業界主流**：台灣政府/學術專案幾乎都用 TGOS（內政部國土測繪中心）。個人/社群專案則用 Nominatim 或 Google Maps API。

**本專案的決策理由**：
評估了三個方案——Google Maps API（有費用）、TGOS（官方最準但等申請）、Nominatim（免費但需要調整 query 格式）。為了讓專案能快速推進，先用 Nominatim，並設計了之後可以只換掉 `geocode()` 函式就能切換服務的架構。

---

## 整體架構

```
data/raw/atmfc.pdf
        │
        ▼  parse_pdf.py（pdfplumber）
data/processed/atm_data.csv
        │
        ▼  geocode.py（Nominatim API）
data/processed/atm_geocoded.json
        │
        ▼  index.html（Leaflet.js）──── GitHub Pages
           地圖 + 銀行篩選 UI
```

每一層獨立、可替換，這種設計叫**關注點分離（Separation of Concerns）**。

---

## parse_pdf.py 解析

### 這段做什麼？

把 PDF 表格轉成 CSV 的過程：

```
PDF（XY 座標上的文字碎片）→ pdfplumber 幾何重組 → 表格結構 → CSV
```

pdfplumber 不是「讀 PDF 文字」，而是分析文字的 XY 座標與線條，推斷哪些文字屬於同一格。

### 關鍵細節

```python
for row in table[1:]:   # 跳過每頁重複的表頭
```

PDF 共 86 頁，每頁都有表頭列（代號、銀行名稱⋯）。`[1:]` 是 Python 的切片語法，意思是「從第 1 個元素開始」（第 0 個是表頭），避免 86 個表頭混進資料。

```python
with open(OUT_PATH, "w", encoding="utf-8-sig") as f:
```

`utf-8-sig` = UTF-8 + BOM（Byte Order Mark）。開頭的 3 個特殊 byte（`\xef\xbb\xbf`）是讓 Excel 認出「這是 UTF-8，用正確編碼開啟中文」。

> **踩到的坑**：正是因為 Windows 終端機無法正確顯示 UTF-8 中文，導致我用眼睛判斷欄位名時把「裝設地點」誤看成「設施地點」，造成 KeyError。教訓：永遠用程式碼驗證欄位名，不要靠眼睛看終端輸出。

---

## geocode.py 解析

### 核心概念：Geocoding

Geocoding = 把文字地址轉成地球上的一個點（緯度 lat / 經度 lng）。有了座標，才能在地圖上畫圖釘。

---

### 段落一：正則表達式（Regular Expression）

```python
ADDR_RE = re.compile(
    r'^(?P<city>[^市縣]+[市縣])'
    r'(?:[^區鄉鎮市]+[區鄉鎮市])?'
    r'(?P<road>.+?[路街道](?:[\d一二三四五六七八九十百千]+段)?(?:\d+巷)?(?:\d+弄)?)'
    r'(?P<num>\d+(?:-\d+)?)號'
)
```

正則表達式是**文字的模板**，描述「我要抓的字長什麼形狀」。

| 片段 | 意思 | 比對範例 |
|------|------|---------|
| `^` | 從字串開頭 | |
| `(?P<city>[^市縣]+[市縣])` | 命名群組 `city`：抓到第一個「市」或「縣」 | `台北市`、`彰化縣` |
| `(?:[^區鄉鎮市]+[區鄉鎮市])?` | 區/鄉/鎮，`?` 代表可選 | `中正區`（有些地址沒有） |
| `(?P<road>.+?[路街道]...)` | 命名群組 `road`：路名含段/巷/弄 | `重慶南路一段`、`中央路2巷` |
| `[\d一二三四五六七八九十百千]+段` | 段的前綴可以是阿拉伯或中文數字 | `2段`、`一段` |
| `(?P<num>\d+(?:-\d+)?)號` | 命名群組 `num`：門牌，含連字格式 | `120號`、`62-5號` |

**為什麼要解析地址？** Nominatim 不接受台灣原始格式（`台北市中正區重慶南路一段120號`），但接受「門牌號放最前面」（`120 重慶南路一段 台北市`）。這是這個專案最關鍵的發現，透過測試找出來的。

---

### 段落二：parse_addr() — 地址解析函式

```python
def parse_addr(addr: str) -> str | None:
    addr_clean = addr.split('、')[0]  # 多門牌只取第一個
    m = ADDR_RE.match(addr_clean)
    if m:
        return f"{m.group('num')} {m.group('road')} {m.group('city')}"
    m2 = ROAD_RE.match(addr_clean)   # fallback：沒有門牌號的地址
    if m2:
        return f"{m2.group('road')} {m2.group('city')}"
    return None
```

`-> str | None` 是 **型別提示（Type Hint）**：明確告訴讀程式碼的人「這個函式可能回傳 None（失敗）」，不需要看函式內容就能知道要處理失敗情況。

`addr.split('、')[0]`：部分地址是 `中山東路一段27號7樓、27號8樓`（ATM 跨兩個門牌），取第一個就夠用。

**Fallback 設計**：當正則找不到門牌號時（如 `台北市大安區清水路`，只有路名），退而求其次用路名 + 城市查詢。寧可精確度低一點，也不要完全放棄這筆資料。

---

### 段落三：geocode() — HTTP API 呼叫

```python
params = urllib.parse.urlencode({
    "q": q,
    "format": "json",
    "limit": 1,
    "countrycodes": "tw",
})
url = "https://nominatim.openstreetmap.org/search?" + params
```

`urlencode` 把 Python dict 轉成 **URL Query String**：
- 輸入：`{"q": "120 重慶南路一段 台北市"}`
- 輸出：`q=120+%E9%87%8D%E6%85%B6%E5%8D%97%E8%B7%AF...`（中文被 URL 編碼）

這是 HTTP GET 請求的標準格式。

```python
headers={"User-Agent": "tw-fx-atm/0.1 (dodiddone0518@gmail.com)"}
```

**User-Agent**：每個 HTTP 請求都要告訴伺服器「我是誰」。Nominatim 的使用政策要求提供可聯絡的識別資訊，以便追蹤濫用行為。沒有 User-Agent 會被拒絕。

```python
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
except Exception as e:
    print(f"  [ERROR] {e}")
return None, None
```

`timeout=10`：10 秒沒回應就放棄。`try/except` 是**防禦性程式設計**——網路隨時可能斷，API 隨時可能回錯。不能讓一筆失敗炸掉整個 1,962 筆的批次工作。

---

### 段落四：main() — 批次控制與 Rate Limiting

```python
time.sleep(1.1)  # Nominatim: max 1 req/sec
```

**Rate Limiting（速率限制）**：Nominatim 是免費公共服務，規定每秒最多 1 次請求。睡 1.1 秒（比 1 多一點緩衝）是：
- 尊重 API 服務條款
- 避免自己的 IP 被封鎖
- 避免對公共服務造成不必要的負載

```python
json.dump(results, f, ensure_ascii=False, indent=2)
```

`ensure_ascii=False`：預設 JSON 會把中文轉成 `台北`，加了這個參數後中文直接保留，人類可讀。

---

## 成果數字

| 版本 | 成功率 |
|------|--------|
| 第一版 regex（只支援中文段數） | 86% |
| 修正後（支援阿拉伯數字段、巷弄、連字號門牌） | **98%** |
| **正式跑完全部 1,962 筆（2026-05-07，Mac）** | **97.5%（1,913 筆）** |

主要改善：`2段` → 支援、`2巷100號` → 支援、`62-5號` → 支援、多地址單元 → 取第一個。

---

## 踩到的坑（2026-05-07 Mac 補跑）

### 坑 1 — 全部 GEO_FAIL：SSL 憑證問題

**症狀**：跑完 1,962 筆，成功 0 筆，每筆都出現：
```
[ERROR] <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate>
```

**原因**：Mac 上用官方 `.pkg` 安裝的 Python，**不會自動使用系統的 SSL 憑證**，需要手動安裝 Python 自己的憑證包（certifi）。這是 Mac + Python 的老問題，Windows 不會遇到。

**解法**：執行 Python 安裝目錄下的修復腳本：
```bash
/Applications/Python 3.12/Install Certificates.command
```
這個指令會安裝/更新 `certifi` 套件，並建立 symlink 讓 Python 的 `urllib` 找得到正確的憑證。

**教訓**：Mac 上 Python 第一次打 HTTPS API 之前，先確認憑證有裝。症狀就是所有 API 請求都失敗，錯誤訊息含 `CERTIFICATE_VERIFY_FAILED`。

---

### 坑 2 — API 打太多次被 rate limit，重跑要從頭來

**症狀**：原本的 `geocode.py` 沒有進度儲存，中途中斷（429 太多、手動 Ctrl+C、任何錯誤）就要從第 1 筆重跑。1,962 筆跑 36 分鐘，中斷一次就浪費一輪。

**解法**：加入**斷點續跑**機制。

每跑完一筆，立刻把結果寫進 `data/processed/atm_geocoded_progress.jsonl`（每行一筆 JSON）。重新啟動時先讀這個檔，算出哪些 index 已完成，直接跳過。全部跑完後自動刪除進度檔，只留最終的 `atm_geocoded.json`。

```python
# 讀取進度
done = load_progress()   # 回傳 {index: record}

# 跑的時候跳過已完成的
for i, row in enumerate(rows):
    if i in done:
        continue
    # ... geocode ...
    progress_file.write(json.dumps(rec) + "\n")
    progress_file.flush()   # 立刻寫入磁碟，不要等 buffer
```

**`flush()` 為什麼重要**：Python 的檔案寫入預設有 buffer，不一定馬上寫到磁碟。加了 `flush()` 才能保證程式被強制中止時，最後那幾筆不會遺失。

**教訓**：任何跑超過 5 分鐘的批次作業，都應該加進度儲存。代價很低（多幾行程式碼），效益很高（中斷不用從頭來）。

---

## 踩到的坑（2026-05-08 regex 除錯）

### 坑 3 — 區名包含「鎮/市」字，regex 提前停止

**症狀**：高雄市前鎮區、桃園市平鎮區、台南市新市區等地址，geocoding query 變成 `355 區保泰路 高雄市`，路名前面多一個「區」字，Nominatim 查不到。

**原因**：原本的區段 pattern 是 `[^區鄉鎮市]+[區鄉鎮市]`，意思是「遇到 區鄉鎮市 就停」。`前鎮區` 裡的「鎮」符合停止條件，regex 吃到 `前鎮` 就停了，把 `區` 留給路名，造成 `區保泰路`。

**第一次嘗試修法**（失敗）：把 pattern 改成 `.+[區鄉鎮]`（貪婪，不含市）。
結果：縣轄市地址（彰化縣彰化市、南投縣南投市等）壞了——這些地址的區名結尾是「市」，拿掉市就無法正確吃掉區名，「市」洩漏進路名。

**正確修法**：`(?:.+(?:[區鄉鎮]|(?<![區鄉鎮])市))?`

邏輯：貪婪匹配，結尾必須是「區/鄉/鎮」，或「前一個字不是區鄉鎮的市」（負向回顧斷言 lookbehind）。

| 地址 | 區名 | 說明 |
|------|------|------|
| 高雄市前鎮區保泰路 | 前鎮區 | 貪婪往後取，最後一個有效停止點是「區」 |
| 彰化縣彰化市成功路 | 彰化市 | 「市」前面是「化」，不是區鄉鎮，視為縣轄市 |
| 台北市信義區市府路 | 信義區 | 「市」前面是「區」，lookbehind 失敗，不停在市，往前退到「區」 |

**教訓**：地名 pattern 不能用簡單的「遇到特定字停止」邏輯，因為台灣地名本身就含有這些字（前鎮、平鎮、新市）。遇到解析率不明原因下降時，先印出 query 字串逐一比對原始地址。

---

## 本步驟學到的概念

- **Regular Expression**：文字模板，用來從非結構化字串中擷取結構化資料
- **HTTP GET / Query String**：如何用程式碼呼叫外部 API
- **Rate Limiting**：使用公共 API 的禮節與限制
- **Defensive Programming**：try/except、timeout、fallback
- **Type Hints**：`str | None` 讓程式碼意圖更清晰
- **Separation of Concerns**：每個函式只做一件事，方便之後替換 geocoding 服務
- **Mac SSL 憑證**：官方 Python `.pkg` 安裝後需要手動跑 `Install Certificates.command`
- **斷點續跑（Checkpoint）**：`.jsonl` 逐行存進度 + `flush()` 確保寫入，批次作業必備
