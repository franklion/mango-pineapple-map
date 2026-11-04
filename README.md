# 芒果鳳梨散步地圖

帶孩子旅行，把世界變成故事。

一個記錄家庭旅遊的地圖網站：首頁是台灣縣市地圖，標出走過的地方；點進每趟旅程，可以看到住宿、美食、景點、公園與步行路線，以及沿途的小故事和實用提醒。

## 專案結構

```
public/index.html   網站本體（單一檔案，旅程資料在 TRIPS 陣列）
wrangler.jsonc      Cloudflare Workers 部署設定（只上線 public/）
```

## 技術說明

- 純靜態網站，沒有建置步驟。部署在 Cloudflare Workers（靜態資源模式），push 到 `main` 會自動部署；`public/` 也能直接放到任何靜態主機。
- 地圖使用 [MapLibre GL JS](https://maplibre.org/) 4.7.1（jsDelivr 載入），Apple 地圖風格的自訂樣式寫在 `index.html` 的 `MAP_THEMES` / `appleStyle()`，含淺色與深色兩套。
- 向量圖磚與字型即時讀取 [OpenFreeMap](https://openfreemap.org/)（OpenMapTiles 架構，OpenStreetMap 資料），只下載畫面上看得到的部分，任何地區都能直接瀏覽，新增旅程不需要準備地圖資料。中文標籤使用裝置本機字型（Apple 裝置為蘋方）。
- 地圖程式庫在首頁顯示後於背景預先載入，進入旅程頁時通常已就緒。
- 首頁台灣縣市邊界來自 [taiwan-atlas](https://github.com/dkaoster/taiwan-atlas)，已簡化並預先投影成 SVG 路徑內嵌在 `index.html`。

## 本機預覽

```bash
cd public && python3 -m http.server 8000
# 開啟 http://localhost:8000
```

建議透過 HTTP 開啟；地圖資料來自網路，預覽時需要連網。

## 新增一趟旅程

1. 在 `public/index.html` 的 `TRIPS` 陣列新增一筆：
   - `id`、`start`（`YYYY-MM-DD`，用來排序與首頁旗子日期）、`title`、`region`、`county`（例：`新竹縣`，首頁會塗色）、`pin`（`flag: "left"` 可讓旗子放左邊）、`dates`、`length`、`transport`、`lead`、`story`、`blog`（部落格連結，可省略）、`highlight`（特別段落，可省略）
   - `places[]`：每個地點的 `kind`（stay / food / play / park / move / wish）、`name`、精確 `lat` / `lon`（從 Google 地圖複製）、`note`、`tags`，可選 `nick`、`age`、`day`、`tip`、`address` / `area`、`offRoute`、`wish`、`labelLeft`
   - 行程順序二選一：`route`（步行路線：`stops`、`how`、`tips`，地圖畫成動態虛線）或 `days`（逐日行程：每天 `label`、`date`、`stops`、`note`，地圖每天一條細線）
   - `map.bounds`：地圖預設範圍（實際會自動框住步行路線上的地點）
2. commit 並 push 到 `main`，Cloudflare 會自動部署。

## 資料來源與授權

- 地圖：© [OpenFreeMap](https://openfreemap.org/)、© [OpenMapTiles](https://www.openmaptiles.org/)、資料來自 © [OpenStreetMap](https://www.openstreetmap.org/copyright) 貢獻者
- 台灣縣市邊界：[taiwan-atlas](https://github.com/dkaoster/taiwan-atlas)（資料源自內政部國土測繪中心，政府資料開放授權）
- 旅程文字與心得：© 芒果鳳梨散步地圖，保留所有權利
