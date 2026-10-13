#!/bin/bash
# paper-ablation-5000 -- workstation n1_lagrangian (seed 30) on ksm-ubuntu GPU0.
# Operator approval 2026-09-14 (KST): "그렇게 해줘. ksm-ubuntu 사용해도 괜찮고."
# Pairs with the workstation reference trpo_r3a_ref_full_260912_145151 (same machine, seed, anchor, marinelab pin),
# so n1 - ref can be read on a second machine beside the DGX pair (container PLAN Update 2026-09-14 14시 05분).
# Same arm as the commented-out row in launch_chain_r3a_split.sh (md5 85c8a9b8) and the pending record
# r3a5000_n1_lagrangian_s30, with one deliberate difference: the trainer runs from a scratch cwd instead of the
# anchor worktree, so nothing is written into /workspace/constrained-albc-r3a (train.py:216 roots logs/ at cwd and
# Hydra writes outputs/ at cwd). $RUNCWD/logs -> /workspace/constrained-albc/logs (gitignored). The scratch cwd holds
# no python package, so it cannot shadow constrained_albc/marinelab (the main repo root would).
# As-run gate: cfgdiff.py (semantic; tensors by value) against the DGX n1 run's params must report identical,
# ignoring seed/run_name/log_dir and the DGX path prefixes. Measured 2026-09-14: DGX ref vs workstation ref = identical.
# Launch: nohup setsid bash <this> > <LOGDIR>/ws_n1_launcher.out 2>&1 < /dev/null &
# Plant ledger decision/197 + decision/209: same pre-<item> state as every table row (nothing applied, by design).
set -u
W=/workspace/constrained-albc-r3a
ML=/workspace/marinelab-r3a
H=3791441873bc0346b534aff168d785a8dac4eddc
MLH=8cc84a54540f9fd06a835efc3f33d117dd8b2a84
TAG=n1_lagrangian; SEED=30
TASK=Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0; VARIANT=section5; GROUP=paper_ablation_r3a
P=/workspace/constrained-albc/.hq/community/programs/paper-ablation-5000
RUNCWD=/workspace/constrained-albc/.hq/work/paper_ablation_r3a/ws_train_cwd
LOGS=/workspace/constrained-albc/logs
DGXN1=$LOGS/rsl_rl/albc_ablation/paper_ablation_r3a_dgx/trpo_dgx_n1_lagrangian_260913_065642
LOGDIR=$P/launch-logs-r3a
alog="$LOGDIR/ws_$TAG.log"; CHAIN="$LOGDIR/ws_n1_chain.log"
PY=/workspace/isaaclab/_isaac_sim/python.sh
say(){ echo "[$(date +%FT%T%z)] $*" | tee -a "$CHAIN"; }
FATAL_RE="Traceback|:[[:space:]]+[-+]?(nan|inf)[[:space:]]*$"
fatal_in(){ sed 's/\x1b\[[0-9;]*[A-Za-z]//g; s/\r/\n/g' "$1" | grep -qiE "$FATAL_RE"; }
stop(){ local i; kill -TERM -- -"$1" 2>/dev/null
  for i in $(seq 1 9); do kill -0 "$1" 2>/dev/null || break; sleep 10; done
  kill -KILL -- -"$1" 2>/dev/null; wait "$1"; }

mkdir -p "$LOGDIR" "$RUNCWD"
[ -e "$RUNCWD/logs" ] || ln -s "$LOGS" "$RUNCWD/logs"
[ "$(readlink "$RUNCWD/logs")" = "$LOGS" ] || { say "FATAL $RUNCWD/logs is not a symlink to $LOGS"; exit 2; }
cd "$RUNCWD" || exit 2
export PYTHONPATH="$W:$ML${PYTHONPATH:+:$PYTHONPATH}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TERM=xterm CUDA_VISIBLE_DEVICES=0

for rd in $(find logs/rsl_rl/ -mindepth 3 -maxdepth 3 -type d -path "*/$GROUP/*_r3a_${TAG}_*" 2>/dev/null); do
  [ -f "$rd/.chain_ok" ] && { say "SKIP ws $TAG (already complete: $rd)"; exit 0; }
done
[ "$(git -C "$W" rev-parse HEAD)" = "$H" ] && [ "$(git -C "$ML" rev-parse HEAD)" = "$MLH" ] || { say "FATAL heads"; exit 2; }
[ -z "$(git -C "$W" status --porcelain)" ] && [ -z "$(git -C "$ML" status --porcelain)" ] || { say "FATAL dirty tree"; exit 2; }
origins=$("$PY" -c "import importlib.util as u; print(u.find_spec('constrained_albc').origin, u.find_spec('marinelab').origin)" 2>/dev/null | tail -1)
case "$origins" in "$W/"*" $ML/"*) ;; *) say "FATAL import origins: $origins"; exit 2;; esac
[ -f "$DGXN1/params/env.yaml" ] && [ -f "$DGXN1/params/agent.yaml" ] || { say "FATAL DGX n1 params missing"; exit 2; }
[ -f "$P/cfgdiff.py" ] || { say "FATAL $P/cfgdiff.py missing"; exit 2; }
for i in $(seq 1 90); do
  [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0)" -lt 1500 ] && break
  [ "$i" = 90 ] && { say "FATAL GPU0 busy for 15 min"; exit 2; }; sleep 10
