"""
Nominatim (OpenStreetMap) geocoding test
測試前 20 筆地址，觀察成功率與回應格式
"""

import csv
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "data" / "processed" / "atm_data.csv"
TEST_SIZE = 20

def geocode_nominatim(address: str) -> dict | None:
    base = "https://nominatim.openstreetmap.org/search"
    params = urllib.parse.urlencode({
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "tw",
    })
    url = f"{base}?{params}"
    try:
        # Nominatim 要求 User-Agent 含聯絡資訊
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "tw-fx-atm/0.1 (dodiddone0518@gmail.com)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception as e:
        return {"error": str(e)}

def main():
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    sample = rows[:TEST_SIZE]
    results = []

    for i, row in enumerate(sample):
        addr = row["地址"]
        print(f"[{i+1}/{TEST_SIZE}] {addr}")
        resp = geocode_nominatim(addr)

        lat = lng = None
        status = "失敗"

        if isinstance(resp, list) and resp:
            lat = resp[0].get("lat")
            lng = resp[0].get("lon")
            status = "成功" if lat and lng else "有結果但無座標"
        elif isinstance(resp, dict) and "error" in resp:
            status = f"錯誤: {resp['error']}"

        results.append({
            "地址": addr,
            "status": status,
            "lat": lat,
            "lng": lng,
            "raw": json.dumps(resp, ensure_ascii=False)[:200],
        })
        print(f"   → {status}  lat={lat}  lng={lng}")
        time.sleep(1.1)  # Nominatim 規定每秒最多 1 次請求

    success = sum(1 for r in results if r["status"] == "成功")
    print(f"\n成功率：{success}/{TEST_SIZE}")
    print("\n失敗列表：")
    for r in results:
        if r["status"] != "成功":
            print(f"  {r['地址']}  →  {r['status']}")
            print(f"  raw: {r['raw']}")

if __name__ == "__main__":
    main()
