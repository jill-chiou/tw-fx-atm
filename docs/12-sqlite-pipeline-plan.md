# A1 計畫：SQLite Pipeline

> 建立日期：2026-05-13
> 狀態：待實作
> 目標：將 JSON-based merge pipeline 改寫為 SQLite 資料庫，提升可維護性與備審技術廣度。

---

## 為什麼要做

目前的資料流是：

```
atm_geocoded.json + *_currencies.json  →  merge_currencies.py  →  atm_with_currencies.json
```

全部用 Python dict 做 join，不易查詢、不易追蹤來源、每次重新 merge 都要重跑整個流程。

改為 SQLite 的好處：
- **可查詢**：用 SQL 直接分析幣別覆蓋率、缺漏銀行、Gap B 統計，不用再寫 Python 計數邏輯
- **來源追蹤**：每筆資料有 `source_file` + `scraped_at`，月更後可以追蹤哪些筆是新增/異動
- **面試加分**：能展示「資料庫 schema 設計 + ETL pipeline + ORM-free raw SQL + export 給前端」的完整技術棧
- **前端不動**：export 出來的 `atm_with_currencies.json` 格式完全不變

---

## Schema 設計

### Table 1：`atm_locations`

存 FISC 位置資料（骨幹），每台 ATM 一筆。

```sql
CREATE TABLE atm_locations (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  bank_code   TEXT NOT NULL,          -- FISC 代號（e.g. "007"）
  bank_name   TEXT NOT NULL,          -- 銀行名稱（e.g. "第一商業銀行"）
  location    TEXT,                   -- 裝設地點（e.g. "信義分行"）
  city        TEXT,                   -- 縣市（e.g. "台北市"）
  address     TEXT,                   -- 地址
  lat         REAL,                   -- geocoding 結果
  lng         REAL,
  source      TEXT NOT NULL           -- 'fisc' | 'bank_website'（Gap B）
);
```

**為什麼有 `source`？**
Gap B 的 22 筆是官網直接補入、沒有 FISC 記錄的 ATM（`bank_website`）。
保留這個欄位讓前端或分析腳本可以選擇性呈現。

---

### Table 2：`bank_currencies`

存每台 ATM 支援的幣別，正規化為一幣一筆（1NF）。

```sql
CREATE TABLE bank_currencies (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  atm_id      INTEGER NOT NULL REFERENCES atm_locations(id),
  currency    TEXT NOT NULL,          -- 'USD' | 'JPY' | 'CNY' | 'EUR' | 'HKD'
  is_fallback INTEGER NOT NULL DEFAULT 0  -- 1 = 用 FALLBACK_CURRENCIES 填入，非逐台確認
);
```

**為什麼拆成一幣一筆？**
方便用 `GROUP BY currency` 查各幣別覆蓋台數，也可以 `WHERE is_fallback = 0` 過濾只看精確資料。

---

### Table 3：`scrape_log`

每次爬蟲或 import 的執行記錄。

```sql
CREATE TABLE scrape_log (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  bank_name    TEXT NOT NULL,
  source_file  TEXT NOT NULL,         -- e.g. 'megabank_currencies.json'
  record_count INTEGER NOT NULL,
  imported_at  TEXT NOT NULL,         -- ISO 8601
  notes        TEXT                   -- e.g. 'fallback applied: 12 rows'
);
```

---

### View：`atm_export`

用來 export JSON 給前端，格式與現有 `atm_with_currencies.json` 相同。

```sql
CREATE VIEW atm_export AS
SELECT
  l.id,
  l.bank_code,
  l.bank_name,
  l.location,
  l.city,
  l.address,
  l.lat,
  l.lng,
  l.source,
  GROUP_CONCAT(c.currency, ',') AS currencies_csv
FROM atm_locations l
LEFT JOIN bank_currencies c ON c.atm_id = l.id
GROUP BY l.id;
```

