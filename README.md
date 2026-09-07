# Spine Banner 成品

這個資料夾只保留可直接使用的正式檔案，沒有生成工具、測試角色、QA 截圖或舊版壓縮包。

```text
spine2dAssets/
├── index.html
├── README.md
├── natural-motion-demo/       # 12 · 烈焰猴王
└── banners/
    ├── shared/
    │   ├── common-spine-player.js
    │   ├── spine-player-3.8.css
    │   └── spine-player-3.8.js
    ├── 01-champions-night/
    ├── 02-star-summit/
    ├── ...
    ├── 14-temujin/
    └── 15-cowboy-hat-tip/
```

每款 Banner 至少包含以下標準檔案，並共用 `banners/shared` 播放器；素材圖檔依動畫需要可有一張或多張：

```text
index.html
banner.json
banner.atlas
*.png
embed-code.txt
```

首頁不使用 iframe。頁面只需引入 `common-spine-player.js`，它會自動載入共用 Spine runtime 與樣式、依可見範圍載入 Banner、離開畫面時暫停並停放播放器、限制同時使用的 WebGL 實例；控制列預設隱藏。14、15 款也已轉成標準 `banner.json + banner.atlas`，不再各自複製一套播放器。

## 使用方式

- 全部 Banner：開啟根目錄的 `index.html`
- 單款 Banner：開啟 `banners/款式名稱/index.html`；12 款位於 `natural-motion-demo/index.html`
- 嵌入其他網頁：複製該款資料夾內 `embed-code.txt` 的內容，不需要 iframe
- 搬移專案：複製整個 `spine2dAssets` 資料夾即可

本機預覽：<http://127.0.0.1:4188/>
