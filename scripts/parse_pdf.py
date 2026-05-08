"""
解析 FISC 外幣 ATM 位置 PDF → CSV
來源：財金資訊股份有限公司「提領外幣ATM位置查詢一覽」
更新：2026/3/31，共 86 頁，約 1,720 筆
"""

import pdfplumber
import csv
from pathlib import Path

PDF_PATH = Path(__file__).parent.parent / "data" / "raw" / "atmfc.pdf"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "atm_data.csv"

HEADER = ["代號", "銀行名稱", "裝設地點", "縣市", "地址"]

def parse():
    rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table[1:]:  # 跳過每頁重複的表頭
                if row and any(cell for cell in row):
                    rows.append(row)

    # PDF 合併儲存格跨頁時，代號/銀行名稱會是 None 或空字串
    # 向前填充：沿用上一筆的值
    last_code = last_bank = ""
    for row in rows:
        if row[0]:
            last_code = row[0]
            last_bank = row[1]
        else:
            row[0] = last_code
            row[1] = last_bank

    # PDF 由 Excel 匯出，部分銀行的 VLOOKUP 公式錯誤，名稱欄印出 #N/A
    # 用代號對照表補正
    BANK_NAME_FIX = {
        "012": "台北富邦商業銀行",
    }
    for row in rows:
        if row[1] == "#N/A" and row[0] in BANK_NAME_FIX:
            row[1] = BANK_NAME_FIX[row[0]]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"完成：共 {len(rows)} 筆，輸出至 {OUT_PATH}")

if __name__ == "__main__":
    parse()
