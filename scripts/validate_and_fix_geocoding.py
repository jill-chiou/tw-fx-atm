"""
驗證並修復 atm_geocoded.json 的座標問題：
1. 多重座標（含 ;）→ 取第一個值
2. 無座標 → 標記，輸出清單
3. 座標超出台灣範圍 → 標記（金門離島例外）
4. 輸出 30 筆抽樣 Google Maps 連結供手動核對
"""

import json
import random
import csv
from pathlib import Path

JSON_PATH   = Path(__file__).parent.parent / "data" / "processed" / "atm_geocoded.json"
SAMPLE_PATH = Path(__file__).parent.parent / "data" / "processed" / "sample_validation.csv"

# 台灣含離島的合理範圍
LAT_MIN, LAT_MAX = 21.9, 25.4
LNG_MIN, LNG_MAX = 118.0, 122.1  # 包含金門 118.x

with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

fixed = []
report = {"multi": [], "no_coord": [], "out_of_range": []}

for r in data:
    lat = r.get("lat")
    lng = r.get("lng")

    # 多重座標：取第一個
    if lat and ";" in str(lat):
        lat = str(lat).split(";")[0].strip()
        lng = str(lng).split(";")[0].strip()
        report["multi"].append({**r, "lat": lat, "lng": lng})

    # 無座標
    if not lat:
        report["no_coord"].append(r)

    # 超出範圍（有座標才檢查）
    if lat:
        try:
            if not (LAT_MIN <= float(lat) <= LAT_MAX) or not (LNG_MIN <= float(lng) <= LNG_MAX):
                report["out_of_range"].append({**r, "lat": lat, "lng": lng})
        except ValueError:
            pass

    fixed.append({**r, "lat": lat, "lng": lng})

# --- 報告 ---
print("=" * 50)
print("資料驗證結果")
print("=" * 50)
print(f"總筆數：{len(data)}")
print(f"多重座標已取第一值：{len(report['multi'])} 筆")
print(f"無座標：{len(report['no_coord'])} 筆")
print(f"座標超出範圍：{len(report['out_of_range'])} 筆")

if report["out_of_range"]:
    print("\n超出範圍明細：")
    for r in report["out_of_range"]:
        print(f"  {r['銀行名稱']} {r['裝設地點']}  lat={r['lat']} lng={r['lng']}")

if report["no_coord"]:
    print("\n無座標明細：")
    for r in report["no_coord"]:
        print(f"  {r['銀行名稱']} {r['裝設地點']}  {r['地址']}")

# --- 寫回修復後的 JSON ---
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)
print(f"\n已寫回：{JSON_PATH}")

# --- 抽樣 30 筆產生 Google Maps 連結 ---
has_coord = [r for r in fixed if r.get("lat") and ";" not in str(r["lat"])]
sample = random.sample(has_coord, min(30, len(has_coord)))

with open(SAMPLE_PATH, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["銀行名稱", "裝設地點", "地址", "lat", "lng", "Google Maps 連結"])
    for r in sample:
        maps_url = f"https://www.google.com/maps?q={r['lat']},{r['lng']}"
        writer.writerow([r["銀行名稱"], r["裝設地點"], r["地址"], r["lat"], r["lng"], maps_url])

print(f"抽樣 30 筆 Google Maps 連結：{SAMPLE_PATH}")
print("\n打開 CSV，點連結核對座標位置是否在正確地址附近")
