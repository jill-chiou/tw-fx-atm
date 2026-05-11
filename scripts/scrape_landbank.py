"""
臺灣土地銀行外幣 ATM 幣別（直接套用 FISC）
來源: https://www.landbank.com.tw/Location/Atm/ATM%E4%BD%8D%E7%BD%AE

調查結論（2026-05-11）：
- 官網 ATM 查詢頁無「外幣」篩選功能，無幣別資訊
- 官網 FAQ 外幣業務列出現鈔換匯幣別（USD/JPY/HKD/EUR/AUD/CAD/CNY），但未說明 ATM 支援幣別
- 第三方比率網（findrate.tw）列出 9 個據點，少於 FISC 的 12 筆（資料可能較舊）
- 無法確認各台幣別，保守標記全部 12 台為 USD/JPY
"""

import json
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/landbank_currencies.json"

CURRENCIES = ["JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    atms = [r for r in fisc_data if "土地銀行" in r.get("銀行名稱", "")]

    records = [
        {
            "bank": "臺灣土地銀行",
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
