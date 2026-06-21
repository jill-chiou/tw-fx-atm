"""
建立 data/atm.db 與 schema。
執行：python scripts/db_init.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "atm.db"


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        DROP TABLE IF EXISTS bank_currencies;
        DROP TABLE IF EXISTS scrape_log;
        DROP TABLE IF EXISTS atm_locations;
        DROP VIEW  IF EXISTS atm_export;

        CREATE TABLE IF NOT EXISTS atm_locations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_code   TEXT NOT NULL,
            bank_name   TEXT NOT NULL,
            location    TEXT,
            city        TEXT,
            address     TEXT,
            lat         REAL,
            lng         REAL,
            source      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bank_currencies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            atm_id      INTEGER NOT NULL REFERENCES atm_locations(id),
            currency    TEXT NOT NULL,
            is_fallback INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS scrape_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name    TEXT NOT NULL,
            source_file  TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            imported_at  TEXT NOT NULL,
            notes        TEXT
        );

        CREATE VIEW IF NOT EXISTS atm_export AS
        SELECT
            l.id,
            l.bank_code,
            l.bank_name,
            l.location,
            l.city,
            l.address,
            l.lat,
            l.lng,
            l.source,
            GROUP_CONCAT(c.currency, ',') AS currencies_csv
        FROM atm_locations l
        LEFT JOIN bank_currencies c ON c.atm_id = l.id
        GROUP BY l.id;
    """)
    conn.commit()
    conn.close()
    print(f"DB 初始化完成：{db_path}")


if __name__ == "__main__":
    init_db()
