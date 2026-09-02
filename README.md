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
    └── 11-beauty-wink/
```

每款 Banner 資料夾固定只有五個檔案：

```text
index.html
banner.json
banner.atlas
banner.png
embed-code.txt
```

## 使用方式

- 全部 Banner：開啟根目錄的 `index.html`
- 單款 Banner：開啟 `banners/款式名稱/index.html`
- 嵌入其他網頁：複製該款資料夾內 `embed-code.txt` 的內容
- 搬移專案：複製整個 `spine2dAssets` 資料夾即可

本機預覽：<http://127.0.0.1:4188/>
