# Copyright (c) 2024, Quadruped DRL Training Platform
# SPDX-License-Identifier: MIT

"""Run a trained Go2 policy in evaluation / play mode.

Usage:
    isaaclab -p sim/scripts/play.py --task Go2-Obstacle-Play-v0 --checkpoint path/to/model.pt
    isaaclab -p sim/scripts/play.py --task Go2-Flat-Play-v0 --checkpoint path/to/model.pt --num_envs 4

Record an MP4 on a specific terrain:
    isaaclab -p sim/scripts/play.py --task Go2-Obstacle-Play-v0 --checkpoint path/to/model.pt \
        --terrain_config stairs --video --headless
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from datetime import datetime

# Ensure project root is on sys.path so 'sim' package is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# --------------------------------------------------------------------------- #
# 1. Parse CLI & launch simulator                                             #
# --------------------------------------------------------------------------- #
parser = argparse.ArgumentParser(description="Evaluate a trained Go2 policy.")
parser.add_argument("--task", type=str, default="Go2-Obstacle-Play-v0", help="Play-variant task id.")
parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint (.pt).")
parser.add_argument("--num_envs", type=int, default=None, help="Override environment count.")
parser.add_argument("--num_steps", type=int, default=5000, help="Number of simulation steps to run.")
parser.add_argument(
    "--terrain_config",
    type=str,
    default=None,
    help="Terrain preset name (flat, easy, obstacle, hard, stairs, slopes) or path to a terrain YAML file.",
)
parser.add_argument("--video", action="store_true", help="Record an MP4 of the rollout.")
parser.add_argument("--video_length", type=int, default=400, help="Number of steps to record.")
parser.add_argument("--video_dir", type=str, default=None, help="Output directory for recorded video.")
parser.add_argument(
    "--track_robot",
    action="store_true",
    help="Keep the camera locked on the robot in env 0 instead of a fixed world view.",
)

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Rendering must be enabled for the video wrapper to capture frames, even headless.
if args_cli.video:
    args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# --------------------------------------------------------------------------- #
# 2. Imports after simulator launch                                           #
# --------------------------------------------------------------------------- #
import gymnasium as gym
import torch
from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper

import sim.envs.go2_obstacle_env  # noqa: F401
from sim.terrains.terrain_presets import get_terrain_cfg


def _apply_terrain_override(env_cfg: ManagerBasedRLEnvCfg, terrain_config: str) -> str:
    """Swap the scene terrain for a named preset or a YAML-defined terrain.

    Returns the resolved terrain label, used for naming the output video.
    """
    if os.path.isfile(terrain_config):
        terrain_cfg = get_terrain_cfg(yaml_path=terrain_config)
        label = os.path.splitext(os.path.basename(terrain_config))[0]
        print(f"[INFO] Custom terrain YAML: {terrain_config}")
    else:
        terrain_cfg = get_terrain_cfg(preset=terrain_config)
        label = terrain_config
        print(f"[INFO] Terrain preset: {terrain_config}")

    if terrain_cfg is None:
        # "flat" preset -> a plain ground plane, no generator.
        env_cfg.scene.terrain.terrain_type = "plane"
        env_cfg.scene.terrain.terrain_generator = None
        env_cfg.scene.terrain.max_init_terrain_level = None
        return label

    # Presets are shared module-level objects; copy before mutating.
    terrain_cfg = copy.deepcopy(terrain_cfg)
    # Match the _PLAY sizing: a small, non-curriculum patch frames well on camera.
    terrain_cfg.num_rows = 5
    terrain_cfg.num_cols = 5
    terrain_cfg.curriculum = False

    env_cfg.scene.terrain.terrain_type = "generator"
    env_cfg.scene.terrain.terrain_generator = terrain_cfg
    env_cfg.scene.terrain.max_init_terrain_level = None
    return label


def main():
    task_entry = gym.spec(args_cli.task)
    env_cfg_cls = task_entry.kwargs["env_cfg_entry_point"]
    agent_cfg_cls = task_entry.kwargs["rsl_rl_cfg_entry_point"]

    import importlib

    if isinstance(env_cfg_cls, str):
        mod, cls = env_cfg_cls.rsplit(":", 1)
        env_cfg: ManagerBasedRLEnvCfg = getattr(importlib.import_module(mod), cls)()
    else:
        env_cfg = env_cfg_cls()

    if isinstance(agent_cfg_cls, str):
        mod, cls = agent_cfg_cls.rsplit(":", 1)
        agent_cfg: RslRlOnPolicyRunnerCfg = getattr(importlib.import_module(mod), cls)()
    else:
        agent_cfg = agent_cfg_cls()

    if args_cli.num_envs is not None:
        env_cfg.scene.num_envs = args_cli.num_envs

    # Terrain override (applied after _PLAY __post_init__ so it wins).
    terrain_label = "default"
    if args_cli.terrain_config:
        terrain_label = _apply_terrain_override(env_cfg, args_cli.terrain_config)

    # Camera framing for recorded footage.
    if args_cli.track_robot:
        env_cfg.viewer.origin_type = "asset_root"
        env_cfg.viewer.asset_name = "robot"
        env_cfg.viewer.env_index = 0
        env_cfg.viewer.eye = (2.5, 2.5, 1.5)
        env_cfg.viewer.lookat = (0.0, 0.0, 0.3)
    if args_cli.video:
        env_cfg.viewer.resolution = (1280, 720)

    render_mode = "rgb_array" if args_cli.video else None
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=render_mode)

    if args_cli.video:
        video_dir = args_cli.video_dir or os.path.join(
            _project_root, "logs", "videos", f"{terrain_label}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        )
        os.makedirs(video_dir, exist_ok=True)
        env = gym.wrappers.RecordVideo(
            env,
            video_folder=video_dir,
            step_trigger=lambda step: step == 0,
            video_length=args_cli.video_length,
            name_prefix=f"go2_{terrain_label}",
            disable_logger=True,
        )
        print(f"[INFO] Recording {args_cli.video_length} steps to: {video_dir}")

    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    # Load checkpoint
    log_dir = os.path.dirname(args_cli.checkpoint)
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    runner.load(args_cli.checkpoint)

    print(f"[INFO] Running inference with checkpoint: {args_cli.checkpoint}")
    print(f"[INFO] Environments: {env_cfg.scene.num_envs}, Steps: {args_cli.num_steps}")
    print(f"[INFO] Terrain: {terrain_label}")

    # Get the policy
    policy = runner.get_inference_policy(device=agent_cfg.device)

    obs = env.get_observations()
    for step in range(args_cli.num_steps):
        actions = policy(obs)
        obs, _, _, _ = env.step(actions)

    print("[INFO] Evaluation complete.")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
