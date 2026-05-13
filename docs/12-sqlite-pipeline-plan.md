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
輸出：atm_locations table（約 1,971 筆）
```

邏輯：
1. 讀 `atm_geocoded.json` → INSERT 全部，source="fisc"
2. 讀 `atm_with_currencies.json` → 找 `source == "bank_website"` 的筆 → INSERT，source="bank_website"
3. 寫入 `scrape_log`：`source_file="atm_geocoded.json"`, `record_count=1960`

---

### Step 3：匯入幣別資料

**腳本：`scripts/db_import_currencies.py`**

```
輸入：data/processed/ 下所有 *_currencies.json
       + FALLBACK_CURRENCIES 常數（從 merge_currencies.py 搬過來）
       + FISC_EXCLUDE 常數（同上）
輸出：bank_currencies table（約 4,000–5,000 筆，一幣一筆）
```

邏輯（對每台 ATM 逐筆比對，與現在 merge 邏輯一致）：
1. build_lookup()：從所有 JSON 建 (bank_kw, branch) → currencies 的對照表
2. 對 `atm_locations` 每筆，做 branch 子字串雙向比對 → INSERT currencies（is_fallback=0）
3. 比對不到的 → FALLBACK_CURRENCIES → INSERT（is_fallback=1）
4. FISC_EXCLUDE 的筆 → 不 INSERT（在 Step 2 就不匯入，或這裡跳過）
5. 每個 JSON 寫一筆 scrape_log

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
- 目前 `merge_currencies.py` 的 `FALLBACK_CURRENCIES` 和 `FISC_EXCLUDE` 常數直接搬到 `db_import_currencies.py` 即可
