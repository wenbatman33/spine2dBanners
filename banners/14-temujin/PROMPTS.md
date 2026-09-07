# 鐵木真 · 橫式遊戲 Banner

620 × 272。由根目錄展示頁預覽，或複製 `embed-code.txt` 嵌入其他網頁；搬移時保留本資料夾與 `banners/shared`，不依賴 CDN 或建置工具。

```html
<div data-spine="14-temujin"></div>
<script src="./banners/shared/common-spine-player.js"></script>
```

動態：標題固定；大型武將上胸呼吸、頭部微動和抬臂；Q 版角色上身呼吸、點頭和持刀手臂擺動，脚底固定，沒有整體忽大忽小。15 格火焰序列分為三個區域向右上飄移，雙層暖色煙霧緩慢流動，32 顆火星隨風上飄。循環 4.2 秒，金字及刀刃另有閃光，播放器控制隱藏。系統啟用減少動態效果時，顯示靜止構圖。這是視覺展示，尚未指定「立即出征」的遊戲連結。

## 素材與生成方式

使用內建圖像生成工具，未使用額外 API／CLI。參考使用者提供的直式 `鐵木真_500kb.webp` 的雙角色、火光和金字呈現方式，重新安排橫式構圖。

- `artwork.png`：火焰場景、大型武將、金字及按鈕。
- `character.png`：前景 Q 版角色。
- `light.png`：沿用現有足球 Banner 的金色光效貼圖。
- `fire.png`：沿用既有 Banner 的 15 格火焰圖集。
- `smoke.png`：沿用現有煙霧貼圖，以播放時的色彩和透明度調整成暖色戰場煙霧。
- `banner.json`：Spine 3.8 動畫與輪廓網格。
- `banner.atlas`：圖集資訊。
- `../shared/`：全站共用播放器與生命週期管理器。
- `embed-code.txt`：直接嵌入其他網頁的語法。

生成工具的透明背景請求輸出仍含棋盤格，因此以 Spine 輪廓網格僅顯示素材本體；原始 PNG 不宣稱具備透明 alpha。播放器畫布外部透明，嵌入網頁可自行設定容器底色。

## Prompt set

### 1. 橫式主視覺

Create a new premium horizontal game promotional banner inspired by the reference vertical Mongol khan banner. Redesign natively for 620:272, do not stretch. Left half: large dimensional metallic-gold Chinese brush calligraphy exactly "鐵木真", readable complete strokes and generous margins, dark burgundy shadow. Subtitle exactly "一代天驕　征戰天下". Compact red-and-gold button "立即出征". Right half: original fierce realistic adult Mongol warrior in an ivory fur hat with gold medallion, blue lamellar armor and fur collar, shouting, clenched fist raised above a rounded red-orange fire backplate. Leave lower-right foreground for a separate chibi character; do not draw the chibi here. Rich painted mobile-game advertising quality; no overexposed letters, cyan outline, watermark, or cropped fist. Transparent exterior requested.

### 2. 前景 Q 版角色

Create an isolated full-body original chibi adult Mongol khan with a huge cheerful laughing face, small black moustache, rosy cheeks, ivory fur hat with circular gold medallion, red sleeves, ornate gold lamellar armor and dark boots. Right hand at image-left holds a large raised curved golden saber; left hand rests on hip. Three-quarter view slightly facing viewer-left, warm fire rim lighting matching the main artwork, premium polished 3D mobile-game mascot. Complete silhouette and safe margins around saber, hat, hands and boots. No scenery, lettering, frame, or particles. Transparent background requested.

### 3. 背景處理的後續請求

Background removal only. Preserve the exact banner/character, typography, proportions and positions. Remove the gray-and-white checkerboard outside the subject and replace with real transparent alpha. Do not redraw or crop; preserve fur and blade edges.

實際交付保留第 3 步輸出，使用輪廓網格排除其外部棋盤背景。
