# Commercial birthday Spine reference analysis

Reference ID: `ffb9f5222ef7a3e2341fb27408d7318f`

## Reference-page taxonomy

The commercial page is not one animation template. Its eight reference banners use two production methods:

- Six largely sequence-driven banners: 1–14 animated bones, 22–77 attachment swaps, 0–4 meshes.
- Two true layered rigs: 54–56 bones, 25–38 animated bones, 4–12 meshes and only 4–14 sequence frames.
- Seven of the eight run at about 0.97 seconds. The short loop is a deliberate advertising rhythm rather than a slow cinematic drift.

## Birthday banner structure

- 620×272, Spine 3.8.99, 0.97-second loop.
- 54 total bones, 25 animated bones, 22 slots, 34 images, 14 attachment-sequence frames and 4 meshes.
- Main depth groups: base/clip, stage background, additive background word, music notes, curved stage wording, subject body, subject hand patch, finger deformation, present box, two present glows, headline sequence, additive headline, ribbon burst, sign, and five foreground audience-hand groups.
- The visual focus is produced by staggered foreground hands and title changes, not by moving the complete canvas as one image.

## Main subject and gift motion

- `singer_hand` moves horizontally from +1.6px to −16.31px, rotates about 4.64° and compresses to 90.5% width.
- The gift is parented to the hand. It grows to 118.5% width and 107.7% height around 0.533s, with −3.35° shear.
- The index fingertip rotates from +2.98° to −10.67°.
- The middle fingertip rotates from +3.63° to −6.49°.
- The ring and little fingertips receive smaller delayed rotations around 0.567s.
- Two additive light slots pulse on the gift while inheriting the hand/gift movement.
- Result: the hand reaches and subtly closes while the gift swells forward. It is not a rigid full-character wobble.

## Foreground audience motion

- Five visible hand groups use separate bones and different phases.
- Their vertical range is roughly 9–27px, with rotations roughly −10.57° to +10.04°.
- The far-right hand also scales between 91.7% and 106.7%.
- Motions repeat on half-second offsets, so the crowd never rises or falls together.
- An additive highlight on the far-right hand pulses eight times across the loop.

## Background and secondary motion

- The background is not a single moving bitmap. Separate layers include background word, two music notes, stage-word path deformation, three linked stage-word bones, ribbon burst, sign and additive accents.
- The ribbon layer remains staged, then uses a stepped off-screen-to-onscreen burst around 0.8–0.833s, including translation, 25.77° rotation change and 1.734→0.943 scale snap.
- One note performs a stepped entrance at 0.733–0.767s with about 152px horizontal and 133px vertical travel plus a 49° rotation change.
- The second note pulses continuously between 78.1% and 125.5% scale and changes opacity nine times.
- The curved stage wording deforms through four mesh/path states while its linked bones rise by about 23px.

## Headline effects

- The headline is not just one glint over one PNG.
- Fourteen full attachment frames swap every 0.0667s from 0.0667s to 0.9s.
- The full-frame sequence contains changing confetti, paint splashes, edge highlights and title lighting.
- A separate additive title layer also jitters horizontally by about 4.6px and scales 0.98→1.01.
- Supporting words, music notes and the 130% sign use their own opacity/scale timing.

## Why the first gift version failed

- Background: one flattened image with only ±3px movement, visually perceived as static.
- Subject: one rigid body; no hand, wrist or finger animation.
- Gift: independent, but its wobble was disconnected from any hand follow-through.
- Crowd: one flattened strip, so all hands moved together.
- Text: two static PNGs plus one restrained clipped glint; no full-title sequence, paint burst, shadow offset, outline pulse or supporting-word motion.
- Matte: the generated woman arrived with a baked checkerboard. Vision segmentation removed the field but left visible bright contamination around hair and jacket edges.
- The first version had 10 animated bones and 2 animated slots, far below the reference's 25 animated bones and 22-slot layer density.

## Rebuild acceptance criteria

- Replace the contaminated woman source; no white/checkerboard fringe on a dark matte at 200% inspection.
- Main subject must have actual hand follow-through. Use a clean hand/forearm patch rig or a consistent character sequence, not full-character wobble as a substitute.
- Gift motion must be driven with the hand and include forward scale, tilt and light response.
- Split foreground hands into at least four phase groups.
- Split the background into far stage, mid gift/neon shapes, confetti/ribbons and light accents with visibly different parallax.
- Use a 12–14-frame headline effect plus separate shadow/outline/glow timing.
- Keep the loop near 0.97 seconds and verify at 620×272 and mobile display sizes.
