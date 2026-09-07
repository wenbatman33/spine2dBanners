# AI 素材生成提示詞

本頁素材使用內建 GPT Image 生成工具製作；由於此介面未提供透明背景參數，角色先生成純綠分離背景，再轉成真正 RGBA PNG。

## 背景與標題

```text
Use case: ads-marketing
Asset type: premium animated game promotion banner background, final composition ratio 620:272 (very wide horizontal).
Primary request: Create an original high-end Chinese gaming banner for a fiery monkey king glory challenge. The banner will be used behind a separately animated mascot, so keep the entire right 38 percent free of any character or creature.
Scene/backdrop: cinematic red-black volcanic arena, gold sparks, layered flames, premium dark vignette, polished mobile-game advertising art.
Style/medium: premium 3D game key art, embossed metallic Chinese display typography, sharp beveled gold and crimson lettering, highly legible at small banner size.
Composition/framing: all headline, subtitle, badge and CTA confined safely inside the left 58 percent with generous 8 percent margin on every side; clean open space on the right for a mascot overlay; no important element cropped.
Lighting/mood: dramatic orange rim light, gold glow, energetic but controlled contrast.
Color palette: black, deep crimson, molten orange, polished gold.
Text (verbatim): "烈焰猴王" as the largest headline; "榮耀限定挑戰" directly below; small badge "限量登場"; CTA button "立即挑戰".
Constraints: exact Traditional Chinese text, strong thick title strokes, all text fully visible, no thin font, no character, no animal, no person, no logo, no watermark, no English text.
Avoid: flat CSS look, blurry text, illegible pseudo-Chinese, cropped letters, excessive particles over text, any creature in the right-side reserved area.
```

## 8 格角色動作

```text
Use case: stylized-concept
Asset type: production-ready 8-frame character animation sprite sheet for a Spine 2D promotional banner.
Primary request: Create one original cute golden lion king mascot performing a smooth celebratory idle motion across exactly 8 sequential animation poses.
Subject: a friendly chibi golden lion cub, large expressive eyes, round cheeks, small red-and-gold fantasy armor, crown-like flame mane, premium polished 3D mobile-game mascot.
Animation sequence: frame 1 relaxed neutral pose; frame 2 knees dip slightly and hands begin rising; frame 3 torso lifts and elbows bend; frame 4 hands rise higher; frame 5 joyful anticipation; frame 6 both fists near shoulders; frame 7 widest smile and lifted chest; frame 8 peak celebration with both fists raised. The final runtime will play frames 1→8→1 in reverse, so poses must form a smooth progression.
Composition/framing: exactly 4 columns by 2 rows, eight equal cells, one complete character centered in every cell, front three-quarter view facing slightly left, full body visible including ears, mane, hands, feet and tail; same camera, same scale, same character identity, same costume, same lighting and identical foot baseline in every cell.
Style/medium: high-end 3D-rendered mobile game mascot, crisp detailed fur, polished cinematic highlights, expressive but anatomically coherent motion.
Background: genuinely transparent background in every cell.
Constraints: no text, no labels, no numbers, no panel borders, no shadows crossing into adjacent cells, no extra characters, no missing limbs, no duplicated limbs, no changing costume, no changing camera angle, no changing body proportions, no cropped body parts, consistent silhouette and registration across all eight frames.
Avoid: storyboard captions, white background, checkerboard background, inconsistent identity, pose jumps, distorted arms or legs, blurry fur, low-resolution character.
```

## 純綠分離背景修正

```text
Use case: precise-object-edit
Asset type: 8-frame character sprite sheet for chroma key extraction.
Primary request: Change only the uniform black background to perfectly uniform chroma green RGB #00FF00.
Constraints: preserve the eight lion characters pixel-for-pixel in their exact poses, positions, scale, costume, face, tail, 4-by-2 registration and image dimensions; do not alter, redraw, move, resize or crop the characters; the green background must be completely flat and identical #00FF00 everywhere, with no gradient, texture, shadow, halo or lighting spill; clean hard separation up to the antialiased silhouette edges.
Avoid: transparency checkerboard, black remnants, green clothing, green reflections, text, labels, borders, shadows, changed anatomy.
```
