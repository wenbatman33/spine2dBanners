# 欧冠巅峰之夜 · Spine Player 版

这是可由 Spine 3.8 Player 直接读取的 620×272 动态 Banner，不是 GIF。

## Runtime 文件

- `spine-3.8/runtime/champions-league-2026.json`
- `spine-3.8/runtime/champions-league-2026.atlas`
- `spine-3.8/runtime/champions-league-2026.png`

默认动画名称：`animation`

Spine 版本：`3.8.99`

循环长度：`0.97s`

## 本地预览

在本目录执行：

```bash
python3 -m http.server 4188 --bind 127.0.0.1
```

然后打开：

```text
http://127.0.0.1:4188/player/
```

## 动画图层

- 画面轻微推镜与位移
- 中央球员独立手臂，两次挥拳激励
- 标题区域定点蓝金爆闪
- 奖杯中心脉冲星芒
- 底部金色粒子与弧光漂浮
- 球场中心柔光呼吸

中央球员手臂、特效、镜头与光效均为独立 Spine 骨骼和 Slot；其余人物维持主视觉图层，可在 Spine 编辑器中继续拆分。
