#!/usr/bin/env python3
"""Build the portable Spine 3.8 pink beauty wink advertising banner."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from ai_typography_material import material_fill

from build_treasure_chest_banner import (
    FONT_CJK,
    FONT_LATIN,
    alpha_layer,
    chroma_extract,
    cjk,
    crop_alpha,
    draw_centered,
    next_power,
    region,
    render_text_mask,
    screen_bone,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/banners/champions-league-2026/series/11-beauty-wink"
SOURCE = OUT / "source"
IMAGES = OUT / "spine-3.8/images"
RUNTIME = OUT / "spine-3.8/runtime"
QA = OUT / "qa"

WIDTH, HEIGHT = 620, 272
S = 2
DURATION = 2.8
POSE_DISPLAY_SCALE = 1.10
FONT_ANGULAR = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/c745f84f5eb15b1f594d3769dc86146fccee61ff.asset/AssetData/WeibeiSC-Bold.otf"
FONT_BRUSH = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/13b8ce423f920875b28b551f9406bf1014e0a656.asset/AssetData/Xingkai.ttc"


def crop_cover(image: Image.Image, width: int, height: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        crop_width = round(image.height * target_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    else:
        crop_height = round(image.width / target_ratio)
        top = max(0, (image.height - crop_height) // 2)
        image = image.crop((0, top, image.width, top + crop_height))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def prepare_keyposes() -> tuple[dict[str, Image.Image], dict[str, dict[str, float]]]:
    master = Image.open(SOURCE / "beauty-keyposes-green.png").convert("RGB")
    cell_width, cell_height = master.width // 3, master.height // 2
    # The runtime keeps one open-eye portrait permanently visible. Only two
    # tiny opaque eyelid patches are faded over the eyes; the face, hair and
    # body never switch texture, so there is no character flicker.
    open_cell = master.crop((0, 0, cell_width, cell_height))
    closed_cell = master.crop((cell_width * 2, 0, cell_width * 3, cell_height))
    base, base_bbox = crop_alpha(chroma_extract(open_cell), 3)
    display_width = base.width / S * POSE_DISPLAY_SCALE
    display_height = base.height / S * POSE_DISPLAY_SCALE
    scale = POSE_DISPLAY_SCALE / S
    base_registration = {
        "x": 0,
        "y": round(display_height / 2, 3),
        "width": round(display_width, 3),
        "height": round(display_height, 3),
    }

    images: dict[str, Image.Image] = {"beauty_base": base}
    registrations: dict[str, dict[str, float]] = {"beauty_base": base_registration}

    # Pose 3 was generated 33 source pixels to the left of pose 1. Sampling
    # with that registration aligns its painted closed lids to the fixed open
    # portrait. The boxes cover only the eye sockets, not the whole face.
    target_boxes = {
        "left_lid": (177, 183, 263, 226),
        "right_lid": (261, 183, 348, 226),
    }
    closed_offset_x = 33
    for name, (left, top, right, bottom) in target_boxes.items():
        patch = closed_cell.crop((left - closed_offset_x, top, right - closed_offset_x, bottom)).convert("RGBA")
        feather = Image.new("L", patch.size, 0)
        ImageDraw.Draw(feather).rounded_rectangle(
            (3, 3, patch.width - 4, patch.height - 4),
            radius=14,
            fill=255,
        )
        feather = feather.filter(ImageFilter.GaussianBlur(3.0))
        patch.putalpha(feather)
        images[name] = patch

        center_x = (left + right) / 2 - base_bbox[0]
        center_y = (top + bottom) / 2 - base_bbox[1]
        registrations[name] = {
            "x": round((center_x - base.width / 2) * scale, 3),
            "y": round((base.height - center_y) * scale, 3),
            "width": round(patch.width * scale, 3),
            "height": round(patch.height * scale, 3),
        }
    return images, registrations


def themed_text_mask(text: str, font_path: str, size: int, max_width: int, embolden: int = 0) -> Image.Image:
    scratch = Image.new("L", (520 * S, 112 * S), 0)
    font = ImageFont.truetype(font_path, size * S)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((18 * S - bbox[0], 10 * S - bbox[1]), text, font=font, fill=255)
    glyph = scratch.crop(scratch.getbbox())
    if embolden:
        glyph = glyph.filter(ImageFilter.MaxFilter(embolden * 2 + 1))
    if glyph.width > max_width * S:
        glyph = glyph.resize((max_width * S, round(glyph.height * max_width * S / glyph.width)), Image.Resampling.LANCZOS)
    return glyph


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    # Generous transparent safe area is intentional: MaxFilter outlines and
    # the positive 3D shadow must never be clipped by the texture rectangle.
    canvas = Image.new("RGBA", (380 * S, 164 * S), (0, 0, 0, 0))
    top_mask = Image.new("L", canvas.size, 0)
    bottom_mask = Image.new("L", canvas.size, 0)
    line1 = themed_text_mask("心动奖金", FONT_ANGULAR, 53, 296, embolden=1)
    line2 = themed_text_mask("眨眼挑战", FONT_BRUSH, 50, 288, embolden=2)
    # Rotate with expand=True instead of shearing a tightly cropped glyph box.
    # The former affine transform discarded the detached left stroke of “心”.
    line1 = line1.rotate(-1.2, resample=Image.Resampling.BICUBIC, expand=True)
    line2 = line2.rotate(1.6, resample=Image.Resampling.BICUBIC, expand=True)
    top_mask.paste(line1, ((canvas.width - line1.width) // 2 - 4 * S, 18 * S))
    bottom_mask.paste(line2, ((canvas.width - line2.width) // 2 + 3 * S, 86 * S))
    face = ImageChops.lighter(top_mask, bottom_mask)

    for offset in range(10, 2, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(face, (offset * S, offset * S))
        canvas.alpha_composite(alpha_layer(shifted.filter(ImageFilter.MaxFilter(5)), (35, 0, 57, 252)))

    canvas.alpha_composite(alpha_layer(top_mask.filter(ImageFilter.MaxFilter(21)), (49, 0, 65, 255)))
    canvas.alpha_composite(alpha_layer(top_mask.filter(ImageFilter.MaxFilter(13)), (242, 34, 168, 255)))
    canvas.alpha_composite(alpha_layer(top_mask.filter(ImageFilter.MaxFilter(7)), (255, 208, 92, 255)))
    canvas.alpha_composite(alpha_layer(top_mask.filter(ImageFilter.MaxFilter(3)), (255, 248, 251, 255)))
    canvas.alpha_composite(material_fill(top_mask, 3, 246))

    canvas.alpha_composite(alpha_layer(bottom_mask.filter(ImageFilter.MaxFilter(19)), (42, 0, 58, 255)))
    canvas.alpha_composite(alpha_layer(bottom_mask.filter(ImageFilter.MaxFilter(11)), (255, 198, 69, 255)))
    canvas.alpha_composite(alpha_layer(bottom_mask.filter(ImageFilter.MaxFilter(5)), (255, 53, 179, 255)))
    canvas.alpha_composite(material_fill(bottom_mask, 4, 248))
    bevel = ImageChops.subtract(face, face.transform(face.size, Image.Transform.AFFINE, (1, 0, -2 * S, 0, 1, -2 * S), resample=Image.Resampling.BILINEAR))
    canvas.alpha_composite(alpha_layer(bevel, (255, 255, 255, 135)))
    title, bbox = crop_alpha(canvas, 14 * S)
    title_face = face.crop(bbox)

    glints: list[Image.Image] = []
    for index in range(7):
        center = -30 * S + (title.width + 60 * S) * index / 6
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [(center - 9 * S, 0), (center + 2 * S, 0), (center + 46 * S, title.height), (center + 28 * S, title.height)],
            fill=155,
        )
        clipped = ImageChops.multiply(title_face, stripe.filter(ImageFilter.GaussianBlur(2 * S))).point(lambda value: round(value * 0.42))
        glint = Image.new("RGBA", title.size, (255, 255, 255, 0))
        glint.putalpha(clipped)
        glints.append(glint)
    return title, glints


def render_kicker() -> Image.Image:
    image = Image.new("RGBA", (270 * S, 36 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((14 * S, 5 * S), "PINK BONUS CHALLENGE", font=ImageFont.truetype(FONT_LATIN, 21 * S), fill=(255, 157, 230, 255), stroke_width=S, stroke_fill=(67, 0, 67, 255))
    return crop_alpha(image, 5 * S)[0]


def render_subtitle() -> Image.Image:
    image = Image.new("RGBA", (286 * S, 40 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2 * S, 2 * S, 284 * S, 38 * S), radius=18 * S, fill=(72, 4, 78, 240), outline=(255, 116, 213, 255), width=2 * S)
    draw_centered(draw, (7 * S, 2 * S, 279 * S, 38 * S), "眨眼参与 · 最高赢 8,888", cjk(18 * S), fill=(255, 247, 252, 255), stroke_width=S, stroke_fill=(72, 0, 64, 255))
    return image


def render_cta() -> Image.Image:
    image = Image.new("RGBA", (184 * S, 48 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [(13*S,2*S),(171*S,2*S),(182*S,24*S),(171*S,46*S),(13*S,46*S),(2*S,24*S)]
    draw.polygon([(x + 3 * S, y + 3 * S) for x, y in outer], fill=(48, 0, 54, 235))
    draw.polygon(outer, fill=(255, 205, 65, 255))
    draw.line(outer + [outer[0]], fill=(255, 250, 190, 255), width=2 * S)
    inner = [(18*S,7*S),(166*S,7*S),(175*S,24*S),(165*S,40*S),(18*S,40*S),(9*S,24*S)]
    draw.polygon(inner, fill=(218, 20, 143, 255))
    draw.line(inner + [inner[0]], fill=(255, 89, 202, 255), width=2 * S)
    draw.line((28*S,11*S,156*S,11*S), fill=(255, 229, 248, 255), width=2 * S)
    draw_centered(draw, (14*S,6*S,170*S,42*S), "立即挑战", cjk(24 * S), fill=(255, 250, 218, 255), stroke_width=2*S, stroke_fill=(76, 0, 54, 255))
    return image


def prepare_images() -> tuple[dict[str, Image.Image], dict[str, dict[str, float]]]:
    background = crop_cover(Image.open(SOURCE / "background-master.png").convert("RGB"), WIDTH * S, HEIGHT * S).convert("RGBA")
    poses, registrations = prepare_keyposes()
    title, glints = render_title()
    images: dict[str, Image.Image] = {
        "background": background,
        "title": title,
        "kicker": render_kicker(),
        "subtitle": render_subtitle(),
        "cta": render_cta(),
    }
    images.update(poses)
    images.update({f"title_glint_{index}": glint for index, glint in enumerate(glints)})

    flare_source = Image.open(ROOT / "assets/banners/champions-league-2026/series/06-gift-goddess/spine-3.8/images/flare.png").convert("RGBA")
    flare_source, _ = crop_alpha(flare_source, 2)
    flare_source = flare_source.resize((320 * S, 200 * S), Image.Resampling.LANCZOS)
    pink_flare = Image.new("RGBA", flare_source.size, (255, 75, 211, 0))
    pink_flare.putalpha(flare_source.getchannel("A"))
    images["pink_flare"] = pink_flare
    return images, registrations


def pack(images: dict[str, Image.Image]) -> tuple[int, int]:
    padding = 6
    placements: list[tuple[str, int, int, int, int]] = []
    free: list[tuple[int, int, int, int]] = [(padding, padding, 2048 - padding * 2, 2048 - padding * 2)]

    def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def contains(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return bx >= ax and by >= ay and bx + bw <= ax + aw and by + bh <= ay + ah

    for name, image in sorted(images.items(), key=lambda item: item[1].width * item[1].height, reverse=True):
        required_width, required_height = image.width + padding, image.height + padding
        candidates = [
            (min(width - required_width, height - required_height), max(width - required_width, height - required_height), x, y)
            for x, y, width, height in free
            if required_width <= width and required_height <= height
        ]
        if not candidates:
            raise RuntimeError(f"atlas too large while placing {name}")
        _, _, left, top = min(candidates)
        placed = (left, top, required_width, required_height)
        placements.append((name, left, top, image.width, image.height))

        split: list[tuple[int, int, int, int]] = []
        for free_left, free_top, free_width, free_height in free:
            current = (free_left, free_top, free_width, free_height)
            if not intersects(current, placed):
                split.append(current)
                continue
            placed_right = left + required_width
            placed_bottom = top + required_height
            free_right = free_left + free_width
            free_bottom = free_top + free_height
            if left > free_left:
                split.append((free_left, free_top, left - free_left, free_height))
            if placed_right < free_right:
                split.append((placed_right, free_top, free_right - placed_right, free_height))
            if top > free_top:
                split.append((free_left, free_top, free_width, top - free_top))
            if placed_bottom < free_bottom:
                split.append((free_left, placed_bottom, free_width, free_bottom - placed_bottom))
        free = [
            candidate
            for candidate in split
            if candidate[2] > 0
            and candidate[3] > 0
            and not any(candidate != other and contains(other, candidate) for other in split)
        ]

    used_width = max(left + width + padding for _, left, _, width, _ in placements)
    used_height = max(top + height + padding for _, _, top, _, height in placements)
    atlas_width, atlas_height = next_power(used_width), next_power(used_height)
    if atlas_width > 2048 or atlas_height > 2048:
        raise RuntimeError(f"atlas too large: {atlas_width}x{atlas_height}")
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for name, left, top, _, _ in placements:
        atlas.alpha_composite(images[name], (left, top))
    atlas_path = RUNTIME / "banner.png"
    atlas.save(atlas_path, optimize=True)
    pngquant = shutil.which("pngquant")
    if pngquant:
        quantized = atlas_path.with_suffix(".quant.png")
        result = subprocess.run([pngquant, "--force", "--strip", "--speed", "1", "--quality", "72-96", "--output", str(quantized), str(atlas_path)], check=False, capture_output=True)
        if result.returncode == 0 and quantized.exists():
            quantized.replace(atlas_path)
        elif quantized.exists():
            quantized.unlink()
    digest = hashlib.sha256(atlas_path.read_bytes()).hexdigest()[:12]
    lines = [f"banner.png?asset={digest}", f"size: {atlas_width},{atlas_height}", "format: RGBA8888", "filter: Linear,Linear", "repeat: none"]
    for name, left, top, width, height in placements:
        lines += [name, "  rotate: false", f"  xy: {left}, {top}", f"  size: {width}, {height}", f"  orig: {width}, {height}", "  offset: 0, 0", "  index: -1"]
    (RUNTIME / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return atlas_width, atlas_height


def build_skeleton(images: dict[str, Image.Image], registrations: dict[str, dict[str, float]]) -> dict[str, object]:
    title_width, title_height = images["title"].width / S, images["title"].height / S
    bones = [
        {"name": "root"},
        {"name": "background", "parent": "root"},
        screen_bone("pink_flare", 493, 139),
        screen_bone("beauty", 491, 272),
        screen_bone("kicker", 172, 14),
        screen_bone("title", 170, 89),
        {"name": "title_glint", "parent": "title"},
        screen_bone("subtitle", 169, 174),
        screen_bone("cta", 168, 228),
    ]
    slots = [
        {"name": "background", "bone": "background", "attachment": "background"},
        {"name": "pink_flare", "bone": "pink_flare", "attachment": "pink_flare", "blend": "additive", "color": "ffffff2c"},
        {"name": "beauty", "bone": "beauty", "attachment": "beauty_base"},
        {"name": "left_lid", "bone": "beauty", "attachment": "left_lid", "color": "ffffff00"},
        {"name": "right_lid", "bone": "beauty", "attachment": "right_lid", "color": "ffffff00"},
        {"name": "kicker", "bone": "kicker", "attachment": "kicker"},
        {"name": "title", "bone": "title", "attachment": "title"},
        {"name": "title_glint", "bone": "title_glint", "attachment": "title_glint_0", "blend": "additive", "color": "ffffff72"},
        {"name": "subtitle", "bone": "subtitle", "attachment": "subtitle"},
        {"name": "cta", "bone": "cta", "attachment": "cta"},
    ]
    attachments: dict[str, object] = {
        "background": {"background": region("background", WIDTH, HEIGHT)},
        "pink_flare": {"pink_flare": region("pink_flare", 320, 200)},
        "beauty": {
            "beauty_base": region(
                "beauty_base",
                registrations["beauty_base"]["width"],
                registrations["beauty_base"]["height"],
                registrations["beauty_base"]["x"],
                registrations["beauty_base"]["y"],
            )
        },
        "left_lid": {"left_lid": region("left_lid", **registrations["left_lid"])},
        "right_lid": {"right_lid": region("right_lid", **registrations["right_lid"])},
        "kicker": {"kicker": region("kicker", images["kicker"].width / S, images["kicker"].height / S)},
        "title": {"title": region("title", title_width, title_height)},
        "title_glint": {f"title_glint_{index}": region(f"title_glint_{index}", title_width, title_height) for index in range(7)},
        "subtitle": {"subtitle": region("subtitle", images["subtitle"].width / S, images["subtitle"].height / S)},
        "cta": {"cta": region("cta", images["cta"].width / S, images["cta"].height / S)},
    }
    blink_colors = [
        {"color": "ffffff00"},
        {"time": 0.28, "color": "ffffff00"},
        {"time": 0.36, "color": "ffffffb8"},
        {"time": 0.43, "color": "ffffffff"},
        {"time": 0.50, "color": "ffffff9c"},
        {"time": 0.58, "color": "ffffff00"},
        {"time": DURATION, "color": "ffffff00"},
    ]
    wink_colors = [
        {"time": 1.30, "color": "ffffff00"},
        {"time": 1.43, "color": "ffffffb8"},
        {"time": 1.55, "color": "ffffffff"},
        {"time": 2.08, "color": "ffffffff"},
        {"time": 2.20, "color": "ffffff90"},
        {"time": 2.34, "color": "ffffff00"},
        {"time": DURATION, "color": "ffffff00"},
    ]
    animation = {
        "slots": {
            "left_lid": {"color": blink_colors[:-1] + wink_colors},
            "right_lid": {"color": blink_colors},
            "title_glint": {"attachment": [{"time": round(0.72 + index * 0.10, 3), "name": f"title_glint_{index}"} for index in range(7)]},
            "pink_flare": {
                "color": [
                    {"color": "ffffff2c"},
                    {"time": 1.28, "color": "ffffff2c"},
                    {"time": 1.52, "color": "ffffff86"},
                    {"time": 2.14, "color": "ffffff64"},
                    {"time": 2.44, "color": "ffffff2c"},
                    {"time": DURATION, "color": "ffffff2c"},
                ]
            },
        },
        "bones": {
            "beauty": {
                "translate": [{}, {"time": 1.40, "x": -1.0, "y": 0.6}, {"time": 2.14, "x": -1.0, "y": 0.6}, {"time": 2.44}, {"time": DURATION}],
                "rotate": [{}, {"time": 1.40, "angle": -0.65}, {"time": 2.14, "angle": -0.65}, {"time": 2.44}, {"time": DURATION}],
            },
            "pink_flare": {
                "scale": [{"x": 0.68, "y": 0.68}, {"time": 1.52, "x": 1.06, "y": 1.06}, {"time": 2.18, "x": 0.86, "y": 0.86}, {"time": DURATION, "x": 0.68, "y": 0.68}],
                "rotate": [{}, {"time": DURATION, "angle": 28}],
            },
            "title": {"translate": [{}, {"time": 0.72, "x": 1.5}, {"time": 1.04}, {"time": DURATION}]},
            "cta": {"scale": [{}, {"time": 1.40, "x": 1.06, "y": 1.06}, {"time": 1.64}, {"time": 2.12, "x": 1.035, "y": 1.035}, {"time": 2.34}, {"time": DURATION}]},
        },
    }
    return {
        "skeleton": {"hash": "codex-beauty-wink-v1", "spine": "3.8.99", "x": -310, "y": -136, "width": WIDTH, "height": HEIGHT, "images": "./images/"},
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {"animation": animation},
    }


def static_preview(images: dict[str, Image.Image], registrations: dict[str, dict[str, float]]) -> None:
    preview = images["background"].copy()

    def paste_center(name: str, x: float, y: float) -> None:
        layer = images[name]
        preview.alpha_composite(layer, (round(x * S - layer.width / 2), round(y * S - layer.height / 2)))

    flare = images["pink_flare"].copy()
    flare.putalpha(flare.getchannel("A").point(lambda value: round(value * 0.46)))
    preview.alpha_composite(flare, (round(493 * S - flare.width / 2), round(139 * S - flare.height / 2)))
    registration = registrations["beauty_base"]
    pose = images["beauty_base"].resize((round(registration["width"] * S), round(registration["height"] * S)), Image.Resampling.LANCZOS)
    center_x = 491 * S
    center_y = round((272 - registration["y"]) * S)
    preview.alpha_composite(pose, (round(center_x - pose.width / 2), round(center_y - pose.height / 2)))
    paste_center("kicker", 172, 14)
    paste_center("title", 170, 86)
    paste_center("subtitle", 169, 174)
    paste_center("cta", 168, 228)
    QA.mkdir(parents=True, exist_ok=True)
    preview.save(QA / "beauty-wink-static.png", optimize=True)

def main() -> None:
    for directory in (IMAGES, RUNTIME, QA):
        directory.mkdir(parents=True, exist_ok=True)
    images, registrations = prepare_images()
    for pattern in ("beauty_expr_*.png", "beauty_[0-9].png"):
        for stale in IMAGES.glob(pattern):
            stale.unlink()
    (QA / "beauty-wink-poses.png").unlink(missing_ok=True)
    for name, image in images.items():
        image.save(IMAGES / f"{name}.png", optimize=True)
    atlas_width, atlas_height = pack(images)
    skeleton = build_skeleton(images, registrations)
    (RUNTIME / "banner.json").write_text(json.dumps(skeleton, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    static_preview(images, registrations)
    report = {
        "atlas": f"{atlas_width}x{atlas_height}",
        "atlas_bytes": (RUNTIME / "banner.png").stat().st_size,
        "duration": DURATION,
        "character_base_textures": 1,
        "eyelid_patches": 2,
        "blink": True,
        "wink": True,
        "identity_locked": True,
        "character_scale_animation": False,
        "full_character_texture_switching": False,
        "mesh_eye_deformation": False,
        "portable": True,
    }
    (QA / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 11 · 心动奖金眨眼挑战\n\n单一固定人物底图加两片小型闭眼眼皮贴图：双眼自然眨眼与单眼媚眼；没有人物贴图切换、眼球 Mesh 变形或整体缩放。\n\n完整可搬移 HTML 位于项目根目录 `banners/11-beauty-wink/`。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
