# Spine Banner 成品

這個資料夾只保留可直接使用的正式檔案，沒有生成工具、測試角色、QA 截圖或舊版壓縮包。

```text
spine2dAssets/
├── index.html
├── README.md
└── banners/
    ├── shared/
    │   ├── spine-player-3.8.css
    │   └── spine-player-3.8.js
    ├── 01-champions-night/
    ├── 02-star-summit/
    ├── ...
    ├── 14-temujin/
    └── 15-cowboy-hat-tip/
```

01–11 款主要使用以下檔案，並共用 `banners/shared` 播放器：

```text
index.html
banner.json
banner.atlas
banner.png
embed-code.txt
```

14、15 款則把播放器、動畫資料、圖檔和 `index.html` 都放在各自的單一資料夾中，可單獨搬移，不需要複製 `shared`。15 款為「狂野印第安對決」，有槍口頂帽、停留再放回的循環動作；嵌入語法在該款的 `embed-code.txt`。

## 使用方式

- 全部 Banner：開啟根目錄的 `index.html`
- 單款 Banner：開啟 `banners/款式名稱/index.html`
- 嵌入其他網頁：複製該款資料夾內 `embed-code.txt` 的內容
- 搬移專案：複製整個 `spine2dAssets` 資料夾即可

本機預覽：<http://127.0.0.1:4188/>
