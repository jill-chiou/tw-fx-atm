"""
彰化商業銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.bankchb.com/frontend/atm.jsp

調查結論（2026-05-11）：
- FISC 只有 1 台彰銀外幣 ATM
- 官網 ATM 查詢頁為 XML 框架結構，無法直接取得幣別資訊
- 台數過少（1 台），未深入調查，保守標記 USD/JPY
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/bankchb_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    atms = [r for r in fisc_data if "彰化商業" in r.get("銀行名稱", "")]

    records = [
        {
            "bank": "彰化商業銀行",
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
