#!/usr/bin/env bash
# Run remaining student evals sequentially on GPU 1.
# Called after TCN eval_dr completes.
set -e

# Uses isaaclab's runtime (./isaaclab.sh) but the eval scripts now live in the
# constrained-albc repo (post 2026-05-25 repo 3-split).
ALBC=/workspace/constrained-albc
cd /workspace/isaaclab
# Teacher / student checkpoints are injected by the caller (no hardcoded run).
# Export TEACHER / TCN_CKPT / GRU_CKPT before invoking, e.g.:
#   TEACHER=logs/.../<teacher_run>/model_4999.pt \
#   TCN_CKPT=logs/.../<tcn_run>/models/student_999.pt \
#   GRU_CKPT=logs/.../<gru_run>/models/student_999.pt ./run_student_evals.sh
TEACHER=${TEACHER:?set TEACHER to the teacher checkpoint path}
TCN_CKPT=${TCN_CKPT:?set TCN_CKPT to the student-TCN checkpoint path}
GRU_CKPT=${GRU_CKPT:?set GRU_CKPT to the student-GRU checkpoint path}
STAMP=$(date +%Y%m%d_%H%M%S)

run() {
    local name="$1"; shift
    local log=/workspace/isaaclab/logs/archive/launch_scripts/${name}_${STAMP}.log
    echo "[${name} $(date)] START" | tee "$log"
    CUDA_VISIBLE_DEVICES=1 "$@" 2>&1 | tee -a "$log"
    local rc=${PIPESTATUS[0]}
    echo "[${name} $(date)] END rc=$rc" | tee -a "$log"
    [ $rc -ne 0 ] && { echo "[${name}] FAILED"; exit $rc; }
}

# 1. TCN switching (zero-cmd DR re-sample)
run eval_tcn_switching ./isaaclab.sh -p "$ALBC/constrained_albc/analysis/eval_dr.py" segmented \
    --teacher_ckpt "$TEACHER" --student_ckpt "$TCN_CKPT" \
    --encoder_type tcn --num_envs 64 --headless

# 2. GRU command-tracking DR sweep
run eval_gru_dr ./isaaclab.sh -p "$ALBC/constrained_albc/analysis/eval_student.py" dr \
    --teacher_ckpt "$TEACHER" --student_ckpt "$GRU_CKPT" \
    --encoder_type gru --num_envs 64 --headless

# 3. GRU switching
run eval_gru_switching ./isaaclab.sh -p "$ALBC/constrained_albc/analysis/eval_dr.py" segmented \
    --teacher_ckpt "$TEACHER" --student_ckpt "$GRU_CKPT" \
    --encoder_type gru --num_envs 64 --headless

echo "[evals $(date)] ALL DONE"
