#!/bin/bash
# paper-ablation-5000 grasp-step exam (evaluation only): payload toggle at t = 15 s under a 30 s zero-command hold.
# Rows: the approved pilot (selected teacher model_9998 on its own task and DORAEMON box, not a paper-table row)
# and the four ready anchor-B rows (p3b 5000/7500, R3a GRU, R3b TCN) on the section-5 exam box.
# Cells: row x {pick, drop}, tiers soft,medium,hard (none has no payload mass), 64 envs, seed 42, GPU1 under the lock.
# Launch (human only): EXPECT_GRASP_HEAD=<eval/grasp-step commit> nohup bash <this> > .hq/work/paper_ablation_r3a/grasp_chain_v1.out 2>&1 &
set -u
EXPECT_GRASP_HEAD="${EXPECT_GRASP_HEAD:?set EXPECT_GRASP_HEAD to the eval/grasp-step commit}"
G=/workspace/constrained-albc-grasp; ML=/workspace/marinelab-r3a; MAIN=/workspace/constrained-albc
EXPECT_ML_HEAD=8cc84a54540f9fd06a835efc3f33d117dd8b2a84
OUT=${OUT:-$MAIN/.hq/work/paper_ablation_r3a/grasp_v1}; NENV=${NENV:-64}; ONLY=${ONLY:-}; LOCK=/root/gpu1.lock
P3B=$MAIN/logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518
IB=$MAIN/logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813
SROOT=$MAIN/logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3
REF=Isaac-ConstrainedALBC-TRPO-SimToReal-v0; OLD=Isaac-ConstrainedALBC-TRPO-v0
CUDNN_DIR=/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle/nvidia/cudnn/lib; BASE_LD=${LD_LIBRARY_PATH:-}
# row|task|checkpoint|encoder|dr_from|fault
ROWS="pilot_inc9998|$OLD|$IB/model_9998.pt||$IB|off
p3b_5000|$REF|$P3B/model_5000.pt||$P3B|healthy
p3b_7500|$REF|$P3B/model_7500.pt||$P3B|healthy
r3a_gru_student|$REF|$SROOT/trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754/models/student_999.pt|gru|$P3B|healthy
r3b_tcn_student|$REF|$SROOT/trpo_sd_p3b7500_tcn_dr5_s30_260906_013849/models/student_999.pt|tcn|$P3B|healthy"
say(){ echo "[$(date +%FT%T%z)] $*"; }
full(){ git -C "$1" rev-parse --verify "$2^{commit}" 2>/dev/null; }
GRASP_FULL=$(full "$G" "$EXPECT_GRASP_HEAD") || true
[ -n "$GRASP_FULL" ] || { say "FATAL EXPECT_GRASP_HEAD $EXPECT_GRASP_HEAD is not a commit in $G"; exit 86; }
pins(){
  [ "$(git -C "$G" rev-parse HEAD)" = "$GRASP_FULL" ] || { say "FATAL grasp HEAD != $GRASP_FULL"; return 1; }
  [ "$(git -C "$ML" rev-parse HEAD)" = "$EXPECT_ML_HEAD" ] || { say "FATAL marinelab HEAD != $EXPECT_ML_HEAD"; return 1; }
  [ -z "$(git -C "$G" status --short)" ] && [ -z "$(git -C "$ML" status --short)" ] || { say "FATAL grasp or marinelab tree dirty"; return 1; }
}
trap 'say "TERM: stopping evals under $OUT"; pkill -f -- "--output_dir $OUT/" ; kill 0; exit 143' TERM INT
pins || exit 86
mkdir -p "$OUT"; BAD=0
say "GRASP START grasp=$GRASP_FULL ml=$EXPECT_ML_HEAD out=$OUT nenv=$NENV"
cell(){ # row task ckpt enc dr fault dir start_with
  local row=$1 task=$2 ck=$3 enc=$4 dr=$5 fault=$6 dir=$7 sw=$8 d=$OUT/$1_$7
  local id="row=$row dir=$dir task=$task ckpt=$ck size=$(stat -c %s "$ck" 2>/dev/null) enc=$enc dr=$dr fault=$fault grasp=$GRASP_FULL ml=$EXPECT_ML_HEAD nenv=$NENV"
  if [ -f "$d/.complete" ] && [ "$(cat "$d/.complete")" = "$id" ]; then say "SKIP $row $dir (complete)"; return 0; fi
  [ -f "$ck" ] || { say "ERROR missing checkpoint $ck"; BAD=1; return 0; }
  local pol=(--checkpoint "$ck"); [ -n "$enc" ] && pol=(--student_ckpt "$ck" --teacher_ckpt "$P3B/model_7500.pt" --encoder_type "$enc")
  local fa=(); [ "$fault" = healthy ] && fa=(--fault_fixed_health 1,1,1,1,1,1)
  (
    flock 9 || exit 87
    pins || exit 86
    [ -d "$d" ] && mv "$d" "$d.stale_$(date +%s)"
    mkdir -p "$d"; cd "$G" || exit 86
    export PYTHONPATH="$G:$ML" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TERM=xterm CUDA_VISIBLE_DEVICES=1
    if [ -n "$enc" ]; then export LD_LIBRARY_PATH=$CUDNN_DIR${BASE_LD:+:$BASE_LD}; else export LD_LIBRARY_PATH=$BASE_LD; fi
    say "CELL $row $dir"
    timeout -k 60 3600 /workspace/isaaclab/isaaclab.sh -p constrained_albc/analysis/eval.py static --task "$task" "${pol[@]}" \
      --num_envs "$NENV" --seed 42 --headless "${fa[@]}" --env-dr-anchor --doraemon-dr-from "$dr" \
      --levels soft,medium,hard --hold-zero-cmd --hold-seconds 30 --save-extras \
      --payload-toggle-step 750 --payload-start-with "$sw" --output_dir "$d" > "$d.log" 2>&1
    rc=$?; [ $rc = 0 ] || { say "END $row $dir eval rc=$rc"; exit 1; }
    # --levels: a level missing from the eval output fails the readout (rc 1) instead of passing on the rest.
    python3 "$G/tools/grasp_step_readout.py" "$d" --levels soft,medium,hard > "$d/readout.txt" 2>&1; rrc=$?
    [ $rrc = 0 ] || { say "END $row $dir readout rc=$rrc (2 = instrument check failed)"; exit 1; }
    echo "$id" > "$d/.complete"; say "END $row $dir ok"
  ) 9>"$LOCK" &
  wait $! || BAD=1
}
while IFS='|' read -r row task ck enc dr fault; do
  [ -n "$ONLY" ] && [ "$row" != "$ONLY" ] && continue
  cell "$row" "$task" "$ck" "$enc" "$dr" "$fault" pick 0.0
  cell "$row" "$task" "$ck" "$enc" "$dr" "$fault" drop 1.0
done <<< "$ROWS"
for m in "$OUT"/*/grasp_step_readout.md; do [ -f "$m" ] && { echo "### $(basename "$(dirname "$m")")"; cat "$m"; echo; }; done > "$OUT/grasp_summary.md"
[ $BAD = 0 ] && { say "GRASP COMPLETE"; exit 0; } || { say "GRASP INCOMPLETE (see ERROR/END lines)"; exit 1; }
