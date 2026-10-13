#!/bin/bash
# paper-ablation-5000 — R3a-anchor comparison chain, GPU0, sequential, 1 seed (s30), 5000 it, 4096 envs.
# Operator decisions 2026-09-11 KST: anchor R3a lineage, 1 seed + tail claim, reference arm from scratch,
# N6a/N6b in the weekend queue (N6b = nominal-point plant incl. buoy scales 1.0). PLAN §8-R-2 / §8-R-9.
# 2026-09-12 review: reference arm first (it is every row's denominator and the only arm with an expected
# trajectory -- p3b, same seed and config). 2026-09-12 codex review (ground 4): an arm is complete only when this
# chain wrote <run>/.chain_ok (rc 0, final fatal scan clean, model_4999.pt loads); only those are skipped on a re-run
# and only those are graded by exam_chain_r3a.sh. Source checks run once at start even if every arm is skipped.
# Fire only after the pending-launch artifacts for every run-id below are approved (gates 264/352/441/444).
# NOT set -e: a failed arm is recorded and the chain moves on.
W=/workspace/constrained-albc-r3a          # constrained-albc worktree, branch anchor/r3a-5000
ML=/workspace/marinelab-r3a                # marinelab worktree @ 8cc84a5 (pre 09-07 f70f752 velocity 2.40 / bcfb01a)
EXPECT_HEAD="${EXPECT_HEAD:?set EXPECT_HEAD to the anchor/r3a-5000 commit}"
EXPECT_ML_HEAD=8cc84a54540f9fd06a835efc3f33d117dd8b2a84
GROUP=paper_ablation_r3a
LOGDIR=/workspace/constrained-albc/.hq/community/programs/paper-ablation-5000/launch-logs-r3a
mkdir -p "$LOGDIR"; CHAIN="$LOGDIR/chain.log"
cd "$W" || exit 1
export PYTHONPATH="$W:$ML${PYTHONPATH:+:$PYTHONPATH}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TERM=xterm CUDA_VISIBLE_DEVICES=0
# A metric line ending in a signed nan/inf ("Mean value_function loss: nan"), matched after stripping ANSI escapes and
# splitting carriage returns. NOT a bare nan token: healthy logs carry DORAEMON lines "Entropy opt rejected ... (neg_H
# 44.3 -> nan, KL=229.6)" (doraemon.py:666). Measured 2026-09-12: 0 hits on five healthy logs (38,275 iterations:
# p5_teacher, p3, p3b, p3b_resume, p3c_extend), 52 on the broken N6b smoke; the only mid-line nan in them is DORAEMON.
FATAL_RE="Traceback|:[[:space:]]+[-+]?(nan|inf)[[:space:]]*$"
fatal_in(){ sed 's/\x1b\[[0-9;]*[A-Za-z]//g; s/\r/\n/g' "$1" | grep -qiE "$FATAL_RE"; }
CHAIN_ID=$(date +%Y%m%dT%H%M%S)-$$
say(){ echo "[$(date +%FT%T%z)] $*" | tee -a "$CHAIN"; }

source_checks(){
  local h mh d md origins
  h=$(git -C "$W" rev-parse HEAD); mh=$(git -C "$ML" rev-parse HEAD)
  d=$(git -C "$W" status --porcelain | wc -l)      # whole tree: both roots are on PYTHONPATH
  md=$(git -C "$ML" status --porcelain | wc -l)
  origins=$(/workspace/isaaclab/_isaac_sim/python.sh -c "import importlib.util as u; print(u.find_spec('constrained_albc').origin, u.find_spec('marinelab').origin)" 2>/dev/null | tail -1)
  [ "$h" = "$(git -C "$W" rev-parse --verify "$EXPECT_HEAD^{commit}")" ] || { say "FATAL HEAD $h != $EXPECT_HEAD"; exit 2; }
  [ "$mh" = "$(git -C "$ML" rev-parse --verify "$EXPECT_ML_HEAD^{commit}")" ] || { say "FATAL marinelab HEAD $mh != $EXPECT_ML_HEAD"; exit 2; }
  [ "$d" = 0 ] && [ "$md" = 0 ] || { say "FATAL dirty tree (albc $d, marinelab $md; finding/407)"; exit 2; }
  case "$origins" in "$W/"*" $ML/"*) ;; *) say "FATAL import origins: $origins"; exit 2;; esac
}

preflight(){
  local i
  source_checks
  for i in $(seq 1 90); do   # last: GPU0 must be idle (< 1500 MiB) -- up to 15 min, else stop the chain
    [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0)" -lt 1500 ] && return 0
    sleep 10
  done
  say "FATAL GPU0 busy for 15 min"; exit 2
}

stop(){   # timeout leads its own process group, so the python grandchild dies too; TERM, then KILL after 90 s
  local i; kill -TERM -- -"$1" 2>/dev/null
  for i in $(seq 1 9); do kill -0 "$1" 2>/dev/null || break; sleep 10; done
  kill -KILL -- -"$1" 2>/dev/null; wait "$1"
}

