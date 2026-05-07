"""
NLSC Geocoding API 測試腳本
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

def geocode_nlsc(address: str) -> dict | None:
    base = "https://geocode.nlsc.gov.tw/QueryAddr"
    params = urllib.parse.urlencode({
        "queryType": "0",
        "outSR": "4326",
        "format": "json",
        "addr": address,
    })
    url = f"{base}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tw-fx-atm/0.1"})
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
        resp = geocode_nlsc(addr)

        # 嘗試解析座標
        lat = lng = None
        status = "失敗"
        if resp and "AddressMatchList" in resp:
            match_list = resp["AddressMatchList"]
            if match_list:
                first = match_list[0]
                lat = first.get("y")
                lng = first.get("x")
                status = "成功" if lat and lng else "有結果但無座標"

        elif resp and "error" in resp:
            status = f"錯誤: {resp['error']}"

        results.append({
            "地址": addr,
            "status": status,
            "lat": lat,
            "lng": lng,
            "raw": json.dumps(resp, ensure_ascii=False)[:200],
        })
        print(f"   → {status}  lat={lat}  lng={lng}")
        time.sleep(0.3)

    success = sum(1 for r in results if r["status"] == "成功")
    print(f"\n成功率：{success}/{TEST_SIZE}")
    print("\n失敗列表：")
    for r in results:
        if r["status"] != "成功":
            print(f"  {r['地址']}  →  {r['status']}")
            print(f"  raw: {r['raw']}")

if __name__ == "__main__":
    main()
