"""
匯入幣別資料到 bank_currencies table。
執行：python3 scripts/db_import_currencies.py
"""

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "atm.db"
PROCESSED = ROOT / "data" / "processed"

SCRAPED_FILES = [
    PROCESSED / "skbank_currencies.json",
    PROCESSED / "megabank_currencies.json",
    PROCESSED / "cathaybk_currencies.json",
    PROCESSED / "ctbc_currencies.json",
    PROCESSED / "sinopac_currencies.json",
    PROCESSED / "hncb_currencies.json",
    PROCESSED / "esunbank_currencies.json",
    PROCESSED / "taishinbank_currencies.json",
    PROCESSED / "bot_currencies.json",
    PROCESSED / "firstbank_currencies.json",
    PROCESSED / "fubon_currencies.json",
    PROCESSED / "scsb_currencies.json",
    PROCESSED / "tcb_currencies.json",
    PROCESSED / "landbank_currencies.json",
    PROCESSED / "yuanta_currencies.json",
    PROCESSED / "tbb_currencies.json",
    PROCESSED / "bankchb_currencies.json",
]

# 手動 mapping: (銀行名稱片段, API branch) → FISC 裝設地點
MANUAL_MAP: dict[tuple, str] = {
    ("兆豐", "松山機場第一航廈國際線內候機室"):          "松山機場第一航廈出境大廳",
    ("兆豐", "松山機場華航收付處"):                   "華航收付處",
    ("兆豐", "桃園機場第二航廈一樓入境"):               "桃園國際機場第二航廈一樓入境大廳",
    ("兆豐", "桃園機場第一航廈一樓入境南側"):            "桃園國際機場第一航廈入境大廳一樓",
    ("兆豐", "桃園機場第二航廈一樓入境北側"):            "桃園國際機場第二航廈一樓入境北側",
    ("兆豐", "桃園國際機場第二航廈出境三樓管制區B、C區"): "桃園國際機場第二航廈三樓管制區",
    ("兆豐", "桃園國際機場第二航廈三樓管制區A、D區"):    "桃園國際機場第二航廈三樓管制區",
    ("兆豐", "桃園機場第一航廈一樓入境"):               "桃園國際機場第一航廈入境大廳一樓",
    ("兆豐", "桃園機場華航收付處"):                   "華航收付處",
    ("兆豐", "高雄國際機場新國際航廈"):                "高雄國際機場國際航廈",
    ("兆豐", "中鋼簡易分行"):                        "中鋼簡易型分行",
    ("玉山", "國立台灣大學第二行政大樓"):              "台大第二行政大樓",
    ("玉山", "玉山希望大樓"):                         "希望大樓",
}

PENDING: set[tuple] = {
    ("兆豐", "新店分行"),
}

FALLBACK_CURRENCIES: dict[str, list[str]] = {
    "台新": ["CNY", "EUR", "JPY", "USD"],
    "兆豐": ["CNY", "EUR", "HKD", "JPY", "USD"],
    "新光": ["CNY", "HKD", "JPY", "USD"],
    "玉山": ["CNY", "HKD", "JPY", "USD"],
    "華南": ["CNY", "HKD", "JPY", "USD"],
}


FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def to_halfwidth(s: str) -> str:
    return s.translate(FULLWIDTH_DIGITS)


def normalize_branch(branch: str) -> str:
    branch = re.sub(r'[（(]營業廳[)）]', '', branch).strip()
    branch = branch.lstrip('-').strip()
    return branch


def normalize_addr(addr: str) -> str:
    addr = addr.strip().replace('臺', '台')
    addr = re.sub(r'^\d{3,5}', '', addr).strip()
    addr = re.sub(r'^[^\s]{2,6}[市縣][^\s]{2,4}[區鄉鎮市]', '', addr).strip()
    for ch, d in zip('一二三四五六七八九', '123456789'):
        addr = addr.replace(f'{ch}段', f'{d}段')
    addr = re.sub(r'(\d+)-(\d+)', r'\1之\2', addr)
    addr = re.sub(r'(\d+)號之(\d+)', r'\1之\2號', addr)
    addr = re.sub(r'\s+', '', addr)
    addr = re.sub(r'[\dB]\d*[樓FfBb層].*$', '', addr)
    addr = re.sub(r'及.*$', '', addr)
    addr = re.sub(r'(\d+)[、,，]\d+.*號', r'\1號', addr)
    addr = re.sub(r'[（(][^)）]*[)）]', '', addr)
    return addr.strip()


