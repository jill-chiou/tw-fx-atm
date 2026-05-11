"""
合作金庫商業銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.tcb-bank.com.tw/about-tcb/info/locations/foreign-exchange?tab=3

調查結論（2026-05-11）：
- 官網 ATM 篩選只有「美金」「日幣」兩個選項，無 CNY/HKD/EUR
- 官網備註「鈔券幣別依各分行放置為準，欲前往提領者請於營業時間內電話洽詢」
  → 是備料（實體鈔券庫存）問題，非系統幣別差異
- 保守標記全部 15 台為 USD/JPY
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/tcb_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    atms = [r for r in fisc_data if "合作金庫" in r.get("銀行名稱", "")]

    records = [
        {
            "bank": "合作金庫銀行",
            "branch": a["裝設地點"],
            "address": a.get("地址", ""),
            "lat": a.get("lat", ""),
            "lng": a.get("lng", ""),
            "currencies": CURRENCIES,
        }
        for a in atms
    ]

    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆（FISC 來源），幣別保守標記 {CURRENCIES}")
    print(f"已存至 {OUTPUT}")


if __name__ == "__main__":
    main()
