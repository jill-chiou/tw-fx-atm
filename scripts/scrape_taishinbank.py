"""
台新國際商業銀行外幣 ATM 幣別爬蟲
來源: https://www.taishinbank.com.tw/TSB/service-and-support/atm-location/
API:  POST /eServiceA/misc/GetCustomATM.jsp  (functoinName="CustomAtm")

與舊版（使用 aboutLocationCurrency.jsp）的差別：
  - 本版為機台層級，每台 ATM 有獨立幣別欄位
  - 總計 3,524 台（含台幣 ATM），篩選有外幣服務者輸出
  - 可完整覆蓋便利商店、學校、醫院等非分行場所的外幣 ATM

API 回傳欄位說明：
  USD, JPY, CNY, EUR, FOREIGN_SAVE: "y" 表示支援，"" 表示不支援

輸出: data/processed/taishinbank_currencies.json

每筆格式:
{
  "bank": "台新銀行",
  "branch": "全家-康福",
  "address": "台北市內湖區康樂街87號",
  "lat": "25.069568",
  "lng": "121.618904",
  "currencies": ["JPY", "USD"]
}
"""

import json
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

API_URL = "https://www.taishinbank.com.tw/eServiceA/misc/GetCustomATM.jsp"
REFERER = "https://www.taishinbank.com.tw/TSB/service-and-support/atm-location/"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "taishinbank_currencies.json"

HEADERS = {
    "User-Agent": "tw-fx-atm-bot/1.0",
    "Referer": REFERER,
}

# ATM service code → currency code mapping
CURRENCY_FIELDS = {
    "USD": "USD",
    "JPY": "JPY",
    "CNY": "CNY",
    "EUR": "EUR",
}


def fetch_page(session: requests.Session, page: int) -> dict:
    resp = session.post(
        API_URL,
        data={
            "city": "",
            "region": "",
            "atmService": "",
            "pageNum": page,
            "functoinName": "CustomAtm",  # typo is intentional (server-side)
            "latlon": "",
        },
        headers=HEADERS,
        timeout=20,
        verify=False,
    )
    resp.raise_for_status()
    return resp.json()


def parse_atm(item: dict) -> dict | None:
    currencies = sorted(
        code for field, code in CURRENCY_FIELDS.items()
        if item.get(field) == "y"
    )
    if not currencies:
        return None  # 無外幣服務，略過

    city = item.get("CITY", "")
    region = item.get("REGION", "")
    address_tail = item.get("ADDRESS", "")
    # 組合完整地址
    address = city + region + address_tail

    return {
        "bank": "台新銀行",
        "branch": item.get("SITE_NAME", "").strip(),
        "address": address.strip(),
        "lat": item.get("LATITUDE", ""),
        "lng": item.get("LONGITUDE", ""),
        "currencies": currencies,
    }


def scrape() -> list[dict]:
    records = []

    with requests.Session() as session:
        # 第一頁：取得總頁數
        first = fetch_page(session, 1)
        total_pages = first.get("maxNum", 1)
        total_atms = first.get("customAtmCount", 0)
        print(f"  總 ATM 數：{total_atms}，共 {total_pages} 頁")

        pages = [first] + [None] * (total_pages - 1)

        for page in range(1, total_pages + 1):
            data = pages[page - 1] if page == 1 else fetch_page(session, page)
            for item in data.get("customAtmList", []):
                rec = parse_atm(item)
                if rec:
                    records.append(rec)
            if page % 20 == 0:
                print(f"  Page {page}/{total_pages}，目前 {len(records)} 筆外幣 ATM")
            time.sleep(0.15)

    return records


def main():
    print("台新銀行外幣 ATM 爬蟲啟動（機台層級版）")
    records = scrape()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n共 {len(records)} 筆外幣 ATM，已存至 {OUTPUT}")

    # 幣別統計
    from collections import Counter
    all_curr = []
    for r in records:
        all_curr.extend(r["currencies"])
    for curr, cnt in sorted(Counter(all_curr).items()):
        print(f"  {curr}: {cnt}")


if __name__ == "__main__":
    main()
