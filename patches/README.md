# Patches

## `isaaclab-2.3.2-compat.patch`

Makes [CURT1S03/quadruped-drl-platform](https://github.com/CURT1S03/quadruped-drl-platform)
run on **Isaac Lab 2.3.2 / rsl-rl-lib 3.1.2**. Upstream targets a newer Isaac Lab
release, and without these four changes nothing runs at all.

Apply from the root of an upstream checkout:

```bash
git apply /path/to/patches/isaaclab-2.3.2-compat.patch
```

### What each hunk does

**1. `sim/scripts/train.py` — remove a dead import**

```python
from isaaclab_rl.rsl_rl.utils import handle_deprecated_rsl_rl_cfg
```

`isaaclab_rl.rsl_rl.utils` does not exist in 2.3.2; the package contains only
`rl_cfg`, `vecenv_wrapper`, `exporter`, `distillation_cfg`, `rnd_cfg` and
`symmetry_cfg`. The import raises `ModuleNotFoundError` before training starts.

**2. `sim/scripts/train.py` — remove its call site**

`handle_deprecated_rsl_rl_cfg(agent_cfg, rsl_rl_version)` goes with it. Its job
was migrating deprecated config fields, which hunk 3 does statically instead.

**3. `sim/agents/go2_ppo_cfg.py` — `empirical_normalization` → `obs_groups`**

```python
-    empirical_normalization = False
+    obs_groups = {"policy": ["policy"], "critic": ["policy"]}
```

`obs_groups` is a required field on `RslRlOnPolicyRunnerCfg` in rsl-rl 3.x, while
`empirical_normalization` is deprecated. The environment exposes a single
`policy` observation group, so actor and critic both map to it.

**4. `sim/scripts/play.py` — two changed return signatures**

```python
-    obs, _ = env.get_observations()
+    obs = env.get_observations()
-        obs, _, _, _, _ = env.step(actions)
+        obs, _, _, _ = env.step(actions)
```

In 2.3.2, `RslRlVecEnvWrapper.get_observations()` returns a `TensorDict` rather
than an `(obs, extras)` tuple, and `step()` returns four values
`(obs, rewards, dones, extras)` rather than five.

### Note on `play.py`

Hunk 4 is the minimum needed to make upstream playback run.
[`scripts/play.py`](../scripts/play.py) in this repository is a fuller
replacement that already includes it, and adds terrain selection, video recording
and a robot-tracking camera. Copy that file over `sim/scripts/play.py` instead of
relying on the patch alone.

### Verifying whether you need this

```bash
./scripts/verify_runtime.sh
```

It reports whether `isaaclab_rl.rsl_rl.utils` is importable. If it is, you are on
a newer Isaac Lab and this patch will likely conflict — check each hunk by hand.
