"""
元大商業銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.yuantabank.com.tw/bank/spotMap/list.do?type=5

調查結論（2026-05-11）：
- 官網外幣提款機頁面回傳 403，requests 無法存取（反爬機制）
- 官網外幣存款說明頁（foreignDeposit/list2.do）同樣 403
- 搜尋結果顯示元大外幣 ATM 提供 USD（單筆上限 1,000）、JPY（單筆上限 100,000）
- 無法確認是否有其他幣別，保守標記全部 7 台為 USD/JPY
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/yuanta_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    atms = [r for r in fisc_data if "元大" in r.get("銀行名稱", "")]

    records = [
        {
            "bank": "元大商業銀行",
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
