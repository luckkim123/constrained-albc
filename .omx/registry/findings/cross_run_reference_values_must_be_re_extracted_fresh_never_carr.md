---
title: "cross-run reference values must be RE-EXTRACTED fresh, never carried forward (E4 stale-teacher-column gate)"
tags: ["cross-run", "carry-forward", "stale", "baseline", "teacher", "report-coverage", "provenance", "gate", "dr_harder", "e4"]
created: 2026-06-08T06:27:12.566305
updated: 2026-06-08T06:27:12.566305
sources: ["experiments/rsl_rl/albc_trpo_teacher/dr_harder/trpo_e4_budget_half_260607_041243/analysis/diagnose-20260608-160000/report.md", "static_260607_182214"]
links: ["coverage_lint_ok_is_a_floor_not_a_quality_gate_re_analysis_uses_.md"]
category: convention
confidence: high
schemaVersion: 1
---

# cross-run reference values must be RE-EXTRACTED fresh, never carried forward (E4 stale-teacher-column gate)

A report often carries a column of values from ANOTHER run — a `teacher hard`
reference column inside an experiment's tracking/reward/constraint tables, the
canonical-baseline numbers a comparison narrative leans on. Those cross-run
reference values go STALE the moment the source run is re-evaluated, and a
carried-over stale value flips the comparison story silently.

The dr_harder E4 (`trpo_e4_budget_half`) 2026-06-08 incident: the E4 report had a
`teacher hard` column whose att_norm value was carried forward from an OLD report
(read ~1.06 / "+45%·+21%" gaps), but the canonical teacher had since been
re-evaluated to `static_260607_182214` where hard att_norm ss_error = 1.2834
(the real gaps are +324%·+187%). The carried value made "roll/yaw beat the
teacher" read true when it was false. The depth/regression gate could NOT catch
it: the E4 report GREW (2669->3888 words), so a "did it shrink" gate waved it
through. E1/E2/E3 had the same `teacher hard` column with the value re-synced but
the source eval id never cited in prose — value right, provenance absent.

Two distinct failure modes, both independent of the depth gate:
- STALE value: the carried reference number disagrees with the source run's
  current canonical summary.json.
- UNCITED source: the reference column has no `static_<ts>` eval id cited, so it
  cannot be audited back to a file even when the number happens to be right.

The rule (asymmetry is the point): a re-analysis MUST carry forward the OLD
report's prose/findings/tables and never shrink (the report-shrink rule), but it
must NEVER carry forward a cross-run reference VALUE — re-open the source run's
current `summary.json` and re-extract every cross-run number fresh, and cite the
source eval id next to it.

The gate that enforces it (omx-core, commit on exp/coverage-carryforward-gate):
`omx report-coverage --path <report.md> --root <root> --cross-run-refs <refs.json>`
where refs.json is a JSON list of `{label, summary_path, field, reported_value}`,
one per cross-run cell. `check_cross_run_refs` verifies BOTH provenance (eval id
cited, derived from summary_path's parent dir) AND value (matches summary.json at
`field` within rounding tolerance). A stale value or uncited source loud-fails
(exit 2). Verified on the real E4 report: correct teacher value -> pass; injected
stale 1.06 -> STALE fail; E1 report (teacher column, eval id uncited) -> UNCITED
fail. Distinct from [[coverage lint ok is a floor not a quality gate; re-analysis
uses OLD report as base, never shrinks]] (that gate guards DEPTH/shrink; this one
guards cross-run VALUE freshness — a report can pass one and fail the other).

