#!/usr/bin/env bash
# OMX Isaac Lab REFERENCE evaluator (committed; ships keep_policy=pass_only).
#
# CONTRACT (re-impl of OMC contracts.ts:178-201): the LAST non-empty stdout line
# MUST be a JSON object {"pass": <bool>} with an OPTIONAL numeric "score". Under
# pass_only (this reference's default) score is omitted; exp-init (#3) fills the
# D5 score formula later when a profile opts into score_improvement.
#
# This is an HONEST DOCUMENTED STUB. A live run is NOT invoked here (eval_dr needs
# Isaac Sim + a checkpoint, unavailable in unit tests). The block below shows
# EXACTLY where the live eval slots in; the stub emits a deterministic verdict so
# the contract is testable end-to-end without a GPU.
#
# To make this a REAL evaluator, exp-init replaces the STUB block with the
# project's own eval command, e.g. (paths are illustrative — substitute your
# repo/eval entrypoint; nothing here is machine-specific):
#   cd "$OMX_PROJECT_DIR" && python <your_eval_entrypoint> static \
#       --task "$OMX_TASK" --num_envs 64 --headless >/dev/null 2>&1
#   # then parse the run's summary.json into a pass/score verdict and echo it.
set -euo pipefail

# --- STUB verdict (replace with live eval_dr in exp-init) -------------------
# Honors OMX_REF_PASS for deterministic tests: 1/unset -> pass, 0 -> fail.
if [[ "${OMX_REF_PASS:-1}" == "0" ]]; then
  echo '{"pass": false}'
else
  echo '{"pass": true}'
fi
