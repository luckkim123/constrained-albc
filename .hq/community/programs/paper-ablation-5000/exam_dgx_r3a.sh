#!/bin/bash
# paper-ablation-5000 (2026-09-14): CORE exam of the three DGX-trained runs -- dgx_ref (the DGX baseline), n1_lagrangian,
# n4_residual. exam_chain_r3a.sh skipped n1/n4 as "(no complete run)" because they live on the DGX, not in $W/logs.
# Grader = the workstation rows' grader: eval tree afa3c6b + marinelab 8cc84a5 (both clean), p3b final DORAEMON box
# (--env-dr-anchor --doraemon-dr-from), CORE 4 cells, --att-amp-deg 15, 64 envs, seed 42, --save-extras
# (+ --save-moments on healthy), 5400 s cap, same identity/.complete/validate_cell as exam_chain_r3a.sh d29fb4d9.
# Checkpoints = copies of the DGX runs under $MAIN/logs (md5 pinned below, rechecked inside the lock before each cell).
# Order: model_4999 of n4 first (the first grading ever of the residual task), ref, n1; then model_2500 of the same three
# (same-run second checkpoint: n4 ended unconverged, noise std 1.49). DGX rows compare with dgx_ref only (PLAN 1200).
# GPU1 through /root/gpu1.lock per cell. Rerun skips complete cells. Stop: kill -TERM <this pid>.
set -u
W_CODE=/workspace/constrained-albc-eval
ML=/workspace/marinelab-r3a
MAIN=/workspace/constrained-albc
EXPECT_ML_HEAD=8cc84a54540f9fd06a835efc3f33d117dd8b2a84
DR_FROM=$MAIN/logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518
G=$MAIN/logs/rsl_rl
RUNS=("dgx_n4_residual|Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0|$G/albc_ablation/paper_ablation_r3a_dgx/main_residualtdc_simtoreal_dgx_n4_residual_260913_144308|f921699d787ae57a4f9fb4c1821f74d6|6325f89fbc9b1683da899a141ad9de59"
      "dgx_ref|Isaac-ConstrainedALBC-TRPO-SimToReal-v0|$G/albc_trpo_teacher/paper_ablation_r3a_dgx/trpo_dgx_ref_260912_144855|8a820d41d05ebf67ae8f71dd10b194d5|08484ef56f141c5fccc38b04e3ae46bd"
      "dgx_n1_lagrangian|Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0|$G/albc_ablation/paper_ablation_r3a_dgx/trpo_dgx_n1_lagrangian_260913_065642|e9428c4acb5f5ddd2b97a2f7cec3d2cf|08c0fb754f4974aa7ca2ad4246ab24e8")
CORE=("1,1,1,1,1,1 0 healthy" "1,1,1,0,0,1 0 pair34" "1,1,1,1,1,1 1 healthy_d1" "1,1,1,1,1,1 2 healthy_d2")
NENV=64
OUT=$MAIN/.hq/work/paper_ablation_r3a/exam_v3_dgx
LOCK=/root/gpu1.lock
mkdir -p "$OUT"; LOG=$OUT/exam.log
cd "$W_CODE" || exit 1
export PYTHONPATH="$W_CODE:$ML" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TERM=xterm CUDA_VISIBLE_DEVICES=1
say(){ echo "[$(date +%FT%T%z)] $*" | tee -a "$LOG"; }
trap 'trap - TERM INT; say "stopped by signal"; pkill -TERM -f -- "--output_dir $OUT/"; sleep 5; pkill -KILL -f -- "--output_dir $OUT/"; kill 0' TERM INT
EVAL_HEAD_FULL=$(git -C "$W_CODE" rev-parse --verify 'afa3c6b^{commit}') || { say "FATAL afa3c6b not in $W_CODE"; exit 2; }
anchor_hash(){ cat "$DR_FROM"/events.out.tfevents* | md5sum | cut -c1-32; }
ANCHOR_MD5=$(anchor_hash)
code_ok(){
  [ "$(git -C "$W_CODE" rev-parse HEAD)" = "$EVAL_HEAD_FULL" ] || { say "FATAL eval HEAD moved"; return 1; }
  [ "$(git -C "$ML" rev-parse HEAD)" = "$EXPECT_ML_HEAD" ] || { say "FATAL marinelab HEAD moved"; return 1; }
  [ "$(git -C "$W_CODE" status --porcelain | wc -l)" = 0 ] || { say "FATAL eval worktree dirty"; return 1; }
  [ "$(git -C "$ML" status --porcelain | wc -l)" = 0 ] || { say "FATAL marinelab worktree dirty"; return 1; }
  [ "$(anchor_hash)" = "$ANCHOR_MD5" ] || { say "FATAL exam box changed: $DR_FROM"; return 1; }
}
validate_cell(){  # cell_dir moments(0|1) -> 0 when the evaluator output is complete (copied from exam_chain_r3a.sh)
  python3 - "$1" "$2" <<'PY'
import json, os, sys
import numpy as np
d, mom = sys.argv[1], sys.argv[2] == "1"
s = json.load(open(os.path.join(d, "summary.json")))
levels = [k for k in ("none", "soft", "medium", "hard") if k in s]
assert levels, "summary.json has no tier"
json.load(open(os.path.join(d, "extras_meta.json")))
for lv in levels:
    z = np.load(os.path.join(d, f"extras_{lv}.npz"))
    assert "costs" in z.files and z["costs"].ndim == 3, lv
    if mom:
        assert all(k in z.files for k in ("m_thr", "m_buoy", "m_grav_buoy")), lv
PY
}
identity(){  # row task ckpt h dl mom -- same fields as the chain's identity for a non-student, no-override row
  printf 'arm=%s task=%s ckpt=%s enc=none teacher=none cfg=%s,%s nenv=%s seg=full eval=%s ml=%s anchor=%s extras=1 moments=%s ovr=none\n' \
    "$1" "$2" "$(readlink -f "$3") $(stat -c '%s %Y' "$3")" "$4" "$5" "$NENV" "$EVAL_HEAD_FULL" "$EXPECT_ML_HEAD" "$ANCHOR_MD5" "$6"
}
cell_done(){ [ -f "$1/.complete" ] && [ "$(cat "$1/.complete")" = "$2" ]; }

