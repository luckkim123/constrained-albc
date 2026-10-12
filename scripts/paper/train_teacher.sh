#!/usr/bin/env bash
# Paper teacher fine-tune (run trpo_rr_FTP_s30_260927_182609, checkpoint model_7200).
#
# Resumes the starting teacher checkpoint (model_6400 plus its doraemon_state.pt, from an
# earlier training chain that is not part of this release) on a plant moved toward the
# tank, for 801 iterations (6400 -> 7200):
#   action delay 7-11 steps = control_delay_steps [7,13] x strength [0.60,0.70]
#                             (hi stays 13 so the privileged delay observation keeps its scale)
#   inertia_scale [3.6,6.2]
#   DORAEMON frozen (doraemon.step_interval=1000000)
# The Hydra overrides below are the complete set the paper teacher ran with.
#
# Usage (from anywhere; nothing outside the repo is hardcoded):
#   RESUME_CKPT=/path/to/model_6400.pt OUT_DIR=/path/to/out \
#   ISAACLAB_SH=/path/to/isaaclab/isaaclab.sh scripts/paper/train_teacher.sh
# Optional: NENV (4096), ITERS (801), SEED (30), RUN_NAME (rr_FTP_s30), GPU (0).
# Prints the command and exits unless ARMED=1.
set -euo pipefail

: "${RESUME_CKPT:?RESUME_CKPT must point at the starting model_6400.pt}"
: "${OUT_DIR:?OUT_DIR must be set (logs/ is written under it)}"
: "${ISAACLAB_SH:?ISAACLAB_SH must point at isaaclab.sh}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RESUME_DIR="$(cd "$(dirname "$RESUME_CKPT")" && pwd)"
CKPT_NAME="$(basename "$RESUME_CKPT")"
[ -f "$RESUME_DIR/$CKPT_NAME" ] || { echo "missing $RESUME_CKPT"; exit 2; }
[ -f "$RESUME_DIR/doraemon_state.pt" ] || { echo "missing doraemon_state.pt next to $CKPT_NAME"; exit 2; }

RESUME_RUN=resume_src

CMD=("$ISAACLAB_SH" -p "$REPO/scripts/train.py"
  --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0
  --num_envs "${NENV:-4096}" --max_iterations "${ITERS:-801}" --headless --seed "${SEED:-30}"
  --run_group retrain_rollpitch_r1
  --resume --load_run "$RESUME_RUN" --checkpoint "$CKPT_NAME"
  "env.randomization.control_delay_steps=[7,13]"
  "env.randomization.obs_delay_steps=[0,5]"
  "env.fault.thruster_always_dead=[0,3]" env.disturbance.enable=True
  "env.randomization.control_delay_strength_range=[0.60,0.70]"
  "env.randomization.inertia_scale=[3.6,6.2]"
  env.reward.yaw.k=0.0
  "env.reward.bias_weights=[1.5,1.0,0.0]"
  env.doraemon.performance_lb=-20.0
  env.doraemon.step_interval=1000000
  env.delta_scale=0.04
  env.reward.att_roll_weight=1.0
  "env.reward.k_sstv=-5.0"
  agent.run_name="${RUN_NAME:-rr_FTP_s30}")

if [ "${ARMED:-0}" != "1" ]; then
  echo "DRY (set ARMED=1 to launch, cwd = $OUT_DIR):"; printf " %q" "${CMD[@]}"; echo; exit 0
fi
# train.py resumes from logs/rsl_rl/<experiment>/<load_run>/<checkpoint> relative to the cwd,
# and the DORAEMON runner reads doraemon_state.pt from the same directory.
SRC="$OUT_DIR/logs/rsl_rl/albc_trpo_teacher/$RESUME_RUN"
mkdir -p "$SRC"
ln -sf "$RESUME_DIR/$CKPT_NAME" "$SRC/$CKPT_NAME"
ln -sf "$RESUME_DIR/doraemon_state.pt" "$SRC/doraemon_state.pt"

cd "$OUT_DIR"
CUDA_VISIBLE_DEVICES="${GPU:-0}" "${CMD[@]}"
