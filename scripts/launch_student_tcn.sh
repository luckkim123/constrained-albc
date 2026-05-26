#!/usr/bin/env bash
# Student-TCN: train encoder via BC from a teacher checkpoint on GPU 1.
# Sequential with launch_student_gru.sh (runs AFTER TCN completes).
set -e

# Uses isaaclab's runtime (./isaaclab.sh) but the train_student.py script now lives
# in the constrained-albc repo (post 2026-05-25 repo 3-split).
ALBC=/workspace/constrained-albc
cd /workspace/isaaclab

# Teacher run dir is injected by the caller (no hardcoded run -- the teacher is
# whichever trained checkpoint you distil from). Path relative to /workspace/isaaclab.
TEACHER_RUN_DIR=${TEACHER_RUN_DIR:?set TEACHER_RUN_DIR to the teacher run directory}

RUN_NAME="student_tcn"
STAMP=$(date +%Y%m%d_%H%M%S)
STDOUT_LOG="/workspace/isaaclab/logs/archive/launch_scripts/${RUN_NAME}_${STAMP}.log"
mkdir -p "$(dirname "$STDOUT_LOG")"

echo "[${RUN_NAME} $(date)] START" | tee -a "$STDOUT_LOG"
CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p "$ALBC/scripts/train_student.py" \
    --encoder_type tcn \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --teacher_run_dir "$TEACHER_RUN_DIR" \
    --teacher_checkpoint model_4999.pt \
    --num_envs 2048 \
    --max_iterations 1000 \
    --n_steps_per_rollout 24 \
    --n_epochs 5 \
    --minibatch_size 8192 \
    --lr 5e-4 \
    --lambda_latent 1.0 \
    --save_interval 100 \
    --seed 42 \
    --logger wandb \
    --wandb_project constrained_albc_student \
    --run_name "$RUN_NAME" \
    --headless 2>&1 | tee -a "$STDOUT_LOG"
RC=${PIPESTATUS[0]}
echo "[${RUN_NAME} $(date)] END rc=${RC}" | tee -a "$STDOUT_LOG"
exit "$RC"
