# Blue Guard Hero — Spine 4.3

這個資料夾只保留已通過結構重建的 V4。舊 V1～V3 已移到垃圾桶。

```text
blue_guard_hero/
├── project/
│   ├── blue-guard-hero.spine   Spine Editor 專案
│   ├── source.json             可重建的骨架來源
│   └── images-v4/              專案使用的透明 PNG 分件
├── runtime/
│   ├── json/                   推薦的跨引擎 JSON 輸出
│   └── binary/                 Spine 4.3 鎖版 Binary 輸出
├── source/                     角色母圖、分件母圖與定位資料
├── qa/                         最終重組與 Runtime 回讀證據
└── docs/                       動作清單與後續素材需求
```

## 目前動畫

- `idle_combat`：1.6 秒循環
- `walk_forward`：1.0 秒循環，含 `foot_r`、`foot_l` 事件

遊戲引擎優先使用 `runtime/json/` 內的 JSON、Atlas、PNG。需要 Spine
Editor 編輯時，開啟 `project/blue-guard-hero.spine`，不要把
`project/images-v4/` 分開移動。

重新生成分件與骨架來源：

```bash
python3 tools/extract_blue_guard_hero_parts.py
python3 tools/build_blue_guard_hero.py
```

