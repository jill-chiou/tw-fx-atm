# Step 03 — GitHub Pages：把地圖部署到網路上

> 讓任何人都能用瀏覽器打開地圖，不需要在自己電腦跑 local server。

---

## 什麼是 GitHub Pages？

GitHub Pages 是 GitHub 提供的**靜態網站托管服務**。把 HTML / CSS / JS / JSON 放進 repo，GitHub 就會自動把它們變成一個可公開訪問的網址。

**靜態**的意思：沒有後端伺服器、沒有資料庫，純粹是「把檔案送給瀏覽器」。本專案剛好符合——地圖邏輯在 `index.html`，資料在 `atm_geocoded.json`，全部都是靜態檔。

---

## 部署步驟

1. GitHub Repo → **Settings** → 左側 **Pages**
2. **Branch** 選 `main`，資料夾選 `/ (root)` → **Save**
3. 等約 1-2 分鐘，頁面重整後出現：
   > Your site is live at `https://intomoonlight.github.io/tw-fx-atm`

網址規則：`https://{GitHub帳號}.github.io/{repo名稱}`

---

## 成果

| 項目 | 網址 |
|------|------|
| 公開地圖 | https://intomoonlight.github.io/tw-fx-atm |
| 顯示筆數 | 1,939 筆外幣 ATM 座標 |

---

## 踩到的坑

### 坑 1 — Private repo 無法開啟 Pages（需付費）

**症狀**：Settings → Pages 顯示「Upgrade or make this repository public to enable Pages」，沒有 Branch 選單。

**原因**：GitHub Pages 免費版只支援 **public** repo。Private repo 需要 GitHub Pro（$4/月）才能開 Pages。

**解法**：Settings → General → 最底下「Change repository visibility」→ 改成 **Public**。

**教訓**：備審作品集本來就適合公開，改 public 反而讓面試官能直接看 code，是加分項。

---

### 坑 2 — `data/` 被 .gitignore 擋掉，JSON 沒進 git

**症狀**：本機地圖正常，GitHub Pages 上地圖空白，開 DevTools 看到 `fetch` 404。

**原因**：`.gitignore` 有一行 `data/`，把整個 data 目錄排除。`atm_geocoded.json` 沒有進 git，GitHub 上根本沒有這個檔案。

**解法**：在 `.gitignore` 加例外：
```
data/
!data/processed/atm_geocoded.json
```
然後 force-add：
```bash
git add -f data/processed/atm_geocoded.json
```

**教訓**：靜態網站的資料檔必須進 git 才能被 GitHub Pages 服務。`git status` clean 只代表沒有未 commit 的變更，不代表所有需要的檔案都在 repo 裡。

---

## 本步驟學到的概念

- **靜態網站托管**：不需要後端，只要把檔案交給 CDN，任何人都能訪問
- **GitHub Pages 限制**：免費版只支援 public repo
- **.gitignore 例外規則**：`!` 前綴可以讓某個路徑不受上層規則影響
- **DevTools Network 面板**：部署後出問題，第一步是看 fetch 有沒有 404
