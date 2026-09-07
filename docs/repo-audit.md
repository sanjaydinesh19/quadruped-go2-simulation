# Repository audit

Before writing any code, three open-source quadruped locomotion repositories were
audited to pick a base. This records what was found and why one was chosen.

## Candidates

| Repository | Robot | Verdict |
|---|---|---|
| [CURT1S03/quadruped-drl-platform](https://github.com/CURT1S03/quadruped-drl-platform) | Unitree Go2 | **Selected** |
| [mturan33/isaaclab-anymal-locomotion](https://github.com/mturan33/isaaclab-anymal-locomotion) | ANYmal-C | Rejected |
| [H0rvex/isaaclab-quadruped-robust-locomotion](https://github.com/H0rvex/isaaclab-quadruped-robust-locomotion) | Unitree Go2 | Rejected |

## The finding that applied to all three

**None of them ran as cloned, and none shipped trained weights.** A search across
all three for `*.pt`, `*.pth`, `*.onnx` and `*.jit` returned nothing. Every one of
them is a thin layer over NVIDIA Isaac Sim + Isaac Lab, which must be installed
separately. "Clone and run a walking dog" was not achievable with any of them —
training was always going to be step one.

## CURT1S03/quadruped-drl-platform — selected

- Registers **its own four Gym environments** (`Go2-Obstacle-v0`, `Go2-Flat-v0`
  and Play variants).
- **Six terrain presets** — `flat`, `easy`, `obstacle`, `hard`, `stairs`,
  `slopes` — plus YAML-defined custom terrain. The default obstacle environment
  alone composes six sub-terrains with a difficulty curriculum.
- Ships a FastAPI backend and React dashboard for launching and monitoring runs.
- Windows-oriented defaults in the README and `config.py`, but these are pydantic
  `BaseSettings` fields and can be overridden from a `.env`, so Linux works.

Weaknesses: only four commits, no tests, and `play.py` had no way to record video
or switch terrain — which is what `scripts/play.py` here fixes.

## mturan33/isaaclab-anymal-locomotion — rejected

Genuinely good educational content: a from-scratch PPO implementation benchmarked
at 96% of RSL-RL's performance, plus an interactive keyboard-control script that
would have made a nice live demo.

Rejected because it covers only two terrains (flat and the stock
`ROUGH_TERRAINS_CFG`), and installation is fragile — the README instructs
`cp -r isaaclab-anymal-locomotion/source/* source/` but the repository contains
no `source/` directory. Files must be hand-placed to match the registered
`entry_point` module path. It also commits `__pycache__` and `.idea` artifacts.

## H0rvex/isaaclab-quadruped-robust-locomotion — rejected

**Registers no environment at all.** Its `play_policy.sh` delegates to stock
Isaac Lab's `play.py` with the stock task `Isaac-Velocity-Rough-Unitree-Go2-v0`.
Its ~6,300 lines of Python are TensorBoard scalar extraction, plotting and
robustness-evaluation tooling — not simulation. The 185 MB checkout is almost
entirely MP4 and GIF footage.

As a *walking dog simulator* it contributes nothing that stock Isaac Lab does not
already provide. It is, however, the best of the three on methodology — its
version matrix, domain-randomisation plan and failure analysis are worth reading,
and its documented approach informed this project's `docs/` layout and the
future-work items around domain randomisation.
