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

**欄位名猜錯**：因為 Windows 終端機無法正確顯示 UTF-8 中文，CSV 欄位名在螢幕上是亂碼。我用眼睛猜欄位名，把「裝設地點」誤寫成「設施地點」，導致後續 geocode.py 跑到一半 KeyError 崩潰。

**教訓**：永遠用程式碼驗證欄位名（`print(list(reader.fieldnames))`），不要靠肉眼看亂碼終端輸出。

---

## 本步驟學到的概念

- **pdfplumber**：透過幾何分析把 PDF 表格還原成結構化資料
- **Python 切片 `[1:]`**：從第 1 個元素開始取，用來跳過重複的表頭
- **utf-8-sig**：UTF-8 加 BOM，讓 Excel 正確辨識中文編碼
- **CSV 寫入**：`csv.writer` + `writerow` / `writerows` 的用法
