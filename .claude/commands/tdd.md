# Test-Driven Development（for Python Scripts）

這個專案的 Python 腳本都有明確的輸入輸出格式，適合用簡單的 assert 做保護。
不需要完整的 pytest 套件，用內嵌 assert 就夠。

---

## 核心規則

**修改任何函數前，先寫一個會失敗的 assert，確認它真的失敗，再寫修改，再確認 assert 通過。**

不先寫 assert 就修改 = 不知道自己改了什麼。

---

## 這個專案需要測試保護的高風險區域

### 1. 地址正規化（`merge_currencies.py`）

正規化邏輯最容易改壞，每個 case 都應該有對應的 assert：

```python
# 在 merge_currencies.py 底部或獨立的 test_normalize.py 加上這段
def test_normalize():
    cases = [
        # (輸入, 預期輸出)
        ("臺北市中正區重慶南路一段122-1號", "台北市中正區重慶南路1段122之1號"),
        ("新北市板橋區文化路二段10之3號",   "新北市板橋區文化路2段10之3號"),
        ("高雄市三民區九如一路123號",        "高雄市三民區九如1路123號"),
        # 加入你在驗證時遇到過的 edge case
    ]
    for raw, expected in cases:
        result = normalize_address(raw)
        assert result == expected, f"\n輸入: {raw}\n預期: {expected}\n實際: {result}"
    print("✅ 地址正規化全數通過")

if __name__ == "__main__":
    test_normalize()
```

### 2. 爬蟲輸出格式

每個 scraper 都應確認輸出結構正確：

```python
# 在每個 scrape_xxx.py 末尾加
def validate_output(data: list[dict]):
    assert len(data) > 0, "爬到 0 筆，可能爬蟲失敗"
    required_keys = {"branch", "address", "currencies"}
    for item in data[:3]:  # 抽查前 3 筆
        missing = required_keys - set(item.keys())
        assert not missing, f"缺少欄位：{missing}，資料：{item}"
    assert all(isinstance(item["currencies"], list) for item in data), \
        "currencies 欄位應為 list"
    print(f"✅ 格式驗證通過：{len(data)} 筆")
```

### 3. Merge 結果完整性

```python
# merge_currencies.py 末尾
def validate_merge(original: list, merged: list):
    assert len(merged) == len(original), \
        f"merge 後筆數變了：{len(original)} → {len(merged)}"
    with_currencies = [a for a in merged if a.get("currencies")]
    assert len(with_currencies) >= 640, \
        f"有幣別資料的筆數少於預期：{len(with_currencies)}"
    print(f"✅ Merge 完成：{len(with_currencies)} / {len(merged)} 筆有幣別資料")
```

---

## 新爬蟲的開發流程

1. **先寫 `validate_output()`** → 執行 → 確認它因為「沒有資料」而失敗
2. 寫爬蟲邏輯
3. 執行 → 確認 `validate_output()` 通過
4. 再執行一次完整流程 + `merge_currencies.py` → 確認 merge 數字正確

不要跳過步驟 1，否則 validate 通過只是因為 assert 本身有問題。

---

## 遇到這些藉口時的回應

| 藉口 | 實際情況 |
|------|---------|
| 「這個腳本很簡單不需要測試」 | 地址正規化也「很簡單」，但之前發現 X/Y 座標對調的 bug |
| 「我已經用眼睛看過輸出了」 | 眼睛看過的 3 筆不代表 646 筆都對 |
| 「先讓它跑起來，測試之後再加」 | 之後永遠不會加，而且此時改已知邏輯最危險 |
