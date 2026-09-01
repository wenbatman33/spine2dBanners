# 球员手臂拆分生成记录

生成模式：ImageGen 内建编辑模式。

## 无手臂底图

```text
Use case: precise-object-edit
Asset type: clean plate for a 620x272 Spine 2D animated football banner
Primary request: remove only the central foreground player's raised clenched fist and the entire bent forearm. Reconstruct the hidden background and the natural edge of his white jersey/shoulder.
Constraints: preserve all three faces and identities, trophy, every Chinese text glyph, CTA, colors, lighting, positions, and all other pixels as faithfully as possible.
```

## 独立手臂

```text
Use case: background-extraction
Asset type: independent transparent character limb sprite for Spine 2D
Primary request: extract and recreate only the central foreground player's complete raised clenched fist and bent arm, including the hand, forearm, elbow, white jersey sleeve, and shoulder connection. Match skin tone, anatomy, jersey fabric, trim, lighting, proportions, perspective, and sharpness.
Constraints: only one arm sprite; no head, face, trophy, text, logo, duplicate fingers, extra limbs, or watermark.
```

> 审查结果：此生成手臂因比例、肩膀接点和透视不一致而被否决，未进入最终 Atlas。原始文件改名为 `source-character/rejected-generated-arm-source.png` 留作问题记录。

## 最终采用方式

最终 `images/arm.png` 直接取自 `champions-league-2026-keyart-master.png` 中原球员的拳头、前臂与袖口像素，并以手工遮罩拆分。没有重新生成手掌、手指、皮肤或球衣，因此能保持与主图一致的身份、比例、光线和透视。
