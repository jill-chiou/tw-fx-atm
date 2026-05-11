"""
華南商業銀行外幣 ATM 幣別爬蟲
來源: https://www.hncb.com.tw/wps/portal/HNCB/locations/atm
資料: /hncb/XML/ATM.xml
輸出: data/processed/hncb_currencies.json
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

XML_URL = "https://www.hncb.com.tw/hncb/XML/ATM.xml"
REFERER = "https://www.hncb.com.tw/wps/portal/HNCB/locations/atm"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "hncb_currencies.json"

CURRENCY_NAMES = {
    "美元": "USD",
    "日幣": "JPY",
    "人民幣": "CNY",
    "港幣": "HKD",
}


def text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return (child.text or "").strip() if child is not None else ""


def scrape() -> list[dict]:
    resp = requests.get(
        XML_URL,
        headers={
            "User-Agent": "tw-fx-atm-bot/1.0",
            "Referer": REFERER,
        },
        timeout=30,
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    records = []
    for item in root.iter():
        if item.tag.split("}")[-1] != "OutsideMachineList":
            continue
        if text(item, "IS_FOREIGN_DRAWING") != "Y":
            continue

        cash_list = text(item, "CASH_LIST")
        currencies = sorted(code for name, code in CURRENCY_NAMES.items() if name in cash_list)
        if not currencies:
            continue

        records.append({
            "bank": "華南銀行",
            "branch": text(item, "PLACE_LOCATION"),
            "address": text(item, "PLACE_ADDRESS"),
            "lat": text(item, "LATITUDE"),
            "lng": text(item, "LONGITUDE"),
            "currencies": currencies,
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
