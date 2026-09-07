#!/usr/bin/env bash
# Render the trained Go2 policy across every terrain preset and collect the MP4s.
#
# Usage:
#   ./render_demo.sh                 # newest checkpoint, all terrains
#   ./render_demo.sh path/to/model_1500.pt
#   TERRAINS="stairs slopes" ./render_demo.sh
set -euo pipefail

PROJECT_ROOT=/workspace/quadruped-drl-platform
ISAAC_PY=/workspace/isaaclab/_isaac_sim/python.sh
TERRAINS="${TERRAINS:-flat easy obstacle hard stairs slopes}"
NUM_ENVS="${NUM_ENVS:-16}"
VIDEO_LENGTH="${VIDEO_LENGTH:-400}"
NUM_STEPS="${NUM_STEPS:-450}"

cd "$PROJECT_ROOT"

CKPT="${1:-$(ls -t logs/runs/go2_obstacle_course/*/model_*.pt 2>/dev/null | head -1)}"
if [[ -z "$CKPT" || ! -f "$CKPT" ]]; then
  echo "ERROR: no checkpoint found. Pass one explicitly: ./render_demo.sh path/to/model.pt" >&2
  exit 1
fi

OUT_DIR="$PROJECT_ROOT/logs/demo_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$OUT_DIR"
echo "Checkpoint : $CKPT"
echo "Output dir : $OUT_DIR"
echo

for terrain in $TERRAINS; do
  echo "=== Rendering: $terrain ==="
  if PYTHONUNBUFFERED=1 "$ISAAC_PY" sim/scripts/play.py \
      --task Go2-Obstacle-Play-v0 \
      --checkpoint "$CKPT" \
      --num_envs "$NUM_ENVS" \
      --num_steps "$NUM_STEPS" \
      --terrain_config "$terrain" \
      --video \
      --video_length "$VIDEO_LENGTH" \
      --video_dir "$OUT_DIR/$terrain" \
      --track_robot \
      --headless > "$OUT_DIR/$terrain.log" 2>&1; then
    mp4=$(find "$OUT_DIR/$terrain" -name '*.mp4' | head -1)
    if [[ -n "$mp4" ]]; then
      echo "  OK  -> $mp4 ($(du -h "$mp4" | cut -f1))"
    else
      echo "  WARN: ran clean but produced no MP4 (see $OUT_DIR/$terrain.log)"
    fi
  else
    echo "  FAILED (see $OUT_DIR/$terrain.log)"
  fi
done

echo
echo "=== Summary ==="
find "$OUT_DIR" -name '*.mp4' -printf '%p\t%s bytes\n' | sort
echo
echo "Fetch them with:"
echo "  scp -i ~/.ssh/id_ed25519 -r imvreir2spahuz-64411178@ssh.runpod.io:$OUT_DIR ."
