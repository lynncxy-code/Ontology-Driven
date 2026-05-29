"""诊断版 rollout 录制脚本 v2

相比 v1 多录：
1. base_pos / base_quat — 机器人底座的实际世界位姿（解开"机器人在哪里"之谜）
2. default_joint_pos — Isaac Lab 配置的默认关节角（如果 obs 里的 joint_pos 是 delta，加上这个就是绝对值）
3. body_names / body_poses — 所有 link 的世界位姿（直接 ground truth FK 结果）
4. 不止录 obs 里的 joint_pos，再录 data.joint_pos 和 data.joint_pos_target，互相印证

使用：scp 上去覆盖 ~/IsaacLab/scripts/imitation_learning/robomimic/play_record_trajectory.py 然后跑 ~/run_rollout_record.sh
"""

import argparse
import copy
import datetime
import json
import os
import torch

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Evaluate robomimic policy + record trajectory (v2 diagnostic).")
parser.add_argument("--disable_fabric", action="store_true", default=False)
parser.add_argument("--task", type=str, default=None)
parser.add_argument("--checkpoint", type=str, default=None)
parser.add_argument("--horizon", type=int, default=800)
parser.add_argument("--num_rollouts", type=int, default=1)
parser.add_argument("--seed", type=int, default=101)
parser.add_argument("--norm_factor_min", type=float, default=None)
parser.add_argument("--norm_factor_max", type=float, default=None)
parser.add_argument("--enable_pinocchio", default=False, action="store_true")
parser.add_argument("--save_trajectory", type=str, default="/home/avic/rollout_trajectory.json")

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import numpy as np
import robomimic.utils.file_utils as FileUtils
import robomimic.utils.torch_utils as TorchUtils

import isaaclab_tasks  # noqa
from isaaclab_tasks.utils import parse_env_cfg

if args_cli.enable_pinocchio:
    import isaaclab_tasks.manager_based.manipulation.pick_place  # noqa


def _to_list(t):
    if torch.is_tensor(t):
        return t.detach().cpu().tolist()
    return list(t)


def rollout_with_record(policy, env, success_term, horizon, device):
    policy.start_episode()
    obs_dict, _ = env.reset()
    frames = []
    success = False

    robot = env.scene["robot"]

    # --- 一次性记录的元信息 ---
    body_names = list(robot.data.body_names)
    joint_names = list(robot.data.joint_names)
    default_joint_pos = _to_list(robot.data.default_joint_pos[0])

    print(f"[V2] joint_names ({len(joint_names)}): {joint_names}")
    print(f"[V2] body_names ({len(body_names)}): {body_names}")
    print(f"[V2] default_joint_pos: {default_joint_pos}")

    for i in range(horizon):
        obs = copy.deepcopy(obs_dict["policy"])
        for ob in obs:
            obs[ob] = torch.squeeze(obs[ob])

        obj = _to_list(obs["object"])

        # 多源关节角
        obs_joint_pos = _to_list(obs["joint_pos"]) if "joint_pos" in obs else None
        data_joint_pos = _to_list(robot.data.joint_pos[0])
        data_joint_pos_target = _to_list(robot.data.joint_pos_target[0])

        # 底座位姿（root_pose_w 是世界系）
        root_pos = _to_list(robot.data.root_pos_w[0])     # [x,y,z] in world
        root_quat = _to_list(robot.data.root_quat_w[0])   # [w,x,y,z] in world

        # 所有 link 的世界位姿（ground truth FK）
        body_pos = _to_list(robot.data.body_pos_w[0])     # [N,3]
        body_quat = _to_list(robot.data.body_quat_w[0])   # [N,4] wxyz

        frame = {
            "step": i,
            "object_pos": obj[0:3],
            "object_quat": obj[3:7],
            "right_eef_pos": _to_list(obs["right_eef_pos"]),
            "right_eef_quat": _to_list(obs["right_eef_quat"]),
            "left_eef_pos": _to_list(obs["left_eef_pos"]),
            "left_eef_quat": _to_list(obs["left_eef_quat"]),
            "joint_pos_obs": obs_joint_pos,           # 可能是 delta
            "joint_pos_data": data_joint_pos,          # 绝对值（理论上）
            "joint_pos_target": data_joint_pos_target, # 命令目标
            "base_pos": root_pos,
            "base_quat": root_quat,
            "body_pos": body_pos,
            "body_quat": body_quat,
            # 兼容旧字段
            "joint_pos": data_joint_pos,
        }
        frames.append(frame)

        actions = policy(obs)
        if args_cli.norm_factor_min is not None and args_cli.norm_factor_max is not None:
            actions = ((actions + 1) * (args_cli.norm_factor_max - args_cli.norm_factor_min)) / 2 + args_cli.norm_factor_min

        actions = torch.from_numpy(actions).to(device=device).view(1, env.action_space.shape[1])
        obs_dict, _, terminated, truncated, _ = env.step(actions)

        if bool(success_term.func(env, **success_term.params)[0]):
            success = True
            break

    meta_extras = {
        "joint_names": joint_names,
        "body_names": body_names,
        "default_joint_pos": default_joint_pos,
    }
    return success, frames, meta_extras


def main():
    device = TorchUtils.get_torch_device(try_to_use_cuda=True)

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
    env_cfg.terminations.time_out = None
    if hasattr(env_cfg, "recorders"):
        env_cfg.recorders = None

    env = gym.make(args_cli.task, cfg=env_cfg).unwrapped
    success_term = env_cfg.terminations.success

    policy, _ = FileUtils.policy_from_checkpoint(
        ckpt_path=args_cli.checkpoint, device=device, verbose=True
    )

    all_rollouts = []
    results = []
    last_meta = {}
    for trial in range(args_cli.num_rollouts):
        success, frames, meta = rollout_with_record(policy, env, success_term, args_cli.horizon, device)
        results.append(success)
        all_rollouts.append({
            "trial_id": trial,
            "success": success,
            "num_steps": len(frames),
            "frames": frames,
        })
        last_meta = meta
        print(f"[INFO] Trial {trial}: {success} ({len(frames)} steps)", flush=True)

    succ_count = sum(1 for r in results if r)

    output = {
        "metadata": {
            "task": args_cli.task,
            "checkpoint": args_cli.checkpoint,
            "datetime": datetime.datetime.now().isoformat(),
            "num_rollouts": len(results),
            "success_count": succ_count,
            "success_rate": succ_count / len(results),
            "fps": 20,
            "frame_keys": [
                "step", "object_pos", "object_quat",
                "right_eef_pos", "right_eef_quat", "left_eef_pos", "left_eef_quat",
                "joint_pos_obs", "joint_pos_data", "joint_pos_target",
                "base_pos", "base_quat", "body_pos", "body_quat", "joint_pos",
            ],
            **last_meta,
        },
        "rollouts": all_rollouts,
    }
    os.makedirs(os.path.dirname(args_cli.save_trajectory) or ".", exist_ok=True)
    with open(args_cli.save_trajectory, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[INFO] Trajectory saved to: {args_cli.save_trajectory}", flush=True)
    print(f"[INFO] File size: {os.path.getsize(args_cli.save_trajectory) / 1024:.1f} KB", flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
