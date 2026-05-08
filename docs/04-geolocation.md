# Step 04 — 裝置定位與距離排序

> 讓使用者一鍵找到附近最近的外幣 ATM。

---

## 功能設計

點「定位」按鈕後：

1. 瀏覽器詢問使用者是否允許取得位置
2. 取得成功 → 地圖移至使用者位置，並標示藍色圓點
3. 計算使用者與所有目前**顯示中**的 ATM 的距離
4. 畫面下方出現「附近的外幣 ATM」面板，列出最近 5 筆（含距離、可點擊跳至地圖）
5. 切換銀行篩選器時，面板自動更新

---

## Geolocation API

這是瀏覽器的內建 API，W3C 標準，不需要安裝任何套件：

```javascript
navigator.geolocation.getCurrentPosition(
  pos => {
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
  },
  error => {
    // 使用者拒絕、裝置不支援、逾時
  }
);
```

### 手機 vs 電腦的差異

API 介面完全相同，差別在底層硬體：

| | 手機 | 電腦 |
|---|---|---|
| 定位來源 | GPS 晶片 + WiFi + 基地台 | WiFi 位置 + IP（無 GPS）|
| 精確度 | 3~10 公尺 | 幾十公尺到幾公里不等 |

程式碼不需要區分裝置，瀏覽器會自動用最精確的來源。

**限制**：必須是 HTTPS 才能使用 Geolocation API。`http://` 底下瀏覽器會直接拒絕。GitHub Pages 預設 HTTPS，沒問題。

---

## 距離計算：直線 vs 步行

### 為什麼選直線距離（Haversine）？

做決策前評估了兩個選項：

| | 直線距離（Haversine）| 步行距離（routing API）|
|---|---|---|
| 運算方式 | 純數學公式，本地計算 | 每筆打一次 routing API |
| 速度 | 毫秒內算完 1,939 筆 | 1,939 筆要打 1,939 次 API |
| 準確度 | 鳥飛距離，不考慮道路 | 實際步行路線 |
| 費用 | 免費 | OSRM 免費但慢；Google Maps 要錢 |

**結論：直線距離對這個使用情境「夠好」。**

原因：
1. ATM finder 的查詢範圍通常是幾百公尺內，這個尺度下直線和步行差距很小
2. 除非中間有河、高架、圍牆，否則直線排出的「最近」，步行順序幾乎相同
3. **Google Maps 自己的「附近」排序也是直線距離**，只有使用者點「導航」才計算路線——這不是因為 Google 做不到，而是在使用者還沒決定要去哪之前，提前算路線是浪費運算資源

這個思路叫「夠好就好（Good Enough）」：不為邊緣案例犧牲整體效能，等真正需要精確路線時（未來做「導航」功能），再換掉排序函式就好。

### Haversine 公式

計算地球表面兩點之間的直線距離（考慮地球曲率）：

```javascript
function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371000; // 地球半徑（公尺）
  const toRad = x => x * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat/2)**2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}
```

在台灣的尺度（城市內幾公里），Haversine 誤差可以忽略。

---

## 成果

| 功能 | 說明 |
|------|------|
| 定位按鈕 | Header 右側，點擊取得位置 |
| 使用者標記 | 地圖上藍色圓點，點開顯示「你在這裡」|
| 附近面板 | 畫面下方，列出最近 5 筆 ATM + 直線距離 |
| 篩選器聯動 | 切換銀行篩選時，附近面板自動重新排序 |
| 點擊跳轉 | 點附近面板的 ATM，地圖自動移過去並開 popup |

---

## 本步驟學到的概念

- **Geolocation API**：瀏覽器內建，不需要套件，需要 HTTPS
- **Haversine 公式**：考慮地球曲率的直線距離計算
- **Good Enough 工程決策**：直線距離在合理使用情境下夠準，不需要為邊緣案例引入複雜的 routing API
- **API 設計**：`showNearby()` 與篩選器解耦，任何改變可見 ATM 的操作都能觸發更新
