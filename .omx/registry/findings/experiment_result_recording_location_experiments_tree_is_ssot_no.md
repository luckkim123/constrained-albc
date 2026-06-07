---
title: "experiment result recording location (experiments tree is SSOT, not docs/results)"
tags: ["albc", "conventions", "results", "report", "experiments", "docs", "ssot"]
created: 2026-06-07T06:09:38.001037
updated: 2026-06-07T06:09:38.001037
sources: []
links: ["constrained_albc_experiment_conventions.md", "experiment_output_directory_standard_logs_vs_experiments_index_t.md", "experiment_launch_checklist_run_id_wandb_latest_alias_naming.md"]
category: convention
confidence: high
schemaVersion: 1
---

# experiment result recording location (experiments tree is SSOT, not docs/results)

Where an experiment result is recorded (user-confirmed 2026-06-07). SSOT = the experiments/ tree, NOT a parallel docs/results/<id>.md. Reason: the user reads inside experiments/, and exp-analyze already writes the canonical report.md there -- a second copy under docs/results is a drift source. Full definition: docs/plans/2026-06-07-experiment-dir-standard.md section "결과 기록 위치".

THREE DOCUMENT ROLES in the experiments tree (never conflate):

  experiments/.../<group>/DESIGN.md
    = experiment PLAN / design. The intent: hypothesis, which knob, variable isolation, expected outcome.
    Written BEFORE the run. A campaign's plan lives here (distinct from the cross-repo docs/plans/ neutral zone --
    an experiment's own plan is its DESIGN.md).

  experiments/.../<group>/README.md
    = campaign SUMMARY / index. Every run id + a one-line finding + the campaign verdict. The "what is in this
    campaign" entry point. Written/updated DURING and AFTER runs.

  experiments/.../<run_id>/analysis/diagnose-<ts>/report.md
    = per-run RESULT. The canonical exp-analyze output (report.md + report.ko.md + manifest.json + plots/).
    Written AFTER the run. THIS is the per-run result SSOT.

KEY RULES:

1. per-run result SSOT = report.md (engine output of exp-analyze), not a hand-written summary. A hand summary can
   NEVER replace report.md. Any "write up these results" request = run exp-analyze into the experiments tree, not
   author prose elsewhere. (rule 03-analysis-quality re-confirmed: 결과 = report.md, 손으로 쓴 요약은 정본 아님.)

2. docs/results/ is NO LONGER the SSOT for per-run results -- superseded by the experiments tree. Do NOT author new
   per-run result files under docs/results/. Existing docs/results/<id>.md become pointers or are retired; they are
   not the truth. (This replaces the old "results-system: docs/results/<id>.md" rule in 02-operations.)

3. Discovery: to find a campaign's results, read its <group>/README.md (the index). To find one run's result, open
   that run's analysis/diagnose-<ts>/report.md. To find why an experiment was run, read <group>/DESIGN.md.

4. Cadence: per-run report.md written as each run completes; campaign README/verdict updated as runs land. Separate
   from changelog (changelog = final code change only).

