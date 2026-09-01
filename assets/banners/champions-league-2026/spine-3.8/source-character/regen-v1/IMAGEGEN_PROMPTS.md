# 01 Layered Regeneration — ImageGen Prompt Set

Mode: built-in ImageGen.

## Rejected central player v1

Using the supplied football banner as visual reference, create one isolated central foreground male football player for the same premium 2026/27 European championship advertisement. Preserve the reference's dramatic white-and-gold kit, athletic proportions, open-mouth victory shout, and raised clenched fist. Show one anatomically complete continuous figure from the full head through neck, both shoulders, torso, both arms and waist; no cropped joints, duplicate limbs, missing hands, collage seams, text, logo, watermark, or other people. Photorealistic commercial sports key art, crisp blue-and-gold stadium rim light. Neutral removable background with strong silhouette separation.

Rejected because the source retained over-sharpened etched skin and a baked checkerboard background.

## Accepted central player v2

Generate a new clean source photograph for only the central foreground football player in this banner. Premium live-action sports advertising photography, natural human skin pores and facial detail, realistic plain woven white football jersey with restrained gold/navy trim, normal fabric folds, physically correct anatomy and hands. One athletic adult male player celebrating with mouth open and one fist raised beside the chest. Show the entire continuous figure from the complete top of the hair through neck, both shoulders, both full arms and hands, torso, waist and a small portion of the shorts. Keep generous empty margin around every body edge. Camera and lighting should match the supplied blue stadium banner, but do not copy the artificial etched/micro-engraved texture from the reference. Absolutely no embossed skin, no illustration, no painterly filter, no over-sharpened AI texture, no duplicate fingers, no extra limbs, no cropped joints, no text, logos, watermark, trophy, or other people. Background must be a single perfectly flat evenly lit chroma green color #00ff21 with no gradient, shadow, vignette, halo, or green reflection. One raster PNG.

## Accepted clean background plate

Remove all three football players and the trophy from the supplied banner while preserving the complete stadium, star-shaped blue light architecture, pitch, sparks, Simplified Chinese headline, date line, and red call-to-action button exactly in their original locations. Reconstruct the covered stadium areas naturally with matching perspective and lighting. Do not add new people, trophies, text, logos, watermarks, or foreground objects. Keep the same wide composition and premium commercial sports-advertising finish.

## Accepted text-free advertising plate

Create a text-free clean background plate from this exact wide European football stadium advertising banner. Remove every Chinese character, number, date line, subtitle, red call-to-action button, gold underline, and all typography shadows or remnants from the entire image. Preserve the same blue night stadium, star-shaped luminous roof structure, football pitch, audience, blue and gold sparks, camera perspective, lighting, and wide aspect ratio. Reconstruct all areas behind the removed typography seamlessly with matching stadium detail. Do not add people, players, trophies, balls, logos, watermarks, signs, buttons, text-like marks, or readable symbols. Keep premium photorealistic commercial sports-advertising quality. Output one raster PNG at the same composition.

## Accepted rear-left player

Create one isolated tall blond male football striker for a premium European football championship banner. Anatomically complete continuous figure from full head and tied-back hair through neck, shoulders, torso, both complete arms and upper legs. Natural alert match stance, light-blue short-sleeve kit, realistic hands and fingers, correct human proportions, photorealistic commercial sports key art, cool stadium rim light. No cropped joints, extra limbs, missing hands, text, logo, watermark, trophy, or other people. Even vivid chroma-key green background (#00ff21), no green reflection on the subject.

## Accepted rear-right player

Create one isolated young male football winger for a premium European football championship banner. Anatomically complete continuous figure from full head and hair through neck, shoulders, torso, both complete arms and upper legs. Natural attentive match stance looking to the side, dark-blue and red striped short-sleeve kit, realistic hands and fingers, correct human proportions, photorealistic commercial sports key art, cool stadium rim light. No cropped joints, extra limbs, missing hands, text, logo, watermark, trophy, or other people. Even vivid chroma-key green background (#00ff21), no green reflection on the subject.

## Accepted trophy

Create one isolated premium European football championship trophy asset matching the polished silver cup shown in the reference banner. Full trophy visible from both handles to the base, centered, front three-quarter view, photorealistic commercial sports advertising quality, crisp metal reflections with cool blue rim light and a subtle warm gold accent, correct symmetrical trophy anatomy, no people, no hands, no text, no logo, no watermark. Place it against an evenly lit vivid chroma-key green background (#00ff21) with strong clean silhouette separation and no green reflections on the trophy. Output a single raster PNG.

## Rejected candidates

The first two central-player candidates were rejected because their displayed checkerboard backgrounds were baked into RGB pixels instead of real alpha. The accepted central layer uses macOS Vision person segmentation; the two rear players use Vision alpha masks plus green-spill cleanup.
