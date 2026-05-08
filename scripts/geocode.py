"""
Geocode all ATM records via Nominatim (OpenStreetMap).
Output: data/processed/atm_geocoded.json
Supports resume: progress is saved to atm_geocoded_progress.jsonl after each record.
"""

import re
import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "data" / "processed" / "atm_data.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "atm_geocoded.json"
PROGRESS_PATH = Path(__file__).parent.parent / "data" / "processed" / "atm_geocoded_progress.jsonl"

ADDR_RE = re.compile(
    r'^(?P<city>[^市縣]+[市縣])'
    r'(?:.+(?:[區鄉鎮]|(?<![區鄉鎮])市))?'
    # 路/街/道 + 可選段(中文或阿拉伯數字) + 可選巷弄
    r'(?P<road>.+?[路街道](?:[\d一二三四五六七八九十百千]+段)?(?:\d+巷)?(?:\d+弄)?)'
    # 號碼可含連字號(62-5號)，允許後接樓層或多個地址單元
    r'(?P<num>\d+(?:-\d+)?)號'
)

# 僅路名+城市的 fallback（無號碼時）
ROAD_RE = re.compile(
    r'^(?P<city>[^市縣]+[市縣])'
    r'(?:.+(?:[區鄉鎮]|(?<![區鄉鎮])市))?'
    r'(?P<road>.+?[路街道])',
)

def parse_addr(addr: str) -> str | None:
    # 先嘗試完整號碼
    # 多地址單元(27號7樓、27號8樓)只取第一個號碼
    addr_clean = addr.split('、')[0]
    m = ADDR_RE.match(addr_clean)
    if m:
        return f"{m.group('num')} {m.group('road')} {m.group('city')}"
    # fallback: 只用路名+城市
    m2 = ROAD_RE.match(addr_clean)
    if m2:
        return f"{m2.group('road')} {m2.group('city')}"
    return None

def geocode(q: str) -> tuple[str, str] | tuple[None, None]:
    params = urllib.parse.urlencode({
        "q": q,
        "format": "json",
        "limit": 1,
        "countrycodes": "tw",
    })
    url = "https://nominatim.openstreetmap.org/search?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "tw-fx-atm/0.1 (dodiddone0518@gmail.com)"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            if data:
                return data[0]["lat"], data[0]["lon"]
            return None, None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"  [429] rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  [ERROR] HTTP {e.code}")
                return None, None
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None, None
    return None, None

def load_progress() -> dict[int, dict]:
    """載入已完成的進度，回傳 {index: record}"""
    done = {}
    if not PROGRESS_PATH.exists():
        return done
    with open(PROGRESS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                done[rec["_idx"]] = rec
    return done

def main():
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    done = load_progress()

    if done:
        print(f"找到進度檔，已完成 {len(done)}/{total} 筆，從第 {max(done)+2} 筆繼續...")

    ok = sum(1 for r in done.values() if r["lat"] is not None)
    fail_parse = sum(1 for r in done.values() if r["lat"] is None and r.get("_q") is None)
    fail_geo = sum(1 for r in done.values() if r["lat"] is None and r.get("_q") is not None)

    progress_file = open(PROGRESS_PATH, "a", encoding="utf-8")

    try:
        for i, row in enumerate(rows):
            if i in done:
                continue

            addr = row["地址"]
            q = parse_addr(addr)

            if not q:
                fail_parse += 1
                lat = lon = None
                print(f"[{i+1}/{total}] PARSE_FAIL: {addr}")
            else:
                lat, lon = geocode(q)
                if lat:
                    ok += 1
                    if (i + 1) % 50 == 0:
                        print(f"[{i+1}/{total}] OK  成功率目前 {ok}/{i+1}")
                else:
                    fail_geo += 1
                    print(f"[{i+1}/{total}] GEO_FAIL: {q}")
                time.sleep(1.1)  # Nominatim: max 1 req/sec

            rec = {
                "_idx": i,
                "_q": q,
                "代號": row["代號"],
                "銀行名稱": row["銀行名稱"],
                "裝設地點": row["裝設地點"],
                "縣市": row["縣市"],
                "地址": addr,
                "lat": lat,
                "lng": lon,
            }
            done[i] = rec
            progress_file.write(json.dumps(rec, ensure_ascii=False) + "\n")
            progress_file.flush()
    finally:
        progress_file.close()

    # 按原始順序輸出，去掉內部欄位
    results = []
    for i in range(total):
        r = done[i]
        results.append({k: v for k, v in r.items() if not k.startswith("_")})

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 完成後刪除進度檔
    PROGRESS_PATH.unlink(missing_ok=True)

    print(f"\n完成 {total} 筆")
    print(f"  成功:        {ok}")
    print(f"  解析失敗:    {fail_parse}")
    print(f"  Geocode失敗: {fail_geo}")
    print(f"輸出: {OUT_PATH}")

if __name__ == "__main__":
    main()
