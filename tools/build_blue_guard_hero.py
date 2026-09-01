#!/usr/bin/env python3
"""Build the anatomically registered V4 Spine JSON source.

This rig is authored against the V4 neutral master instead of retargeting an
unrelated skeleton. Attachment transforms are calculated from the extraction
metadata so every body piece reconstructs at its original master coordinates.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "assets/characters/blue_guard_hero"
META_PATH = HERO / "source/parts-meta.json"
OUTPUT = HERO / "project/source.json"

ORIGIN = (512.0, 1410.0)


def world(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] - ORIGIN[0], ORIGIN[1] - point[1]


def vec(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    aw, bw = world(a), world(b)
    return bw[0] - aw[0], bw[1] - aw[1]


def angle(vector: tuple[float, float]) -> float:
    return math.degrees(math.atan2(vector[1], vector[0]))


def length(vector: tuple[float, float]) -> float:
    return math.hypot(*vector)


def normalize(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def local_point(point_world: tuple[float, float], origin_world: tuple[float, float], rotation: float) -> tuple[float, float]:
    dx = point_world[0] - origin_world[0]
    dy = point_world[1] - origin_world[1]
    radians = math.radians(rotation)
    cosine, sine = math.cos(radians), math.sin(radians)
    return dx * cosine + dy * sine, -dx * sine + dy * cosine


JOINTS = {
    "pelvis": (512, 800),
    "neck": (512, 350),
    "arm_r_shoulder": (370, 435),
    "arm_r_elbow": (310, 595),
    "arm_r_grip": (246, 775),
    "arm_l_shoulder": (650, 430),
    "arm_l_elbow": (694, 590),
    "arm_l_grip": (770, 775),
    "leg_front_hip": (450, 825),
    "leg_front_knee": (405, 1015),
    "leg_front_ankle": (350, 1280),
    "leg_rear_hip": (565, 825),
    "leg_rear_knee": (610, 1015),
    "leg_rear_ankle": (650, 1280),
}


def rotate_frames(values: list[tuple[float, float]]) -> list[dict]:
    return [{"time": time, "value": value} for time, value in values]


def translate_frames(values: list[tuple[float, float, float]]) -> list[dict]:
    return [{"time": time, "x": x, "y": y} for time, x, y in values]


def make_animations() -> dict:
    # Values are small offsets from setup. The loops prioritize connected joints,
    # readable weight shift, and stable equipment over exaggerated motion.
    idle_times = [0.0, 0.8, 1.6]
    idle = {
        "bones": {
            "pelvis": {"translate": translate_frames([(0, 0, 0), (0.8, 1.5, -4), (1.6, 0, 0)])},
            "torso": {"rotate": rotate_frames(list(zip(idle_times, [-0.4, 1.0, -0.4])))},
            "head": {"rotate": rotate_frames(list(zip(idle_times, [0.3, -0.7, 0.3])))},
            "arm_r_upper": {"rotate": rotate_frames(list(zip(idle_times, [-1.0, 0.8, -1.0])))},
            "arm_r_forearm": {"rotate": rotate_frames(list(zip(idle_times, [0.7, -0.5, 0.7])))},
            "sword": {"rotate": rotate_frames(list(zip(idle_times, [0.3, -0.3, 0.3])))},
            "arm_l_upper": {"rotate": rotate_frames(list(zip(idle_times, [0.5, -0.6, 0.5])))},
            "arm_l_forearm": {"rotate": rotate_frames(list(zip(idle_times, [-0.4, 0.5, -0.4])))},
            "shield": {"rotate": rotate_frames(list(zip(idle_times, [-0.1, 0.2, -0.1])))},
        }
    }

    times = [0.0, 0.25, 0.5, 0.75, 1.0]
    walk = {
        "bones": {
            "pelvis": {"translate": translate_frames([
                (0, -4, 0), (0.25, 0, -8), (0.5, 4, 0),
                (0.75, 0, -8), (1.0, -4, 0),
            ])},
            "torso": {"rotate": rotate_frames(list(zip(times, [1.2, 0, -1.2, 0, 1.2])))},
            "head": {"rotate": rotate_frames(list(zip(times, [-1.0, 0, 1.0, 0, -1.0])))},
            "leg_front_thigh": {"rotate": rotate_frames(list(zip(times, [-10, 0, 10, 0, -10])))},
            "leg_front_lower": {"rotate": rotate_frames(list(zip(times, [5, 15, 1, 9, 5])))},
            "leg_rear_thigh": {"rotate": rotate_frames(list(zip(times, [10, 0, -10, 0, 10])))},
            "leg_rear_lower": {"rotate": rotate_frames(list(zip(times, [1, 9, 5, 15, 1])))},
            "arm_r_upper": {"rotate": rotate_frames(list(zip(times, [4, 1, -4, -1, 4])))},
            "arm_r_forearm": {"rotate": rotate_frames(list(zip(times, [-2, -1, 2, 1, -2])))},
            "sword": {"rotate": rotate_frames(list(zip(times, [-2, 0, 2, 0, -2])))},
            "arm_l_upper": {"rotate": rotate_frames(list(zip(times, [-3, -1, 3, 1, -3])))},
            "arm_l_forearm": {"rotate": rotate_frames(list(zip(times, [1.5, 0.5, -1.5, -0.5, 1.5])))},
            "shield": {"rotate": rotate_frames(list(zip(times, [1.5, 0.5, -1.5, -0.5, 1.5])))},
        },
        "events": [
            {"time": 0.25, "name": "foot_r", "string": "right"},
            {"time": 0.75, "name": "foot_l", "string": "left"},
        ],
    }
    return {"idle_combat": idle, "walk_forward": walk}


def main() -> None:
    meta = json.loads(META_PATH.read_text())

    pelvis_world = world(JOINTS["pelvis"])
    torso_angle = 90.0

    right_upper_vec = vec(JOINTS["arm_r_shoulder"], JOINTS["arm_r_elbow"])
    right_upper_angle = angle(right_upper_vec)
    right_fore_vec = vec(JOINTS["arm_r_elbow"], JOINTS["arm_r_grip"])
    right_fore_angle = angle(right_fore_vec)
    left_upper_vec = vec(JOINTS["arm_l_shoulder"], JOINTS["arm_l_elbow"])
    left_upper_angle = angle(left_upper_vec)
    left_fore_vec = vec(JOINTS["arm_l_elbow"], JOINTS["arm_l_grip"])
    left_fore_angle = angle(left_fore_vec)

    front_thigh_vec = vec(JOINTS["leg_front_hip"], JOINTS["leg_front_knee"])
    front_thigh_angle = angle(front_thigh_vec)
    front_lower_vec = vec(JOINTS["leg_front_knee"], JOINTS["leg_front_ankle"])
    front_lower_angle = angle(front_lower_vec)
    rear_thigh_vec = vec(JOINTS["leg_rear_hip"], JOINTS["leg_rear_knee"])
    rear_thigh_angle = angle(rear_thigh_vec)
    rear_lower_vec = vec(JOINTS["leg_rear_knee"], JOINTS["leg_rear_ankle"])
    rear_lower_angle = angle(rear_lower_vec)

    arm_r_local = local_point(world(JOINTS["arm_r_shoulder"]), pelvis_world, torso_angle)
    arm_l_local = local_point(world(JOINTS["arm_l_shoulder"]), pelvis_world, torso_angle)
    front_hip_local = (world(JOINTS["leg_front_hip"])[0] - pelvis_world[0], world(JOINTS["leg_front_hip"])[1] - pelvis_world[1])
    rear_hip_local = (world(JOINTS["leg_rear_hip"])[0] - pelvis_world[0], world(JOINTS["leg_rear_hip"])[1] - pelvis_world[1])

    sword_world_angle = 130.0
    shield_world_angle = 0.0

    bones = [
        {"name": "root"},
        {"name": "pelvis", "parent": "root", "x": pelvis_world[0], "y": pelvis_world[1], "length": 80},
        {"name": "torso", "parent": "pelvis", "rotation": torso_angle, "length": 450},
        {"name": "head", "parent": "torso", "x": 450, "rotation": 0, "length": 150},

        {"name": "leg_rear_thigh", "parent": "pelvis", "x": rear_hip_local[0], "y": rear_hip_local[1],
         "rotation": rear_thigh_angle, "length": length(rear_thigh_vec)},
        {"name": "leg_rear_lower", "parent": "leg_rear_thigh", "x": length(rear_thigh_vec),
         "rotation": normalize(rear_lower_angle - rear_thigh_angle), "length": length(rear_lower_vec)},
        {"name": "leg_front_thigh", "parent": "pelvis", "x": front_hip_local[0], "y": front_hip_local[1],
         "rotation": front_thigh_angle, "length": length(front_thigh_vec)},
        {"name": "leg_front_lower", "parent": "leg_front_thigh", "x": length(front_thigh_vec),
         "rotation": normalize(front_lower_angle - front_thigh_angle), "length": length(front_lower_vec)},

        {"name": "arm_r_upper", "parent": "torso", "x": arm_r_local[0], "y": arm_r_local[1],
         "rotation": normalize(right_upper_angle - torso_angle), "length": length(right_upper_vec)},
        {"name": "arm_r_forearm", "parent": "arm_r_upper", "x": length(right_upper_vec),
         "rotation": normalize(right_fore_angle - right_upper_angle), "length": length(right_fore_vec)},
        {"name": "sword", "parent": "arm_r_forearm", "x": length(right_fore_vec),
         "rotation": normalize(sword_world_angle - right_fore_angle), "length": 586},

        {"name": "arm_l_upper", "parent": "torso", "x": arm_l_local[0], "y": arm_l_local[1],
         "rotation": normalize(left_upper_angle - torso_angle), "length": length(left_upper_vec)},
        {"name": "arm_l_forearm", "parent": "arm_l_upper", "x": length(left_upper_vec),
         "rotation": normalize(left_fore_angle - left_upper_angle), "length": length(left_fore_vec)},
        {"name": "shield", "parent": "arm_l_forearm", "x": length(left_fore_vec),
         "rotation": normalize(shield_world_angle - left_fore_angle), "length": 130},
    ]

    world_transforms = {
        "torso": (pelvis_world, torso_angle),
        "head": (world(JOINTS["neck"]), torso_angle),
        "leg_rear_thigh": (world(JOINTS["leg_rear_hip"]), rear_thigh_angle),
        "leg_rear_lower": (world(JOINTS["leg_rear_knee"]), rear_lower_angle),
        "leg_front_thigh": (world(JOINTS["leg_front_hip"]), front_thigh_angle),
        "leg_front_lower": (world(JOINTS["leg_front_knee"]), front_lower_angle),
        "arm_r_upper": (world(JOINTS["arm_r_shoulder"]), right_upper_angle),
        "arm_r_forearm": (world(JOINTS["arm_r_elbow"]), right_fore_angle),
        "arm_l_upper": (world(JOINTS["arm_l_shoulder"]), left_upper_angle),
        "arm_l_forearm": (world(JOINTS["arm_l_elbow"]), left_fore_angle),
        "sword": (world(JOINTS["arm_r_grip"]), sword_world_angle),
        "shield": (world(JOINTS["arm_l_grip"]), shield_world_angle),
    }

    slot_names = [
        "leg_rear_lower", "leg_rear_thigh", "leg_front_lower", "leg_front_thigh",
        "arm_r_upper", "arm_l_upper", "torso", "head",
        "arm_r_forearm", "sword", "arm_l_forearm", "shield",
    ]
    slots = [{"name": f"slot_{name}", "bone": name, "attachment": name} for name in slot_names]

    attachments = {}
    for name in slot_names:
        info = meta["parts"][name]
        left, top, right, bottom = info["bbox"]
        width, height = info["size"]
        center_px = (left + width / 2.0, top + height / 2.0)

        bone_origin, bone_angle = world_transforms[name]
        if name in ("sword", "shield"):
            grip_px = tuple(info["grip_px"])
            grip_world = world(grip_px)
            center_delta_world = (
                world(center_px)[0] - grip_world[0],
                world(center_px)[1] - grip_world[1],
            )
            radians = math.radians(bone_angle)
            local = (
                center_delta_world[0] * math.cos(radians) + center_delta_world[1] * math.sin(radians),
                -center_delta_world[0] * math.sin(radians) + center_delta_world[1] * math.cos(radians),
            )
        else:
            local = local_point(world(center_px), bone_origin, bone_angle)

        attachment = {
            "path": name,
            "x": round(local[0], 3),
            "y": round(local[1], 3),
            "rotation": round(-bone_angle, 3),
            "width": width,
            "height": height,
        }
        attachments[f"slot_{name}"] = {name: attachment}

    output = {
        "skeleton": {
            "hash": "blue-guard-hero-v4",
            "spine": "4.3.23",
            "x": -700,
            "y": -20,
            "width": 1400,
            "height": 1460,
            "fps": 60,
            "images": "./images-v4/",
        },
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "events": {
            "foot_l": {"string": "left"},
            "foot_r": {"string": "right"},
        },
        "animations": make_animations(),
    }

    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT}")
    print(f"Bones: {len(bones)}, slots: {len(slots)}, animations: {', '.join(output['animations'])}")


if __name__ == "__main__":
    main()
