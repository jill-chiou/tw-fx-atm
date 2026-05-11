"""
國泰世華商業銀行外幣 ATM 幣別爬蟲
來源: https://www.cathaybk.com.tw/cathaybk/personal/contact/locations/#atm
API:  /CathayBK/service/Locations/LocationsGetData.ashx
輸出: data/processed/cathaybk_currencies.json

Type 欄位對應:
  USD: "1" → 有美元
  JPY: "1" → 有日圓
  (官網目前只有 USD / JPY 兩種)
"""

import json
from pathlib import Path
import requests

API_URL = "https://www.cathaybk.com.tw/CathayBK/service/Locations/LocationsGetData.ashx"
REFERER = "https://www.cathaybk.com.tw/cathaybk/personal/contact/locations/#atm"
OUTPUT  = Path(__file__).parent.parent / "data/processed/cathaybk_currencies.json"

CURRENCY_FLAGS = {"USD": "USD", "JPY": "JPY"}


def scrape() -> list[dict]:
    resp = requests.get(
        API_URL,
        headers={"User-Agent": "tw-fx-atm-bot/1.0", "Referer": REFERER},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    records = []
    for city, entries in data.get("Atm", {}).items():
        for item in entries:
            t = item.get("Type", {})
            currencies = [iso for flag, iso in CURRENCY_FLAGS.items() if t.get(flag) == "1"]
            if not currencies:
                continue
            records.append({
                "bank": "國泰世華銀行",
                "branch": item["SetAddressKind"],
                "address": item.get("Address", ""),
                "lat": item.get("Latitude", ""),
                "lng": item.get("Longitude", ""),
                "currencies": sorted(currencies),
            })

    return records


def main():
    records = scrape()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆，已存至 {OUTPUT}")

    from collections import Counter
    combos = Counter(tuple(r["currencies"]) for r in records)
    for combo, n in sorted(combos.items(), key=lambda x: -x[1]):
        print(f"  {n:3d} 筆  {' + '.join(combo)}")


if __name__ == "__main__":
    main()
