"""
台新國際商業銀行外幣 ATM 幣別爬蟲
來源: https://www.taishinbank.com.tw/TSB/service-and-support/branch-finder/
幣別 API: POST /eServiceA/misc/aboutLocationCurrency.jsp?branchCode=NNN

注意：幣別資料為分行層級（含臨櫃換鈔），非 ATM 機台專屬。
回傳格式 {"日圓JPY": "1000,5000,10000", ...}，key 中包含貨幣代碼。

輸出: data/processed/taishinbank_currencies.json

每筆格式:
{
  "bank": "台新銀行",
  "branch": "外幣部(總行)",
  "address": "台北市中山區中山北路二段44號",
  "lat": "25.0551596",
  "lng": "121.5202956",
  "currencies": ["CAD", "CNY", "EUR", "HKD", "JPY", "USD"]
}
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import unquote

import requests
import urllib3

urllib3.disable_warnings()

BRANCH_FINDER_URL = (
    "https://www.taishinbank.com.tw/TSB/service-and-support/branch-finder/"
)
CURRENCY_API_URL = (
    "https://www.taishinbank.com.tw/eServiceA/misc/aboutLocationCurrency.jsp"
)
OUTPUT = Path(__file__).parent.parent / "data" / "processed" / "taishinbank_currencies.json"
TOTAL_PAGES = 26

HEADERS = {
    "User-Agent": "tw-fx-atm-bot/1.0",
    "Referer": BRANCH_FINDER_URL,
}

# Regex to pull currency code from key like "日圓JPY" -> "JPY"
# CJK chars are \w in Python so \b doesn't work; currency code is always at key end
CURRENCY_CODE_RE = re.compile(r"([A-Z]{3})$")

# Google Maps URL pattern: /place/ENCODED_ADDR/@lat,lng,
MAPS_PLACE_RE = re.compile(r"/place/([^/]+)/@([\d.]+),([\d.]+),")
BRANCH_CODE_RE = re.compile(r"qryWait\('(\d+)'\)")

# Branch name sits in <span class="title-detail">
TITLE_DETAIL_RE = re.compile(
    r'class="title-detail">(.*?)</span>', re.DOTALL
)


def extract_currency_codes(raw: dict) -> list[str]:
    codes = set()
    for key in raw:
        m = CURRENCY_CODE_RE.search(key)
        if m:
            codes.add(m.group(1))
    return sorted(codes)


def scrape_page(session: requests.Session, page: int) -> list[dict]:
    resp = session.get(
        BRANCH_FINDER_URL, params={"page": page}, headers=HEADERS,
        timeout=15, verify=False,
    )
    resp.raise_for_status()
    html = resp.content.decode("utf-8", errors="replace")

    # Split by qryWait to get per-branch blocks
    parts = re.split(r"(?=qryWait\(')", html)
    branches = []

    for part in parts:
        code_m = BRANCH_CODE_RE.search(part)
        if not code_m:
            continue
        code = code_m.group(1)

        # Address + coordinates from Google Maps URL
        maps_m = MAPS_PLACE_RE.search(part)
        address = unquote(maps_m.group(1)) if maps_m else ""
        lat = maps_m.group(2) if maps_m else ""
        lng = maps_m.group(3) if maps_m else ""

        # Remove zip code prefix (5 digits) from address
        address = re.sub(r"^\d{5}", "", address).strip()

        # Branch name
        title_m = TITLE_DETAIL_RE.search(part)
        name = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""

        branches.append({
            "code": code,
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng,
        })

    return branches


def get_currencies(session: requests.Session, branch_code: str) -> list[str]:
    resp = session.post(
        CURRENCY_API_URL,
        data={"branchCode": branch_code, "locale": ""},
        headers=HEADERS,
        timeout=10,
        verify=False,
    )
    resp.raise_for_status()
    try:
        raw = resp.json()
    except Exception:
        return []
    return extract_currency_codes(raw)


def scrape() -> list[dict]:
    records = []

    with requests.Session() as session:
        all_branches = []
        for page in range(1, TOTAL_PAGES + 1):
            branches = scrape_page(session, page)
            all_branches.extend(branches)
            print(f"  Page {page:2d}: {len(branches)} branches")
            time.sleep(0.3)

        print(f"\n共 {len(all_branches)} 個分行，查詢幣別中...")

        for i, b in enumerate(all_branches, 1):
            currencies = get_currencies(session, b["code"])
            if currencies:
                records.append({
                    "bank": "台新銀行",
                    "branch": b["name"],
                    "address": b["address"],
                    "lat": b["lat"],
                    "lng": b["lng"],
                    "currencies": currencies,
                })
                print(f"  [{i:3d}/{len(all_branches)}] {b['code']} {b['name'][:16]:16s}  {' '.join(currencies)}")
            else:
                print(f"  [{i:3d}/{len(all_branches)}] {b['code']} {b['name'][:16]:16s}  (無外幣)")
            time.sleep(0.2)

    return records


def main():
    print("台新銀行幣別爬蟲啟動")
    records = scrape()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n共 {len(records)} 筆有幣別，已存至 {OUTPUT}")


if __name__ == "__main__":
    main()
