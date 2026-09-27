# 外幣 ATM 地圖整合專案

> 荷蘭申請 Portfolio 素材（Maastricht BISS Portfolio、RSM Motivation 佐證）。全域脈絡見 `~/.claude/CLAUDE.md`，申請規劃見 Obsidian。
> 英文版 `README.en.md` 是給 admissions 讀的，改數字時中英文要一起改。

## 專案目標

整合全台 17 家銀行外幣 ATM 位置與可領幣別，做成互動地圖（GitHub Pages 靜態網站）。

## 線上 Demo

https://jill-chiou.github.io/tw-fx-atm

## 技術棧

```
FISC（財金資訊公司）PDF（8/31 版 108 頁）
  → pdfplumber → atm_data.csv（2,363 筆）
  → TGOS 批次比對 → atm_geocoded.json（2,351 筆有座標，99.5%）
  → 17 家銀行幣別（8 家爬蟲、8 家全行固定幣別、1 家手動）
  → SQLite pipeline → atm_with_currencies.json（2,378 筆 = FISC 2,356 + 官網補入 22，幣別 100%）
  → Leaflet.js 地圖 → GitHub Pages
```

## 目前狀態

- [x] Phase 1–3 全部完成（地圖、RWD、幣別爬蟲、SQLite pipeline、幣別篩選）
- [x] 最近一次月更：2026-09-27（FISC 8/31 版；6 月之後中斷三個月才補跑）
- 座標待查：與官網座標相距 > 200m 的 90 筆（`data/processed/coord_check_vs_bank.csv`），未逐筆判定

## 月更步驟（2026-09 實跑順序）

1. `update_from_fisc.py` → `export_for_tgos.py` → 使用者手動上傳 TGOS（EPSG:4326）→ 結果存 `tgos_result.csv` → `import_tgos_result.py` → `validate_and_fix_geocoding.py`
2. 重跑 8 支連網爬蟲（cathaybk、esunbank、hncb、megabank、sinopac、skbank、taishinbank、firstbank）
3. 重跑 8 支由 FISC 清單產生的腳本（ctbc、bot、bankchb、fubon、landbank、tbb、tcb、yuanta），**必須在步驟 1 之後**
4. `merge_currencies.py` → SQLite 四步 → `check_coords_vs_bank.py`

注意：
- `validate_and_fix_geocoding.py` 每次都會重抽並覆蓋 `sample_validation.csv`（5 月人工核對的原始紀錄），跑完要 `git checkout` 還原
- `review_sample_maps.py` 不帶參數會讀寫 5 月的檔案；新一輪抽樣要帶 `<抽樣檔> <結果檔>`
- 國泰、永豐、台新官網曾從本機連線逾時（網路層），過一陣子重試即恢復；爬蟲失敗不會覆蓋舊檔
- TGOS 配錯的座標加在 `validate_and_fix_geocoding.py` 的 `COORD_OVERRIDES`，重新匯入後仍會套用

## 待確認

- 兆豐「新店分行」（`merge_currencies.py` 的 `PENDING`）、國泰「全家\_葵爾特店」（官網補入）：FISC 8/31 版仍未收錄，等下次更新（被動）

## GitHub

https://github.com/jill-chiou/tw-fx-atm（public）
