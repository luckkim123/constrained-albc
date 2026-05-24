#!/usr/bin/env bash
# Run TCN then GRU sequentially on GPU 1.
# If TCN fails, GRU does not start.

# The child launchers are siblings of this script in constrained-albc/scripts/
# (post 2026-05-25 repo 3-split). Resolve relative to this script's own dir.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[sequential $(date)] START — TCN first, then GRU"

"$SCRIPT_DIR/launch_student_tcn.sh"
TCN_RC=$?
echo "[sequential $(date)] TCN finished rc=${TCN_RC}"

if [ "$TCN_RC" -ne 0 ]; then
    echo "[sequential $(date)] ABORT — TCN failed (rc=${TCN_RC}), GRU not started."
    exit "$TCN_RC"
fi

"$SCRIPT_DIR/launch_student_gru.sh"
GRU_RC=$?
echo "[sequential $(date)] GRU finished rc=${GRU_RC}"

echo "[sequential $(date)] DONE TCN=${TCN_RC} GRU=${GRU_RC}"
exit "$GRU_RC"
