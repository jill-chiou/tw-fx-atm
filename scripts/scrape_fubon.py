"""
台北富邦商業銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.fubon.com/banking/locations/locations.htm?tab=branch
API:  GET /Fubon_Portal/banking/locations/branch_newVersion.jsp?type=fc_atm
      （需 session cookie，外部無法直接呼叫）

調查結論（2026-05-11）：
- 官網明確說明：「外幣ATM提供美金面額50元、日圓面額1萬元」
- 篩選選項只有一個「外幣ATM(美金,日圓)」，無幣別分類
- 全行統一 USD / JPY，無個別機台差異
- 直接以 FISC 的 39 筆套用，不需爬 API
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/fubon_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    fubon_atms = [r for r in fisc_data if "富邦" in r.get("銀行名稱", "")]

    records = []
    for atm in fubon_atms:
        records.append({
            "bank": "台北富邦銀行",
            "branch": atm["裝設地點"],
            "address": atm.get("地址", ""),
            "lat": atm.get("lat", ""),
            "lng": atm.get("lng", ""),
            "currencies": CURRENCIES,
        })

    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆（FISC 來源），幣別統一標記 {CURRENCIES}")
    print(f"已存至 {OUTPUT}")


if __name__ == "__main__":
    main()
