---
title: "engine-gap: omx CLI gaps found re-analyzing teacher (2026-06-06 round 2)"
tags: ["engine-gap", "omx-harness", "cli-bug", "exp-analyze", "silent-empty"]
created: 2026-06-06T10:55:43.854709
updated: 2026-06-06T10:55:43.854709
sources: ["diagnose-20260606-194621"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: omx CLI gaps found re-analyzing teacher (2026-06-06 round 2)

Three NEW omx HARNESS gaps surfaced re-analyzing trpo_main_teacher (fix in ~/oh-my-experiments, NOT workspace). These are SEPARATE from the 4 in engine_gap_omx_cli_skill_gaps (dr-harder round 1) but same family.

[ENGINE-GAP 5 — silent-empty, highest value] omx reduce summarize --cv-field <WRONG_FIELD> returns {"cv": []} with exit 0 and NO error and NO 'available fields' hint. A session without a harness-audit goal copies the empty result as 'no data' = the exact dr-harder failure mode (DON'T trust empty output, but here it is the CLI not the engine). Note omx plot at least prints 'available: [...]' on a bad --series; cv-field is inconsistent. [WHERE] omx-core cli.py summarize handler / add_cv. [SPEC] when base_field not found in the ingested records, loud-fail (exit 2) with the list of available fields, mirroring omx plot's 'available:' message. CORRECT usage is --cv-field ss_error (the metric field), NOT an axis name. [STATUS] proposed.

[ENGINE-GAP 6] omx plot --format eval_summary cannot render per_axis_bar (or any view): EvalSummaryAdapter.ingest returns series={} (only summary records), so --series <anything> errors 'not in source; available: []'. But metrics.yaml declares per_axis_bar in views AND eval_summary in sources = declared-vs-implemented mismatch. Workaround: reference the eval_dr-rendered summary_<axis>.png PNGs directly (promote them). [WHERE] omx-core ingest/eval_summary.py (no series builder) + a per_axis_bar plotter for SummaryRecords. [SPEC] either build a bar view from summary records (axis x dr_level), or drop per_axis_bar/eval_summary from the profile's promised views. [STATUS] proposed.

[ENGINE-GAP 7] OmxPaths report path drops a path segment vs the run's real location. Run lives at experiments/rsl_rl/albc_trpo_teacher/dr_harder/<run>/ but report_md(output_root='experiments', group='albc_trpo_teacher/dr_harder') lands at experiments/albc_trpo_teacher/dr_harder/<run>/analysis/ — the 'rsl_rl' segment is missing, so the report tree is a SIBLING of the run tree, not beside it. Cause: profile output_root='experiments' but real layout is experiments/rsl_rl/<exp>/<group>/<run>. [WHERE] workspace .omx/profile/metrics.yaml output_root (workspace-fixable: set output_root: experiments/rsl_rl) OR pass group='rsl_rl/albc_trpo_teacher/dr_harder'. Verify which is canonical across runs before changing. [STATUS] proposed (needs decision: output_root vs group convention).

[MINOR] omx promote-plots is not incremental-safe: re-passing an already-promoted --referenced name loud-fails (it is gone from scratch). Pass only NEW plots on a second promote call. Not silent (exit nonzero) so low severity. [STATUS] noted.
