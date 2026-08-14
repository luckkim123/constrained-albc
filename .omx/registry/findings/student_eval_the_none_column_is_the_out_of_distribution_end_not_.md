---
title: "Student eval: the none column is the OUT-OF-DISTRIBUTION end, not the easy end"
tags: ["student", "distillation", "eval", "dr", "generalization", "doraemon", "methodology", "albc"]
created: 2026-08-14T06:21:59.649748
updated: 2026-08-14T06:21:59.649748
sources: ["diagnose-20260803-223517", "diagnose-20260803-235022", "wiki-curation-2026-08-14"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Student eval: the none column is the OUT-OF-DISTRIBUTION end, not the easy end

Reading a student eval's four DR columns as an easy-to-hard ladder inverts the actual difficulty
order: for a distilled student, `none` is the off-distribution end and `hard` is the trained one.

MECHANISM: `configure_env_for_student` (student runner) disables DORAEMON and substitutes a STATIC
HARD DR box for the whole distillation. The student therefore never trains against a curriculum and
never sees a nominal plant. At eval time the four levels are four FIXED evaluation points, not
curriculum stages, and `none` is the one furthest from anything the student trained on.

EVIDENCE:
- The by-name substitution in `configure_env_for_student`; 0 TB tags under the `DORAEMON/` prefix in
  any distillation run (analysis diagnose-20260803-235022). The pre-registration `next-20260803-184816.md`
  Lane 2 states the same.
- Corroborated by dispersion: `none` carries the HIGHEST CV of the four levels in both baselines
  (C3 53.5%, CTL 51.8%, against 33.0% / 34.0% at soft) -- the signature of an off-distribution point,
  not an easy one (`summary.json none/att_norm`, diagnose-20260803-223517).

CONSEQUENCES:
- A student improvement AT `none` is a GENERALIZATION result and must be reported as one. The B2 CV
  improvement there (51.8 -> 31.8) is generalization, not an in-distribution gain.
- The `tracking` table's four columns must not be narrated as a difficulty ramp for student runs.
- The absent DORAEMON metric group in a student report is absent BY DESIGN, not by omission -- do not
  file it as a coverage failure. See engine-gap: the analysis engine and omx reduce are both unusable
  on student distillation runs.

SCOPE: distillation (Stage-2) runs only. A teacher run trains under the live DORAEMON curriculum, so
for teachers the ordinary easy-to-hard reading holds.

SOURCE: analyses diagnose-20260803-223517 and diagnose-20260803-235022; promoted from three
auto-captured session-log stubs during the 2026-08-14 wiki curation pass.

