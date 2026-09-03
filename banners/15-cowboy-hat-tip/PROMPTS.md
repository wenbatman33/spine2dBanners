# 狂野印第安對決 · 槍口頂帽

620 × 272 橫式 Banner。必需檔案全部在本資料夾，複製整個 `15-cowboy-hat-tip` 即可移到其他網站；不依賴上層目錄、CDN 或建置工具。`index.html` 是 Banner 本體，沒有轉址。嵌入語法在 `embed-code.txt`，首頁卡片也有複製按鈕。

動作為 3.8 秒循環：持槍等待 → 微微收手 → 槍口碰到左側帽簷 → 頂起 → 短暫停留 → 放回 → 槍口離開。帽子是剛性旋轉；槍、手掌、手腕與前臂是一個固定比例的整體，只旋轉和平移，不與固定背景混合變形。袖子底部的裁切邊始終位於畫面下方。槍口沿帽簷接觸點移動；臉、身體、文字、背景固定，不換臉、不縮放人物、不開槍。播放器控制隱藏；系統設定減少動態時顯示靜止姿勢。

這是展示用 Banner，圖上的「立即挑戰」尚未連接遊戲網址。

## 素材

本次使用內建圖像生成工具，沒有另行呼叫圖片 API／CLI。

- `artwork.png`：全新的橫式西部主視覺、裸頭牛仔、金字和按鈕。
- `hat.png`：獨立牛仔帽。
- `gun-hand.png`：獨立左側持槍手臂、左輪手槍與皮袖。
- `banner-data.js`：本地 Spine 3.8 骨架、圖集和輪廓網格資料。
- `spine-player.js`：本地播放器。

生成工具輸出的帽子與手臂圖仍含棋盤格背景，所以 PNG 原圖不宣稱具有透明 alpha。播放時使用素材輪廓網格避開外部背景及槍身孔洞；PNG 本身未用程式重畫或去背。

## 生成提示要點

### 主視覺

Create a premium horizontal Western mobile-game banner, native 620:272 layout. Inspired by the supplied cowboy reference: original handsome adult cowboy, intense green eyes, dark wavy hair, fine moustache, brown leather coat with cream shearling collar and red scarf. Character on the right, bareheaded, without a gun or raised hand, leaving room for separate animated accessories. Warm orange sunset over a frontier saloon street, deep brown shadows, ornate gold frame. Large crisp dimensional metallic-gold Traditional Chinese text on the left, exactly "狂野" and "印第安對決". Red and gold button exactly "立即挑戰". Complete readable strokes, generous margins, no washed-out lettering, no cyan outlines, no watermark.

### 構圖修正

Preserve all left-side typography, the button, scenery, frame and lighting. Move the bareheaded cowboy down and reduce his size slightly so an independent wide-brim hat can fit above his head and rotate without cropping. Keep his entire face visible. No hat, gun or raised hand in this base image.

### 牛仔帽

An isolated premium painted brown leather cowboy hat matching the reference and the character lighting. Wide brim curled upward on image-left, sloping downward to image-right, tall creased crown, reddish leather band and silver buckle. Three-quarter front view. Complete silhouette with safe margins. No person, text, smoke or scenery; transparent background requested.

### 持槍手臂

An isolated adult cowboy hand holding a long-barrel dark blued-steel Western revolver vertically, muzzle pointing up and slightly toward image-right. Wood grip, realistic five-finger anatomy, brown leather sleeve and cream shearling cuff entering from the lower-left. Match the main portrait's warm sunset lighting and premium painted-game style. Keep gun, hand and sleeve connected and fully visible. No firing, muzzle flash, text or scenery; transparent background requested.

### 帽子背景後續處理

Background removal only. Preserve the exact hat, leather grain, brim shape, buckle, lighting and proportions. Remove the background and return real transparent alpha. Do not crop or redraw the hat. The returned image still contained a checkerboard, so its external area is excluded by the playback mesh instead.
