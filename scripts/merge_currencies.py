"""
將爬蟲幣別資料 merge 進 atm_geocoded.json
輸出: data/processed/atm_with_currencies.json

merge 規則:
  1. 以「銀行名稱含 bank」+ 「裝設地點含 branch」做子字串比對
  2. 特殊地點（機場等）用手動 mapping 表補充
  3. 無法比對 → currencies: null
  4. Gap B ATM（爬蟲有、FISC 無）→ 以 source="bank_website" 追加
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

# Gap B 設定：爬蟲有獨立資料、且台數多於 FISC 的銀行
GAP_B_BANKS = [
    {
        "scraper_file": "cathaybk_currencies.json",
        "fisc_name":    "國泰世華商業銀行",
        "bank_code":    "013",
    },
    {
        "scraper_file": "esunbank_currencies.json",
        "fisc_name":    "玉山商業銀行",
        "bank_code":    "808",
    },
    {
        "scraper_file": "sinopac_currencies.json",
        "fisc_name":    "永豐商業銀行",
        "bank_code":    "807",
    },
]

# 地址不完整的分行手動補縣市
CITY_OVERRIDES: dict[tuple, str] = {
    ("永豐商業銀行", "新莊副都心分行"): "新北市",
}

# 當分行名稱配對失敗時，依各銀行 ATM 服務頁標示的最小支援幣別作 fallback
# 只有 FISC 全數為外幣 ATM、且官網有明確說明幣別的銀行才放這裡
FALLBACK_CURRENCIES: dict[str, list[str]] = {
    # 台新 ATM 服務頁: USD/JPY/CNY/EUR
    "台新": ["CNY", "EUR", "JPY", "USD"],
    # 兆豐機場 ATM（桃園/松山）官網 API 未回傳部分 hall，套用機場標準幣別
    "兆豐": ["CNY", "EUR", "HKD", "JPY", "USD"],
    # 新光官網 HTML 僅列分行型機台（18筆），其餘商場/醫院型用相同幣別 fallback
    "新光": ["CNY", "HKD", "JPY", "USD"],
    # 玉山非分行場所（醫院、大樓等）官網 HTML 未列，套用標準幣別
    "玉山": ["CNY", "HKD", "JPY", "USD"],
    # 華南溪湖分行 XML 未回傳，套用標準幣別
    "華南": ["CNY", "HKD", "JPY", "USD"],
}

# 官網確認不公開或不存在的機台，從輸出中排除
# (銀行名稱關鍵字, FISC 裝設地點)
FISC_EXCLUDE: set[tuple[str, str]] = {
    ("永豐", "南山人壽-民權(不對外)"),   # 不對外服務
    ("第一", "中華航空公司組派大樓2F"),   # 官網無此機台
    ("第一", "金湖停車場"),              # 官網無此機台
}


def normalize_addr(addr: str) -> str:
    """正規化地址，用於 Gap B 比對。"""
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


def extract_city(addr: str, bank_name: str, branch: str) -> str:
    """從地址擷取縣市欄位；缺失時查 CITY_OVERRIDES。"""
    override = CITY_OVERRIDES.get((bank_name, branch))
    if override:
        return override
    addr = addr.replace('臺', '台')
    m = re.match(r'^\d{0,5}\s*([^\s]{2,4}[市縣])', addr)
    return m.group(1) if m else ''


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

        # 找出 bank 的短關鍵字（去掉通用詞）
        bank_kw = bank.replace("銀行", "").replace("國際商業", "").replace("商業", "").replace("儲蓄", "")

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
        # 子字串雙向比對：scraper branch 在 FISC loc 裡，或 FISC loc 在 scraper branch 裡
        if branch_or_fisc in fisc_loc or fisc_loc in branch_or_fisc:
            return currencies
    # fallback：非分行場所的 ATM 套用該銀行的最小幣別集合
    for bank_kw, fallback in FALLBACK_CURRENCIES.items():
        if bank_kw in fisc_bank:
            return fallback
    return None


def find_gap_b(fisc_data: list[dict]) -> list[dict]:
    """回傳爬蟲有、FISC 無的 ATM，格式與 atm_with_currencies.json 相同。"""
    gap_b = []
    for cfg in GAP_B_BANKS:
        fpath = ROOT / "data/processed" / cfg["scraper_file"]
        if not fpath.exists():
            continue
        scraper_data = json.loads(fpath.read_text(encoding="utf-8"))
        fisc_entries = [x for x in fisc_data if x["銀行名稱"] == cfg["fisc_name"]]
        fisc_addr_set   = {normalize_addr(x["地址"]) for x in fisc_entries}
        fisc_branch_set = {x["裝設地點"] for x in fisc_entries}

        for item in scraper_data:
            branch    = item["branch"]
            norm_addr = normalize_addr(item.get("address", ""))
            addr_hit   = norm_addr in fisc_addr_set
            branch_hit = any(branch in fb or fb in branch for fb in fisc_branch_set)
            if addr_hit or branch_hit:
                continue
            gap_b.append({
                "代號":    cfg["bank_code"],
                "銀行名稱": cfg["fisc_name"],
                "裝設地點": branch,
                "縣市":    extract_city(item.get("address", ""), cfg["fisc_name"], branch),
                "地址":    item.get("address", ""),
                "lat":     item.get("lat", ""),
                "lng":     item.get("lng", ""),
                "currencies": item.get("currencies"),
                "source":  "bank_website",
            })
    return gap_b


def main():
    fisc_data = json.loads(GEOCODED.read_text(encoding="utf-8"))

    # 載入所有爬蟲結果
    scraped = []
    for f in SCRAPED_FILES:
        if f.exists():
            scraped.extend(json.loads(f.read_text(encoding="utf-8")))

    lookup = build_lookup(scraped)

    matched = fallback_matched = unmatched = excluded = 0
    result = []
    for entry in fisc_data:
        bank_name = entry.get("銀行名稱", "")
        loc       = entry.get("裝設地點", "")

        # 官網確認不存在或不對外的機台，直接排除
        if any(kw in bank_name and loc == exc_loc for kw, exc_loc in FISC_EXCLUDE):
            excluded += 1
            continue

        # 先嘗試分行名稱精確配對，再嘗試 fallback
        currencies = None
        for (bank_kw, branch_or_fisc), currs in lookup.items():
            if bank_kw not in bank_name:
                continue
            if branch_or_fisc in loc or loc in branch_or_fisc:
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
        new_entry["source"] = "fisc"
        result.append(new_entry)

    # Gap B：爬蟲有、FISC 無的 ATM，直接追加
    gap_b = find_gap_b(fisc_data)
    result.extend(gap_b)

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(result)
    with_cur = matched + fallback_matched + len(gap_b)
    scraped_banks = {item["bank"] for item in scraped}
    print(f"總筆數：{total}（FISC {len(fisc_data) - excluded} + Gap B {len(gap_b)}，排除 {excluded} 筆）")
    print(f"有幣別（分行精確配對）：{matched}")
    print(f"有幣別（fallback 配對）：{fallback_matched}")
    print(f"有幣別（Gap B 補入）：{len(gap_b)}")
    print(f"有幣別合計：{with_cur}（{with_cur * 100 // total}%）")
    print(f"無幣別：{unmatched}")
    print(f"排除（非公開）：{excluded}")
    print(f"已爬銀行：{', '.join(sorted(scraped_banks))}")
    print(f"輸出：{OUTPUT}")


if __name__ == "__main__":
    main()
