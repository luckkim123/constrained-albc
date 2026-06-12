---
title: "coverage lint ok is a floor not a quality gate; re-analysis uses OLD report as base, never shrinks"
tags: ["exp-analyze", "report-coverage", "re-analysis", "depth-regression", "dr_harder"]
created: 2026-06-08T04:45:44.586552
updated: 2026-06-08T04:45:44.586552
sources: ["diagnose-20260608-120155", "omx-core@bbc4471"]
links: []
category: convention
confidence: high
schemaVersion: 1
---

# coverage lint ok is a floor not a quality gate; re-analysis uses OLD report as base, never shrinks

coverage lint ok:true is a FLOOR, not a quality gate; a re-analysis must use the OLD report as its BASE and never shrink.

## The incident (2026-06-08 dr_harder report-shrink)

The eval/plot code changed (yaw rad/s->deg/s, OOD 5th level, lin_vel error bars), so all
5 dr_harder reports were re-generated. The summary.json NUMBERS were UNCHANGED (P2/P3
touched only periodic/segmented/switching paths + plotters, not static recompute). The
re-analysis was rewritten FROM THE DATA PACK instead of from the OLD report -- and came
out gutted while still passing `omx report-coverage`:

- words 25-39% shorter (teacher 2026->1318, E2 2817->1706)
- data-table rows 40-91% fewer (E3 66->6, E1 17->6, teacher 30->18)
- [FINDING] count down 4-9 per run (E4 22->13)
- the whole `## generalization (in-dist hard vs OOD)` section DELETED (OOD was the PHASE B
  deliverable), encoder z-sweep ranking table gone, per-axis x 4-DR-level table cut to 3 levels

Yet `coverage ok:true` -- because the token lint only checks each group's metric token
appears ONCE (coverage.py: `hits = sum(1 for m in metrics if _referenced(...))`). It
cannot see depth, a deleted section (OOD maps to no metric group), or a gutted table.

## The rule

1. **coverage ok:true == FLOOR, not quality.** Passing the token lint means you did not
   skip a whole diagnostic FAMILY. It does NOT mean you analyzed thoroughly. The depth bar
   is rule 03-analysis-quality.md (per-axis x ALL 4 DR levels; heavy-tail vs DC-bias
   separated; encoder z-sweep ranking; a dedicated generalization/OOD section; all 10
   per-constraint rows normalized J_C/d_k) PLUS ">= the OLD report", never "the lint went
   green".
2. **A re-analysis uses the OLD report.md as its literal BASE.** Start from a copy of the
   latest existing `<run>/analysis/<diagnose-*>/report.md`; update ONLY the changed plot
   references and corrected numbers on top of it. Do NOT re-derive the prose from the data
   pack -- that is what loses sections. New evidence ADDS; corrections SUBSTITUTE; nothing
   silently vanishes.
3. **If the draft is shorter than the OLD report, STOP -- that is the regression.** Measure:
   `wc -w` + count `[FINDING]` + table rows (`^|`) in both. Fewer words past ~10%, OR any
   drop in findings, OR any drop in table rows = analysis was deleted.

## The harness gates that now enforce it (omx-core, commit bbc4471)

`omx report-coverage` gained two opt-in gates (back-compat: a profile/CLI without them
cannot fail):

- `required_sections` (metrics.yaml): declared section tokens MUST appear as markdown
  HEADINGS (matched on heading text only, not prose). The constrained-albc profile declares
  `[tracking, generalization, reward, trpo, critic, encoder, constraint, doraemon, verdict]`
  -- so deleting the generalization section now loud-fails.
- `--baseline <prior report.md>` (or `--baseline auto` = latest sibling analysis): compares
  word / [FINDING] / table-row counts vs the report being replaced; any drop in findings or
  tables, or words past 10% tolerance, is a hard fail (exit 2) with an actionable message.

Verified on the actual incident: linting the shrunk 2026-06-08 teacher report vs its OLD
baseline returns `missing_sections=['generalization']` + `regression words 2026->1318
findings 16->12 tables 30->18`, exit 2.

## When to run it

For a re-analysis (a run that already has a report), When-done MUST include:
`omx report-coverage --path <new report.md> --root <root> --min-coverage 0.5 --baseline auto`
The analysis is not done until this passes.

## Relation to the 2026-06-06 gate

This is a DIFFERENT failure mode from `report_completeness_gate_must_run_before_writing_not_after`.
That one: groups skipped because coverage was audited AFTER drafting (fix = PRE-WRITE TodoWrite
per group + the lint as backstop). This one: the PRE-WRITE checklist + token lint both PASSED,
yet the report still shrank in depth because it was rewritten short from scratch instead of from
the OLD base. The token lint is necessary but not sufficient; the section + regression gates close
the remaining hole.
