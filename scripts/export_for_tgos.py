"""
把 atm_data.csv 整理成 TGOS 批次地址比對服務要求的格式。
輸出：data/processed/tgos_input.csv（ANSI/cp950 編碼）

上傳到 TGOS portal 後，下載結果再用 import_tgos_result.py 合併。
"""

import csv
from pathlib import Path

IN_PATH  = Path(__file__).parent.parent / "data" / "processed" / "atm_data.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "tgos_input.csv"

with open(IN_PATH, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "Address", "Response_Address", "Response_X", "Response_Y"])
    for i, row in enumerate(rows):
        writer.writerow([i, row["地址"], "", "", ""])

print(f"完成：{len(rows)} 筆")
print(f"輸出：{OUT_PATH}")
print()
print("下一步：")
print("  1. 上傳 tgos_input.csv 到 TGOS 批次地址比對服務")
print("  2. 座標系統選 EPSG:4326 (WGS84)")
print("  3. 下載結果，存成 data/processed/tgos_result.csv")
print("  4. 執行 python scripts/import_tgos_result.py")
