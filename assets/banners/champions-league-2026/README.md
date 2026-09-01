# Champions League 2026 Banner 系列

## 網頁入口

- `gallery/`：十一款 Banner 的統一雙欄全覽，手機自動改成單欄。
- `gift/`：第 06 款女神送禮的獨立 Spine Player。
- `player/`：第 01 款歐冠 Banner 的獨立播放器與共用 Spine Player 程式。

## 素材結構

```text
champions-league-2026/
├── gallery/       十一款全覽頁
├── gift/          女神送禮獨立頁
├── player/        基礎播放器與 vendor
├── series/        第 02～11 款 Banner
├── spine-3.8/     第 01 款 Banner
└── docs/          生成提示、播放器及後續動作需求
```

每款 `spine-3.8/runtime/` 都是遊戲或網頁真正載入的三個檔案：

- `banner.json`
- `banner.atlas`
- `banner.png`

`images/` 是建置用的分層 PNG，不是部署時必須逐張載入的檔案。
