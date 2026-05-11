"""
中國信託商業銀行外幣 ATM 幣別爬蟲
來源: https://www.ctbcbank.com/twrbo/zh_tw/index/h_locate_index/h_ATMlocate_inquiry.html
API:  POST /IB/api/adapters/IB_Adapter/resource/preLogin  (resource=/twrbo-general/qu002/023)

重要發現（2026-05-09）：
- 官網幣別篩選（USD/JPY/CNY）為前端 UI 功能，不反映個別機台差異
- checkForeignCurrency() 對所有 ATM 永遠回傳 true
- CTBC 所有外幣 ATM（atmType=2）統一支援 USD、JPY、CNY
- 因此直接以 FISC 的 167 筆中信外幣 ATM，全部標記 ["USD","JPY","CNY"]

此腳本不爬取 API（需要 session token，無法從外部直接呼叫），
改為直接產出 CTBC 外幣 ATM 幣別結論，供 merge_currencies.py 使用。
"""

import json
from pathlib import Path

ROOT   = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/ctbc_currencies.json"

CURRENCIES = ["CNY", "JPY", "USD"]


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))
    ctbc_atms = [r for r in fisc_data if "中國信託" in r.get("銀行名稱", "")]

    records = []
    for atm in ctbc_atms:
        records.append({
            "bank": "中國信託銀行",
            "branch": atm["裝設地點"],
            "address": atm.get("地址", ""),
            "lat": atm.get("lat", ""),
            "lng": atm.get("lng", ""),
            "currencies": CURRENCIES,
        })

    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆（FISC 來源），幣別統一標記 {CURRENCIES}")
    print(f"已存至 {OUTPUT}")
    print()
    print("注意：CTBC 官網調查結論（2026-05-09）：")
    print("  - API 不支援外部直接呼叫（bot 保護 + session token）")
    print("  - 官網幣別篩選為前端 UI，不反映個別機台差異")
    print("  - 所有外幣 ATM 統一支援 USD/JPY/CNY")


if __name__ == "__main__":
    main()
