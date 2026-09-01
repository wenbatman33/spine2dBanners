# Blue Guard Hero — 遊戲常用動作清單

角色規格：左手持盾、右手持劍、三分之二側面朝畫面右方。所有動作必須沿用 `reference/blue-guard-hero-master-v1.png` 的臉型、比例、裝備、色彩與握持方式。

## 第一階段：可玩 MVP

| ID | 動作 | 建議長度 | 循環 | 必要事件 |
| --- | --- | ---: | :---: | --- |
| `idle_relaxed` | 一般待機、呼吸與輕微重心變化 | 2.4 秒 | 是 | — |
| `idle_combat` | 盾牌向前、劍保持警戒 | 1.8 秒 | 是 | — |
| `walk_forward` | 持盾前進 | 0.9 秒 | 是 | `foot_l`, `foot_r` |
| `run_forward` | 壓低重心奔跑，盾與劍穩定 | 0.65 秒 | 是 | `foot_l`, `foot_r` |
| `jump_start` | 屈膝起跳 | 0.22 秒 | 否 | `takeoff` |
| `jump_loop` | 空中姿勢 | 0.45 秒 | 是 | — |
| `fall_loop` | 下墜姿勢 | 0.45 秒 | 是 | — |
| `land` | 落地吸震後回到警戒 | 0.28 秒 | 否 | `land` |
| `attack_slash_1` | 右手劍由右上向左下斬 | 0.62 秒 | 否 | `attack_start`, `hit`, `attack_end` |
| `attack_slash_2` | 反方向回斬，可接第一擊 | 0.58 秒 | 否 | `attack_start`, `hit`, `attack_end` |
| `attack_thrust` | 盾牌掩護下向前突刺 | 0.55 秒 | 否 | `attack_start`, `hit`, `attack_end` |
| `guard_loop` | 左盾正面防禦 | 0.8 秒 | 是 | `guard_on` |
| `block_hit` | 盾牌受擊、身體吸收衝擊 | 0.32 秒 | 否 | `block`, `camera_shake` |
| `hurt_front` | 正面受傷後恢復站立 | 0.48 秒 | 否 | `hurt` |
| `death_back` | 向後倒地並停留 | 1.25 秒 | 否 | `weapon_drop`, `dead` |

## 第二階段：完整戰鬥

| ID | 動作 | 用途 |
| --- | --- | --- |
| `draw_weapon` | 拔劍進入戰鬥 |
| `sheathe_weapon` | 收劍回到一般待機 |
| `attack_overhead` | 高傷害蓄力下劈 |
| `attack_uppercut` | 由下往上的挑斬 |
| `attack_charge` | 蓄力循環，可控制時間 |
| `attack_charge_release` | 蓄力後重斬 |
| `combo_finisher` | 三連擊終結技 |
| `shield_bash` | 盾擊、造成硬直 |
| `parry` | 短時間精準格擋 |
| `guard_break` | 防禦被破壞 |
| `dodge_back` | 向後閃避 |
| `dodge_roll` | 前滾或側滾 |
| `knockback` | 被重擊向後滑退 |
| `knockdown` | 被擊倒在地 |
| `get_up` | 起身回到警戒 |
| `stun_loop` | 暈眩循環 |

## 第三階段：探索與互動

| ID | 動作 | 用途 |
| --- | --- | --- |
| `pickup_item` | 彎腰拾取物品 |
| `use_item` | 使用藥水或道具 |
| `open_chest` | 開啟寶箱 |
| `push_object` | 推動場景物件 |
| `climb_loop` | 攀爬梯子或繩索 |
| `talk_gesture` | 對話手勢 |
| `victory` | 戰鬥勝利姿勢 |
| `level_up` | 升級演出 |
| `sleep_loop` | 休息或睡眠 |

## 動畫品質規則

- 角色的左手永遠控制盾牌，右手永遠控制劍。
- 臉型、頭身比例、衣服長度、盾牌尺寸與劍長不可在動作之間漂移。
- 腳掌接觸地面時必須鎖定，禁止腳滑。
- 攻擊必須包含預備、出力、命中、跟隨與收招，不可只有手臂旋轉。
- 劍、盾、圍巾、腰布需有不同幅度的延遲與慣性。
- 循環動畫的第一幀與最後一幀必須在姿勢、速度與曲線切線上連續。
- 所有攻擊以事件標記輸出命中時間，不把傷害判定硬寫在動畫影格中。

