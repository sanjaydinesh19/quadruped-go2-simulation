# Terrain

## The training mix

`Go2-Obstacle-v0` trains on a procedurally generated field: a **10 × 20 grid of
8 × 8 m tiles** — 200 tiles in total — drawn from six sub-terrain types.

| Sub-terrain | Share | Description |
|---|---:|---|
| `pyramid_stairs` | 20% | ascending steps |
| `boxes` | 20% | random raised grid blocks |
| `random_rough` | 20% | uniform height noise |
| `pyramid_stairs_inv` | 15% | descending steps |
| `hf_pyramid_slope` | 15% | inclined ramp |
| `hf_pyramid_slope_inv` | 10% | declined ramp |

Machine-readable copy: [`results/terrain_mix.csv`](../results/terrain_mix.csv).

## Curriculum

Rows of the grid increase in difficulty. `max_init_terrain_level = 5` caps where
robots spawn at the start of training; as they succeed, they are promoted to
harder rows. This is why the reward curve keeps climbing rather than plateauing —
the policy is chasing a target that keeps getting harder underneath it.

The `_PLAY` configurations disable the curriculum and shrink the grid to 5 × 5,
so evaluation is deterministic and frames well on camera.

## The six presets

Selectable at playback with `--terrain_config`:

| Preset | Content |
|---|---|
| `flat` | a plain ground plane — no generator |
| `easy` | gentle height noise, shallow slopes |
| `obstacle` | the training mix above |
| `hard` | steeper slopes, taller steps, rougher noise |
| `stairs` | stairs only, ascending and descending |
| `slopes` | slopes only, inclined and declined |

`flat` is the special case: the preset resolves to `None`, and the scene switches
`terrain_type` to `"plane"` instead of running the generator at all. It is a
distinct code path and worth testing separately from the others.

## Evaluating outside the training distribution

Five of the six presets are *not* what the policy trained on. `stairs` and
`slopes` isolate components of the training mix, so the policy handles them well.
`easy` is strictly simpler. `flat` is trivial.

`hard` is the interesting one: steeper and rougher than anything in the mix, and
the footage shows the policy struggling. That is an honest out-of-distribution
result rather than a bug, and it is the clearest argument for the domain
randomisation and harder-curriculum items in the future work.

## A trap for anyone extending this

The terrain presets are **shared module-level objects**. Mutating one to resize
it or disable its curriculum corrupts it for every later run in the same process
— render `stairs` then `slopes` in one batch and the second inherits the first's
mutations. `scripts/play.py` deep-copies the preset before touching it.
