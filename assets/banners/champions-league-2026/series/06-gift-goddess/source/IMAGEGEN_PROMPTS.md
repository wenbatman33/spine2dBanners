# 06 Gift Goddess — ImageGen prompt set

Mode: built-in ImageGen.

## Background

Premium textless birthday-gift campaign background for a 620×272 Spine banner. Deep black and midnight-purple party stage, cyan/electric-blue neon panels, subtle magenta accents, floating confetti and soft bokeh. Keep the left 48% dark and clean for large Chinese copy, reserve center-right for a woman cutout, and keep a dark bottom crowd zone. Background only; no people, body parts, readable text, logos, watermark, chromatic fringe, green screen, or giant central flare.

## Woman

Glamorous adult East Asian woman, clearly age 25–32, in a metallic blue-violet jacket and dark top, smiling and presenting an empty gift-sized space. Both arms extend naturally; both hands coherently support and frame an empty square area in front of her chest. Complete waist-up silhouette with both elbows, wrists and hands visible, accurate anatomy, cyan rim light and magenta accents, no gift, text, logo, watermark, duplicated limbs or detached parts.

## Gift

One independent premium square birthday gift box in three-quarter view, deep cobalt-blue box with glossy cyan ribbon and an oversized elegant bow. Match cyan/magenta campaign lighting. Genuine transparent alpha; exactly one closed box and one bow; no people, hands, text, logo, watermark, distant glow haze, or malformed geometry.

## Foreground crowd

Transparent horizontal strip of six to eight excited adult audience hands and partial forearms reaching upward from the bottom edge. Include one glow stick and one unprinted light sign at far left. Dark silhouettes with controlled cyan/magenta rim lighting, coherent anatomy, no faces, text, logos, gift boxes, detached hands, malformed fingers, or full-screen noise.

The generated woman arrived with a baked checkerboard, so the runtime source uses Apple Vision person segmentation plus connected-background removal and RGB edge decontamination before atlas packing.

## V2 reference-informed rebuild

### Eight-frame character sequence

One precisely registered 4×2 sprite sheet of the same adult East Asian woman in a metallic blue-violet jacket, performing a human gift-offering loop: gift close to chest, wrists lift, arms extend, gift reaches forward, tilt left, return center, tilt right, return to frame one. Fixed camera, scale, baseline, head and torso; only forearms, wrists, fingers and gift move. Uniform pure green background, black grid separators, no text or logos.

### Far stage

Edit the original neon stage by removing every gift box, bow, ribbon, confetti piece and floating object, then reconstruct the hidden floor and panels. Preserve the wide dark-left copy area and cyan-magenta stage perspective.

### Midground gift cluster

Transparent cluster of three cobalt gift boxes with cyan ribbons, violet rim lighting and curling ribbon loops, composed on one baseline for placement behind the presenter.

### Confetti overlay

Sparse transparent cyan, magenta, pink and white party confetti with three curling streamers, strong empty gaps and no full-screen glow or noise.
