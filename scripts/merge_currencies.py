"""
將爬蟲幣別資料 merge 進 atm_geocoded.json
輸出: data/processed/atm_with_currencies.json

merge 規則:
  1. 以「銀行名稱含 bank」+ 「裝設地點含 branch」做子字串比對
  2. 特殊地點（機場等）用手動 mapping 表補充
  3. 無法比對 → currencies: null
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
GEOCODED = ROOT / "data/processed/atm_geocoded.json"
OUTPUT   = ROOT / "data/processed/atm_with_currencies.json"

SCRAPED_FILES = [
    ROOT / "data/processed/skbank_currencies.json",
    ROOT / "data/processed/megabank_currencies.json",
    ROOT / "data/processed/cathaybk_currencies.json",
    ROOT / "data/processed/ctbc_currencies.json",
    ROOT / "data/processed/sinopac_currencies.json",
    ROOT / "data/processed/hncb_currencies.json",
    ROOT / "data/processed/esunbank_currencies.json",
    ROOT / "data/processed/taishinbank_currencies.json",
    ROOT / "data/processed/bot_currencies.json",
    ROOT / "data/processed/firstbank_currencies.json",
    ROOT / "data/processed/fubon_currencies.json",
    ROOT / "data/processed/scsb_currencies.json",
    ROOT / "data/processed/tcb_currencies.json",
    ROOT / "data/processed/landbank_currencies.json",
    ROOT / "data/processed/yuanta_currencies.json",
    ROOT / "data/processed/tbb_currencies.json",
    ROOT / "data/processed/bankchb_currencies.json",
]

# 手動 mapping: (銀行名稱片段, API branch) → FISC 裝設地點
MANUAL_MAP = {
    ("兆豐", "松山機場第一航廈國際線內候機室"):     "松山機場第一航廈出境大廳",
    ("兆豐", "松山機場華航收付處"):              "華航收付處",           # 松山那筆（地址 405巷）
    ("兆豐", "桃園機場第二航廈一樓入境"):          "桃園國際機場第二航廈一樓入境大廳",
    ("兆豐", "桃園機場第一航廈一樓入境南側"):       "桃園國際機場第一航廈入境大廳一樓",
    ("兆豐", "桃園機場第二航廈一樓入境北側"):       "桃園國際機場第二航廈一樓入境北側",
    ("兆豐", "桃園國際機場第二航廈出境三樓管制區B、C區"): "桃園國際機場第二航廈三樓管制區",
    ("兆豐", "桃園國際機場第二航廈三樓管制區A、D區"):   "桃園國際機場第二航廈三樓管制區",
    ("兆豐", "桃園機場第一航廈一樓入境"):          "桃園國際機場第一航廈入境大廳一樓",
    ("兆豐", "桃園機場華航收付處"):              "華航收付處",           # 桃園那筆（地址 航站南路1號）
    ("兆豐", "高雄國際機場新國際航廈"):            "高雄國際機場國際航廈",
    ("兆豐", "中鋼簡易分行"):                 "中鋼簡易型分行",
    ("玉山", "國立台灣大學第二行政大樓"):         "台大第二行政大樓",
    ("玉山", "玉山希望大樓"):                  "希望大樓",
}

# 待確認，暫不 merge
PENDING = {
    ("兆豐", "新店分行"),
}

# 當分行名稱配對失敗時，依各銀行 ATM 服務頁標示的最小支援幣別作 fallback
# 只有 FISC 全數為外幣 ATM、且官網有明確說明幣別的銀行才放這裡
FALLBACK_CURRENCIES: dict[str, list[str]] = {
    # 台新 ATM 服務頁 (personal/digital/.../atm_service/): USD/JPY/RMB/EUR
    "台新": ["CNY", "EUR", "JPY", "USD"],
}


def normalize_branch(branch: str) -> str:
    """正規化 branch 名稱，消除常見格式差異。"""
    # 兆豐官網在某些分行後帶「(營業廳)」/「（營業廳）」，FISC 通常不帶或以不同方式標記
    branch = re.sub(r'[（(]營業廳[)）]', '', branch).strip()
    # 永豐官網部分分行前帶「-」前綴（資料問題）
    branch = branch.lstrip('-').strip()
    return branch


def build_lookup(scraped: list[dict]) -> dict:
    """
    回傳 {(銀行片段, FISC裝設地點): currencies} 的 lookup。
    同時處理一般子字串比對和手動 mapping。
    """
    lookup: dict[tuple, list] = {}

    # 手動 mapping: API branch → FISC 裝設地點
    branch_to_fisc: dict[tuple, str] = {}
    for (bank_kw, api_branch), fisc_loc in MANUAL_MAP.items():
        branch_to_fisc[(bank_kw, api_branch)] = fisc_loc

    for item in scraped:
        bank  = item["bank"]        # e.g. "新光銀行"
        branch = normalize_branch(item["branch"])
        currencies = item["currencies"]

        # 找出 bank 的短關鍵字（去掉「銀行」）
        bank_kw = bank.replace("銀行", "").replace("國際商業", "").replace("商業", "")

        # 手動 mapping
        manual_fisc = branch_to_fisc.get((bank_kw, branch))
        if manual_fisc:
            key = (bank_kw, manual_fisc)
            # 同一 FISC 地點被多筆 API branch 對應 → 取聯集
            existing = lookup.get(key, [])
            merged = sorted(set(existing) | set(currencies))
            lookup[key] = merged
        elif (bank_kw, branch) not in PENDING:
            if not branch:
                continue  # 空 branch 會造成萬用符合，跳過
            lookup[(bank_kw, branch)] = currencies

    return lookup


def find_currencies(fisc_bank: str, fisc_loc: str, lookup: dict) -> list | None:
    """給定 FISC 一筆記錄，在 lookup 中找對應幣別。"""
    for (bank_kw, branch_or_fisc), currencies in lookup.items():
        # bank 必須吻合
        if bank_kw not in fisc_bank:
            continue
        # FISC 裝設地點含 branch_or_fisc（子字串比對）
        if branch_or_fisc in fisc_loc:
            return currencies
    # fallback：非分行場所的 ATM 套用該銀行的最小幣別集合
    for bank_kw, fallback in FALLBACK_CURRENCIES.items():
        if bank_kw in fisc_bank:
            return fallback
    return None


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))

    # 載入所有爬蟲結果
    scraped = []
    for f in SCRAPED_FILES:
        if f.exists():
            scraped.extend(json.loads(f.read_text(encoding="utf-8")))

    lookup = build_lookup(scraped)

    matched = fallback_matched = unmatched = 0
    result = []
    for entry in fisc_data:
        bank_name = entry.get("銀行名稱", "")
        loc       = entry.get("裝設地點", "")

        # 先嘗試分行名稱精確配對，再嘗試 fallback
        currencies = None
        for (bank_kw, branch_or_fisc), currs in lookup.items():
            if bank_kw not in bank_name:
                continue
            if branch_or_fisc in loc:
                currencies = currs
                matched += 1
                break
        if currencies is None:
            for bank_kw, fallback in FALLBACK_CURRENCIES.items():
                if bank_kw in bank_name:
                    currencies = fallback
                    fallback_matched += 1
                    break
        if currencies is None:
            unmatched += 1

        new_entry = dict(entry)
        new_entry["currencies"] = currencies
        result.append(new_entry)

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(result)
    scraped_banks = {item["bank"] for item in scraped}
    print(f"總筆數：{total}")
    print(f"有幣別（分行精確配對）：{matched}")
    print(f"有幣別（fallback 配對）：{fallback_matched}")
    print(f"有幣別合計：{matched + fallback_matched}（{(matched + fallback_matched)*100//total}%）")
    print(f"無幣別：{unmatched}")
    print(f"已爬銀行：{', '.join(sorted(scraped_banks))}")
    print(f"輸出：{OUTPUT}")


if __name__ == "__main__":
    main()
