#!/usr/bin/env bash
# Print the runtime versions that matter before starting a run.
# Mismatches here are the usual cause of import errors in the upstream code.
set -uo pipefail

ISAACLAB_PATH="${ISAACLAB_PATH:-/workspace/isaaclab}"
ISAAC_PY="$ISAACLAB_PATH/_isaac_sim/python.sh"

echo "=== GPU ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || echo "no nvidia-smi"

echo
echo "=== Isaac Sim ==="
cat "$ISAACLAB_PATH/_isaac_sim/VERSION" 2>/dev/null || echo "VERSION file not found"

echo
echo "=== Python packages ==="
if [[ -x "$ISAAC_PY" ]]; then
  "$ISAAC_PY" -m pip list 2>/dev/null | grep -Ei '^(isaaclab|isaaclab_rl|isaaclab_tasks|rsl-rl-lib|torch|gymnasium) '
else
  echo "ERROR: $ISAAC_PY not executable" >&2
fi

echo
echo "=== Compatibility probe ==="
if [[ -x "$ISAAC_PY" ]]; then
  "$ISAAC_PY" - <<'PY' 2>/dev/null
try:
    import isaaclab_rl.rsl_rl.utils  # noqa: F401
    print("isaaclab_rl.rsl_rl.utils present -> upstream code may run unpatched")
except ModuleNotFoundError:
    print("isaaclab_rl.rsl_rl.utils MISSING -> apply patches/isaaclab-2.3.2-compat.patch")
PY
fi
