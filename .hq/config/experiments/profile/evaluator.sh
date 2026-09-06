#!/usr/bin/env bash
# OMX evaluator for constrained-albc: wraps `eval.py static` (rule 03 SSOT eval tool).
#
# CONTRACT (OMC contracts.ts:178-201): the LAST non-empty stdout line MUST be a
# JSON object {"pass": <bool>}. Invoked as `bash .omx/profile/evaluator.sh` with
# cwd set by the caller (`omx eval --cwd <project_dir>`); this script also cd's
# explicitly so it works when run standalone too.
#
# Required env:
#   OMX_CHECKPOINT  path to the checkpoint to grade. MUST go through the
#                   experiments/<run_id>/train/<model>.pt symlink (eval.py's
#                   eval_dir_for_checkpoint needs a "train" path segment to route
#                   output to experiments/<run_id>/eval/; a bare logs/ path
#                   silently falls back to a legacy dir -- rule 03 eval gotcha 2).
# Optional env:
#   OMX_TASK        task id (default: Isaac-ConstrainedALBC-TRPO-v0)
#   OMX_NUM_ENVS    eval env count (default: 64)
#
# simplified: pass = eval.py exited 0 (a full static DR sweep completed). No
# numeric score -- metrics.yaml ships keep_policy=pass_only/score_formula=null
# (rules.md is still the unfilled interview template), so there is no approved
# success threshold to grade against yet. Add "score" once rules.md/metrics.yaml
# define one and keep_policy flips to score_improvement.
set -euo pipefail

: "${OMX_CHECKPOINT:?OMX_CHECKPOINT is required: path to experiments/<run_id>/train/<model>.pt}"

cd /workspace/constrained-albc

case "$OMX_CHECKPOINT" in
  */train/*) ;;
  *) echo "OMX_CHECKPOINT must go through the experiments/<run_id>/train/ symlink (got: $OMX_CHECKPOINT); see rule 03 eval gotcha 2" >&2; exit 1 ;;
esac
[[ -f "$OMX_CHECKPOINT" ]] || { echo "OMX_CHECKPOINT does not exist: $OMX_CHECKPOINT" >&2; exit 1; }

OMX_TASK="${OMX_TASK:-Isaac-ConstrainedALBC-TRPO-v0}"
OMX_NUM_ENVS="${OMX_NUM_ENVS:-64}"

# NEVER pass --output_dir here: the train/ symlink segment checked above is what
# lets eval.py auto-route output to experiments/<run_id>/eval/static_<ts>/
# (rule 03 eval gotcha 1).
if python constrained_albc/analysis/eval.py static \
    --task "$OMX_TASK" --checkpoint "$OMX_CHECKPOINT" \
    --num_envs "$OMX_NUM_ENVS" --headless; then
  echo '{"pass": true}'
else
  echo '{"pass": false}'
fi
