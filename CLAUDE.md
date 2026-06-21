# 外幣 ATM 地圖整合專案

> 推甄 Side Project 1。全域脈絡見 `~/.claude/CLAUDE.md`，推甄規劃見 Obsidian。

## 專案目標

整合全台 17 家銀行外幣 ATM 位置與可領幣別，做成互動地圖（GitHub Pages 靜態網站）。

## 線上 Demo

https://jill-chiou.github.io/tw-fx-atm

## 技術棧

```
金管會 PDF（86頁）
  → pdfplumber → CSV（1,962 筆）
  → TGOS geocoding → atm_geocoded.json（98.5% 成功率）
  → Leaflet.js 地圖 + 幣別爬蟲（17 家全覆蓋，100%）
  → SQLite pipeline（atm_locations / bank_currencies / source_log）
  → GitHub Pages 部署
```

## 目前狀態

- [x] Phase 1–3 全部完成（地圖、RWD、幣別爬蟲、SQLite pipeline）
- [x] 月更腳本驗證（2026-06-10 手動執行：無差異，FISC 1,961 筆，環境正常）

## 待確認

- 兆豐「新店分行」、中信「全家\_葵爾特店」：等 FISC 下次更新（被動）

## GitHub

https://github.com/jill-chiou/tw-fx-atm（public）
