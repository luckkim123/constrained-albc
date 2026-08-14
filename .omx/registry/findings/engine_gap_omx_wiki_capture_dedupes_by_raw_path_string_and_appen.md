---
title: "engine-gap: omx wiki capture dedupes by raw path string and appends without an equality check, so one report can be captured twice byte-identically"
tags: ["engine-gap", "omx", "wiki", "capture-flush", "dedupe", "hygiene", "worktree", "dead-pointer", "implemented", "omx-0.11.2"]
created: 2026-08-14T06:42:05.550564
updated: 2026-08-14T07:25:38.032540
sources: ["wiki-curation-2026-08-14", "omx-core 3e8147d", "omx-core 9ef2487"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
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

---

## Update (2026-08-14T07:25:38.032540)

[STATUS] implemented 2026-08-14 in omx-core v0.11.2 (commits 3e8147d, 9ef2487) -- this spec is closed.

WHAT LANDED, against the two [WHERE] items above:
1. `capture.py flush_produced_reports` now keys dedupe on `report_path.resolve()`, falling back to the
   raw string on OSError. One file under two spellings is one report, so it is read, integrity-verified
   and captured once.
2. `ingest.py ingest_knowledge` skips an identical re-add instead of appending it. Comparison is
   block-level against the existing content with the `## Update (ts)` header and the title H1 stripped,
   so a re-capture is recognised across its changing timestamp. The action returns as `unchanged` --
   the value `wiki sync` already used. INV-2 holds: tags/sources/links/confidence/status still merge
   and `updated` still advances; only a byte-equal body is skipped.

This also makes true what `flush_produced_reports`' own docstring already claimed
("capture_session is append-merge so re-flushing is a no-op merge"), which it was not.

VERIFICATION: three regression tests, each watched failing first --
`test_flush_dedupes_two_spellings_of_one_report_path`,
`test_identical_content_does_not_append_a_second_time`,
`test_returns_the_score_the_page_actually_carries`. Full suite `pytest -q` 1071 passed / 2 skipped;
the 4 wandb failures are a missing optional dependency and reproduce identically on main. Confirmed
end-to-end through the real CLI on a scratch root: an identical re-add returns `"action": "unchanged"`
and adds no second block.

STILL OPEN (deliberately not in the patch): rewriting the stored `sources` entry to a REPO-RELATIVE
path. That would make a pointer survive a worktree retirement -- the 16 stubs naming the retired
`constrained-albc-student` worktree are the motivating case -- but it changes the format of data
already on disk and needs a migration. The verification rule stands meanwhile: a wiki source pointer
that fails to resolve is NOT evidence the source is gone; re-resolve the run path against the main
repo first.

