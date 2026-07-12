"""Student policy training configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass

# Repo root = constrained-albc/ (this file is constrained_albc/envs/main/student/config.py,
# so five levels up). Used to anchor log_dir_root to an ABSOLUTE path: train_student.py runs
# via isaaclab.sh from /workspace/isaaclab, so a relative root would leak student output into
# the isaaclab repo. Anchoring here keeps teacher and student output in one source-of-truth tree.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


@dataclass
class StudentCfg:
    """Hyperparameters for student encoder supervised training."""

    # Experiment. experiment_name shares the teacher's "albc_trpo" prefix (2026-05-26) so
    # teacher (albc_trpo_teacher) and student (albc_trpo_student) cluster together under
    # both logs/rsl_rl/ and experiments/rsl_rl/.
    experiment_name: str = "albc_trpo_student"
    run_name: str = "student_tcn"
    seed: int = 42

    # Teacher (set by the caller; no hardcoded run -- the teacher is whichever
    # trained checkpoint you distil from).
    teacher_run_dir: str = ""
    teacher_checkpoint: str = "model_4999.pt"

    # Architecture
    encoder_type: str = "tcn"       # "tcn" or "gru"
    policy_obs_dim: int = 69        # attitude-only: 20 proprio + 46 history + 3 integral
    privileged_dim: int = 28        # attitude-only: 24 DR + 3 measured lin_vel + 1 control delay (critic-only)
    latent_dim: int = 9             # must match teacher encoder output

    # TCN-specific
    # H=9 mirrors teacher's embedded history: stride=3 x 3 steps = 9 physical
    # steps at 50 Hz (180 ms). Sampled at stride=1 for denser temporal signal.
    # Kernels shrunk to fit H=9: (3,3,3) strides (1,1,1) -> L_out 9->7->5->3.
    tcn_history: int = 9
    tcn_input_channels: int = 32    # after per-step channel transform
    tcn_conv_channels: tuple[int, ...] = (64, 128, 128)
    tcn_conv_kernels: tuple[int, ...] = (3, 3, 3)
    tcn_conv_strides: tuple[int, ...] = (1, 1, 1)
    tcn_head_hidden: int = 128

    # GRU-specific
    gru_layers: int = 1
    gru_hidden: int = 128
    # Intermediate head layer dim (128 -> gru_head_hidden -> latent_dim).
    # 0 disables intermediate layer (shallow head: Linear + LN(latent)).
    # Teacher's encoder has a 128->64->9 pattern; matching this eases
    # representation of teacher's per-dim latent structure (per-dim stds
    # 0.17..0.48). Default 64 adds ~8K params, ~10% inference cost.
    gru_head_hidden: int = 64

    # Training
    num_envs: int = 4096
    n_steps_per_rollout: int = 24
    n_epochs: int = 5
    minibatch_size: int = 8192
    lr: float = 5e-4
    max_iterations: int = 1000
    grad_clip_norm: float = 1.0
    lambda_latent: float = 1.0
    save_interval: int = 100

    # Logging. log_dir_root is ABSOLUTE (anchored to the constrained-albc repo) so student
    # output does not leak into the isaaclab cwd train_student.py runs from. It mirrors the
    # teacher layout logs/rsl_rl/<experiment_name>/. experiments_root is derived from this in
    # train_student.py (repo_root/experiments).
    log_dir_root: str = os.path.join(_REPO_ROOT, "logs", "rsl_rl", experiment_name)
    logger: str = "wandb"           # "wandb" or "tensorboard"
    wandb_project: str = "albc_trpo_student"

    # Environment
    task: str = "Isaac-ConstrainedALBC-TRPO-v0"
    device: str = "cuda:0"          # overridden by CUDA_VISIBLE_DEVICES at launch
