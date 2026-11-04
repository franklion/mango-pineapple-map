# 芒果鳳梨散步地圖

帶孩子旅行，把世界變成故事。

一個記錄家庭旅遊的地圖網站：首頁是台灣縣市地圖，標出走過的地方；點進每趟旅程，可以看到住宿、美食、景點、公園與步行路線，以及沿途的小故事和實用提醒。

## 專案結構

```
index.html              網站本體（單一檔案，旅程資料在 TRIPS 陣列）
map/<地區>.json         各地區的向量地圖資料（點進旅程時才下載）
map/fonts.json          地圖拉丁字形（全站共用，中文用裝置本機字型）
tools/build_map_data.py 新地區地圖資料打包工具
```

## 技術說明

- 純靜態網站，沒有建置步驟，任何靜態主機都能直接部署（Cloudflare Pages、GitHub Pages 等）。
- 地圖使用 [MapLibre GL JS](https://maplibre.org/) 4.7.1（jsDelivr 載入），Apple 地圖風格的自訂樣式寫在 `index.html` 的 `MAP_THEMES` / `appleStyle()`，含淺色與深色兩套。
- 向量圖磚來自 [OpenFreeMap](https://openfreemap.org/)（OpenMapTiles 架構，OpenStreetMap 資料），已預先下載、瘦身並打包成 `map/*.json`（gzip + base64），頁面透過自訂 `trip://` 協定解壓後交給 MapLibre。這是為了能在 Claude artifact 的安全限制下運作；搬到外部主機後，也可以改成即時讀取 OpenFreeMap，不必再打包。
- 首頁台灣縣市邊界來自 [taiwan-atlas](https://github.com/dkaoster/taiwan-atlas)，已簡化並預先投影成 SVG 路徑內嵌在 `index.html`。

## 本機預覽

```bash
python3 -m http.server 8000
# 開啟 http://localhost:8000
```

需要透過 HTTP 開啟，直接雙擊 `index.html` 會讀不到 `map/` 資料。

## 新增一趟旅程

1. 在 `index.html` 的 `TRIPS` 陣列新增一筆：
   - `id`、`title`、`region`、`county`（例：`新竹縣`，首頁會塗色）、`pin`、`dates`、`length`、`transport`、`lead`、`story`、`blog`（部落格連結，可省略）
   - `places[]`：每個地點的 `kind`（stay / food / play / park / move / wish）、`name`、精確 `lat` / `lon`（從 Google 地圖複製）、`note`、`tags`，可選 `nick`、`age`、`day`、`tip`、`address` / `area`、`offRoute`、`wish`、`labelLeft`
   - `route`：步行順序 `stops`、`how`（陪走技巧）、`tips`（提醒），可省略
   - `map.bounds`、`mapData`（地區代號）
2. 若是新地區，產生地圖資料（同地區的旅程共用同一檔）：
   ```bash
   python3 tools/build_map_data.py region <key> <minLon,minLat,maxLon,maxLat> [...]
   ```
   bbox 取所有地點外擴約 300 公尺；分散的點可以多給幾個 bbox。字型只需產生一次：`python3 tools/build_map_data.py fonts`。

## 資料來源與授權

- 地圖：© [OpenFreeMap](https://openfreemap.org/)、© [OpenMapTiles](https://www.openmaptiles.org/)、資料來自 © [OpenStreetMap](https://www.openstreetmap.org/copyright) 貢獻者
- 台灣縣市邊界：[taiwan-atlas](https://github.com/dkaoster/taiwan-atlas)（資料源自內政部國土測繪中心，政府資料開放授權）
- 旅程文字與心得：© 芒果鳳梨散步地圖，保留所有權利
