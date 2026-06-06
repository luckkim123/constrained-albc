---
title: "omx CLI tools (not just the engine) silent-fail on misuse — empty != absent"
tags: ["omx-harness", "silent-empty", "cli-bug", "exp-analyze"]
created: 2026-06-06T11:11:08.961616
updated: 2026-06-06T11:11:08.961616
sources: ["diagnose-20260606-194621"]
links: ["don_t_trust_an_engine_s_empty_zero_output_cross_check_the_raw_tb.md"]
category: debugging
confidence: high
schemaVersion: 1
---

# omx CLI tools (not just the engine) silent-fail on misuse — empty != absent

Extension of [[don_t_trust_an_engine_s_empty_zero_output_cross_check_the_raw_tb]]: the empty-output trap is NOT limited to the diagnostic ENGINE (analyze_training.py). The omx CLI REDUCE/PLOT verbs themselves return empty on MISUSE without erroring, which a goal-less session copies as 'no data'.

CONCRETE (teacher re-analysis diagnose-20260606-194621):
- omx reduce summarize --cv-field roll  ->  {"cv": []}  exit 0, no error, no hint. WRONG usage: --cv-field is the METRIC FIELD (ss_error), not an axis. Correct: --cv-field ss_error  -> 28 rows (4 DR x 7 axis). The data was always there; the CLI silently accepted a bad field.
- omx plot --format eval_summary --series ss_error  ->  'not in source; available: []'. Here the cause is structural: EvalSummaryAdapter.ingest returns series={} (summary records only, no series), so eval_summary CANNOT feed --series/per_axis_bar at all, despite the profile declaring per_axis_bar in views + eval_summary in sources.

LESSON: when ANY omx verb returns [] / empty, FIRST suspect your own invocation (re-read --help, dump the source's real fields) before concluding 'no data'. This is the same hypothesis-not-finding discipline as the engine rule, applied one layer up to the CLI. INCONSISTENCY worth noting: omx plot at least prints 'available: [...]' on a bad --series, but omx reduce summarize prints nothing on a bad --cv-field. Both gaps + the path-segment-drop gap are filed in fix-prompt /workspace/docs/plans/2026-06-06-omx-cli-silentfail-and-pathmismatch-fix-prompts.md (GAP A/B) and wiki engine_gap_omx_cli_gaps_found_re_analyzing_teacher_2026_06_06_round_2. CORRECT cv usage for eval summary.json = --cv-field ss_error.
