# 台新銀行幣別爬蟲筆記

> 建立日期：2026-05-11

---

## 1. 問題背景

Session 交接文件（`00-handoff-2026-05-11-windows.md`）記錄台新銀行有 **1,026 台 FISC 外幣 ATM**，完成後可將覆蓋率從 36% 提升至 89%，是最大單一增量。但官網「完全無幣別資訊」，建議用 Network tab 找 API。

---

## 2. 調查過程

### 2.1 官網結構

台新的分行據點查詢入口在：

```
https://www.taishinbank.com.tw/TSB/service-and-support/branch-finder/
```

該頁共 26 頁，每頁 4 筆，合計 **104 個分行**。

Form action 是 `/TSB/search/service-items/`，但 service 選項只有無障礙服務（service01–service11），**沒有「外幣ATM」篩選**。

### 2.2 發現幣別 API

在頁面 inline JS（`qryWait` 函數）中發現：

```javascript
$.ajax({
    url: 'https://www.taishinbank.com.tw/eServiceA/misc/aboutLocationCurrency.jsp',
    type: 'post',
    data: { branchCode: branchId, locale: locale },
    ...
});
```

這個 API 可以呼叫，**無需登入或特殊 header**：

```python
POST /eServiceA/misc/aboutLocationCurrency.jsp
data: branchCode=001, locale=

回傳: {"日圓JPY": "1000,5000,10000", "美元USD": "1,5,10,20,50,100", ...}
```

分行代碼在 `qryWait('001')` 這樣的呼叫中提取，掃描 26 頁後共得到 **104 個代碼**（001–114，有跳號）。

### 2.3 地址來源（v1）

每個分行項目的 HTML 中有 Google Maps URL：

```
https://www.google.com.tw/maps/place/10491%E5%8F%B0%E5%8C%97%E5%B8%82%E4%B8%AD%E5%B1%B1%E5%8D%80.../@25.055,121.522,...
```

從 URL path 的 percent-encode 部分可解碼出完整地址，從 `@lat,lng` 拿到座標。

### 2.4 正確入口：ATM/補摺機據點（v2）

v1 走的是「分行據點」路線，後來發現台新有專屬的 **ATM 查詢頁面**：

```
https://www.taishinbank.com.tw/TSB/service-and-support/atm-location/
```

該頁面有外幣服務的 checkbox 篩選（美元/日圓/人民幣/歐元/存外幣），且查詢結果是**機台層級**（含全家、萊爾富等非分行場所）。

這個頁面的 HTML 透過 `<script src>` 載入了一個 JS 檔：

```
https://www.taishinbank.com.tw/eServiceA/misc/AboutLocationAtm.jsp?t={timestamp}
```

此 JSP 用 `document.writeln()` 注入整個 UI（包含 CSS、表單、分頁），並在底部嵌入查詢邏輯。其中的 `getCustomAtm()` 函數呼叫了真正的資料 API：

```javascript
// 注意 functoin 是原始碼的 typo，不是筆誤
$.ajax({
    url: "https://www.taishinbank.com.tw/eServiceA/misc/GetCustomATM.jsp",
    type: "post",
    data: {
        city: city,          // 縣市名（空字串 = 全台）
        region: region,      // 行政區（空字串 = 全部）
        atmService: atmService, // 11=USD 12=JPY 13=CNY 16=EUR 17=存外幣
        pageNum: pageNum,    // 頁碼，每頁 10 筆
        functoinName: "CustomAtm",
        latlon: latlon       // GPS 座標（離我最近功能用）
    }
});
```

### 2.5 GetCustomATM.jsp 回傳格式

```json
{
  "customAtmList": [
    {
      "SITE_NAME": "全家-康福",
      "CITY": "台北市",
      "REGION": "內湖區",
      "ADDRESS": "康樂街87號",
      "LATITUDE": "25.069568",
      "LONGITUDE": "121.618904",
      "ATM_GET": "y",
      "ATM_SAYE": "y",
      "USD": "",
      "JPY": "y",
      "CNY": "",
      "EUR": "",
      "FOREIGN_SAVE": "",
      "NFC": "y",
      "BARRIERFREE": "y"
    }
  ],
  "customAtmCount": 3524,
  "maxNum": 353,
  "pageNum": 1,
  "startRow": 1,
  "endRow": 10
}
```

- `customAtmCount`：全台台新 ATM 總數（含台幣 ATM）= 3,524
- `maxNum`：總頁數 = 353（每頁 10 筆）
- 幣別欄位：`"y"` 表示支援，`""` 表示不支援

---

## 3. 技術坑

### Pit 1：SSL 憑證

```
SSLError: certificate verify failed: Missing Subject Key Identifier
```

台新網站 SSL 憑證缺少 Subject Key Identifier，需 `verify=False`（`urllib3.disable_warnings()` 消除警告）。

### Pit 2：CJK 字元與 `\b` 邊界

幣別 API 回傳的 key 格式：`"日圓JPY"`, `"美元USD"` 等。

最初用 `re.compile(r"\b([A-Z]{3})\b")` 擷取幣別代碼，**完全沒有 match**。

原因：Python 3 的 `re` 模組中，CJK 字元屬於 `\w`（Unicode word character），所以 `幣JPY` 之間 `幣`→`J` 並非「word boundary」，`\b` 不成立。

