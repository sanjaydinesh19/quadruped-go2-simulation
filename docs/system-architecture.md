# System architecture

## The training loop

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Terrain generator                                         │
│    10 × 20 grid of 8×8 m tiles, six sub-terrain types,       │
│    difficulty curriculum by row                              │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Isaac Sim physics — 200 Hz                                │
│    4,096 Go2 robots stepped in parallel on ONE GPU,          │
│    each with its own terrain patch and velocity command      │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Isaac Lab managers                                        │
│    Observation manager  → 235-dim vector per robot           │
│    Reward manager       → 12 weighted terms per robot        │
│    Termination manager  → time_out | base_contact            │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. PPO update — RSL-RL, 50 Hz policy rate                    │
│    24 steps × 4,096 envs = 98,304 samples per iteration      │
│    5 epochs × 4 mini-batches, adaptive LR on 0.01 KL target  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Checkpoint & render                                       │
│    model_N.pt every 50 iterations → replay across all six    │
│    terrain presets → 720p MP4                                │
└──────────────────────────────────────────────────────────────┘
```

## Why 4,096 environments on one GPU

PPO is sample-hungry. Collecting 147 million environment steps serially would be
hopeless; the entire approach depends on the physics being GPU-parallel, with
observations and rewards computed as batched tensor operations that never leave
the device.

The measured split makes the point: **2.552 s collecting, 0.073 s learning.**
Simulation outweighs the neural network by roughly 35×. This is a physics
throughput problem wearing a machine-learning costume — which is why the run
peaks at 3.1 GB of 24 GB VRAM. Memory was never the constraint.

## Control rates

| Rate | What runs |
|---|---|
| 200 Hz | physics step, PD joint controller |
| 50 Hz | policy inference, observation assembly, reward evaluation |

Decimation of 4. The policy emits joint position targets and the PD controller
tracks them between policy steps.

## Runtime stack

| Component | Version |
|---|---|
| Isaac Sim | 5.1.0-rc.19 |
| Isaac Lab | 2.3.2 |
| RSL-RL | rsl-rl-lib 3.1.2 |
| PyTorch | 2.7.0+cu128 |
| Python | 3.11.13 |
| Gymnasium | 1.2.1 |

Hardware: [`results/hardware.json`](../results/hardware.json).

## Unattended execution

Training ran detached under `nohup` with a watcher process
([`scripts/watch_and_render.sh`](../scripts/watch_and_render.sh)) polling the
training PID every 30 seconds. When training exited, the watcher waited 15
seconds for the final checkpoint to flush, then launched the six-terrain render
automatically and wrote a `RENDER_DONE rc=<code>` marker.

The whole chain lives on the remote host, so a dropped SSH connection or a closed
laptop cannot interrupt it.
