# Spine Banner 成品

根目錄的 `index.html` 是 Vue 3 首頁。每款只顯示動畫、名稱、嵌入碼與複製按鈕；素材與共用播放器統一放在 `banners/`。修改前的原始首頁完整保留於 `index.backup.html`。

採用 Vue 官方支援的[免建置瀏覽器用法](https://vuejs.org/guide/quick-start.html#using-vue-from-cdn)，Vue 3.5.42 正式版及 MIT 授權存放在 `banners/shared/`，不依賴外部 CDN，不需要 npm install 或打包。

## 嵌入 Banner

Vue 頁面先匯入並註冊元件一次：

```js
import { createApp } from "./banners/shared/vue.esm-browser.prod.js";
import SpineBanner from "./banners/shared/SpineBanner.js?v=20260909-src-2";

createApp({
  components: { SpineBanner }
}).mount("#app");
```

之後每款只填資料夾路徑 `src`，首頁的複製按鈕也會複製這一行：

```html
<spine-banner src="./banners/15-cowboy-hat-tip/"></spine-banner>
```

元件透過 Vue [生命週期](https://vuejs.org/api/options-lifecycle.html)：`mounted` 自動載入共用播放器並掛載動畫；`beforeUnmount` 釋放播放器；`src` 改變時自動釋放舊動畫、切換素材。頁面不需要 `data-spine`、`v-spine`、手填 `aria-label` 或呼叫播放器 API。無障礙屬性由播放器內部處理。

`src` 指向包含 `banner.json`、`banner.atlas` 及貼圖的資料夾，不是 Banner 編號或 JSON 檔案。相對路徑以使用元件的 HTML 網頁為基準（有 `<base>` 時依該設定）；資料夾末尾的 `/` 可省略。也支援完整 HTTP／HTTPS 網址，跨網域伺服器需允許 CORS。在每款資料夾的預覽頁中，使用 `src="./"` 即可。

元件 import 與動態載入的共用播放器使用固定程式版本標記，避免瀏覽器把新版 `src` 頁面與舊版 `id` 程式混用。更新這兩個共用 JS 時，同步更新各預覽頁的 import 版本及 `SpineBanner.js` 的 `PLAYER_VERSION`；不要用每次不同的時間戳，Banner 的 `src` 也不需加版本參數。

非 Vue 網頁仍可沿用原本方式（`embed-code.txt` 保留此相容語法）：

```html
<div data-spine="15-cowboy-hat-tip"></div>
<script src="./banners/shared/common-spine-player.js"></script>
```

預設自動循環、隱藏控制列與 Spine Logo、顯示「加载中…」，寬度不超過 620px，小螢幕等比例縮小。共用 runtime 路徑依播放器位置解析；Vue 的素材路徑由 `src` 指定，搬到其他網頁時調整匯入位置與 `src` 即可。舊的非 Vue `data-spine` 嵌入方式仍依共用播放器位置尋找素材，保持相容。

首頁清單在 `index.html` 的 `banners` 陣列，每款一行，填入資料夾路徑與顯示名稱即可；Vue 自動產生卡片並掛載／釋放播放器：

```js
{ src: "./banners/15-cowboy-hat-tip/", name: "15 · 狂野印第安對決" }
```

## 檔案

```text
spine2dAssets/
├── index.html
├── effect.html                # 輸入 src 資料夾路徑即可預覽
├── index.backup.html          # Vue 改版前的原始首頁
├── README.md
├── SPINE_BANNER_ANIMATION_STANDARD.md
└── banners/
    ├── shared/
    │   ├── SpineBanner.js
    │   ├── common-spine-player.js
    │   ├── spine-player-3.8.css
    │   ├── spine-player-3.8.js
    │   ├── vue.esm-browser.prod.js
    │   └── vue.LICENSE.txt
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
index.html       # 該款動畫的獨立預覽
banner.json
banner.atlas
*.png
embed-code.txt
```

Vue 頁面透過 `SpineBanner` 元件管理動畫；非 Vue 頁面引入 `common-spine-player.js`。共用管理器負責載入 Spine runtime 與樣式、依可見範圍載入 Banner、離開畫面時暫停並停放播放器、管理 WebGL 實例；控制列預設隱藏。每款 `index.html` 只供獨立預覽，不轉址、不複製素材；嵌入其他網頁仍直接使用元件，不需要 iframe。

PNG 素材已做調色盤壓縮、移除中繼資料，並縮小過大的貼圖及同步更新圖集座標。27 張 PNG 總計約 7.57 MB（原約 36.68 MB，減少 79%）；保留透明背景與原有 HTML 嵌入方式。此容量不含動畫 JSON、圖集及共用播放器。

## 使用方式

- 預覽全部 Banner：由 HTTP 靜態伺服器開啟根目錄的 `index.html`
- 預覽任意資料夾：開啟根目錄 `effect.html`，填入 `src` 後按「播放」（亦可按 Enter）；重按可重新載入，同時只保留一款播放器。首頁右上方有「效果預覽」連結。
- 預覽單款 Banner：開啟 `banners/該款資料夾/index.html`，例如 <http://127.0.0.1:4188/banners/15-cowboy-hat-tip/>；同樣需透過 HTTP 開啟，不使用 `file://`
- 嵌入 Vue 網頁：註冊 `SpineBanner` 元件後，使用首頁複製按鈕取得元件標籤
- 嵌入非 Vue 網頁：複製該款資料夾內 `embed-code.txt` 的內容，不需要 iframe
- 搬移單款：保留 `banners/該款資料夾/` 與 `banners/shared/` 的相對位置，`script src` 指向共用播放器
- 搬移全部：複製 `banners/` 即可；需要展示頁時再加上根目錄的 `index.html`
- 同一頁放多款 Banner：Vue 元件只需註冊一次；非 Vue 頁面的共用播放器 `script` 只需引入一次

本機預覽：<http://127.0.0.1:4188/>
