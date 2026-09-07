#!/usr/bin/env bash
# Launch the full 1500-iteration obstacle-course training run, detached.
#
#   ./train_obstacle.sh
#
# Requires ISAACLAB_PATH and a checkout of the (patched) upstream project.
# PYTHONUNBUFFERED is essential: without it Python block-buffers on redirect and
# a healthy run looks like a silent failure.
set -euo pipefail

ISAACLAB_PATH="${ISAACLAB_PATH:-/workspace/isaaclab}"
PROJECT_ROOT="${PROJECT_ROOT:-/workspace/quadruped-drl-platform}"
LOG_DIR="${LOG_DIR:-/workspace/trainlogs}"
NUM_ENVS="${NUM_ENVS:-4096}"
MAX_ITER="${MAX_ITER:-1500}"

ISAAC_PY="$ISAACLAB_PATH/_isaac_sim/python.sh"
[[ -x "$ISAAC_PY" ]] || { echo "ERROR: $ISAAC_PY not found or not executable" >&2; exit 2; }

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

nohup env PYTHONUNBUFFERED=1 "$ISAAC_PY" sim/scripts/train.py \
  --task Go2-Obstacle-v0 \
  --num_envs "$NUM_ENVS" \
  --max_iterations "$MAX_ITER" \
  --headless \
  > "$LOG_DIR/obstacle.log" 2>&1 &

echo $! > "$LOG_DIR/obstacle.pid"
echo "training started, pid $(cat "$LOG_DIR/obstacle.pid")"
echo "follow with: tail -f $LOG_DIR/obstacle.log"
