"""
永豐商業銀行外幣 ATM 幣別爬蟲
來源: https://m.sinopac.com/m/bank/atm/m_ATM_search.aspx
API:  /ws/bank/atm/ws_ATM_GetDetail.ashx
輸出: data/processed/sinopac_currencies.json
"""

import json
from pathlib import Path

import requests

API_URL = "https://m.sinopac.com/ws/bank/atm/ws_ATM_GetDetail.ashx"
CITY_URL = "https://m.sinopac.com/ws/bank/atm/ws_ATM_GetCity.ashx"
REFERER = "https://m.sinopac.com/m/bank/atm/m_ATM_search.aspx"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "sinopac_currencies.json"

CURRENCY_FIELDS = {
    "WithdrawUSD": "USD",
    "WithdrawJPY": "JPY",
    "WithdrawCNY": "CNY",
    "WithdrawHKD": "HKD",
}
CURRENCY_FILTERS = {
    "CNY": "ATM_WITHDRAW_CNY",
    "HKD": "ATM_WITHDRAW_HKD",
    "JPY": "ATM_WITHDRAW_JPY",
    "USD": "ATM_WITHDRAW_USD",
}


def post_json(session: requests.Session, url: str, data: dict, allow_empty: bool = False) -> list[dict]:
    resp = session.post(
        url,
        data=data,
        headers={
            "User-Agent": "tw-fx-atm-bot/1.0",
            "Referer": REFERER,
        },
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload or payload[0].get("Header") != "SUCCESS":
        message = payload[0].get("Message") if payload else "empty response"
        if allow_empty and message == "查無資料":
            return []
        raise RuntimeError(f"永豐 API 回傳失敗: {message}")
    return payload[0].get("SubInfo", [])


def scrape() -> list[dict]:
    records_by_atm_no = {}

    with requests.Session() as session:
        cities = post_json(session, CITY_URL, {
            "QueryType": "2",
            "ATMCity": "",
            "ATMDist": "",
            "ATMFunc": "",
            "ATMServ": "",
            "ATMCurr": "",
        })

        for city in cities:
            city_name = city["DataValue"]
            for currency, currency_filter in CURRENCY_FILTERS.items():
                items = post_json(session, API_URL, {
                    "QueryType": "1",
                    "ATMCity": city_name,
                    "ATMDist": "",
                    "ATMFunc": "",
                    "ATMServ": "",
                    "ATMCurr": currency_filter,
                }, allow_empty=True)

                for item in items:
                    currencies = {
                        code
                        for field, code in CURRENCY_FIELDS.items()
                        if str(item.get(field, "")) == "1"
                    }
                    if not currencies:
                        currencies = {currency}

                    record = records_by_atm_no.setdefault(item["ATMNo"], {
                        "bank": "永豐銀行",
                        "branch": item.get("Location", "").strip(),
                        "address": item.get("Address", "").strip(),
                        "lat": item.get("lat", ""),
                        "lng": item.get("lng", ""),
                        "currencies": [],
                    })
                    record["currencies"] = sorted(set(record["currencies"]) | currencies)

    return list(records_by_atm_no.values())


def main():
    records = scrape()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆，已存至 {OUTPUT}")
    for r in records:
        print(f"  {r['branch']:20s}  {' '.join(r['currencies'])}")


if __name__ == "__main__":
    main()
