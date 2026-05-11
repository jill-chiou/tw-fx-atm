"""
上海商業儲蓄銀行外幣 ATM 幣別（手動記錄）
來源: 官網外幣ATM服務說明（由使用者提供，2026-05-11）

據點與幣別：
  國外部（中山北路二段155號）：USD(100) / JPY(10,000) / HKD(500) / CNY(100)
  儲蓄部（建國北路二段120號）：USD(100) / JPY(10,000)

FISC 對應：
  營業部行外無人銀行 → 中山北路二段155號1樓 → USD/HKD/JPY/CNY
  儲蓄部行內無人銀行 → 建國北路二段120號     → JPY/USD
"""

import json
from pathlib import Path

ROOT   = Path(__file__).parent.parent
OUTPUT = ROOT / "data/processed/scsb_currencies.json"

RECORDS = [
    {
        "bank": "上海商業儲蓄銀行",
        "branch": "營業部行外無人銀行",
        "address": "台北市中山區中山北路二段155號1樓",
        "lat": "25.062245",
        "lng": "121.522966",
        "currencies": ["HKD", "JPY", "USD", "CNY"],
    },
    {
        "bank": "上海商業儲蓄銀行",
        "branch": "儲蓄部行內無人銀行",
        "address": "台北市中山區建國北路二段120號",
        "lat": "25.058990",
        "lng": "121.536542",
        "currencies": ["JPY", "USD"],
    },
]


def main():
    OUTPUT.write_text(json.dumps(RECORDS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(RECORDS)} 筆（手動記錄，逐台幣別不同）")
    for r in RECORDS:
        print(f"  {r['branch']}: {r['currencies']}")
    print(f"已存至 {OUTPUT}")


if __name__ == "__main__":
    main()
