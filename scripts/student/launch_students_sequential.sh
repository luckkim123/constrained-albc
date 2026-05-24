#!/usr/bin/env bash
# Run TCN then GRU sequentially on GPU 1.
# If TCN fails, GRU does not start.

cd /workspace/isaaclab

echo "[sequential $(date)] START — TCN first, then GRU"

./scripts/student/launch_student_tcn.sh
TCN_RC=$?
echo "[sequential $(date)] TCN finished rc=${TCN_RC}"

if [ "$TCN_RC" -ne 0 ]; then
    echo "[sequential $(date)] ABORT — TCN failed (rc=${TCN_RC}), GRU not started."
    exit "$TCN_RC"
fi

./scripts/student/launch_student_gru.sh
GRU_RC=$?
echo "[sequential $(date)] GRU finished rc=${GRU_RC}"

echo "[sequential $(date)] DONE TCN=${TCN_RC} GRU=${GRU_RC}"
exit "$GRU_RC"
