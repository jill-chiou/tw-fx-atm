"""
FISC 外幣 ATM 月更新腳本

流程：
1. 下載最新 PDF（https://www.fisc.com.tw/tc/Download/atmfc.pdf）
2. 用 pdfplumber 解析成 rows
3. 與現有 atm_data.csv 比對，找出新增 / 移除的筆
4. 更新 atm_data.csv
5. 更新 atm_geocoded.json（繼承舊座標、標記新筆待 geocoding）
6. 輸出 diff report

執行：
    python3 scripts/update_from_fisc.py

待 geocoding 的新筆（lat: null）會被前端過濾掉，需事後補跑 geocode。
"""

import csv
import json
import urllib.request
import shutil
from datetime import date
from pathlib import Path

ROOT       = Path(__file__).parent.parent
PDF_URL    = "https://www.fisc.com.tw/tc/Download/atmfc.pdf"
PDF_PATH   = ROOT / "data" / "raw" / "atmfc.pdf"
CSV_PATH   = ROOT / "data" / "processed" / "atm_data.csv"
GEO_PATH   = ROOT / "data" / "processed" / "atm_geocoded.json"
HEADER     = ["代號", "銀行名稱", "裝設地點", "縣市", "地址"]
KEY_FIELDS = HEADER  # 全欄位做 key

BANK_NAME_FIX = {"012": "台北富邦商業銀行"}


# ── helpers ──────────────────────────────────────────────────────────────────

def download_pdf(dest: Path):
    print(f"下載 {PDF_URL} ...")
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "tw-fx-atm/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    print(f"  → 儲存至 {dest}")


def parse_pdf(pdf_path: Path) -> list[list[str]]:
    import pdfplumber
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table[1:]:
                if row and any(cell for cell in row):
                    rows.append(list(row))

    last_code = last_bank = ""
    for row in rows:
        if row[0]:
            last_code, last_bank = row[0], row[1]
        else:
            row[0], row[1] = last_code, last_bank

    for row in rows:
        if row[1] == "#N/A" and row[0] in BANK_NAME_FIX:
            row[1] = BANK_NAME_FIX[row[0]]

    return rows


def load_csv(path: Path) -> list[tuple]:
    with open(path, encoding="utf-8-sig") as f:
        return [tuple(r) for r in csv.reader(f)][1:]


def save_csv(path: Path, rows: list[list[str]]):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)


def row_key(d: dict) -> tuple:
    return tuple(d.get(f, "") for f in KEY_FIELDS)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    tmp_pdf = PDF_PATH.with_suffix(".tmp.pdf")

    # 1. 下載
    download_pdf(tmp_pdf)

    # 2. 解析新 PDF
    print("解析 PDF ...")
    new_rows = parse_pdf(tmp_pdf)
    new_set = {tuple(r) for r in new_rows}
    print(f"  新版筆數：{len(new_rows)}")

    # 3. 讀取舊資料
    old_rows = load_csv(CSV_PATH)
    old_set = set(old_rows)
    print(f"  舊版筆數：{len(old_rows)}")

    added   = new_set - old_set
    removed = old_set - new_set
    print(f"  新增：{len(added)} 筆，移除：{len(removed)} 筆")

    if not added and not removed:
        print("無差異，結束。")
        tmp_pdf.unlink()
        return

    # 4. 更新 CSV
    shutil.copy(tmp_pdf, PDF_PATH)
    save_csv(CSV_PATH, new_rows)
    print(f"✓ {CSV_PATH.name} 已更新")

    # 5. 更新 geocoded JSON
    with open(GEO_PATH, encoding="utf-8") as f:
        geocoded = json.load(f)

    removed_keys = removed  # set of tuples

    # 記住被移除筆的座標（供新筆繼承）
    inherited: dict[str, dict] = {}
    for d in geocoded:
        if row_key(d) in removed_keys:
            inherited[d["裝設地點"]] = {
                "lat": d.get("lat"),
                "lng": d.get("lng"),
                "geocode_source": d.get("geocode_source"),
            }

    # 過濾移除
    geocoded = [d for d in geocoded if row_key(d) not in removed_keys]

    # 加入新筆
    report_added = []
    report_pending = []
    for r in sorted(added):
        entry = dict(zip(KEY_FIELDS, r))
        loc = entry["裝設地點"]
        if loc in inherited and inherited[loc]["lat"]:
            entry.update(inherited[loc])
            report_added.append(f"  ✓ 繼承座標：{loc}")
        else:
            entry["lat"] = None
            entry["lng"] = None
            entry["geocode_source"] = "pending"
            report_pending.append(f"  ⚠ 待 geocoding：{loc}（{entry['地址']}）")
        geocoded.append(entry)

    with open(GEO_PATH, "w", encoding="utf-8") as f:
        json.dump(geocoded, f, ensure_ascii=False, indent=2)
    print(f"✓ {GEO_PATH.name} 已更新，共 {len(geocoded)} 筆")

    # 6. Diff report
    today = date.today().isoformat()
    print(f"\n=== Diff report ({today}) ===")
    print(f"移除 {len(removed)} 筆：")
    for r in sorted(removed):
        print(f"  - {r[1]} / {r[2]} / {r[4]}")
    print(f"新增 {len(added)} 筆：")
    for line in report_added:
        print(line)
    for line in report_pending:
        print(line)

    if report_pending:
        print("\n待補跑 geocoding：")
        print("  python3 scripts/geocode.py  （需設定 .env TGOS 金鑰）")

    tmp_pdf.unlink()


if __name__ == "__main__":
    main()
