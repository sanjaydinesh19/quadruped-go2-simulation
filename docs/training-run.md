# Training run

The single run behind every number in this repository and on the demo site.

## Configuration

| Setting | Value |
|---|---|
| Task | `Go2-Obstacle-v0` |
| Parallel environments | 4,096 |
| Iterations | 1,500 |
| Steps per env per iteration | 24 |
| Samples per iteration | 98,304 |
| Total simulated steps | 147,456,000 |
| Checkpoint interval | every 50 iterations |
| Seed | 42 |
| Mode | headless |

## Result

Mean episode reward climbed from **−7.86** to **19.77**.

| Iteration | Mean reward | Note |
|---:|---:|---|
| 29 | −7.86 | robot collapses immediately |
| 103 | 2.10 | reward has crossed zero |
| 198 | 5.78 | |
| 291 | 9.16 | |
| 433 | 10.96 | |
| 895 | 15.24 | |
| 1444 | 18.26 | |
| 1499 | 19.77 | final checkpoint |

These are **samples observed live during the run**, not a dense export. The full
TensorBoard scalar series stayed on the training pod, which was shut down after
the run. Machine-readable copy: [`results/training_samples.csv`](../results/training_samples.csv).

Reward crosses zero somewhere around iteration 60 — between the −7.86 reading at
29 and the +1.81 reading at 102.

## Gait quality

Read live during late training (approximately iteration 950):

| Metric | Value | Meaning |
|---|---:|---|
| Mean episode length | 940 / 1000 | steps survived before timeout |
| `base_contact` terminations | 8.7% | episodes ending with the body hitting the ground |
| `error_vel_xy` | 0.4187 | linear velocity tracking error |
| `track_lin_vel_xy_exp` | 1.1212 | velocity tracking reward earned |

Early in training (~iteration 100) mean episode length was 902–919 while reward
was still near zero. That combination is the signature of a robot that survives
by standing still: it avoids the fall penalty without earning tracking reward.
The later run holds a comparable episode length *and* a high reward, which is
what separates walking from standing.

## Throughput

Benchmarked on an otherwise idle GPU at 4,096 environments:

- **37,400 steps/second**
- **2.63 s** per iteration — 2.552 s collecting rollouts, **0.073 s** on the
  gradient update

Physics simulation dominates by a factor of roughly 35. During the real run,
iteration time was 2.84 s: the pod's built-in Isaac Sim streaming service was
sharing the GPU.

Total wall clock: **about 76 minutes**, peaking at **3.1 GB of 24 GB VRAM** —
so environment count was nowhere near the memory ceiling.

## Rendering

After training exited, a watcher process automatically replayed the final
checkpoint across all six terrain presets:

- 1280×720, 50 fps, 400 frames, 8.0 s per clip
- Six clips, ~8 MB total, in [`videos/`](../videos)

Every clip was verified by extracting frames and inspecting them, not just by
checking the exit code — enough to confirm the terrain override genuinely
applied rather than silently falling back to the default.
