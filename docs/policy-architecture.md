# Policy architecture

An actor–critic MLP trained with PPO. No recurrence, no convolution, no
attention — the difficulty here lives in the reward design and the terrain
curriculum, not the network.

## Shape

```
observation (235)
      │
      ├─ actor  ─ 512 ─ ELU ─ 256 ─ ELU ─ 128 ─ ELU ─ 12   → joint position targets
      └─ critic ─ 512 ─ ELU ─ 256 ─ ELU ─ 128 ─ ELU ─ 1    → state value
```

Both heads read the same observation. `obs_groups` maps
`{"policy": ["policy"], "critic": ["policy"]}` — the critic gets **no privileged
information**, which is the most obvious thing to improve (see
[future work](../README.md#future-work)).

Actions are joint **position targets**, not torques. A PD controller converts
them to torques at the 200 Hz physics rate while the policy runs at 50 Hz —
one policy step per four physics steps.

## Observation vector — 235 dimensions

| Term | Dims | Kind |
|---|---:|---|
| `base_lin_vel` | 3 | proprioception |
| `base_ang_vel` | 3 | proprioception |
| `projected_gravity` | 3 | proprioception — body orientation |
| `velocity_commands` | 3 | the command being tracked |
| `joint_pos` | 12 | proprioception |
| `joint_vel` | 12 | proprioception |
| `actions` | 12 | previous action |
| `height_scan` | 187 | terrain perception |
| **Total** | **235** | |

**187 of 235 dimensions — 80% — are terrain perception.** The height scan is a
grid of raycasts from the body down to the ground, giving the policy a local
heightmap of what it is about to step on. This is what lets one set of weights
handle stairs and slopes without retuning, and it is also the single biggest
obstacle to deploying on hardware: a real robot has no such oracle and needs a
depth camera plus state estimation to approximate it.

Gaussian noise is injected into every proprioceptive term during training
(`enable_corruption`), and disabled for evaluation.

## PPO hyperparameters

| Parameter | Value |
|---|---|
| Learning rate | 1e-3, adaptive |
| Desired KL | 0.01 |
| Clip parameter | 0.2 |
| Learning epochs | 5 |
| Mini-batches | 4 |
| Discount γ | 0.99 |
| GAE λ | 0.95 |
| Entropy coefficient | 0.01 |
| Value loss coefficient | 1.0 |
| Clipped value loss | enabled |
| Max gradient norm | 1.0 |
| Initial action noise σ | 1.0 (scalar) |

The adaptive schedule tunes the learning rate to hold the policy update near the
0.01 KL target, rather than following a fixed decay.

Machine-readable copy: [`results/run_config.json`](../results/run_config.json).