export 腳本再把 `currencies_csv` 拆回 `["USD","JPY",...]` 陣列。
`currencies_csv` 為 NULL（該台無幣別資料）時，export 腳本輸出 `null`，與現有格式一致。

---

## 實作步驟

### Step 1：建立 DB 與 schema

**腳本：`scripts/db_init.py`**

```
python scripts/db_init.py
→ 建立 data/atm.db，跑上面三個 CREATE TABLE + CREATE VIEW
```

---

### Step 2：匯入 FISC 位置資料

**腳本：`scripts/db_import_locations.py`**

```
輸入：data/processed/atm_geocoded.json（1,960 筆，source="fisc"）
       + Gap B 的 22 筆（從 atm_with_currencies.json 裡 source="bank_website" 的那些）
輸出：atm_locations table（1,971 筆 = 1,949 fisc + 22 bank_website）
```

邏輯：
1. 讀 `atm_geocoded.json` → 遇到 `FISC_EXCLUDE` 中的筆跳過 → INSERT，source="fisc"
   （FISC_EXCLUDE 共 11 筆，故實際插入 1,949 筆）
2. 讀 `atm_with_currencies.json` → 找 `source == "bank_website"` 的筆 → INSERT，source="bank_website"
3. 寫入 `scrape_log`：`source_file="atm_geocoded.json"`, `record_count=1949`（實際插入數，非原始檔筆數）

---

### Step 3：匯入幣別資料

**腳本：`scripts/db_import_currencies.py`**

```
輸入：data/processed/ 下所有 *_currencies.json
       + FALLBACK_CURRENCIES 常數（從 merge_currencies.py 搬過來）
       + MANUAL_MAP 常數（同上，機場等特殊地點手動對應）
       + PENDING set（同上，待確認的 branch，build_lookup 時跳過）
輸出：bank_currencies table（約 4,000–5,000 筆，一幣一筆）
```

邏輯（對每台 ATM 逐筆比對，與現在 merge 邏輯一致）：
1. 從 `merge_currencies.py` 搬移以下常數與函式：
   `FALLBACK_CURRENCIES`、`MANUAL_MAP`、`PENDING`、`normalize_branch()`、`normalize_addr()`
2. `build_lookup()`：從所有 JSON 建 `(bank_kw, branch) → currencies` 的對照表
   （含 MANUAL_MAP 手動對應、PENDING 跳過、normalize_branch 正規化）
3. 對 `atm_locations` 每筆，做 branch 子字串雙向比對 → INSERT currencies（is_fallback=0）
4. 比對不到的 → FALLBACK_CURRENCIES → INSERT（is_fallback=1）
5. FISC_EXCLUDE 的筆在 Step 2 已排除，`atm_locations` 中不存在，Step 3 無需另行處理
6. 每個 JSON 寫一筆 scrape_log

---

### Step 4：Export JSON

**腳本：`scripts/db_export.py`**

```
輸入：data/atm.db（讀 atm_export view）
輸出：data/processed/atm_with_currencies.json（格式與現在完全相同）
```

```python
import sqlite3, json

conn = sqlite3.connect("data/atm.db")
rows = conn.execute("SELECT * FROM atm_export").fetchall()
# 組回現有 JSON 格式：currencies_csv → list，其餘欄位直接對應
```

---

### Step 5：驗證

```
python scripts/db_export.py
→ 比較新舊 atm_with_currencies.json 是否等價（銀行別筆數、幣別分布）
```

驗證用一次性腳本（不需要留）：
```python
old = json.load(open("data/processed/atm_with_currencies_old.json"))
new = json.load(open("data/processed/atm_with_currencies.json"))
assert len(old) == len(new)
# 比對每筆的 currencies set
```

---

### Step 6（選做）：月更整合

月更流程從現在的：
```
update_from_fisc.py → 覆蓋 atm_geocoded.json → 重跑 merge_currencies.py
```
改為：
```
update_from_fisc.py → 更新 atm_locations table → db_export.py → 輸出新 JSON
```

---

## 檔案清單

