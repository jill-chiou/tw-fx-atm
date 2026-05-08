# Step 01 — PDF 解析：從原始資料取得結構化表格

> 資料來源：財金資訊股份有限公司「提領外幣ATM位置查詢一覽」（2026/3/31）

---

## 問題：資料被鎖在 PDF 裡

外幣 ATM 的位置清單是官方 PDF，共 86 頁、約 1,962 筆。沒有現成的 API 或 CSV 可以下載，必須自己把表格資料「挖出來」。

---

## 為什麼不直接用 copy-paste？

PDF 裡的「表格」在電腦眼中不是真正的表格，而是一堆分散在 XY 座標上的文字碎片。直接複製貼上會變成亂序的文字流，無法對應到正確的欄位。

---

## 解法：pdfplumber

pdfplumber 是 Python 套件，專門處理 PDF 的幾何結構：
- 分析頁面上的線條（表格框線）
- 計算每段文字的 XY 座標
- 推斷哪些文字屬於同一列、同一欄
- 輸出成 Python list of lists（二維陣列）

---

## 程式碼解析

```python
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if not table:
            continue
        for row in table[1:]:          # [1:] 跳過每頁重複的表頭
            if row and any(cell for cell in row):
                rows.append(row)
```

**`table[1:]`**：PDF 每頁都有表頭列（代號、銀行名稱、裝設地點、縣市、地址）。Python 的切片語法 `[1:]` = 從第 1 個元素開始取，跳過第 0 個（表頭），避免 86 個重複表頭混進資料。

**`any(cell for cell in row)`**：過濾掉完全空白的列（PDF 有時會解析出全 None 的空列）。

```python
with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(HEADER)
    writer.writerows(rows)
```

**`encoding="utf-8-sig"`**：UTF-8 加 BOM（Byte Order Mark）。開頭的 3 個特殊 byte 是給 Excel 的提示，告訴它「用 UTF-8 開啟中文，不要亂碼」。

---

## 成果

| 項目 | 數值 |
|------|------|
| 來源 PDF | 86 頁 |
| 解析筆數 | 1,962 筆 |
| 欄位 | 代號、銀行名稱、裝設地點、縣市、地址 |
| 輸出 | `data/processed/atm_data.csv` |

---

## 踩到的坑

### 坑 1 — 欄位名猜錯（Windows 中文亂碼）

**症狀**：geocode.py 跑到一半 `KeyError` 崩潰。

**原因**：Windows 終端機無法正確顯示 UTF-8 中文，CSV 欄位名在螢幕上是亂碼。用眼睛猜欄位名，把「裝設地點」誤寫成「設施地點」。

**教訓**：永遠用程式碼驗證欄位名（`print(list(reader.fieldnames))`），不要靠肉眼看終端輸出。

---

### 坑 2 — 銀行名稱欄出現 `#N/A`（Excel VLOOKUP 公式錯誤）

**症狀**：CSV 裡代號 `012` 的 39 筆資料，銀行名稱欄全部是 `#N/A`，其他銀行都正常。

**原因**：PDF 是從 Excel 匯出的，Excel 裡的銀行名稱是用 `VLOOKUP` 公式查代號對照表自動填入。代號 `012`（台北富邦商業銀行）在對照表裡查不到，公式回傳 `#N/A`，就這樣直接印進 PDF 裡了。這是**資料提供方的錯誤**，不是 pdfplumber 的問題，我們讀到的就是 `#N/A`。

確認方式：用 `extract_words()` 讀 PDF 原始文字，確認 `012` 那行的銀行名稱格子裡字面上就寫著 `#N/A`。

**解法**：在 `parse_pdf.py` 加代號對照表，遇到 `#N/A` 就用代號補回正確名稱：

```python
BANK_NAME_FIX = {
    "012": "台北富邦商業銀行",
}
for row in rows:
    if row[1] == "#N/A" and row[0] in BANK_NAME_FIX:
        row[1] = BANK_NAME_FIX[row[0]]
```

**教訓**：資料來源是「PDF 由 Excel 匯出」時，Excel 的公式錯誤會原封不動印進 PDF。遇到奇怪的值先確認是 pdfplumber 的問題還是原始資料本身就這樣，方法是用 `extract_words()` 直接看 PDF 裡的文字。

---

### 坑 3 — 跨頁合併儲存格，代號和銀行名稱讀出空白

**症狀**：CSV 裡有 22 筆「代號」和「銀行名稱」是空字串，但其他欄位（裝設地點、地址）都有值。這 22 筆全部屬於台新國際商業銀行（812），前後筆的代號是正確的，只有夾在中間的那筆是空的。

**原因**：PDF 裡同一家銀行的多筆 ATM，「代號」和「銀行名稱」欄是**跨頁的合併儲存格**。合併格的值只存在上一頁，新頁面的第一行在 PDF 結構裡沒有自己的值。pdfplumber 一次只讀一頁，新頁開頭那幾行就讀出空值。

外觀特徵：在 PDF 裡看，這些行的「代號」和「銀行名稱」格子沒有下邊框線，就是因為它是從上一頁延伸下來的合併格。

**解法**：在 `parse_pdf.py` 加「向前填充」，遇到空代號就沿用上一筆的值：

```python
last_code = last_bank = ""
for row in rows:
    if row[0]:
        last_code = row[0]
        last_bank = row[1]
    else:
        row[0] = last_code
        row[1] = last_bank
```

**教訓**：pdfplumber 對跨頁合併儲存格沒有自動處理。解析結果有空值時，先確認是不是合併格問題，再決定是向前填充還是其他修法。

---

## 本步驟學到的概念

- **pdfplumber**：透過幾何分析把 PDF 表格還原成結構化資料
- **Python 切片 `[1:]`**：從第 1 個元素開始取，用來跳過重複的表頭
- **utf-8-sig**：UTF-8 加 BOM，讓 Excel 正確辨識中文編碼
- **CSV 寫入**：`csv.writer` + `writerow` / `writerows` 的用法
