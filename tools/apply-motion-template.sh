#!/usr/bin/env bash
# Apply the reusable sword-and-shield motion library to a compatible Spine file.
# The source project is never modified: a new output .spine file is required.
set -euo pipefail

SPINE_BIN="${SPINE_BIN:-/Applications/Spine.app/Contents/MacOS/Spine}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT_DIR/assets/animation_templates/humanoid-sword-shield-motion-template-essential-v1.spine"
TARGET_SKELETON="${TARGET_SKELETON:-blue_guard_hero_v3}"

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <target.spine> <new-output.spine> [animation ...]" >&2
  exit 2
fi

TARGET="$1"
OUTPUT="$2"
shift 2

[[ -x "$SPINE_BIN" ]] || { echo "Spine CLI not found: $SPINE_BIN" >&2; exit 1; }
[[ -f "$TEMPLATE" ]] || { echo "Motion template not found: $TEMPLATE" >&2; exit 1; }
[[ -f "$TARGET" ]] || { echo "Target project not found: $TARGET" >&2; exit 1; }
[[ "$TARGET" != "$OUTPUT" ]] || { echo "Output must differ from target; the source is never overwritten." >&2; exit 1; }
[[ ! -e "$OUTPUT" ]] || { echo "Output already exists: $OUTPUT" >&2; exit 1; }

mkdir -p "$(dirname "$OUTPUT")"
cp "$TARGET" "$OUTPUT"

ANIMATIONS=(
  idle_relaxed idle_combat walk_forward run_forward
  jump_start jump_loop fall_loop land
  attack_slash_1 attack_slash_2 attack_thrust
  guard_loop block_hit hurt_front death_back
)

if [[ $# -gt 0 ]]; then
  ANIMATIONS=("$@")
fi

ARGS=()
for animation in "${ANIMATIONS[@]}"; do
  ARGS+=(--animation "$animation")
done

"$SPINE_BIN" \
  --input "$TEMPLATE" \
  --output "$OUTPUT" \
  --from humanoid_sword_shield_template \
  --to "$TARGET_SKELETON" \
  "${ARGS[@]}" \
  --replace \
  --import

echo "Applied ${#ANIMATIONS[@]} animations -> $OUTPUT"
