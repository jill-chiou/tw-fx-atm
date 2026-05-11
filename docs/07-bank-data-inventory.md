# 銀行外幣 ATM 資料來源 Inventory

> 調查日期：2026-05-09
> 目的：評估各家銀行幣別資料的可取得性，決定爬蟲優先順序。

---

## 基底資料：FISC 財金公司統一 PDF

所有銀行的外幣 ATM 位置都由財金公司彙整，每月更新一份公開 PDF：

| 欄位 | 內容 |
|------|------|
| URL | https://www.fisc.com.tw/tc/Download/atmfc.pdf |
| 更新頻率 | 每月（2026/04/30 為最新一期） |
| 欄位 | 機構代號、機構名稱、裝設地點、縣市、地址 |
| has_currency | **N**（只有位置，無幣別） |
| 爬取難度 | 極低（直連 PDF，`pdfplumber` 可解析） |

這份 PDF 是目前專案使用的主要資料來源。幣別資訊需另行從各銀行官網補充。

---

## 各銀行 Inventory

| # | 銀行名稱 | 台數 | source_url | source_type | has_currency | crawl_method | 備註 |
|---|---------|------|-----------|-------------|-------------|-------------|------|
| 1 | 台新國際商業銀行 | 1,027 | https://www.taishinbank.com.tw/TSB/service-and-support/atm-location | 動態地圖 | N | Playwright（需逆向 API） | 最大宗，但官網完全不顯示幣別；需從 Network tab 找 API endpoint |
| 2 | 國泰世華商業銀行 | 171 | https://www.cathaybk.com.tw/cathaybk/locations/ | 動態地圖 | 不確定 | Playwright | 有美金/日幣篩選器，API 未公開 |
| 3 | 中國信託商業銀行 | 167 | https://www.ctbcbank.com/twrbo/zh_tw/index/h_locate_index/h_ATMlocate_inquiry.html | 動態地圖 | 不確定 | Playwright | 有按幣別（USD/JPY/CNY）篩選功能，各分行幣別不同 |
| 4 | 玉山商業銀行 | 139 | https://www.esunbank.com/en/about/locations/foreign-currency-atm | 動態地圖 | N | Playwright | 需啟用地理定位才顯示結果，無幣別資訊 |
| 5 | 兆豐國際商業銀行 | 122 | https://www.megabank.com.tw/about/mega-intro/locations?tab=3 | 動態表格 | **Y** | Playwright / requests | **各據點幣別（USD/JPY/EUR/CNY）明確列出**，是大型銀行中透明度最高的 |
| 6 | 永豐商業銀行 | 91 | https://bank.sinopac.com/MMA8/CustomerService/BranchService/ATM.html | 動態地圖+篩選 | 不確定 | Playwright | 有日幣/人民幣/美金/港幣篩選，整合 Google Maps |
| 7 | 華南商業銀行 | 47 | https://www.hncb.com.tw/wps/portal/HNCB/locations/atm | 動態表格 | 不確定 | Playwright | 有 USD/CNY/HKD/JPY 篩選；另有 PDF 清單可下載（無幣別） |
| 8 | 臺灣銀行 | 44 | https://www.bot.com.tw/tw/personal-banking/foreign-exchange/foreign-currency-cash-exchange/foreign-currency-ATM | 靜態說明頁 | **Y（統一）** | 直接套用 FISC | 官網明確說明全行統一：USD/HKD/JPY/CNY；無 EUR。官網地圖（~20 筆）比 FISC（44 筆）少，FISC 更完整（含桃園機場 6 台等）|
| 9 | 第一商業銀行 | 42 | https://www.firstbank.com.tw/sites/fcb/ATMNearYou | 動態地圖 + REST API | **Y（保守）** | requests POST API | API endpoint: `/sites/REST/controller/ATMNearYouRevCTL/searchATM`，免 bot 保護。兩種機型：外幣提款（5）+ 臺外幣二合一（37）= 42 台。API 不回傳幣別，保守標記 USD/JPY |
| 10 | 台北富邦商業銀行 | 39 | https://www.fubon.com/banking/locations/locations.htm?type=atm&zoned=0&tab=1 | 動態地圖 | N | Playwright | 僅美金/日幣兩種；無幣別資訊 |
| 11 | 臺灣新光商業銀行 | 29 | https://www.skbank.com.tw/DE-FCATM/ | **靜態 HTML 表格** | **Y** | requests + BeautifulSoup | **最易爬取**，約 15-20 個據點，幣別逐台列出（USD/JPY/CNY/HKD） |
| 12 | 合作金庫商業銀行 | 15 | https://www.tcb-bank.com.tw/about-tcb/info/locations/foreign-exchange?tab=3 | 動態表格 | 不確定 | Playwright | 備註「幣別依各分行放置為準」；有美金/日幣篩選 |
| 13 | 臺灣土地銀行 | 12 | https://www.landbank.com.tw/Location/Atm/ATM%E4%BD%8D%E7%BD%AE | 動態地圖 | N | — | 無外幣篩選功能，不顯示幣別，優先級低 |
| 14 | 元大商業銀行 | 7 | https://www.yuantabank.com.tw/bank/spotMap/list.do?type=5 | 動態（403） | 不確定 | Playwright（高風險） | 403 封鎖 HTTP 請求，反爬機制明顯 |
| 15 | 臺灣中小企業銀行 | 6 | https://www.tbb.com.tw/zh-tw/about/intro/location/atm | 動態篩選 | N | — | 有「外幣提款」篩選但無幣別資訊，台數少 |
| 16 | 上海商業儲蓄銀行 | 2 | https://www.scsb.com.tw/content/about/about05_a.html | 動態篩選 | N | — | 只有 2 台，優先級極低 |
| 17 | 彰化商業銀行 | 1 | https://www.bankchb.com/frontend/atm.jsp | 動態（XML） | 不確定 | — | 只有 1 台，XML 框架結構，優先級極低 |

