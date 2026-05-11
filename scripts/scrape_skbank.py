"""
新光銀行外幣 ATM 幣別爬蟲 POC
來源: https://www.skbank.com.tw/DE-FCATM/
輸出: data/processed/skbank_currencies.json

每筆格式:
{
  "bank": "新光銀行",
  "branch": "世貿分行",
  "currencies": ["USD", "JPY", "CNY", "HKD"],
  "denominations": {"USD": 100, "JPY": 10000, "CNY": 100, "HKD": 100}
}
"""

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.skbank.com.tw/DE-FCATM/"
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "skbank_currencies.json"

CURRENCY_MAP = {
    "美元": "USD",
    "日圓": "JPY",
    "人民幣": "CNY",
    "港幣": "HKD",
    "歐元": "EUR",
    "英鎊": "GBP",
    "澳幣": "AUD",
}

DENOM_RE = re.compile(r"(美元|日圓|人民幣|港幣|歐元|英鎊|澳幣)([\d,]+)")


def parse_currencies(text: str) -> list[str]:
    return [CURRENCY_MAP[k] for k in CURRENCY_MAP if k in text]


def parse_denominations(text: str) -> dict[str, int]:
    result = {}
    for ch_name, amount_str in DENOM_RE.findall(text):
        iso = CURRENCY_MAP[ch_name]
        result[iso] = int(amount_str.replace(",", ""))
    return result


def cell_lines(td) -> list[str]:
    """Return non-empty text lines from a table cell."""
    lines = []
    for p in td.find_all("p"):
        t = p.get_text(strip=True).replace("\xa0", "").strip()
        if t:
            lines.append(t)
    return lines


def scrape() -> list[dict]:
    resp = requests.get(URL, headers={"User-Agent": "tw-fx-atm-bot/1.0"}, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"  # server omits charset in Content-Type; default ISO-8859-1 is wrong

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="neux-table")
    if not table:
        raise RuntimeError("找不到 .neux-table")

    records = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        branch_lines = cell_lines(cells[0])
        currency_text = cells[1].get_text(strip=True)
        denom_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""

        currencies = parse_currencies(currency_text)
        denominations = parse_denominations(denom_text)

        for branch in branch_lines:
            # strip parenthetical notes like "(帳戶行：士林分行)"
            clean = re.sub(r"（[^）]*）|\([^)]*\)", "", branch).strip()
            if not clean:
                continue
            records.append({
                "bank": "新光銀行",
                "branch": clean,
                "currencies": currencies,
                "denominations": denominations,
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
