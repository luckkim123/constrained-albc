# Analysis discipline (consumed as guidance by exp-analyze / exp-design)

> **SSOT for the full standards:** `/workspace/.claude/rules/03-analysis-quality.md`.
> This file is the exp-analyze-facing digest — the highest-leverage rules that change a verdict.
> Read the SSOT for detail; do not duplicate its full text here.

## Always
- **Query the omx wiki FIRST** (`omx wiki query --root /workspace/constrained-albc`) before diagnosing:
  prior causes, anomaly thresholds, and conventions already live there — do not re-derive from scratch.
- Report **CV = ss_error_std / ss_error** for every metric; mean alone is half the picture.
- Compare **all 4 DR levels** (none/soft/medium/hard) and **all axes** (roll/pitch/vx/vy/vz/yaw), not one slice.
- **Differential-diagnose first** ("why did X fail but Y succeed?"); predict recovery by measured slope, not hope.
- Read the **function body** of a suspect constraint/reward (`mdp/constraints.py`, `mdp/rewards.py`) — never judge it by its name.

## Never
- Call it "heavy-tail" from mean+std alone — that needs per-env peak counting (`analyze.py eval_dr`, which also
  separates heavy-tail from sample-mean divergence). Confusing the two is a documented trap.
- Propose "schedule / adaptive / curriculum" as a default without paper, run-data, or code evidence.
- Add encoder auxiliary losses (reconstruction / z_bounds / contrastive) — verified to collapse z.

## Records (where things live)
- **Results SSOT** = `experiments/<run_id>/analysis/diagnose-*/report.md`; group index = that group's `README.md`;
  top map = `experiments/INDEX.md`.
- **Knowledge / conventions** = omx wiki (`.omx/registry/findings/`), queried as above.