**修正**：改為 `r"([A-Z]{3})$"`（key 尾端取 3 個大寫字母）。

### Pit 3：空 branch 造成萬用符合

部分分行在 HTML 中沒有名稱（例如某些偶數代碼的分行），scraper 產出的 records 有 `branch: ""`。

Merge 腳本的配對邏輯是 `branch_or_fisc in fisc_loc`，而 `"" in 任意字串` 永遠為 True，導致 `("台新", "")` 這個 key 讓台新所有 1,026 個 FISC 紀錄都配到，顯示「52% 覆蓋率」但其實是錯誤的萬用配對。

**修正**：merge 腳本 `build_lookup` 中加入 `if not branch: continue`。

### Pit 4：幣別資料是分行層級，非 ATM 層級

`aboutLocationCurrency.jsp` 回傳的是**分行臨櫃換鈔資料**，面額（如 USD $1/$5/$10）也是紙鈔面額，不是 ATM 特有資訊。

這帶來的問題見 §4。

---

## 4. 覆蓋率缺口分析

| 項目 | 數量 |
|------|------|
| FISC 台新外幣 ATM 總數 | 1,026 |
| 台新分行（branch-finder 頁面）| 104 |
| 分行中有地址/名稱的 | 74 |
| 目前實際 merge 上的 ATM | ~74–100（分行同名配對）|
| 未配對的 ATM | ~920+ |

**為何 920+ 台配不到？**

Merge 邏輯是用分行名稱（如「敦南分行」）當子字串，比對 FISC 的 `裝設地點`。

- **可配對**：裝設地點含分行名稱的 → 例如「台新銀行敦南分行」
- **不可配對**：裝設地點是非分行場所 → 例如「7-ELEVEN XX店」、「全家便利商店XX門市」、「台北醫學大學」等

台新有大量 ATM 設在便利商店、商場、學校、醫院等，這些 FISC `裝設地點` 中不含任何分行名稱，無法透過分行名稱配對。

---

## 5. 解決方案評估

### 方案 A：座標距離配對（較精準）

- 台新分行 74 筆有 lat/lng
- `atm_geocoded.json` 也有每台 ATM 的座標（TGOS 地理編碼）
- 對每台未配對的台新 FISC ATM，找最近的台新分行（例如 500m 以內），套用該分行幣別

優點：精準；缺點：同一分行附近可能有多台不同功能 ATM，需設合理距離閾值。

### 方案 B：預設幣別 fallback（較保守）

台新 ATM 服務頁明確記載外幣 ATM 支援：**USD、JPY、RMB（CNY）、EUR**。

對所有未透過分行名稱配對的台新 FISC ATM，套用 `["CNY", "EUR", "JPY", "USD"]`。

優點：簡單可行，且 FISC 的紀錄本來就是外幣 ATM；  
缺點：比實際資訊保守（主要分行支援 9 種幣別，此法只給 4 種）。

### 建議做法

**兩段式**：
1. 先用分行名稱配對（精確版，有名稱的給完整幣別清單）
2. 剩餘未配對的台新 ATM → 套用 fallback `["CNY", "EUR", "JPY", "USD"]`

預計覆蓋率：分行配對 ~100 + fallback ~920 = ~1020 → 新增 ~1020 筆，覆蓋率從 36% → ~88–89%。

---

## 6. 輸出檔案（v2 機台層級版）

```
data/processed/taishinbank_currencies.json
```

- 共 **1,011 筆**外幣 ATM（從 3,524 台全部台新 ATM 中篩選）
- 幣別分布：JPY 999、USD 166、CNY 43、EUR 26
- 每筆有完整地址（縣市+區域+街道）和 lat/lng

### v1 → v2 演進

| 版本 | API | 筆數 | 層級 | 精確配對 FISC |
|------|-----|------|------|-------------|
| v1（aboutLocationCurrency.jsp）| 分行幣別 | 102 | 分行 | ~190 |
| v2（GetCustomATM.jsp）| 機台幣別 | 1,011 | ATM | 1,007 |

---

## 7. 待辦

- [x] 實作方案 B fallback（`merge_currencies.py`）
- [x] 找到機台層級 API，覆蓋率提升至 1026/1026
- [x] 將 `*_currencies.json` 加入 git tracking

---

## 8. 跨平台注意事項

### 遺失的幣別檔案

所有 `data/processed/*_currencies.json`（skbank, megabank, cathaybk, ctbc, esunbank, hncb, sinopac）都被 `.gitignore` 排除，上一個 session 在 Mac 產出的檔案無法在 Windows 上取用。

**建議修正 `.gitignore`**：

```diff
 data/processed/*
 !data/processed/atm_geocoded.json
+!data/processed/*_currencies.json
+!data/processed/atm_with_currencies.json
```

這樣每次跑完爬蟲 commit，下次換機器就不需要重跑。

### Script 路徑

所有爬蟲腳本輸出使用 `Path(__file__).parent.parent / "data/processed/"` ——相對路徑，跨平台無問題。

調試時避免寫 hardcoded Windows 路徑（如 `C:\Users\user1\Python\temp\`），改用 `Path(__file__).parent.parent / "tmp/"` 或直接寫入 `data/processed/`。