cell(){  # row task ckpt md5 health delay name
  local d=$OUT/$1/$7 mom=0 mflag=() extra=() id rc
  [ "$7" = healthy ] && { mom=1; mflag=(--save-moments); }
  [ "$6" != 0 ] && extra=(--control-delay "$6")
  id=$(identity "$1" "$2" "$3" "$5" "$6" "$mom")
  cell_done "$d" "$id" && { say "skip $1/$7 (complete)"; return 0; }
  (
    flock 9 || { say "FATAL cannot take $LOCK"; exit 86; }
    code_ok || exit 86
    [ "$(md5sum < "$3" | cut -c1-32)" = "$4" ] || { say "FATAL checkpoint md5 changed: $3"; exit 86; }
    [ -e "$d" ] && mv "$d" "$d.stale_$(date +%Y%m%dT%H%M%S)"
    mkdir -p "$d"
    { echo "$id" | tr ' ' '\n'; echo "ckpt_md5=$4"; echo "source=DGX run copy; compare with dgx_ref only"; echo "lock_acquired=$(date +%FT%T%z)"; } > "$d/RUN_CONDITIONS.txt"
    say "start $1/$7"
    timeout -k 60 5400 /workspace/isaaclab/isaaclab.sh -p constrained_albc/analysis/eval.py static --task "$2" --checkpoint "$3" \
      --num_envs "$NENV" --seed 42 --headless --fault_fixed_health "$5" --att-amp-deg 15 "${extra[@]}" \
      --env-dr-anchor --doraemon-dr-from "$DR_FROM" --save-extras "${mflag[@]}" --output_dir "$d" > "$d.log" 2>&1
    rc=$?
    echo "rc=$rc end=$(date +%FT%T%z)" >> "$d/RUN_CONDITIONS.txt"
    if [ "$rc" = 0 ] && validate_cell "$d" "$mom" >> "$d.log" 2>&1; then echo "$id" > "$d/.complete"; exit 0; fi
    exit $(( rc == 0 ? 3 : rc ))
  ) 9>"$LOCK" &
  wait $!; rc=$?
  say "done $1/$7 rc=$rc complete=$(cell_done "$d" "$id" && echo yes || echo NO)"
  return $rc
}

code_ok || exit 2
say "=== START pid=$$ eval=$EVAL_HEAD_FULL ml=$EXPECT_ML_HEAD anchor=$ANCHOR_MD5"
first=1; fails=0
for m in 4999 2500; do
  for e in "${RUNS[@]}"; do
    IFS='|' read -r arm task rdir md5_4999 md5_2500 <<< "$e"
    row=$arm; want=$md5_4999; [ "$m" = 2500 ] && { row=${arm}_m2500; want=$md5_2500; }
    for c in "${CORE[@]}"; do
      set -- $c
      cell "$row" "$task" "$rdir/model_$m.pt" "$want" "$1" "$2" "$3"; rc=$?
      [ "$rc" = 86 ] && { say "=== FATAL stop (source/lock/checkpoint check failed)"; exit 2; }
      if [ "$rc" != 0 ]; then
        fails=$((fails + 1))
        [ "$first" = 1 ] && { say "=== FIRST CELL FAILED -- batch stopped"; exit 3; }
      fi
      first=0
    done
  done
done
say "=== BATCH END failed_cells=$fails"
[ "$fails" = 0 ]
