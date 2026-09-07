# Troubleshooting

Every entry here is a failure that actually occurred during this project.

## `ModuleNotFoundError: No module named 'isaaclab_rl.rsl_rl.utils'`

Upstream imports `handle_deprecated_rsl_rl_cfg` from a module that does not exist
in Isaac Lab 2.3.2. Apply
[`patches/isaaclab-2.3.2-compat.patch`](../patches/isaaclab-2.3.2-compat.patch),
which removes the import and its single call site.

## `TypeError: __init__() missing 1 required positional argument: 'obs_groups'`

RSL-RL 3.x requires `obs_groups` on the runner config; upstream sets the
deprecated `empirical_normalization` instead. The patch replaces it with:

```python
obs_groups = {"policy": ["policy"], "critic": ["policy"]}
```

The environment exposes only a `policy` observation group, so both the actor and
the critic read it.

## `ValueError: too many values to unpack (expected 2)` in `play.py`

The `RslRlVecEnvWrapper` API changed. In Isaac Lab 2.3.2:

- `get_observations()` returns a `TensorDict` — **not** a `(obs, extras)` tuple
- `step()` returns **four** values, not five

```python
obs = env.get_observations()          # not: obs, _ = ...
obs, _, _, _ = env.step(actions)      # not: obs, _, _, _, _ = ...
```

## Training runs but the log is empty, then the process exits 0

Python block-buffers stdout when redirected to a file, and Isaac Sim's shutdown
path can skip the flush. A completely healthy run then looks like a silent
failure.

**Always `export PYTHONUNBUFFERED=1`.** This cost real debugging time — the first
successful playback appeared to produce no output at all.

## `--checkpoint ''` — `FileNotFoundError: ''`

```bash
# BROKEN — passes an empty checkpoint
CKPT=$(ls -t .../model_*.pt | head -1) PYTHONUNBUFFERED=1 python.sh play.py --checkpoint "$CKPT"
```

A `VAR=value` prefix on a simple command sets an environment variable **for that
command only**; the shell expands `"$CKPT"` on the same line using its *previous*
value, which is empty. Separate the assignment with `;` or a newline:

```bash
CKPT=$(ls -t .../model_*.pt | head -1); PYTHONUNBUFFERED=1 python.sh play.py --checkpoint "$CKPT"
```

## Rendering a batch of terrains, and later terrains look wrong

Terrain presets are shared module-level objects. Resizing one or disabling its
curriculum mutates it for every subsequent run in the same process.
`scripts/play.py` deep-copies before mutating. If you write your own batch
renderer, do the same.

## No video file, but the run exits 0

`--video` must set `enable_cameras=True` *before* the `AppLauncher` starts,
otherwise Isaac Sim launches without a render pipeline and `RecordVideo` captures
nothing. `scripts/play.py` handles this. Also confirm `moviepy` is importable
from the Isaac interpreter — the videos here were encoded with moviepy 2.1.2.

## RunPod: `scp` fails with "subsystem request failed on channel 0"

RunPod's SSH proxy supports neither the sftp subsystem nor legacy `scp -O`, and a
pod with no exposed TCP port has no direct route. Base64 over the interactive
shell works:

```bash
printf 'base64 -w0 /path/to/file.mp4\nexit\n' \
  | ssh -tt <pod>@ssh.runpod.io -i ~/.ssh/id_ed25519 \
  | grep -oE '^[A-Za-z0-9+/=]{200,}$' | tr -d '\n' | base64 -d > file.mp4
```

Roughly 7 seconds per 1.3 MB. Verify with `md5sum` on both ends.

## RunPod: remote commands hang or report "doesn't support PTY"

The proxy needs a PTY and does not accept a command argument. Force one and feed
the command on stdin:

```bash
printf 'nvidia-smi\nexit\n' | ssh -tt <pod>@ssh.runpod.io -i ~/.ssh/id_ed25519
```
