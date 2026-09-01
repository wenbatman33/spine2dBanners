# 09 · 開箱暴擊

Spine 3.8.99 開寶箱廣告 Banner，畫布為 620×272，循環長度 2.4 秒。

## 動畫節奏

- 0.00–0.30 秒：閉箱蓄力與重量下壓。
- 0.30–0.56 秒：四個一致造型的關鍵姿勢快速開蓋。
- 0.52–1.84 秒：金幣展示、雙層加色光暈、標題高光與 CTA 脈衝。
- 1.84–2.14 秒：關箱回彈。
- 2.14–2.40 秒：短暫停頓後無縫循環。

## 可直接部署的檔案

- `spine-3.8/runtime/banner.json`
- `spine-3.8/runtime/banner.atlas`
- `spine-3.8/runtime/banner.png`

六段独立开箱姿势共用同一箱底锚点，以短交叉过渡连续开盖；最高箱盖保留安全边界，不再切顶。

完整可搬移 HTML 在專案根目錄的 `banners/09-treasure-chest/`。

## 來源與建置

- `source/chest-keyposes-master.png`：原始四姿勢生成稿。
- `source/chest-keyposes-green.png`：保留深色木紋的去背中間稿。
- `source/background-master.png`：無文字寶庫背景。
- `tools/build_treasure_chest_banner.py`：PNG 分層、Spine JSON、atlas 與 QA 圖建置器。
