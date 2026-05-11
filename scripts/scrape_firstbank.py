"""
第一商業銀行外幣 ATM 幣別
來源: https://www.firstbank.com.tw/sites/fcb/ATMNearYou
API:  POST /sites/REST/controller/ATMNearYouRevCTL/searchATM

調查結論（2026-05-11）：
- 外幣提款（5 台）+ 臺外幣二合一提款機（37 台）= 42 台，與 FISC 吻合
- 官網說明：USD/JPY 全機台；CNY/HKD「部份機台」
- API 回傳資料不含幣別細節，僅有機型與無障礙功能標籤
- 保守處理：全部標記 USD/JPY，避免高估 CNY/HKD 覆蓋
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT     = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/firstbank_currencies.json"

API_URL = "https://www.firstbank.com.tw/sites/REST/controller/ATMNearYouRevCTL/searchATM"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.firstbank.com.tw/sites/fcb/ATMNearYou",
}

FUNC_IDS = {
    "外幣提款": "1565691865002",
    "臺外幣二合一提款機": "1565691865023",
}

CURRENCIES = ["JPY", "USD"]


def fetch_all(func_id):
    assets = []
    for page in range(1, 20):
        data = urllib.parse.urlencode({
            "atm_city": "", "atm_area": "",
            "searchATMFunctionId": func_id,
            "pageNumber": str(page),
        }).encode()
        req = urllib.request.Request(API_URL, data=data, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read())
        assets.extend(d["asset"])
        if page >= d["pageEnd"]:
            break
    return assets


def main():
    all_assets = []
    for label, func_id in FUNC_IDS.items():
        batch = fetch_all(func_id)
        print(f"{label}: {len(batch)} 筆")
        all_assets.extend(batch)

    records = []
    for a in all_assets:
        records.append({
            "bank": "第一商業銀行",
            "branch": a["branchTitle"],
            "address": a.get("branchAddress", ""),
            "lat": a.get("branchLatitude", ""),
            "lng": a.get("branchLongitude", ""),
            "currencies": CURRENCIES,
        })

    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆，幣別保守標記 {CURRENCIES}")
    print(f"已存至 {OUTPUT}")


if __name__ == "__main__":
    main()
