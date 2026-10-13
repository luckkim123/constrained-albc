#!/usr/bin/env bash
# retrain-rollpitch round 1 teacher launcher.
# Program: .hq/community/programs/retrain-rollpitch-2026-09-19/PLAN.md
# Operator authority: 2026-09-19 11:51 KST ("... 학습은 iter 5000으로 제한하고 ...
#   yaw 제어는 해도 좋고 안해도 좋다 ... 제일 중요한것은 roll, pitch 제어 성능이야.
#   최대한 효율적으로 gpu0, 1, dgx 까지 모두 가능한 재원은 전부 사용하도록 하고")
# REQUIRES RR_ARMED=1.
#
# Arms (all keep p6's overrides; deltas are listed per arm):
#   A  rponly       yaw.k=0, bias_weights=[1.5,1,0]            (main candidate)
#   D  rponly-slew  A + delta_scale=0.04  (0.04*50Hz = 2.0 rad/s < measured 2.40)
#   C  rponly-dr    A + control_delay_strength_range=[0.0,1.0] (DORAEMON regains delay)
#   P  probe        A + doraemon.enable=False                  (measures the lb percentile)
#   S  smoke        A, 20 iters, for env.yaml verification only
set -euo pipefail
cd /workspace/worktrees/retrain-rollpitch
[ "$(git rev-parse --short HEAD)" = "1d90a4e" ] || { echo "HEAD != 1d90a4e"; exit 2; }
[ "$(git branch --show-current)" = "retrain/rollpitch-r1" ] || { echo "wrong branch"; exit 2; }

ARM="${RR_ARM:?set RR_ARM=A|C|D|P|S}"
GPU="${RR_GPU:-0}"
LB="${RR_LB:--20.0}"           # A/C/D: set from the probe percentile. P/S: placeholder.
case "$ARM" in
  A) ITERS="${RR_ITERS:-5000}"; NAME="${RR_NAME:-rr_A_rponly_s30}";      EXTRA=() ;;
  D) ITERS="${RR_ITERS:-5000}"; NAME="${RR_NAME:-rr_D_rponly_slew_s30}"; EXTRA=( env.delta_scale=0.04 ) ;;
  C) ITERS="${RR_ITERS:-5000}"; NAME="${RR_NAME:-rr_C_rponly_dr_s30}";   EXTRA=( "env.randomization.control_delay_strength_range=[0.0,1.0]" ) ;;
  P) ITERS="${RR_ITERS:-300}";  NAME="${RR_NAME:-rr_P_probe_s30}";       EXTRA=( env.doraemon.enable=False ) ;;
  PD) ITERS="${RR_ITERS:-300}"; NAME="${RR_NAME:-rr_PD_probe_slew_s30}"; EXTRA=( env.doraemon.enable=False env.delta_scale=0.04 ) ;;
  S) ITERS="${RR_ITERS:-20}";   NAME="${RR_NAME:-rr_S_smoke_s30}";       EXTRA=() ;;
  *) echo "unknown RR_ARM=$ARM"; exit 2 ;;
esac

CMD=(/workspace/isaaclab/isaaclab.sh -p scripts/train.py
  --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0
  --num_envs 4096 --max_iterations "$ITERS" --headless --seed 30
  --run_group retrain_rollpitch_r1
  "env.randomization.control_delay_steps=[0,13]"
  "env.randomization.obs_delay_steps=[0,5]"
  "env.fault.thruster_always_dead=[0,3]" env.disturbance.enable=True
  "env.randomization.control_delay_strength_range=[0.98,1.0]"
  "env.randomization.inertia_scale=[2.0,5.4]"
  env.reward.yaw.k=0.0
  "env.reward.bias_weights=[1.5,1.0,0.0]"
  env.doraemon.performance_lb="$LB"
  "${EXTRA[@]}"
  agent.run_name="$NAME")

if [ "${RR_ARMED:-0}" != "1" ]; then
  echo "DRY (set RR_ARMED=1 to launch):"; printf " %q" "${CMD[@]}"; echo; exit 0
fi
unset DISPLAY                     # teardown segfault guard (rc=1 on a completed run)
export TERM=xterm
export CUDA_VISIBLE_DEVICES="$GPU"
"${CMD[@]}" > "/workspace/${NAME}.log" 2>&1
