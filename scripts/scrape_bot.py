"""
臺灣銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.bot.com.tw/tw/personal-banking/foreign-exchange/foreign-currency-cash-exchange/foreign-currency-ATM

調查結論（2026-05-11）：
- 官網明確列出全行統一幣別：USD / HKD / JPY / CNY（面額：100 / 500 / 10,000 / 100）
- 無 EUR；無個別機台差異
- 官網地圖（bot.map.com.tw）僅列約 20 筆，FISC 的 44 筆更完整（含桃園機場 6 台等）
- 因此直接以 FISC 的 44 筆臺灣銀行外幣 ATM，全部標記 ["HKD","JPY","USD","CNY"]
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/bot_currencies.json"

CURRENCIES = ["HKD", "JPY", "USD", "CNY"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    bot_atms = [r for r in fisc_data if "臺灣銀行" in r.get("銀行名稱", "")]

    records = []
    for atm in bot_atms:
        records.append({
            "bank": "臺灣銀行",
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
