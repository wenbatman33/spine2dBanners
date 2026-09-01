# Spine 2D 素材專案

最上層就是可直接使用的成品；开发来源放在后面，不影响抽取使用。

```text
spine2dAssets/
├── index.html       八款 Banner 实际展示页（不是转址）
├── banners/         每款都可整包复制的独立静态 HTML
├── vendor/          总览页共用的 Spine Player
├── assets/          可編輯來源
├── deliverables/    可直接交付的壓縮包
├── tools/           重新建置素材的腳本
└── README.md        本導覽
```

## 最常使用的入口

- Banner 八款全覽：`index.html`
- 单款 Banner：复制 `banners/对应名称/` 整个资料夹，其中 `index.html` 可直接播放
- 勇者 Spine 4.3 專案：`assets/characters/blue_guard_hero/project/blue-guard-hero.spine`
- 勇者遊戲引擎輸出：`assets/characters/blue_guard_hero/runtime/`
- 最終交付 ZIP：`deliverables/`

本機伺服器運行在專案根目錄時：

- <http://127.0.0.1:4188/>
- <http://127.0.0.1:4188/banners/08-forward-dribble/>

## 目前正式版本

| 素材 | 正式版本 | 位置 |
| --- | --- | --- |
| 八款廣告 Banner | Spine 3.8.99 | `banners/` |
| 女神送禮 Banner | 單一連續人物 Mesh、2× 貼圖 | `series/06-gift-goddess/` |
| 藍衣盾劍勇者 | Spine 4.3 V4 | `assets/characters/blue_guard_hero/` |
| 盾劍動作模板 | Essential v1 | `assets/animation_templates/` |

舊版 V1～V3、過期交付包與測試截圖已移到 macOS 垃圾桶的
`spine2dAssets-cleanup-20260831`，需要時仍可復原。
