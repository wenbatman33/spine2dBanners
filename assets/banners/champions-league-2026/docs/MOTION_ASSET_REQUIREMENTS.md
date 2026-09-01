# 自然人物动作所需素材

当前 Banner 是已经合成文字、背景与球员的单张平面图。若要制作符合人体结构、没有拼贴接缝的 Spine 动作，需要以下其中一种素材方案。

## 推荐：连续动作序列帧

- 每款 12～16 张 PNG，尺寸统一为 620×272。
- 镜头、人物身份、脸部、球衣、比例、脚点与背景必须保持一致。
- 可用动作：自然呼吸、点头、视线转移、肩膀带动转身、进球后的后仰与回正。
- 禁止动作：头部脱离颈部、脸部或头部缩放、肢体拉长、关节反折、手指增减、人物之间互相穿透。
- Spine 以 attachment 序列播放这些帧，不再切割头部。

### 可用于图生视频／动作生成工具的提示词

> Preserve the exact football players, facial identity, uniforms, body proportions, camera, typography, stadium background and banner composition. Add only subtle anatomically correct human motion: natural breathing, a small head turn driven from the neck and shoulders, realistic weight shift, and a gentle return to the original pose. No floating head, no disconnected neck, no body stretching, no extra limbs or fingers, no morphing faces, no camera-angle change, no text changes. Seamless short loop, 12 to 16 clean frames, 620x272 composition.

## 备选：真正分层角色素材

每位球员至少需要：

- 无人物的干净背景 PNG。
- 完整头颈 PNG，不可只切脸。
- 胸腔与骨盆分层 PNG。
- 左右上臂、前臂与手掌 PNG，关节处保留足够重叠。
- 正确的颈部、肩膀、手肘和骨盆旋转支点。

取得上述素材前，当前版本只保留完整人物原图与场景／文字特效，不再使用头部切片动画。
