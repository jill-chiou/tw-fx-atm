"""
臺灣中小企業銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.tbb.com.tw/zh-tw/about/intro/location/atm

調查結論（2026-05-11）：
- 官網 ATM 查詢頁有「外幣提款」篩選選項
- 篩選結果顯示據點名稱與地址，但無幣別細節
- 官網無任何說明文字標示外幣 ATM 支援的具體幣別
- 保守標記全部 6 台為 USD/JPY
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/tbb_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    atms = [r for r in fisc_data if "中小企業" in r.get("銀行名稱", "")]

    records = [
        {
            "bank": "臺灣中小企業銀行",
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
