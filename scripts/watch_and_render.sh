#!/usr/bin/env bash
# Wait for the running training job to exit, then render every terrain preset.
# Deployed to the pod and run under nohup so it survives SSH disconnects.
set -uo pipefail

TRAIN_PID="${TRAIN_PID:-5678}"
LOG=/workspace/trainlogs/render.log
PROJECT_ROOT=/workspace/quadruped-drl-platform

: > "$LOG"
echo "=== watcher armed $(date -u +%Y-%m-%dT%H:%M:%SZ), waiting on train PID $TRAIN_PID ===" >> "$LOG"

while kill -0 "$TRAIN_PID" 2>/dev/null; do
  sleep 30
done

echo "=== training process exited $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG"
sleep 15   # let the final checkpoint finish flushing to disk

cd "$PROJECT_ROOT" || { echo "=== RENDER_DONE rc=1 (bad project root) ===" >> "$LOG"; exit 1; }

FINAL_CKPT=$(ls -t logs/runs/go2_obstacle_course/*/model_*.pt 2>/dev/null | head -1)
echo "=== final checkpoint: ${FINAL_CKPT:-NONE} ===" >> "$LOG"
echo "=== last training lines ===" >> "$LOG"
grep -E "Learning iteration|Mean reward" /workspace/trainlogs/obstacle.log 2>/dev/null | tail -4 >> "$LOG"

./render_demo.sh >> "$LOG" 2>&1
rc=$?

echo "=== RENDER_DONE rc=$rc at $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG"
