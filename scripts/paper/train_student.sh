#!/usr/bin/env bash
# Paper student distillation (run trpo_sd_rr_ft_ftp7200_s30_260927_192341, checkpoint student_999).
#
# Distills the GRU student from the paper teacher (model_7200 of the run produced by
# scripts/paper/train_teacher.sh) on the same plant the teacher was fine-tuned on. The
# DAgger schedule hands control from the teacher to the student: the probability of
# executing the teacher action anneals 1 -> 0 over the first 600 iterations, and each env
# executes either the teacher or the student action (mix=select).
# The arguments and Hydra overrides below are the complete set the paper student ran with.
#
# Usage (from anywhere; nothing outside the repo is hardcoded):
#   TEACHER_CKPT=/path/to/teacher_run/model_7200.pt OUT_DIR=/path/to/out \
#   ISAACLAB_SH=/path/to/isaaclab/isaaclab.sh scripts/paper/train_student.sh
# Optional: SEED (30), RUN_NAME (sd_rr_ft_ftp7200_s30), GPU (0).
# Prints the command and exits unless ARMED=1.
set -euo pipefail

: "${TEACHER_CKPT:?TEACHER_CKPT must point at the teacher checkpoint (model_7200.pt)}"
: "${OUT_DIR:?OUT_DIR must be set (logs/ is written under it)}"
: "${ISAACLAB_SH:?ISAACLAB_SH must point at isaaclab.sh}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEACHER_RUN_DIR="$(cd "$(dirname "$TEACHER_CKPT")" && pwd)"
CKPT_NAME="$(basename "$TEACHER_CKPT")"
[ -f "$TEACHER_RUN_DIR/$CKPT_NAME" ] || { echo "missing $TEACHER_CKPT"; exit 2; }

CMD=("$ISAACLAB_SH" -p "$REPO/scripts/train_student.py"
  --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0
  --encoder_type gru --gru_hidden 128 --gru_head_hidden 64
  --teacher_run_dir "$TEACHER_RUN_DIR" --teacher_checkpoint "$CKPT_NAME"
  --num_envs 2048 --max_iterations 1000 --n_steps_per_rollout 24 --n_epochs 5 --minibatch_size 8192
  --lr 0.0005 --lambda_latent 1.0 --save_interval 100
  --dagger_beta_start 1.0 --dagger_beta_end 0.0 --dagger_anneal_iters 600 --dagger_mix select
  --seed "${SEED:-30}" --logger tensorboard --run_group retrain_rollpitch_r1
  --run_name "${RUN_NAME:-sd_rr_ft_ftp7200_s30}" --headless
  "env.randomization.control_delay_steps=[7,13]"
  "env.fault.thruster_always_dead=[0,3]" env.disturbance.enable=True
  "env.randomization.obs_delay_steps=[0,5]"
  "env.randomization.inertia_scale=[3.6,6.2]"
  "env.randomization.control_delay_strength_range=[0.60,0.70]"
  env.reward.yaw.k=0.0
  "env.reward.bias_weights=[1.5,1.0,0.0]"
  env.delta_scale=0.04
  env.reward.att_roll_weight=1.0
  "env.reward.k_sstv=-5.0"
  env.doraemon.performance_lb=-20.0)

if [ "${ARMED:-0}" != "1" ]; then
  echo "DRY (set ARMED=1 to launch, cwd = $OUT_DIR):"; printf " %q" "${CMD[@]}"; echo; exit 0
fi
mkdir -p "$OUT_DIR"
cd "$OUT_DIR"
CUDA_VISIBLE_DEVICES="${GPU:-0}" "${CMD[@]}"
