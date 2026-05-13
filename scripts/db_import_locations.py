"""
匯入 FISC 位置資料與 Gap B bank_website 資料到 atm_locations table。
執行：python3 scripts/db_import_locations.py
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "atm.db"
GEOCODED_PATH  = ROOT / "data/processed/atm_geocoded.json"
ATM_WITH_PATH  = ROOT / "data/processed/atm_with_currencies.json"

# 官網確認不公開或不存在的機台，匯入時排除
# (銀行名稱關鍵字, FISC 裝設地點)
FISC_EXCLUDE: set[tuple[str, str]] = {
    ("永豐", "南山人壽-民權(不對外)"),
    ("第一", "中華航空公司組派大樓2F"),
    ("第一", "金湖停車場"),
    ("永豐", "世貿分行"),
    ("永豐", "三民分行"),
    ("永豐", "岡山分行"),
    ("永豐", "忠孝東路分行"),
    ("永豐", "萬華分行"),
    ("永豐", "興隆分行"),
    ("永豐", "中山分行"),
    ("永豐", "鶯歌分行"),
}


def is_excluded(bank_name: str, location: str) -> bool:
    for kw, loc in FISC_EXCLUDE:
        if kw in bank_name and loc == location:
            return True
    return False


def import_locations() -> None:
    conn = sqlite3.connect(DB_PATH)
    now  = datetime.now(timezone.utc).isoformat()

    # --- Step 1: FISC 位置資料 ---
    geocoded = json.loads(GEOCODED_PATH.read_text(encoding="utf-8"))
    fisc_rows = []
    for r in geocoded:
        if is_excluded(r["銀行名稱"], r["裝設地點"]):
            continue
        fisc_rows.append((
            r["代號"],
            r["銀行名稱"],
            r["裝設地點"],
            r.get("縣市"),
            r.get("地址"),
            r.get("lat"),
            r.get("lng"),
            "fisc",
        ))

    conn.executemany(
        "INSERT INTO atm_locations (bank_code, bank_name, location, city, address, lat, lng, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        fisc_rows,
    )
    conn.execute(
        "INSERT INTO scrape_log (bank_name, source_file, record_count, imported_at, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        ("(all)", "atm_geocoded.json", len(fisc_rows), now,
         f"excluded {len(geocoded) - len(fisc_rows)} FISC_EXCLUDE rows"),
    )
    print(f"FISC 插入：{len(fisc_rows)} 筆（排除 {len(geocoded) - len(fisc_rows)} 筆）")

    # --- Step 2: Gap B bank_website 資料 ---
    atm_with = json.loads(ATM_WITH_PATH.read_text(encoding="utf-8"))
    bank_website_rows = [
        (
            r["代號"],
            r["銀行名稱"],
            r["裝設地點"],
            r.get("縣市"),
            r.get("地址"),
            r.get("lat"),
            r.get("lng"),
            "bank_website",
        )
        for r in atm_with
        if r.get("source") == "bank_website"
    ]

    conn.executemany(
        "INSERT INTO atm_locations (bank_code, bank_name, location, city, address, lat, lng, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        bank_website_rows,
    )
    conn.execute(
        "INSERT INTO scrape_log (bank_name, source_file, record_count, imported_at, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        ("(Gap B)", "atm_with_currencies.json", len(bank_website_rows), now,
         "source=bank_website only"),
    )
    print(f"Gap B 插入：{len(bank_website_rows)} 筆")

    conn.commit()
    conn.close()

    total = len(fisc_rows) + len(bank_website_rows)
    print(f"atm_locations 合計：{total} 筆")


if __name__ == "__main__":
    import_locations()
