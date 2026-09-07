# Reproducing the run

## Requirements

An NVIDIA RTX-class GPU with a working driver. This will not run on integrated
graphics or CPU — Isaac Sim needs Vulkan and CUDA. The run documented here used a
rented RTX 4090; anything from an RTX 3060 upward should train, more slowly.

| Component | Version used |
|---|---|
| Isaac Sim | 5.1.0 |
| Isaac Lab | 2.3.2 |
| rsl-rl-lib | 3.1.2 |
| PyTorch | 2.7.0+cu128 |
| Python | 3.11 |

## 1. Install Isaac Lab

Follow the [official installation guide](https://isaac-sim.github.io/IsaacLab/).
You need `$ISAACLAB_PATH/_isaac_sim/python.sh` to exist and be executable — that
interpreter, not your system Python, runs everything below.

```bash
export ISAACLAB_PATH=/path/to/IsaacLab
./scripts/verify_runtime.sh
```

`verify_runtime.sh` prints the versions that matter and probes whether
`isaaclab_rl.rsl_rl.utils` exists, which tells you whether the patch below is
needed.

## 2. Clone the upstream project and patch it

```bash
git clone https://github.com/CURT1S03/quadruped-drl-platform.git
cd quadruped-drl-platform
git apply /path/to/this/repo/patches/isaaclab-2.3.2-compat.patch
```

The patch is required on Isaac Lab 2.3.2 — upstream targets a newer release.
See [`patches/README.md`](../patches/README.md) for what each hunk fixes. On a
newer Isaac Lab, check `verify_runtime.sh` first; the patch may be unnecessary
or may not apply.

## 3. Install the extended playback script

```bash
cp /path/to/this/repo/scripts/play.py sim/scripts/play.py
```

This supersedes the patch's `play.py` hunk and adds terrain selection, video
recording and a tracking camera.

## 4. Train

```bash
export PROJECT_ROOT=$PWD
/path/to/this/repo/scripts/train_obstacle.sh
tail -f /workspace/trainlogs/obstacle.log
```

About 76 minutes on a 4090 for 1,500 iterations at 4,096 environments. Reduce
`NUM_ENVS` if you have less VRAM — the run peaks at only 3.1 GB, so most cards
will cope.

**Always set `PYTHONUNBUFFERED=1`** (the script does). Without it Python
block-buffers stdout on redirect, and a perfectly healthy run produces an empty
log file that looks exactly like a silent crash.

## 5. Render the demo videos

```bash
cp /path/to/this/repo/scripts/render_demo.sh .
./render_demo.sh
```

Renders the newest checkpoint across all six terrain presets to 720p MP4.
Override with `TERRAINS="stairs slopes"`, `NUM_ENVS`, `VIDEO_LENGTH`.

To chain rendering onto the end of an unattended training run, use
[`scripts/watch_and_render.sh`](../scripts/watch_and_render.sh) — set
`TRAIN_PID` and run it under `nohup`.

## 6. View the site

`index.html` is self-contained apart from the `videos/` directory. Open it
directly, or serve the repository root:

```bash
python3 -m http.server 8000
```

## Expected results

Reward should cross zero near iteration 60 and reach roughly 19–20 by 1,500.
Exact values will differ — terrain generation and environment resets are
stochastic, and the seed only fixes part of that.

If reward is still negative past iteration ~200, something is wrong: check that
the height scanner is attached and producing 187 values, and that the observation
is genuinely 235-dimensional.
