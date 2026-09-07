# Spine Banner 成品

根目錄的 `index.html` 是唯一展示頁。15 款 Banner 素材與共用播放器統一放在 `banners/`，每款資料夾內提供可複製的嵌入語法。

```text
spine2dAssets/
├── index.html
├── README.md
├── SPINE_BANNER_ANIMATION_STANDARD.md
└── banners/
    ├── shared/
    │   ├── common-spine-player.js
    │   ├── spine-player-3.8.css
    │   └── spine-player-3.8.js
    ├── 01-champions-night/
    ├── 02-star-summit/
    ├── ...
    ├── 12-flame-monkey/       # 12 · 烈焰猴王
    ├── 13-airborne-strike/
    ├── 14-temujin/
    └── 15-cowboy-hat-tip/
```

每款 Banner 至少包含以下標準檔案，並共用 `banners/shared` 播放器；素材圖檔依動畫需要可有一張或多張：

```text
banner.json
banner.atlas
*.png
embed-code.txt
```

頁面只需引入 `common-spine-player.js`，它會自動載入共用 Spine runtime 與樣式、依可見範圍載入 Banner、離開畫面時暫停並停放播放器、管理 WebGL 實例；控制列預設隱藏。展示與嵌入均直接使用素材，不需要 iframe 或單款 HTML 頁面。

## 使用方式

- 預覽全部 Banner：由 HTTP 靜態伺服器開啟根目錄的 `index.html`
- 嵌入其他網頁：複製該款資料夾內 `embed-code.txt` 的內容，不需要 iframe
- 搬移單款：保留 `banners/該款資料夾/` 與 `banners/shared/`；嵌入碼中的路徑需對應目標網頁位置
- 搬移全部：複製 `banners/` 即可；需要展示頁時再加上根目錄的 `index.html`
- 同一頁放多款 Banner：每款放一個嵌入用的 `div`，共用播放器的 `script` 只需引入一次

本機預覽：<http://127.0.0.1:4188/>
