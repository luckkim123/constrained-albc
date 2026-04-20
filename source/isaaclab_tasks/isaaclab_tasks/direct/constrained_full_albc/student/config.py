"""Student policy training configuration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StudentCfg:
    """Hyperparameters for student encoder supervised training."""

    # Experiment
    experiment_name: str = "student_policy"
    run_name: str = "student_tcn"
    seed: int = 42

    # Teacher
    teacher_run_dir: str = "logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A"
    teacher_checkpoint: str = "model_4999.pt"

    # Architecture
    encoder_type: str = "tcn"       # "tcn" or "gru"
    policy_obs_dim: int = 87
    privileged_dim: int = 24
    latent_dim: int = 9             # must match r13_A teacher

    # TCN-specific
    tcn_history: int = 50           # H = 50 steps (1.0 s at 50 Hz)
    tcn_input_channels: int = 32    # after per-step channel transform
    tcn_conv_channels: tuple[int, ...] = (64, 128, 128)
    tcn_conv_kernels: tuple[int, ...] = (9, 5, 5)
    tcn_conv_strides: tuple[int, ...] = (2, 1, 1)
    tcn_head_hidden: int = 128

    # GRU-specific
    gru_layers: int = 1
    gru_hidden: int = 128

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

    # Logging
    log_dir_root: str = "logs/rsl_rl/student_policy"
    logger: str = "wandb"           # "wandb" or "tensorboard"
    wandb_project: str = "full_dof_trpo_student"

    # Environment
    task: str = "Isaac-FullDOF-TRPO-v0"
    device: str = "cuda:0"          # overridden by CUDA_VISIBLE_DEVICES at launch
