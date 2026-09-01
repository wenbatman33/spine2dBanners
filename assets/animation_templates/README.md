# Humanoid Sword + Shield Motion Template — Spine Essential 4.3

`humanoid-sword-shield-motion-template-essential-v1.spine` is a real Spine
project containing reusable animation timelines and events. It has no artwork,
so it can be imported into another character that follows the same bone names.

## Required bone names

```text
root
└── body
    └── pelvis
        ├── torso
        │   ├── head
        │   ├── scarf_tail
        │   ├── arm_r_upper → arm_r_forearm → hand_r → sword
        │   └── arm_l_upper → arm_l_forearm → hand_l → shield
        ├── leg_rear_thigh → leg_rear_lower
        └── leg_front_thigh → leg_front_lower
```

Right hand means the character's anatomical right hand. The template always
keeps the sword in `hand_r` and the shield in `hand_l`.

## Apply in Spine Editor

1. Open the target character project.
2. Choose `Spine menu → Import Project`.
3. Select `humanoid-sword-shield-motion-template-essential-v1.spine`.
4. Choose `Animation`, source skeleton `humanoid_sword_shield_template`, then
   choose the compatible target skeleton.
5. Import all animations or only the actions needed by the game.

Spine imports keys only for bones/events/constraints with matching names. The
target artwork remains unchanged.

## Apply by command line

The helper refuses to overwrite the original project:

```bash
./tools/apply-motion-template.sh character.spine character-with-motion.spine
```

For a target skeleton with another name, set it explicitly:

```bash
TARGET_SKELETON=my_character \
  ./tools/apply-motion-template.sh character.spine character-with-motion.spine
```

Or apply selected animations:

```bash
./tools/apply-motion-template.sh character.spine character-with-motion.spine \
  idle_combat walk_forward run_forward attack_slash_1 guard_loop
```

## Included animations

- `idle_relaxed`, `idle_combat`
- `walk_forward`, `run_forward`
- `jump_start`, `jump_loop`, `fall_loop`, `land`
- `attack_slash_1`, `attack_slash_2`, `attack_thrust`
- `guard_loop`, `block_hit`
- `hurt_front`, `death_back`

The project uses only Spine Essential-compatible bones, slots, region
attachments, timelines and events. It deliberately contains no meshes, weights,
IK, transform/path constraints, clipping or physics constraints.
