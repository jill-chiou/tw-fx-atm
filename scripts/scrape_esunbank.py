"""
玉山商業銀行外幣 ATM 幣別爬蟲
來源: https://www.esunbank.com/zh-tw/about/locations/foreign-currency-atm
資料: 頁面內嵌 JavaScript 變數 info / dic
輸出: data/processed/esunbank_currencies.json
"""

import json
import re
from pathlib import Path

import requests

URL = "https://www.esunbank.com/zh-tw/about/locations/foreign-currency-atm"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "esunbank_currencies.json"

INFO_RE = re.compile(r"\bvar\s+info\s*=\s*(\[.*?\])\s*;", re.S)
DIC_RE = re.compile(r"\bvar\s+dic\s*=\s*(\{.*?\})\s*;", re.S)
BRANCH_CODE_RE = re.compile(r"^\d{4}\s+")


def clean_branch(value: str) -> str:
    return BRANCH_CODE_RE.sub("", value or "").strip()


def extract_json_var(html: str, pattern: re.Pattern) -> list | dict:
    match = pattern.search(html)
    if not match:
        raise ValueError("找不到頁面內嵌資料")
    return json.loads(match.group(1))


def scrape() -> list[dict]:
    resp = requests.get(
        URL,
        headers={"User-Agent": "tw-fx-atm-bot/1.0"},
        timeout=20,
    )
    resp.raise_for_status()

    info = extract_json_var(resp.text, INFO_RE)
    dic = extract_json_var(resp.text, DIC_RE)
    id_to_currency = {int(v): k for k, v in dic.items() if k != "TWD"}

    records = []
    for item in info:
        currencies = sorted(
            id_to_currency[currency_id]
            for currency_id in item.get("ATMCurrencyIDs", [])
            if currency_id in id_to_currency
        )
        if not currencies:
            continue

        records.append({
            "bank": "玉山銀行",
            "branch": clean_branch(item.get("Location", "")),
            "address": re.sub(r"^\s*\d{3}\s*", "", item.get("Address", "")).strip(),
            "lat": item.get("Latitude", ""),
            "lng": item.get("Longitude", ""),
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
