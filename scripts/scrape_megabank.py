"""
兆豐國際商業銀行外幣 ATM 幣別爬蟲
來源: https://www.megabank.com.tw/about/about-mega/mega-intro/locations (ATM tab)
API:  /api/client/ATMLocation/GetATMLocation
輸出: data/processed/megabank_currencies.json

每筆格式:
{
  "bank": "兆豐銀行",
  "branch": "大安分行",
  "address": "臺北市大安區信義路三段182號",
  "lat": "25.033",
  "lng": "121.543",
  "currencies": ["JPY"]
}
"""

import json
import re
from pathlib import Path

import requests

API_URL = (
    "https://www.megabank.com.tw/api/client/ATMLocation/GetATMLocation"
    "?sc_lang=zh-TW&sc_site=bank-zh-tw&dic_lang=zh-TW"
    "&itemID=97fd4615f16a46e1991ac86938f60d63"
    "&settingID=82766713ab3e43e785c2bc0da35bd98c"
)
REFERER = "https://www.megabank.com.tw/about/about-mega/mega-intro/locations"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "megabank_currencies.json"

ADDR_RE = re.compile(r"<span>(.*?)</span>")


def extract_address(html: str) -> str:
    m = ADDR_RE.search(html or "")
    return m.group(1) if m else ""


def scrape() -> list[dict]:
    resp = requests.get(
        API_URL,
        headers={"User-Agent": "tw-fx-atm-bot/1.0", "Referer": REFERER},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    records = []
    for item in data:
        # "Currrency" is a typo in the API (3 r's)
        currencies = item.get("KeyValues", {}).get("Currrency", [])
        if not currencies:
            continue
        records.append({
            "bank": "兆豐銀行",
            "branch": item["NameTitle"],
            "address": extract_address(item.get("AddLinkHtml", "")),
            "lat": item.get("Latitude", ""),
            "lng": item.get("Longitude", ""),
            "currencies": sorted(currencies),
        })

    return records


def main():
    records = scrape()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(records)} 筆，已存至 {OUTPUT}")
    for r in records:
        print(f"  {r['branch']:20s}  {' '.join(r['currencies'])}")


if __name__ == "__main__":
    main()
