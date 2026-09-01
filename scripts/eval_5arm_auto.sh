#!/bin/bash
# 5-arm ablation eval — 체인 완주를 기다렸다가 게이트를 통과할 때만 발사한다.
# 발주: paper-hub 조정자 ksm-obsidian-27, 2026-08-24. 프로토콜 정본: posts/finding/010-eval-prep-5arm.md
#
# 전체를 멈추는 것은 G1(체인 자체 실패)뿐이다. arm 단위 실패는 SKIP 하고 집계해 남긴다.
#   G1 체인 5 arm 이 전부 END rc=0 으로 끝났는가
#   G2 arm 의 model_4999.pt 가 실재하는가
#   G3/G4 각 arm 이 summary.json 을 냈는가 — 실패한 arm 만 SKIP 하고 나머지는 계속한다
#         (arm 끼리 독립. PPO 를 맨 앞에 둔 건 미검증 폴백을 일찍 드러내려는 것)

set -u
cd /workspace/constrained-albc || exit 1

# Logs live beside the campaign they describe, not at the workspace root
# (the root rule is "no stray output files"; moved 2026-09-01).
CAMPAIGN_DIR=/workspace/constrained-albc/logs/rsl_rl/albc_ablation/paper_ablation_5000
CHAIN_LOG=$CAMPAIGN_DIR/paper_ablation_5000_chain_stdout.log
LOG=$CAMPAIGN_DIR/eval_5arm_auto.log
DR_FROM=experiments/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813/train
TS=$(date -u +%y%m%d_%H%M%S)
OK=""; FAILED=""

say() { echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }
stop() { say "STOP — $*"; say "=== 자동 발사 중단. 사람 확인 필요 ==="; exit 1; }

say "=== 5-arm eval 자동 발사 대기 시작 (TS=$TS) ==="

# ---- G1: 체인 완주 대기 (최대 8시간) ----
for _ in $(seq 1 960); do
  done_ok=$(/bin/grep -c "END .* rc=0" "$CHAIN_LOG" 2>/dev/null || echo 0)
  done_bad=$(/bin/grep -c "END .* rc=[^0]" "$CHAIN_LOG" 2>/dev/null || echo 0)
  [ "$done_bad" -gt 0 ] && stop "체인 arm 이 rc!=0 으로 끝났다 — $CHAIN_LOG 확인"
  [ "$done_ok" -ge 5 ] && break
  sleep 30
done
[ "$(/bin/grep -c 'END .* rc=0' "$CHAIN_LOG")" -ge 5 ] || stop "8시간 안에 체인이 5 arm 을 못 끝냈다"
say "G1 통과 — 체인 5 arm 전부 rc=0"
pgrep -f launch_chain.sh >/dev/null && { say "체인 프로세스 잔존 — 60s 대기"; sleep 60; }

# ---- arm 정의: PPO 를 맨 앞에 둔다 (카나리아) ----
#        name          task                                              checkpoint glob
ARMS=(
  "ppo|Isaac-ConstrainedALBC-PPO-v0|logs/rsl_rl/*/paper_ablation_5000/*paper_abl_ppo_*/model_4999.pt"
  "full_method|Isaac-ConstrainedALBC-TRPO-v0|logs/rsl_rl/*/paper_ablation_5000/*paper_abl_full_*/model_4999.pt"
  "no_encoder|Isaac-ConstrainedALBC-NoEncoder-v0|logs/rsl_rl/*/paper_ablation_5000/*paper_abl_noenc_*/model_4999.pt"
  "no_constraint|Isaac-ConstrainedALBC-TRPO-NoIPO-v0|logs/rsl_rl/*/paper_ablation_5000/*paper_abl_noconstr_*/model_4999.pt"
  "no_both|Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0|logs/rsl_rl/*/paper_ablation_5000/*paper_abl_nobo_*/model_4999.pt"
)

for entry in "${ARMS[@]}"; do
  name=${entry%%|*}; rest=${entry#*|}; task=${rest%%|*}; glob=${rest#*|}

  # ---- G2: 체크포인트 실재 ----
  hits=$(ls -t $glob 2>/dev/null | wc -l)
  if [ "$hits" -ne 1 ]; then
    say "SKIP [$name] — 체크포인트가 정확히 1개가 아니다 (hits=$hits): $glob"
    FAILED="$FAILED $name"; continue
  fi
  ckpt=$(ls -t $glob 2>/dev/null | head -1)
  if [ ! -f "$ckpt" ]; then
    say "SKIP [$name] — model_4999.pt 가 파일이 아니다: $ckpt"
    FAILED="$FAILED $name"; continue
  fi

  out=$(dirname "$ckpt")/eval_ablation_5000/static_$TS
  say "[$name] 발사 — task=$task ckpt=$ckpt"

  # 실행 조건을 결과 옆에 남긴다 (나중에 '어떤 조건이었나' 추적용)
  mkdir -p "$out"
  cat > "$out/RUN_CONDITIONS.txt" <<EOF
arm=$name
task=$task
checkpoint=$ckpt
doraemon_dr_from=$DR_FROM   # fair-exam anchor: teacher/GRU/TDC/PID 와 같은 DR 박스
num_envs=64  seed=42  headless  fault=off(프로토콜 — 켜지 말 것)
gpu=CUDA_VISIBLE_DEVICES=1 (4060)
launched_by=eval_5arm_auto.sh (paper-hub 조정자 ksm-obsidian-27)
launched_at_utc=$(date -u +%FT%TZ)
protocol=posts/finding/010-eval-prep-5arm.md
EOF

  CUDA_VISIBLE_DEVICES=1 TERM=xterm /isaac-sim/python.sh \
    constrained_albc/analysis/eval.py static \
    --task "$task" --checkpoint "$ckpt" \
    --num_envs 64 --seed 42 --headless \
    --doraemon-dr-from "$DR_FROM" \
    --output_dir "$out" >> "$LOG" 2>&1
  rc=$?

  # ---- G3/G4: summary.json 이 완료 판정선 (로그 아님) ----
  if [ -f "$out/summary.json" ]; then
    say "[$name] OK rc=$rc — $out/summary.json"
    OK="$OK $name"
  else
    # arm 끼리 독립이라 하나가 실패해도 나머지를 막지 않는다.
    # PPO 를 맨 앞에 둔 건 미검증 폴백을 일찍 드러내려는 것이지 중단시키려는 게 아니다.
    say "SKIP [$name] — summary.json 이 없다 (rc=$rc). 로그에서 이 arm 구간을 확인해라"
    [ "$name" = "ppo" ] && say "  PPO 는 eval.py runner_cls_map 에 없어 OnPolicyRunner 폴백을 타는 arm 이다. 폴백 실패가 유력하다"
    FAILED="$FAILED $name"
  fi
done

say "=== 종료 — 성공:${OK:- 없음} / 실패:${FAILED:- 없음} ==="
[ -n "$FAILED" ] && say "실패한 arm 은 사람이 확인해야 한다. 성공한 arm 결과는 그대로 유효하다."