def build_lookup(scraped: list[dict]) -> dict:
    lookup: dict[tuple, list] = {}
    branch_to_fisc: dict[tuple, str] = {}
    for (bank_kw, api_branch), fisc_loc in MANUAL_MAP.items():
        branch_to_fisc[(bank_kw, api_branch)] = fisc_loc

    for item in scraped:
        bank   = item["bank"]
        branch = normalize_branch(item["branch"])
        currencies = item["currencies"]
        bank_kw = (bank.replace("銀行", "").replace("國際商業", "")
                       .replace("商業", "").replace("儲蓄", ""))

        manual_fisc = branch_to_fisc.get((bank_kw, branch))
        if manual_fisc:
            key = (bank_kw, manual_fisc)
            existing = lookup.get(key, [])
            lookup[key] = sorted(set(existing) | set(currencies))
        elif (bank_kw, branch) not in PENDING:
            if not branch:
                continue
            lookup[(bank_kw, branch)] = currencies

    return lookup


def match_currencies(bank_name: str, location: str, lookup: dict) -> tuple[list | None, bool]:
    """回傳 (currencies, is_fallback)。找不到時回傳 (None, False)。"""
    for (bank_kw, branch_or_fisc), currencies in lookup.items():
        if bank_kw not in bank_name:
            continue
        if to_halfwidth(branch_or_fisc) in to_halfwidth(location) or to_halfwidth(location) in to_halfwidth(branch_or_fisc):
            return currencies, False

    for bank_kw, fallback in FALLBACK_CURRENCIES.items():
        if bank_kw in bank_name:
            return fallback, True

    return None, False


def import_currencies() -> None:
    conn = sqlite3.connect(DB_PATH)
    now  = datetime.now(timezone.utc).isoformat()

    # 載入所有爬蟲資料
    scraped: list[dict] = []
    for fpath in SCRAPED_FILES:
        if fpath.exists():
            scraped.extend(json.loads(fpath.read_text(encoding="utf-8")))

    lookup = build_lookup(scraped)

    # Gap B 幣別：從 atm_with_currencies.json 讀（bank_website 那些）
    atm_with_path = PROCESSED / "atm_with_currencies.json"
    atm_with = json.loads(atm_with_path.read_text(encoding="utf-8"))
    gap_b_currencies: dict[tuple, list] = {
        (r["銀行名稱"], r["裝設地點"]): r.get("currencies") or []
        for r in atm_with
        if r.get("source") == "bank_website"
    }

    # 讀取 DB 中所有 atm_locations
    rows = conn.execute(
        "SELECT id, bank_name, location, source FROM atm_locations"
    ).fetchall()

    currency_rows: list[tuple] = []
    stats = {"matched": 0, "fallback": 0, "unmatched": 0, "gap_b": 0}

    for atm_id, bank_name, location, source in rows:
        if source == "bank_website":
            currencies = gap_b_currencies.get((bank_name, location), [])
            for c in currencies:
                currency_rows.append((atm_id, c, 0))
            stats["gap_b"] += 1
        else:
            currencies, is_fallback = match_currencies(bank_name, location, lookup)
            if currencies is None:
                stats["unmatched"] += 1
                continue
            for c in currencies:
                currency_rows.append((atm_id, c, 1 if is_fallback else 0))
            if is_fallback:
                stats["fallback"] += 1
            else:
                stats["matched"] += 1

    conn.executemany(
        "INSERT INTO bank_currencies (atm_id, currency, is_fallback) VALUES (?, ?, ?)",
        currency_rows,
    )

    # scrape_log：每個 JSON 一筆
    for fpath in SCRAPED_FILES:
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        bank_name = data[0]["bank"] if data else fpath.stem
        conn.execute(
            "INSERT INTO scrape_log (bank_name, source_file, record_count, imported_at) "
            "VALUES (?, ?, ?, ?)",
            (bank_name, fpath.name, len(data), now),
        )

    conn.commit()
    conn.close()

    print(f"bank_currencies 插入：{len(currency_rows)} 筆（一幣一筆）")
    print(f"  精確配對：{stats['matched']} 台")
    print(f"  fallback：{stats['fallback']} 台")
    print(f"  Gap B：   {stats['gap_b']} 台")
    print(f"  無幣別：  {stats['unmatched']} 台")


if __name__ == "__main__":
    import_currencies()