---

## 爬取優先順序

### 第一梯隊：馬上可做（資料明確 + 爬取容易）

| 銀行 | 台數 | 理由 |
|------|------|------|
| **臺灣新光商業銀行** | 29 | 靜態 HTML，幣別逐台列出，`requests + BeautifulSoup` 即可，是最佳 POC 選擇 |
| **兆豐國際商業銀行** | 122 | 幣別資訊最透明的大型銀行，Playwright 動態渲染後可解析 |

### 第二梯隊：需 Playwright，但有幣別篩選線索

| 銀行 | 台數 | 做法 |
|------|------|------|
| 中國信託 | 167 | Playwright 操控幣別篩選（選 USD → 記錄 → 選 JPY → 記錄 → ...） |
| 國泰世華 | 171 | 同上 |
| 永豐 | 91 | 同上，含港幣/人民幣 |
| 華南 | 47 | 同上 |

### 第三梯隊：幣別不透明或風險高

| 銀行 | 台數 | 問題 |
|------|------|------|
| 台新 | 1,027 | 最大宗，但官網完全無幣別；需逆向 JS bundle 或找 API；可考慮聯繫資料授權 |
| 玉山 | 139 | 需地理定位才顯示，幣別不透明 |
| 台北富邦 | 39 | 僅美金/日幣，動態頁面 |
| 元大 | 7 | 403 反爬，需瀏覽器模擬 |

### 暫不處理

土地銀行（無幣別功能）、企銀、上海商銀、彰銀（台數過少）。

---

## 新光銀行 POC 結果（2026-05-09）

**腳本**：`scripts/scrape_skbank.py`
**輸出**：`data/processed/skbank_currencies.json`

### 爬取結果

官網共 18 個據點，分 4 個幣別組合：

| 幣別 | 台數 | 據點 |
|------|------|------|
| USD + JPY + CNY + HKD | 1 | 世貿分行 |
| USD + JPY + CNY | 2 | 南東分行、新板分行 |
| USD + JPY | 15 | 復興分行等其他據點 |

### FISC 比對結果

FISC 同銀行共 29 筆，以子字串比對（官網 branch ⊂ FISC 裝設地點）：