完成後新增：

```
data/
└── atm.db                          # SQLite 資料庫

scripts/
├── db_init.py                      # 建立 schema
├── db_import_locations.py          # 匯入 FISC + Gap B 位置資料
├── db_import_currencies.py         # 匯入爬蟲幣別資料
└── db_export.py                    # 輸出 atm_with_currencies.json
```

現有的 `merge_currencies.py` 可以留著當歷史參考，不需要刪。

---

## 注意事項

- `atm.db` 加進 `.gitignore`（binary 檔不適合 git 追蹤），只 commit 腳本和 export 出來的 JSON
- `is_fallback` 欄位在備審說明時可以講：「精確資料 vs 保守估計的區別設計」
- 從 `merge_currencies.py` 搬移的常數：`FALLBACK_CURRENCIES`、`FISC_EXCLUDE`、`MANUAL_MAP`、`PENDING`、`normalize_branch()`、`normalize_addr()`
- `FISC_EXCLUDE` 在 Step 2（db_import_locations.py）過濾，Step 3 不需重複處理
- `scrape_log.record_count` 記錄實際 INSERT 筆數，非來源檔案原始行數

---

## 實作記錄（2026-05-13）

> 狀態：全部完成，驗證通過

### 執行結果

| 腳本 | 結果 |
|------|------|
| `db_init.py` | 建立 `data/atm.db`，3 table + 1 view |
| `db_import_locations.py` | FISC 1,949 筆（排除 11 筆）+ Gap B 22 筆 = 1,971 筆 |
| `db_import_currencies.py` | 3,637 筆（精確 1,908 台、fallback 41 台、Gap B 22 台、無幣別 0 台） |
| `db_export.py` | 輸出 1,971 筆 |

### 資料核對結果

**FISC_EXCLUDE（11 筆）**
全部確認不在 `atm_locations`：永豐 9 筆（含不對外服務、無外幣 ATM 分行）、第一 2 筆（無此機台）。

**Gap B bank_website（22 筆）**
全部正確插入，幣別不為空。

**MANUAL_MAP 機場 ATM（11 個地點）**
全部 `is_fallback=0`（精確配對），包含兆豐松山/桃園/高雄機場、中鋼、玉山大學/大樓。
特別說明：「華航收付處」在 DB 中有**兩筆**（桃園機場 + 松山機場），這是 FISC 原始資料的情況，非 bug。

**Fallback 41 台分布**
| 銀行 | 台數 | 原因 |
|------|------|------|
| 台新 | 18 | 行外 ATM（廠辦、工廠），官網 API 未回傳地點 |
| 新光 | 12 | 商場/醫院型機台，官網 HTML 僅列分行型 |
| 兆豐 | 8 | 桃園機場非主要廳（三樓入境管制區、地下美食街等），MANUAL_MAP 未覆蓋 |
| 玉山 | 2 | 醫院院區，官網未列 |
| 華南 | 1 | 溪湖分行，XML 未回傳 |

**幣別合法值**
只有 `USD / JPY / CNY / EUR / HKD`，無非預期值。

**幣別覆蓋台數**
| 幣別 | 台數 |
|------|------|
| JPY | 1,933 |
| USD | 987 |
| CNY | 517 |
| HKD | 130 |
| EUR | 70 |

### 驗證過程中發現的問題與說明

**問題 1：初次驗證方法有盲點**
用 `(銀行名稱, 裝設地點)` 做 dict key 逐筆比對，當有重複組合時後者靜默覆蓋前者。
正確做法是以 index 順序逐筆比對，才能發現所有差異。

**問題 2：`lat`/`lng` 型別從 string 變 float**
原始 `atm_geocoded.json` 的座標存為字串（`"25.041467"`）；SQLite `REAL` 欄位讀出後為浮點數（`25.041467`）。
實質值相同，前端全部透過 `parseFloat()` 讀取，無影響。此為原始資料格式的小瑕疵（座標應為 number），新格式反而更正確。
