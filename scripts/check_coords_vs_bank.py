"""
以銀行官網座標交叉檢查 TGOS geocoding 結果。
輸出：data/processed/coord_check_vs_bank.csv（距離 > 200m 的待查清單）

只用「官網 API/HTML 自帶座標」的 8 家銀行；其餘 8 家的 *_currencies.json
是由 atm_geocoded.json 產生（座標即 TGOS 結果），比對沒有意義。
距離大只代表兩邊不一致，不代表 TGOS 一定錯（銀行座標也可能有誤）。

執行：
    python3 scripts/check_coords_vs_bank.py
"""

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEO_PATH = ROOT / "data/processed/atm_geocoded.json"
OUT_PATH = ROOT / "data/processed/coord_check_vs_bank.csv"

# 爬蟲檔名 → FISC 銀行名稱關鍵字
REAL_COORD_BANKS = {
    "cathaybk": "國泰", "esunbank": "玉山", "hncb": "華南", "megabank": "兆豐",
    "sinopac": "永豐", "skbank": "新光", "taishinbank": "台新", "firstbank": "第一",
}
THRESHOLD_M = 200
HALFWIDTH = str.maketrans("０１２３４５６７８９（），", "0123456789(),")


def haversine(lat1, lng1, lat2, lng2) -> float:
    r = math.radians
    h = (math.sin(r(lat2 - lat1) / 2) ** 2
         + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lng2 - lng1) / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


def bucket(d: float) -> str:
    if d < 50:
        return "<50m"
    if d < 200:
        return "50-200m"
    if d < 1000:
        return "200m-1km"
    return ">1km"


def main():
    geo = json.loads(GEO_PATH.read_text(encoding="utf-8"))
    results, unmatched = [], 0

    for scraper, kw in REAL_COORD_BANKS.items():
        ref = json.loads((ROOT / f"data/processed/{scraper}_currencies.json").read_text(encoding="utf-8"))
        by_name = defaultdict(list)
        for x in ref:
            if x.get("lat") and x.get("lng"):
                by_name[x["branch"].translate(HALFWIDTH).strip()].append(x)

        for g in geo:
            if kw not in g["銀行名稱"] or not g.get("lat"):
                continue
            cands = by_name.get(g["裝設地點"].translate(HALFWIDTH).strip(), [])
            if len(cands) != 1:  # 找不到或同名多筆 → 不比對
                unmatched += 1
                continue
            b = cands[0]
            d = haversine(float(g["lat"]), float(g["lng"]), float(b["lat"]), float(b["lng"]))
            results.append((d, g, b))

    results.sort(key=lambda t: -t[0])
    counts = Counter(bucket(d) for d, _, _ in results)
    print(f"比對 {len(results)} 筆（未配對 {unmatched} 筆）")
    for k in ("<50m", "50-200m", "200m-1km", ">1km"):
        print(f"  {k:>9}：{counts[k]:>5} 筆（{counts[k] / len(results):.1%}）")

    flagged = [t for t in results if t[0] > THRESHOLD_M]
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["距離m", "銀行名稱", "裝設地點", "地址", "tgos_lat", "tgos_lng",
                    "bank_lat", "bank_lng", "Google Maps（TGOS）", "Google Maps（官網）"])
        for d, g, b in flagged:
            w.writerow([f"{d:.0f}", g["銀行名稱"], g["裝設地點"], g["地址"], g["lat"], g["lng"],
                        b["lat"], b["lng"],
                        f"https://www.google.com/maps?q={g['lat']},{g['lng']}",
                        f"https://www.google.com/maps?q={b['lat']},{b['lng']}"])
    print(f"> {THRESHOLD_M}m 待查 {len(flagged)} 筆 → {OUT_PATH}")


if __name__ == "__main__":
    main()
