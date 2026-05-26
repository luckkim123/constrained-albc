#!/usr/bin/env bash
# Run remaining student evals sequentially on GPU 1.
# Called after TCN eval_dr completes.
set -e

# Uses isaaclab's runtime (./isaaclab.sh) but the eval scripts now live in the
# constrained-albc repo (post 2026-05-25 repo 3-split).
ALBC=/workspace/constrained-albc

# Teacher / student checkpoints are injected by the caller (no hardcoded run).
# Export TEACHER / TCN_CKPT / GRU_CKPT before invoking, e.g.:
#   TEACHER=logs/.../<teacher_run>/model_4999.pt \
#   TCN_CKPT=logs/.../<tcn_run>/models/student_999.pt \
#   GRU_CKPT=logs/.../<gru_run>/models/student_999.pt ./run_student_evals.sh
TEACHER=${TEACHER:?set TEACHER to the teacher checkpoint path}
TCN_CKPT=${TCN_CKPT:?set TCN_CKPT to the student-TCN checkpoint path}
GRU_CKPT=${GRU_CKPT:?set GRU_CKPT to the student-GRU checkpoint path}

# Resolve paths to absolute BEFORE the `cd` below. The eval scripts run from
# /workspace/isaaclab, so a relative path given by a caller sitting in
# constrained-albc (e.g. experiments/<run>/...) would not be found post-cd.
# `realpath -m` normalizes against the current (caller's) cwd without requiring
# the path to exist yet; we then assert existence so a typo fails loudly here.
TEACHER=$(realpath -m "$TEACHER")
TCN_CKPT=$(realpath -m "$TCN_CKPT")
GRU_CKPT=$(realpath -m "$GRU_CKPT")
for ckpt in "$TEACHER" "$TCN_CKPT" "$GRU_CKPT"; do
    [ -f "$ckpt" ] || { echo "ERROR: checkpoint not found: $ckpt" >&2; exit 1; }
done

cd /workspace/isaaclab
STAMP=$(date +%Y%m%d_%H%M%S)

run() {
    local name="$1"; shift
    local log=/workspace/isaaclab/logs/archive/launch_scripts/${name}_${STAMP}.log
    echo "[${name} $(date)] START" | tee "$log"
    CUDA_VISIBLE_DEVICES=1 "$@" 2>&1 | tee -a "$log"
    local rc=${PIPESTATUS[0]}
    echo "[${name} $(date)] END rc=$rc" | tee -a "$log"
    # NOTE: under `set -e`, a trailing `[ $rc -ne 0 ] && {...}` makes the function's
    # exit status 1 whenever rc==0 (the test is false), which set -e treats as the
    # function failing -- aborting the whole script after the first successful stage.
    # Use an explicit if so a successful stage returns 0 and the next stage runs.
    if [ "$rc" -ne 0 ]; then
        echo "[${name}] FAILED"
        exit "$rc"
    fi
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
