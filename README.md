# Quadruped Go2 Simulation

A Unitree Go2 learns to walk on six terrains from scratch with PPO, in NVIDIA
Isaac Lab. No gait is scripted and no trajectory is hand-authored — 4,096 robots
train in parallel on a single GPU, and 147 million simulated steps later one set
of weights walks stairs, slopes and rubble under velocity command.

**[▶ Live demo site](https://sanjaydinesh19.github.io/quadruped-go2-simulation/)**

| | |
|---|---:|
| Simulated steps | 147,456,000 |
| Parallel environments | 4,096 |
| PPO iterations | 1,500 |
| Wall clock | ~76 min on one RTX 4090 |
| Mean reward | −7.86 → **19.77** |
| Terrains rendered | 6 |

## The demo

Six clips in [`videos/`](videos), all driven by the **same** final checkpoint —
nothing is retuned between terrains. The policy reads a height scan of the ground
ahead and adapts its gait on the fly.

`flat` · `easy` · `obstacle` · `hard` · `stairs` · `slopes`

Open [`index.html`](index.html) for the presentation version: a single
self-contained page with the videos, the training curve, the reward breakdown and
the architecture. All HTML, CSS and JavaScript are inline — no build step, no
dependencies.

## What this demonstrates

- **Massively parallel RL.** 4,096 environments on one GPU, 37,400 steps/second.
  The measured split is 2.552 s collecting rollouts against 0.073 s of gradient
  update — this is a physics-throughput problem wearing a machine-learning
  costume.
- **Reward engineering as the real design surface.** The network is a plain MLP.
  Twelve weighted reward terms, spanning seven orders of magnitude, are what
  separate walking from hopping, shuffling and thrashing.
- **Terrain curriculum.** Difficulty escalates beneath the policy as it improves,
  which is why the reward curve keeps climbing instead of plateauing.
- **Generalisation, honestly reported.** Five of the six rendered terrains are
  outside the training distribution. `hard` is visibly the weakest — an
  out-of-distribution result worth showing, not hiding.

## Results

| Iteration | Mean reward |
|---:|---:|
| 29 | −7.86 |
| 103 | 2.10 |
| 291 | 9.16 |
| 895 | 15.24 |
| 1499 | **19.77** |

Late training also held a **940/1000** mean episode length at an **8.7%** fall
rate. That combination is the point: early on, the robot could already survive
~900 steps by standing still and avoiding the fall penalty. Holding a comparable
episode length *while* earning high tracking reward is what makes it walking.

Full numbers in [`docs/training-run.md`](docs/training-run.md); machine-readable
data in [`results/`](results).

## Repository layout

```
index.html                  self-contained demo site
videos/                     six rendered terrain clips (720p, 50 fps)
docs/                       architecture, reward design, terrain, audit, troubleshooting
results/                    metrics, configs and curve samples as CSV/JSON
scripts/                    training, playback and rendering tools
patches/                    Isaac Lab 2.3.2 compatibility patch
```

## Documentation

| Document | Contents |
|---|---|
| [training-run.md](docs/training-run.md) | configuration, reward curve, throughput |
| [policy-architecture.md](docs/policy-architecture.md) | network, 235-dim observation, PPO hyperparameters |
| [reward-design.md](docs/reward-design.md) | all twelve terms and what each prevents |
| [terrain.md](docs/terrain.md) | terrain mix, curriculum, the six presets |
| [system-architecture.md](docs/system-architecture.md) | the end-to-end loop |
| [repo-audit.md](docs/repo-audit.md) | why this base was chosen over two alternatives |
| [reproduce.md](docs/reproduce.md) | step-by-step reproduction |
| [troubleshooting.md](docs/troubleshooting.md) | every failure hit during the project |

## Reproducing

Requires an RTX-class GPU, Isaac Sim 5.1.0 and Isaac Lab 2.3.2. Full steps in
[`docs/reproduce.md`](docs/reproduce.md):

```bash
export ISAACLAB_PATH=/path/to/IsaacLab
./scripts/verify_runtime.sh                              # check versions
git apply patches/isaaclab-2.3.2-compat.patch            # in an upstream checkout
./scripts/train_obstacle.sh                              # ~76 min
./scripts/render_demo.sh                                 # six terrain videos
```

**Trained weights are not included.** `model_1499.pt` stayed on the rented GPU
node, which was shut down after the run. Everything needed to reproduce it is
here, and training takes about 76 minutes.

## Future work

- **Asymmetric actor–critic.** The critic currently sees exactly what the actor
  sees. Feeding it privileged simulator state — true friction, contact forces,
  terrain height — sharpens the value estimate at no deployment cost.
- **Domain randomisation.** Randomise mass, friction, motor strength and latency,
  then measure survival under held-out perturbations.
- **Sim-to-real transfer.** Export to TorchScript for physical Go2 hardware. The
  observation vector is already deployable except for the height scan, which
  needs a real depth camera.
- **Teacher–student distillation.** Distil this height-scan policy into a blind
  student walking on proprioception alone.
- **Harder curriculum.** Train directly on the `hard` preset to close the gap its
  footage exposes.
- **Live training console.** The upstream project ships a FastAPI + React
  dashboard for launching runs and streaming reward curves in the browser.

## Built on

- [CURT1S03/quadruped-drl-platform](https://github.com/CURT1S03/quadruped-drl-platform)
  (MIT) — the Go2 Isaac Lab environments, terrain presets and PPO configuration
  this project trains, patches and extends.
- [NVIDIA Isaac Lab](https://github.com/isaac-sim/IsaacLab) and Isaac Sim.
- [RSL-RL](https://github.com/leggedrobotics/rsl_rl) — the PPO implementation.