- **命中 17/18（94%）**：大多數分行名可直接比對
- **未命中 1/18**：「天母傑仕堡」——FISC 對應條目名稱不同，暫無法自動配對
- **FISC 多出 11 筆**：均為行外 ATM（商場、醫院、便利超商等），官網未列出幣別

### 關鍵發現

1. **官網 ≠ FISC 完整清單**：銀行官網只列自行管理的分行 ATM；行外 ATM 出現在 FISC 但不在官網，幣別資訊需另尋。
2. **字串包含比對有效**（官網分行名 ⊂ FISC 裝設地點）：適合 merge 規則 v1 使用。
3. **面額資訊也取得**：每種幣別的最小提領面額（USD: 50 or 100、JPY: 10,000 等）可一併存入。

---

## 建議執行策略

1. **新光銀行 POC ✅**：已完成。18 筆幣別資料、94% 比對成功。
2. **幣別 merge 規則（Step 6）**：以銀行代號 + 子字串比對作為主要鍵；行外 ATM 無匹配時標 `currencies: null`。
3. **兆豐銀行 ✅**：實測發現不需 Playwright，直接呼叫內部 JSON API 即可。118 筆幣別資料，106/118（89%）命中。
4. **中信、國泰世華、永豐**：Playwright 操控幣別篩選，第三梯隊。
5. **台新銀行**：暫時跳過，先把其他銀行的幣別做完，或另外探查 API endpoint。

---

## 台數與覆蓋率統計

> 資料來源：FISC PDF（2026/04/30）｜總計 1,960 筆

| 排名 | 銀行名稱 | 台數 | 占比 | 幣別爬蟲狀態 |
|------|---------|------|------|------------|
| 1 | 台新國際商業銀行 | 1,026 | 52% | ✅ 完成（1,011 筆，機台層級）|
| 2 | 國泰世華商業銀行 | 171 | 9% | ✅ 完成（171 筆，USD/JPY）|
| 3 | 中國信託商業銀行 | 167 | 9% | ✅ 完成（167 筆，統一 USD/JPY/CNY）|
| 4 | 玉山商業銀行 | 139 | 7% | ✅ 完成（136 筆）|
| 5 | 兆豐國際商業銀行 | 122 | 6% | ✅ 完成（114 筆）|
| 6 | 永豐商業銀行 | 91 | 5% | ✅ 完成（74 筆命中）|
| 7 | 華南商業銀行 | 47 | 2% | ✅ 完成（46 筆）|
| 8 | 臺灣銀行 | 44 | 2% | ✅ 完成（44 筆，統一 USD/HKD/JPY/CNY）|
| 9 | 第一商業銀行 | 42 | 2% | ✅ 完成（42 筆，保守 USD/JPY）|
| 10 | 台北富邦商業銀行 | 39 | 2% | ⏳ 待處理 |
| 11 | 臺灣新光商業銀行 | 29 | 1% | ✅ 完成（17 筆命中）|
| 12 | 合作金庫商業銀行 | 15 | 1% | ⏳ 待處理 |
| 13 | 臺灣土地銀行 | 12 | 1% | ⏳ 待處理 |
| 14 | 元大商業銀行 | 7 | 0% | ⏳ 待處理 |
| 15 | 臺灣中小企業銀行 | 6 | 0% | ⏳ 待處理 |
| 16 | 上海商業儲蓄銀行 | 2 | 0% | ⏳ 待處理 |
| 17 | 彰化商業銀行 | 1 | 0% | ⏳ 待處理 |

### 累積覆蓋率（2026-05-11 現況）

| 完成銀行 | 幣別有資料台數 | 覆蓋率 |
|---------|-------------|--------|
| 台新 + 兆豐 + 國泰世華 + 中信 + 玉山 + 華南 + 永豐 + 新光（2026-05-11 commit）| 1,140 | 58% |
| + 臺灣銀行 | 1,184 | 60% |（fallback 合計 1,799，91%）
| + 第一商業銀行 | 1,226 | 63% |（fallback 合計 1,839，93%）
| 剩餘缺口（台北富邦 39 + 合庫 15 + 土銀 12 + 元大 7 + 企銀 6 + 上海商銀 2 + 彰銀 1）| — | ~82 台 |
