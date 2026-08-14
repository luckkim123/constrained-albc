---
title: "engine-gap: omx wiki capture dedupes by raw path string and appends without an equality check, so one report can be captured twice byte-identically"
tags: ["engine-gap", "omx", "wiki", "capture-flush", "dedupe", "hygiene", "worktree", "dead-pointer"]
created: 2026-08-14T06:42:05.550564
updated: 2026-08-14T06:44:34.800250
sources: ["wiki-curation-2026-08-14"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: omx wiki capture dedupes by raw path string and appends without an equality check, so one report can be captured twice byte-identically

[ENGINE-GAP] The same report can be auto-captured twice under two spellings of its own path, and the
second capture appends a byte-identical Update block to the page instead of being recognised as a
no-op. Measured on this workspace 2026-08-14: 141 of 550 wiki pages carry at least one duplicated
block, about 114 KB of pure repetition, and every affected page is category session-log.

[WHERE] Two places in omx_core, and it takes both to produce the defect:
1. omx_core/wiki/capture.py, capture_flush -- `key = str(report_path)` (line 72). The dedupe key is
   the RAW path string as written into the produced-reports ledger, with no resolve()/normalisation.
   `experiments/.../report.md` and `/workspace/constrained-albc/experiments/.../report.md` are the same
   file and two different keys. The `seen` set is also per-invocation only, so it offers nothing across
   two flushes.
2. omx_core/wiki/ingest.py, ingest_knowledge merge branch --
   `appended = existing.content.rstrip() + f"\n\n---\n\n## Update ({now})\n\n{content}\n"`. The append
   is unconditional; there is no comparison against the existing blocks.

[SPEC]
- capture.py: key on `report_path.resolve()` (falling back to the raw string only if resolve raises),
  so the two spellings collapse to one key.
- ingest.py: before appending, compare the normalised new content against the page's existing blocks;
  if identical, refresh `updated`/`sources`/`tags` and skip the append. This preserves INV-2 (knowledge
  accrues without loss) exactly -- an identical block adds no knowledge to lose.

[EVIDENCE] Verified in source 2026-08-14, plus the corpus measurement above. Concrete instance:
`dagger_mixed_exactly_as_specified_ruling_out_a_mixing_ratio_conf` carries the same finding twice, its
`sources` array holding both the relative and the absolute form of one report path, with the second
block stamped 2026-08-05T09:49:50.

[CONSEQUENCE] Page byte counts overstate content, the `oversized` lint fires on repetition rather than
on substance, and a reader who scrolls past the first `---` sees the same paragraph again and has to
diff two blocks to learn they are identical. The 2026-08-14 curation pass removes the current instances
by deleting the session-log stubs, but nothing prevents recurrence until the two fixes land.

[STATUS] proposed

---

## Update (2026-08-14T06:44:34.800250)

SECOND SYMPTOM OF THE SAME ROOT CAUSE, found 2026-08-14 while auditing whether the session-log stubs
were safe to delete: 16 stubs record their source as
`/workspace/constrained-albc-student/experiments/.../trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md`
-- a git worktree that has since been removed. The path does not resolve; the FILE is alive, at the
same run path under the main repo (`/workspace/constrained-albc/experiments/...`), because the run tree
migrated when the worktree was retired.

Root cause is the one already stated on this page: capture records `str(report_path)` exactly as the
invoking session spelled it, so the stored pointer inherits that session's cwd -- relative vs absolute
(the duplicate-block symptom) and main-repo vs worktree (this one). Both are the same missing
normalisation.

ADDS TO [SPEC]: normalise the recorded source to a REPO-RELATIVE path (relative to the omx root)
rather than storing the absolute or cwd-relative string. That makes the pointer survive a worktree
retirement, a repo move, and a different launch cwd, and it makes the dedupe key correct for free.

VERIFICATION RULE this produced: a wiki source pointer that fails to resolve is NOT evidence the
source is gone. Re-resolve the same run path against the main repo before treating a stub as the sole
surviving copy of a finding. Applying that rule here changed the 2026-08-14 curation audit from
"16 stubs are the only record" to "all 289 stubs have a live source report", which is what made the
mass delete safe.

