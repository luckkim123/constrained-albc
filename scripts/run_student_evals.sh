#!/usr/bin/env bash
# Run remaining student evals sequentially on GPU 1.
# Called after TCN eval_dr completes.
set -e

cd /workspace/isaaclab
TEACHER=logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/model_4999.pt
TCN_CKPT=logs/rsl_rl/student_policy/2026-04-21_04-33-51_student_tcn/models/student_999.pt
GRU_CKPT=logs/rsl_rl/student_policy/2026-04-21_05-13-32_student_gru/models/student_999.pt
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
run eval_tcn_switching ./isaaclab.sh -p scripts/analysis/eval_dr.py segmented \
    --teacher_ckpt "$TEACHER" --student_ckpt "$TCN_CKPT" \
    --encoder_type tcn --num_envs 64 --headless

# 2. GRU command-tracking DR sweep
run eval_gru_dr ./isaaclab.sh -p scripts/analysis/eval_student.py dr \
    --teacher_ckpt "$TEACHER" --student_ckpt "$GRU_CKPT" \
    --encoder_type gru --num_envs 64 --headless

# 3. GRU switching
run eval_gru_switching ./isaaclab.sh -p scripts/analysis/eval_dr.py segmented \
    --teacher_ckpt "$TEACHER" --student_ckpt "$GRU_CKPT" \
    --encoder_type gru --num_envs 64 --headless

echo "[evals $(date)] ALL DONE"
