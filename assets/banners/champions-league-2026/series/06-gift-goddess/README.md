# 06 女神生日限定

這裡只保留目前正式版本，不再並存 V1、V2、V3、V4 資料夾。

```text
06-gift-goddess/
├── source/        正式原始 PNG；raw/ 保留綠幕原圖
├── spine-3.8/
│   ├── images/    2× 分層貼圖
│   └── runtime/   Player／遊戲引擎直接載入
├── qa/            最終構圖、去背與建置報告
└── analysis/      商業參考 Banner 的結構分析
```

## 動畫規格

- 單張完整人物 Mesh，肩膀與手臂沒有拼接附件。
- 81 個 Mesh 頂點中只變形手掌附近 16 點，頭與軀幹不變形。
- 禮物獨立跟隨手掌，前景觀眾分成三組錯相位。
- 8 段斜向文字反光，0.97 秒循環。
- Runtime 約 1.7 MB，貼圖為 2× 清晰度。

重新建置：

```bash
python3 tools/build_gift_goddess_banner.py
```

