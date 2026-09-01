#!/bin/bash
# paper-ablation-5000 sequential launch chain (5 arms).
# NOT set -e: each arm's failure is recorded and the chain continues to the next arm.
cd /workspace/constrained-albc || exit 1

LOGDIR=.omx/programs/paper-ablation-5000/launch-logs
mkdir -p "$LOGDIR"
CHAINLOG="$LOGDIR/chain.log"

run_arm() {
  local tag="$1" task="$2" run_name="$3"
  echo "=== [$(date -u +%FT%TZ)] START $tag (task=$task run_name=$run_name) ===" | tee -a "$CHAINLOG"
  TERM=xterm PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 /workspace/isaaclab/isaaclab.sh -p scripts/train.py \
    --task "$task" \
    --num_envs 4096 --max_iterations 5000 --headless --seed 30 \
    --run_group paper_ablation_5000 \
    --logger wandb --log_project_name paper_ablation_5000 \
    env.fault.enable=True \
    agent.run_name="$run_name" \
    >> "$LOGDIR/${tag}.log" 2>&1
  local rc=$?
  echo "=== [$(date -u +%FT%TZ)] END $tag rc=$rc ===" | tee -a "$CHAINLOG"
}

run_arm full_method   Isaac-ConstrainedALBC-TRPO-v0                 paper_abl_full
run_arm no_encoder    Isaac-ConstrainedALBC-NoEncoder-v0            paper_abl_noenc
run_arm no_constraint Isaac-ConstrainedALBC-TRPO-NoIPO-v0           paper_abl_noconstr
run_arm ppo           Isaac-ConstrainedALBC-PPO-v0                  paper_abl_ppo
run_arm no_both       Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0 paper_abl_nobo

echo "=== [$(date -u +%FT%TZ)] CHAIN COMPLETE ===" | tee -a "$CHAINLOG"