done

say "START ws $TAG task=$TASK variant=$VARIANT seed=$SEED HEAD=$H marinelab=$MLH cwd=$RUNCWD origins=$origins"
touch -d "2 seconds ago" "$alog.start"
timeout -k 120 16h /workspace/isaaclab/isaaclab.sh -p "$W/scripts/train.py" --task "$TASK" --num_envs 4096 --max_iterations 5000 \
  --headless --seed $SEED --run_group "$GROUP" agent.run_name="r3a_$TAG" > "$alog" 2>&1 &
pid=$!; rd=""
for i in $(seq 1 60); do
  rd=$(find logs/rsl_rl/ -mindepth 3 -maxdepth 3 -type d -path "*/$GROUP/*_r3a_${TAG}_*" -newer "$alog.start" 2>/dev/null | head -1)
  [ -n "$rd" ] && [ -f "$rd/params/env.yaml" ] && [ -f "$rd/params/agent.yaml" ] && break
  kill -0 $pid 2>/dev/null || break; sleep 10
done
if [ -z "$rd" ] || [ ! -f "$rd/params/env.yaml" ]; then say "FAIL ws $TAG no params/env.yaml"; stop $pid; exit 1; fi
if ! python3 "$W/tools/check_simtoreal_params.py" --variant "$VARIANT" "$rd" >> "$alog.gate" 2>&1; then
  say "GATE FAIL ws $TAG ($VARIANT) -> kill; see $alog.gate"; stop $pid; exit 1
fi
if [ "$(grep -cE '^[[:space:]]*velocity_limit_sim:' "$rd/params/env.yaml")" != 1 ] || ! grep -qE '^[[:space:]]*velocity_limit_sim: 3\.1[[:space:]]*$' "$rd/params/env.yaml"; then
  say "GATE FAIL ws $TAG velocity_limit_sim is not exactly one 3.1 -> kill"; stop $pid; exit 1
fi
grep -qx "seed: $SEED" "$rd/params/agent.yaml" && grep -qx "seed: $SEED" "$rd/params/env.yaml" || { say "GATE FAIL ws $TAG seed $SEED not in params -> kill"; stop $pid; exit 1; }
if ! "$PY" "$P/cfgdiff.py" "$DGXN1/params/env.yaml" "$rd/params/env.yaml" > "$alog.envdiff" 2>&1 \
   || ! "$PY" "$P/cfgdiff.py" "$DGXN1/params/agent.yaml" "$rd/params/agent.yaml" > "$alog.agentdiff" 2>&1; then
  say "GATE FAIL ws $TAG params differ from DGX n1 (cfgdiff; see $alog.envdiff, $alog.agentdiff) -> kill"; stop $pid; exit 1
fi
say "GATE ok ws $TAG run=$rd (cfgdiff identical to DGX n1 except seed/run_name/log_dir/path prefixes)"
while kill -0 $pid 2>/dev/null; do
  if fatal_in "$alog"; then say "NaN/Traceback ws $TAG at $(grep -c 'Learning iteration' "$alog") it -> kill"; stop $pid; exit 1; fi
  if [ $(( $(date +%s) - $(stat -c %Y "$alog") )) -gt 1200 ]; then say "STALL ws $TAG (log idle 20 min) -> kill"; stop $pid; exit 1; fi
  sleep 60
done
wait $pid; rc=$?; kill -KILL -- -$pid 2>/dev/null
ok=0; why=""
if [ "$rc" != 0 ]; then why="rc $rc"
elif fatal_in "$alog"; then why="fatal line after the last poll"
elif [ ! -s "$rd/model_4999.pt" ]; then why="model_4999.pt missing or empty"
elif ! "$PY" -c "import sys, torch; torch.load(sys.argv[1], map_location='cpu', weights_only=False)" "$rd/model_4999.pt" > "$alog.ckptcheck" 2>&1; then why="model_4999.pt does not load (see $alog.ckptcheck)"
else ok=1; printf 'tag=%s\ntask=%s\nvariant=%s\nalbc_head=%s\nmarinelab_head=%s\nseed=%s max_iterations=5000 num_envs=4096 group=%s\nmachine=ksm-ubuntu-gpu0\ncwd=%s\npairs_with=trpo_r3a_ref_full_260912_145151\nfinished=%s\n' \
       "$TAG" "$TASK" "$VARIANT" "$(git -C "$W" rev-parse HEAD)" "$(git -C "$ML" rev-parse HEAD)" "$SEED" "$GROUP" "$RUNCWD" "$(date +%FT%T%z)" > "$rd/.chain_ok"
fi
say "END ws $TAG rc=$rc ok=$ok${why:+ ($why)} run=$rd"
