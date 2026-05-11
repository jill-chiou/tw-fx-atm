# Verification Before Completion

說「完成」、「跑完了」、「沒問題」之前，必須有**可執行的驗證指令**和**實際輸出**作為證據。

> 「宣稱工作完成但沒有驗證，是不誠實，不是有效率。」

---

## 通關檢查（每次說完成前跑一遍）

```
1. IDENTIFY：哪個指令可以證明這個宣稱？
2. RUN：完整跑一次（不是「上次跑過了」）
3. READ：讀完整輸出，確認數字
4. VERIFY：輸出是否符合預期？
5. 才說完成
```

---

## 各種宣稱的對應驗證方式

| 宣稱 | 必須提供的證據 |
|------|--------------|
| 爬蟲跑完了 | 印出抓到幾筆、幣別種類、前 3 筆 sample |
| merge 完成 | 印出 `len(merged)` 的實際數字，對比上次數字 |
| 地址比對通過 | 印出比對成功率（X / Y 筆），以及失敗的 sample |
| 前端功能正常 | 開 browser 實際點過：篩選、搜尋、底部面板、點擊 ATM marker |
| bug 修好了 | 重現原本的失敗步驟，確認這次不再出現 |

---

## 這個專案的標準驗證輸出格式

每次跑完 scraper 或 merge，輸出應包含：

```
銀行：xxx
抓到：N 筆 ATM 幣別資料
幣別種類：USD, JPY, CNY, HKD
Sample（前 3 筆）：
  { "atm_id": "...", "branch": "...", "currencies": [...] }
  ...
寫入：data/processed/xxx_currencies.json ✅
```

每次跑完 merge_currencies.py，輸出應包含：

```
Merge 完成
總筆數：1,960
有幣別資料：N 筆（XX%）
  新光：N
  兆豐：N
  ...
輸出：data/processed/atm_with_currencies.json ✅
```

---

## 禁止的說法

- 「應該可以」
- 「我有信心這樣沒問題」
- 「看起來對」
- 「上次有跑成功過」

這些話出現的瞬間，就是跳過驗證的信號。
