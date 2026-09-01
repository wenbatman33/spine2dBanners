#!/usr/bin/env python3
"""Extract one registered V4 character master into Spine-ready PNG layers.

Every visible RGB pixel in the output originates from the same approved master.
The script only applies alpha masks, crops transparent bounds, and writes QA
composites. Joint masks deliberately overlap beneath armour/cuffs to keep FK
rotation seams closed.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
CHARACTER = ROOT / "assets/characters/blue_guard_hero"
SOURCE = CHARACTER / "source/rig-master.png"
OUTPUT = CHARACTER / "project/images-v4"
QA = CHARACTER / "qa"
META = CHARACTER / "source/parts-meta.json"

ALPHA_FLOOR = 16
PADDING = 24
ORIGIN_PX = (512, 1410)


# Points are image pixels on the 1024 x 1536 master. Masks overlap 10-30 px at
# joints. The overlap is hidden by armour, cuffs, scarf, tunic, and knee guards.
PARTS = {
    "leg_rear_lower": {
        "polygon": [(525, 968), (628, 956), (665, 1010), (648, 1080),
                    (684, 1160), (710, 1325), (707, 1415), (548, 1418),
                    (548, 1290), (535, 1140)],
        "pivot": (610, 1015),
    },
    "leg_rear_thigh": {
        "polygon": [(510, 800), (628, 805), (654, 920), (642, 1018),
                    (612, 1060), (548, 1050), (523, 955)],
        "pivot": (565, 825),
    },
    "leg_front_lower": {
        "polygon": [(347, 960), (471, 958), (491, 1015), (467, 1100),
                    (440, 1220), (412, 1418), (286, 1418), (307, 1320),
                    (329, 1140)],
        "pivot": (405, 1015),
    },
    "leg_front_thigh": {
        "polygon": [(382, 797), (510, 796), (505, 930), (472, 1048),
                    (414, 1060), (359, 1012), (348, 913)],
        "pivot": (450, 825),
    },
    "torso": {
        "polygon": [(391, 314), (628, 314), (668, 380), (645, 455),
                    (620, 530), (690, 805), (684, 905), (576, 875),
                    (514, 905), (430, 883), (330, 845), (381, 660),
                    (407, 545), (354, 470), (353, 385)],
        "pivot": (512, 800),
    },
    "arm_r_upper": {
        "polygon": [(342, 365), (424, 370), (432, 458), (385, 558),
                    (327, 603), (279, 565), (307, 485)],
        "pivot": (370, 435),
    },
    "arm_r_forearm": {
        "polygon": [(285, 538), (352, 572), (337, 661), (301, 713),
                    (285, 812), (238, 838), (205, 812), (229, 724),
                    (255, 651)],
        "pivot": (310, 595),
        "grip": (246, 775),
    },
    "arm_l_upper": {
        "polygon": [(606, 355), (674, 365), (700, 438), (714, 516),
                    (694, 582), (660, 612), (625, 570), (614, 501)],
        "pivot": (650, 430),
    },
    "arm_l_forearm": {
        "polygon": [(660, 545), (714, 530), (744, 626), (765, 704),
                    (795, 773), (801, 825), (762, 840), (728, 782),
                    (712, 709), (680, 644)],
        "pivot": (694, 590),
        "grip": (770, 775),
    },
    "head": {
        "polygon": [(389, 104), (632, 104), (645, 252), (604, 340),
                    (565, 380), (463, 378), (413, 335), (380, 250)],
        "pivot": (512, 350),
    },
    "sword": {
        "polygon": [(0, 405), (165, 405), (165, 1205), (0, 1205)],
        "pivot": (80, 1060),
        "grip": (80, 1060),
    },
    "shield": {
        "polygon": [(742, 875), (1024, 875), (1024, 1240), (742, 1240)],
        "pivot": (883, 1058),
        "grip": (883, 1058),
    },
}


DRAW_ORDER = [
    "leg_rear_lower", "leg_rear_thigh", "leg_front_lower",
    "leg_front_thigh", "torso", "arm_r_upper", "arm_r_forearm",
    "arm_l_upper", "arm_l_forearm", "head",
]


def cleaned_master() -> Image.Image:
    image = Image.open(SOURCE).convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a < ALPHA_FLOOR:
                pixels[x, y] = (r, g, b, 0)
    return image


def masked_part(master: Image.Image, points: list[tuple[int, int]]) -> Image.Image:
    mask = Image.new("L", master.size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    alpha = Image.new("L", master.size, 0)
    source_alpha = master.getchannel("A")
    alpha.paste(source_alpha, mask=mask)
    layer = master.copy()
    layer.putalpha(alpha)
    return layer


def crop_with_padding(layer: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = layer.getbbox()
    if bbox is None:
        raise RuntimeError("Part mask did not contain visible source pixels")
    left = max(0, bbox[0] - PADDING)
    top = max(0, bbox[1] - PADDING)
    right = min(layer.width, bbox[2] + PADDING)
    bottom = min(layer.height, bbox[3] + PADDING)
    return layer.crop((left, top, right, bottom)), (left, top, right, bottom)


def world(point: tuple[int, int]) -> tuple[int, int]:
    return point[0] - ORIGIN_PX[0], ORIGIN_PX[1] - point[1]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    master = cleaned_master()
    master.save(QA / "master-cleaned.png")

    layers: dict[str, Image.Image] = {}
    metadata = {
        "source": str(SOURCE.relative_to(ROOT)),
        "canvas": list(master.size),
        "origin_px": list(ORIGIN_PX),
        "alpha_floor": ALPHA_FLOOR,
        "padding": PADDING,
        "parts": {},
    }

    for name, spec in PARTS.items():
        layer = masked_part(master, spec["polygon"])
        cropped, bbox = crop_with_padding(layer)
        cropped.save(OUTPUT / f"{name}.png")
        layers[name] = layer

        entry = {
            "bbox": list(bbox),
            "size": list(cropped.size),
            "pivot_px": list(spec["pivot"]),
            "pivot_world": list(world(spec["pivot"])),
            "pivot_in_crop": [spec["pivot"][0] - bbox[0], spec["pivot"][1] - bbox[1]],
        }
        if "grip" in spec:
            entry["grip_px"] = list(spec["grip"])
            entry["grip_world"] = list(world(spec["grip"]))
            entry["grip_in_crop"] = [spec["grip"][0] - bbox[0], spec["grip"][1] - bbox[1]]
        metadata["parts"][name] = entry

    META.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    reconstruction = Image.new("RGBA", master.size, (0, 0, 0, 0))
    for name in DRAW_ORDER:
        reconstruction.alpha_composite(layers[name])
    reconstruction.save(QA / "body-reconstruction.png")

    cell_w, cell_h = 320, 360
    sheet = Image.new("RGBA", (cell_w * 4, cell_h * 3), (24, 26, 32, 255))
    for index, name in enumerate(PARTS):
        part = Image.open(OUTPUT / f"{name}.png").convert("RGBA")
        part.thumbnail((cell_w - 32, cell_h - 48), Image.Resampling.LANCZOS)
        x = (index % 4) * cell_w + (cell_w - part.width) // 2
        y = (index // 4) * cell_h + 16
        sheet.alpha_composite(part, (x, y))
    sheet.save(QA / "parts-contact-sheet.png")

    print(f"Wrote {len(PARTS)} registered PNG parts to {OUTPUT}")
    print(f"Metadata: {META}")
    print(f"QA: {QA / 'body-reconstruction.png'}")


if __name__ == "__main__":
    main()
