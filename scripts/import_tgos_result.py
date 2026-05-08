"""
把 TGOS 批次比對結果合併回 atm_geocoded.json。
輸入：data/processed/tgos_result.csv（TGOS 下載的檔案）
輸出：data/processed/atm_geocoded.json（覆蓋舊的）
"""

import csv
import json
from pathlib import Path

RESULT_PATH = Path(__file__).parent.parent / "data" / "processed" / "tgos_result.csv"
CSV_PATH    = Path(__file__).parent.parent / "data" / "processed" / "atm_data.csv"
OUT_PATH    = Path(__file__).parent.parent / "data" / "processed" / "atm_geocoded.json"

# 讀 TGOS 結果，key = id（對應 atm_data.csv 的行號）
tgos = {}
with open(RESULT_PATH, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        idx = int(row["id"])
        x = row.get("Response_X", "").strip()
        y = row.get("Response_Y", "").strip()
        tgos[idx] = (x or None, y or None)

# 讀原始 CSV（銀行名稱、裝設地點等）
with open(CSV_PATH, encoding="utf-8-sig") as f:
    atm_rows = list(csv.DictReader(f))

ok = fail = 0
results = []
for i, row in enumerate(atm_rows):
    lat, lng = tgos.get(i, (None, None))
    if lat and lng:
        ok += 1
    else:
        fail += 1
    results.append({
        "代號":     row["代號"],
        "銀行名稱": row["銀行名稱"],
        "裝設地點": row["裝設地點"],
        "縣市":     row["縣市"],
        "地址":     row["地址"],
        "lat":      lat,
        "lng":      lng,
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"完成：{len(results)} 筆")
print(f"  有座標：{ok}")
print(f"  無座標：{fail}")
print(f"輸出：{OUT_PATH}")
