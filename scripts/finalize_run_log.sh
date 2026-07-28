#!/bin/bash
# Finalize a run's stdout log after training ends.
#
# Moves the transient launch stdout out of logs_queue/ and into the run's OWN
# data-tier dir (next to its checkpoints), records a light .omx pointer, and
# archives the launch wrapper. This is the convention that replaces the old
# workspace-root logs_queue/ dump (trashed 2026-07-24): heavy stdout belongs in
# logs/rsl_rl/<run_id>/, .omx keeps only a pointer -- same split as
# checkpoint-pointer.json.
#
# run_id is minted by train.py at launch (<label>_<tag>_<ts>), so the launch
# wrapper cannot know the final dir up front -> it dumps to logs_queue/<name>.log
# and this runs AFTER the process exits to relocate it.
#
# Usage: scripts/finalize_run_log.sh <run_name>       e.g. b0cmaxthrust_s30
set -euo pipefail
cd "$(dirname "$0")/.."   # -> constrained-albc repo root
NAME="${1:?usage: finalize_run_log.sh <run_name>}"

# 1) locate the real run dir (exactly one; fail loud otherwise)
mapfile -t DIRS < <(find logs/rsl_rl -maxdepth 3 -type d -name "*${NAME}_2*" 2>/dev/null | sort)
[ "${#DIRS[@]}" -eq 1 ] || { echo "[ERR] expected 1 run dir matching '*${NAME}_2*', found ${#DIRS[@]}: ${DIRS[*]:-<none>}"; exit 1; }
RUNDIR="${DIRS[0]}"
RUNID="$(basename "$RUNDIR")"

# 2) locate the transient stdout log
SRC="$(find logs_queue -maxdepth 1 -name "${NAME}*.log" 2>/dev/null | sort | head -1 || true)"
[ -n "$SRC" ] && [ -f "$SRC" ] || { echo "[ERR] no stdout log at logs_queue/${NAME}*.log"; exit 1; }

# 3) move stdout into the run's data-tier dir
DEST="$RUNDIR/launch.log"
[ -e "$DEST" ] && { echo "[ERR] $DEST already exists -- refusing to overwrite"; exit 1; }
mv "$SRC" "$DEST"
echo "[ok] stdout -> $DEST"

# 4) archive the launch wrapper alongside it (exact reproduction recipe)
[ -f "logs_queue/launch_${NAME}.sh" ] && { mv "logs_queue/launch_${NAME}.sh" "$RUNDIR/launch.sh"; echo "[ok] wrapper -> $RUNDIR/launch.sh"; }

# 5) light pointer in the omx run ledger dir (dir may still be *_PLACEHOLDER)
OMXDIR="$(find .omx/runs -maxdepth 1 -type d -name "*${NAME}*" 2>/dev/null | sort | head -1 || true)"
if [ -n "$OMXDIR" ]; then
  printf '{"stdout": "%s"}\n' "$DEST" > "$OMXDIR/stdout-pointer.json"
  echo "[ok] pointer -> $OMXDIR/stdout-pointer.json"
else
  echo "[warn] no .omx/runs dir for '$NAME' -- pointer skipped"
fi

# 6) drop the dead pid files and remove logs_queue/ if now empty
rm -f "logs_queue/${NAME}.pid" "logs_queue/${NAME}.trainpid"
rmdir logs_queue 2>/dev/null && echo "[ok] logs_queue/ removed (empty)" || echo "[note] logs_queue/ kept (other files remain)"
