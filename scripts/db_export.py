"""
從 atm.db 輸出 atm_with_currencies.json，格式與原有完全相同。
執行：python3 scripts/db_export.py
"""

import json
import sqlite3
from pathlib import Path

ROOT    = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "atm.db"
OUTPUT  = ROOT / "data" / "processed" / "atm_with_currencies.json"


def export_json(db_path: Path = DB_PATH, output: Path = OUTPUT) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM atm_export ORDER BY id").fetchall()
    conn.close()

    result = []
    for r in rows:
        csv = r["currencies_csv"]
        currencies = sorted(csv.split(",")) if csv else None
        result.append({
            "代號":    r["bank_code"],
            "銀行名稱": r["bank_name"],
            "裝設地點": r["location"],
            "縣市":    r["city"],
            "地址":    r["address"],
            "lat":     r["lat"],
            "lng":     r["lng"],
            "currencies": currencies,
            "source":  r["source"],
        })

    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"輸出：{output}（{len(result)} 筆）")


if __name__ == "__main__":
    export_json()
