"""
逐筆開啟 sample_validation.csv 的 Google Maps 連結，人工確認座標是否正確。

用法：
    python3 scripts/review_sample_maps.py

快捷鍵：
    Enter / o = OK
    n         = NG
    s         = skip
    b         = 回到上一筆
    q         = 離開
"""

import csv
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).parent.parent
INPUT_PATH = ROOT / "data" / "processed" / "sample_validation.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "sample_validation_review.csv"

FIELDNAMES = [
    "銀行名稱",
    "裝設地點",
    "地址",
    "lat",
    "lng",
    "Google Maps 連結",
    "review_status",
    "review_note",
    "reviewed_at",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_existing_reviews(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    reviews = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            reviews[row_key(row)] = row
    return reviews


def row_key(row: dict[str, str]) -> str:
    return "|".join(
        [
            row.get("銀行名稱", ""),
            row.get("裝設地點", ""),
            row.get("地址", ""),
            row.get("lat", ""),
            row.get("lng", ""),
        ]
    )


def save_reviews(rows: list[dict[str, str]], reviews: dict[str, dict[str, str]]) -> None:
    output_rows = []
    for row in rows:
        reviewed = reviews.get(row_key(row), {})
        output_rows.append(
            {
                **row,
                "review_status": reviewed.get("review_status", ""),
                "review_note": reviewed.get("review_note", ""),
                "reviewed_at": reviewed.get("reviewed_at", ""),
            }
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)


def first_unreviewed_index(rows: list[dict[str, str]], reviews: dict[str, dict[str, str]]) -> int:
    for index, row in enumerate(rows):
        reviewed = reviews.get(row_key(row), {})
        if not reviewed.get("review_status"):
            return index
    return 0


def print_row(row: dict[str, str], index: int, total: int) -> None:
    print("\n" + "=" * 72)
    print(f"[{index + 1}/{total}] {row['銀行名稱']}｜{row['裝設地點']}")
    print(f"地址：{row['地址']}")
    print(f"座標：{row['lat']}, {row['lng']}")
    print(f"連結：{row['Google Maps 連結']}")
    print("=" * 72)


def main() -> None:
    rows = load_rows(INPUT_PATH)
    if not rows:
        print(f"沒有資料：{INPUT_PATH}")
        return

    reviews = load_existing_reviews(OUTPUT_PATH)
    index = first_unreviewed_index(rows, reviews)

    print(f"讀取：{INPUT_PATH}")
    print(f"結果會即時寫入：{OUTPUT_PATH}")
    print("操作：Enter/o=OK, n=NG, s=skip, b=上一筆, q=離開")

    while 0 <= index < len(rows):
        row = rows[index]
        print_row(row, index, len(rows))
        webbrowser.open(row["Google Maps 連結"])

        answer = input("判定？").strip().lower()
        if answer == "q":
            break
        if answer == "b":
            index = max(0, index - 1)
            continue
        if answer == "s":
            reviews[row_key(row)] = {
                **row,
                "review_status": "skip",
                "review_note": "",
                "reviewed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_reviews(rows, reviews)
            index += 1
            continue

        if answer in ("", "o", "ok", "y", "yes"):
            status = "ok"
            note = ""
        elif answer in ("n", "ng", "no"):
            status = "ng"
            note = input("備註（例如：偏到隔壁、找不到地址，可留空）：").strip()
        else:
            print("看不懂這個輸入，請用 Enter/o/n/s/b/q。")
            continue

        reviews[row_key(row)] = {
            **row,
            "review_status": status,
            "review_note": note,
            "reviewed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_reviews(rows, reviews)
        index += 1

    save_reviews(rows, reviews)
    print(f"\n已保存：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
