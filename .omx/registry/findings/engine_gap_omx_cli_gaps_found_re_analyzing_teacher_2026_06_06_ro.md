---
title: "engine-gap: omx CLI gaps found re-analyzing teacher (2026-06-06 round 2)"
tags: ["engine-gap", "omx-harness", "cli-bug", "exp-analyze", "silent-empty", "wiki", "session-id"]
created: 2026-06-06T10:55:43.854709
updated: 2026-07-06T02:16:31.477399
sources: ["diagnose-20260606-194621", "diagnose-20260606-173330"]
links: ["engine_gap_analyze_training_py_emits_no_reward_8_term_decomposit.md"]
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

---

## Merged from engine_gap_omx_cli_skill_gaps_found_during_dr_harder_reporting_2.md (2026-07-06T02:16:31.477399)

# engine-gap: omx CLI/skill gaps found during dr-harder reporting (2026-06-06)

Four omx HARNESS gaps surfaced writing the dr-harder per-run reports (these are omx-core/skill bugs = fix in ~/oh-my-experiments, NOT workspace-specific). 

[ENGINE-GAP 1] omx session-id (argless) crashes with TypeError: 'str' object is not callable. [WHERE] omx-core session-id verb autogen branch. [SPEC] argless call must hit the autogen fallback the exp-analyze SKILL.md advertises ('flag>env>autogen') and print a fresh id; --session-id X works so the bug is autogen-only. [STATUS] proposed.

[ENGINE-GAP 2] No 'omx wiki read --slug' verb; only add/query/lint/list. query returns truncated snippets, so reading a known page full-text forces a hardcoded read of .omx/registry/findings/<slug>.md (bypasses omx_paths getter). [WHERE] omx-core wiki subcommand. [SPEC] add 'omx wiki read --slug <slug> [--root]' returning full page via getter, loud-fail on missing slug. [STATUS] proposed.

[ENGINE-GAP 3] omx wiki add --from-report rejects multi-line [FINDING] blocks: it requires the line immediately after [FINDING] to be [EVIDENCE:], so a [FINDING] whose claim wraps across 2 lines (normal readable prose) makes it exit 2 with 'not followed by [EVIDENCE'. [WHERE] omx-core report.parse_findings / wiki from-report extractor. [SPEC] lookahead to the next non-empty [EVIDENCE:] line within the block instead of requiring the very next line; a readable report should not break auto-capture. [EVIDENCE] diagnose-20260606-173330 teacher report.md has 6 multi-line [FINDING] blocks; --from-report printed 0 candidates + exit 2. [STATUS] proposed.

[ENGINE-GAP 4 — SKILL, highest value] exp-analyze does NOT enforce metrics.yaml vocabulary completeness: a report can cover only a slice of the profile vocabulary (eval-side) and skip training-dynamics (constraint margins/viol, TRPO line_search/kl/surrogate, critic value/cost_value, reward 8-term decomposition, gradient liveness) and still pass. The profile comments are diagnostic INSTRUCTIONS ('total plateau is diagnosed by decomposition not Reward/total alone', 'cost_value: if it does not converge constraint advantages are noise'), not a passive list. [WHERE] exp-analyze SKILL.md (a vocabulary-coverage step) + optionally omx report-parse (a coverage lint). [SPEC] after drafting report.md, check which metrics.yaml diagnostic tokens are referenced; if training-dynamics groups are absent, require justification or addition. Caught live: first-pass dr-harder reports referenced ~4 training scalars of 44 TB vocabulary tokens; user flagged 'metrics보다 확연히 적다'. [STATUS] proposed.


---

## Merged from omx_cli_tools_not_just_the_engine_silent_fail_on_misuse_empty_ab.md (2026-07-06T02:16:31.477399)

# omx CLI tools (not just the engine) silent-fail on misuse — empty != absent

Extension of [[don_t_trust_an_engine_s_empty_zero_output_cross_check_the_raw_tb]]: the empty-output trap is NOT limited to the diagnostic ENGINE (analyze_training.py). The omx CLI REDUCE/PLOT verbs themselves return empty on MISUSE without erroring, which a goal-less session copies as 'no data'.

CONCRETE (teacher re-analysis diagnose-20260606-194621):
- omx reduce summarize --cv-field roll  ->  {"cv": []}  exit 0, no error, no hint. WRONG usage: --cv-field is the METRIC FIELD (ss_error), not an axis. Correct: --cv-field ss_error  -> 28 rows (4 DR x 7 axis). The data was always there; the CLI silently accepted a bad field.
- omx plot --format eval_summary --series ss_error  ->  'not in source; available: []'. Here the cause is structural: EvalSummaryAdapter.ingest returns series={} (summary records only, no series), so eval_summary CANNOT feed --series/per_axis_bar at all, despite the profile declaring per_axis_bar in views + eval_summary in sources.

LESSON: when ANY omx verb returns [] / empty, FIRST suspect your own invocation (re-read --help, dump the source's real fields) before concluding 'no data'. This is the same hypothesis-not-finding discipline as the engine rule, applied one layer up to the CLI. INCONSISTENCY worth noting: omx plot at least prints 'available: [...]' on a bad --series, but omx reduce summarize prints nothing on a bad --cv-field. Both gaps + the path-segment-drop gap are filed in fix-prompt /workspace/docs/plans/2026-06-06-omx-cli-silentfail-and-pathmismatch-fix-prompts.md (GAP A/B) and wiki engine_gap_omx_cli_gaps_found_re_analyzing_teacher_2026_06_06_round_2. CORRECT cv usage for eval summary.json = --cv-field ss_error.