run_arm(){
  local tag="$1" task="$2" variant="$3" alog="$LOGDIR/$1.log" pid rd="" i
  for rd in $(find logs/rsl_rl/ -mindepth 3 -maxdepth 3 -type d -path "*/$GROUP/*_r3a_${tag}_*" 2>/dev/null); do
    [ -f "$rd/.chain_ok" ] && { say "SKIP $tag (already complete: $rd)"; return; }
  done
  rd=""
  preflight
  say "START $tag task=$task variant=$variant HEAD=$EXPECT_HEAD marinelab=$EXPECT_ML_HEAD"
  touch -d "2 seconds ago" "$alog.start"   # -newer is strict and fs timestamps are coarse
  timeout -k 120 16h /workspace/isaaclab/isaaclab.sh -p scripts/train.py --task "$task" --num_envs 4096 --max_iterations 5000 \
    --headless --seed 30 --run_group "$GROUP" agent.run_name="r3a_$tag" > "$alog" 2>&1 &
  pid=$!
  for i in $(seq 1 60); do   # up to 10 min for params/env.yaml
    rd=$(find logs/rsl_rl/ -mindepth 3 -maxdepth 3 -type d -path "*/$GROUP/*_r3a_${tag}_*" -newer "$alog.start" 2>/dev/null | head -1)
    [ -n "$rd" ] && [ -f "$rd/params/env.yaml" ] && break
    kill -0 $pid 2>/dev/null || break; sleep 10
  done
  if [ -z "$rd" ] || [ ! -f "$rd/params/env.yaml" ]; then say "FAIL $tag no params/env.yaml"; stop $pid; return; fi
  if ! python3 tools/check_simtoreal_params.py --variant "$variant" "$rd" >> "$alog.gate" 2>&1; then
    say "GATE FAIL $tag ($variant) -> kill; see $alog.gate"; stop $pid; return
  fi
  if [ "$(grep -cE '^[[:space:]]*velocity_limit_sim:' "$rd/params/env.yaml")" != 1 ]      || ! grep -qE '^[[:space:]]*velocity_limit_sim: 3\.1[[:space:]]*$' "$rd/params/env.yaml"; then
    say "GATE FAIL $tag velocity_limit_sim is not exactly one 3.1 (marinelab skew) -> kill"; stop $pid; return
  fi
  say "GATE ok $tag run=$rd"
  while kill -0 $pid 2>/dev/null; do   # until exit: fatal pattern first, then stall (no log write for 20 min)
    if fatal_in "$alog"; then say "NaN/Traceback $tag at $(grep -c 'Learning iteration' "$alog") it -> kill"; stop $pid; return; fi
    if [ $(( $(date +%s) - $(stat -c %Y "$alog") )) -gt 1200 ]; then say "STALL $tag (log idle 20 min) -> kill"; stop $pid; return; fi
    sleep 60
  done
  wait $pid; local rc=$?; kill -KILL -- -$pid 2>/dev/null   # reap anything the trainer left in its group
  # completion = rc 0 + a fatal line did not land between the last poll and exit + the final checkpoint deserializes
  local ok=0 why=""
  if [ "$rc" != 0 ]; then why="rc $rc"
  elif fatal_in "$alog"; then why="fatal line after the last poll"
  elif [ ! -s "$rd/model_4999.pt" ]; then why="model_4999.pt missing or empty"
  elif ! /workspace/isaaclab/_isaac_sim/python.sh -c "import sys, torch; torch.load(sys.argv[1], map_location='cpu', weights_only=False)" "$rd/model_4999.pt" > "$alog.ckptcheck" 2>&1; then why="model_4999.pt does not load (see $alog.ckptcheck)"
  else ok=1; printf 'chain_id=%s\ntag=%s\ntask=%s\nvariant=%s\nalbc_head=%s\nmarinelab_head=%s\nseed=30 max_iterations=5000 group=%s\nfinished=%s\n' \
         "$CHAIN_ID" "$tag" "$task" "$variant" "$(git -C "$W" rev-parse HEAD)" "$(git -C "$ML" rev-parse HEAD)" "$GROUP" "$(date +%FT%T%z)" > "$rd/.chain_ok"
  fi
  say "END $tag rc=$rc ok=$ok${why:+ ($why)} run=$rd"
}

say "CHAIN START id=$CHAIN_ID"
source_checks   # once up front: an all-skipped re-run must still refuse a moved or dirty tree
# order: reference arm (canary against p3b), then PLAN §8-R-2 (A6, N1, N4, existing 4), then N6 (§8-R-9)
run_arm ref_full      Isaac-ConstrainedALBC-TRPO-SimToReal-v0                  section5
run_arm a6_ppoenc     Isaac-ConstrainedALBC-PPO-Enc-SimToReal-v0               section5
run_arm n1_lagrangian Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0       section5
run_arm n4_residual   Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0      section5
run_arm noenc         Isaac-ConstrainedALBC-NoEncoder-SimToReal-v0             section5
run_arm ppo           Isaac-ConstrainedALBC-PPO-SimToReal-v0                   section5
run_arm noipo         Isaac-ConstrainedALBC-TRPO-NoIPO-SimToReal-v0            section5
run_arm noboth        Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-SimToReal-v0  section5
run_arm n6a_nodoraemon Isaac-ConstrainedALBC-TRPO-SimToReal-NoDoraemon-v0      n6-nodoraemon
run_arm n6b_nodr      Isaac-ConstrainedALBC-TRPO-SimToReal-NoDR-v0             n6-nodr
say "CHAIN COMPLETE id=$CHAIN_ID"
