---
title: "engine-gap: qualityScore is computed on the incoming append only, so a one-line housekeeping update permanently downgrades a rich page"
tags: ["engine-gap", "omx", "wiki", "quality", "lint", "scoring", "implemented", "omx-0.11.2", "released"]
created: 2026-08-14T06:51:35.841507
updated: 2026-08-14T07:32:37.370003
sources: ["wiki-curation-2026-08-14", "omx-core 3e8147d", "omx-core 9ef2487", "omx-core 385bb81", "omx-core PR#13"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# engine-gap: qualityScore is computed on the incoming append only, so a one-line housekeeping update permanently downgrades a rich page

[ENGINE-GAP] A page's `qualityScore` describes only the LAST content chunk appended to it, not the
page. Because the merge path overwrites the stored score with that chunk's score, closing a lead with a
one-line status note permanently marks a long, well-sourced page as low quality.

[WHERE] omx_core/wiki/quality.py `score_page(content, tags, title)` scores the string it is handed, and
omx_core/wiki/ingest.py passes the INCOMING `content` (not the merged body) while setting
`new_qs = quality_score if quality_score is not None else existing.quality_score` -- so a provided score
always wins, and a lower one silently demotes.

[SPEC] Score the MERGED body on the merge path (`page.content` after append), not the incoming chunk.
If a per-append score is still wanted, keep it as a separate field; the page-level `qualityScore` should
never be able to fall because of a correctly-written short update. Minimal alternative if that is too
invasive: on merge, take `max(existing.quality_score, incoming)`.

[EVIDENCE] All three pages the lint currently flags `low-quality` (score 40 < 50) are victims of this,
not genuinely poor pages:
  engine_gap_heavy_tail_json_pct_peak_gt_thresh_exceeds_100_at_ood   (2404 bytes)
  joint_dr_params_kp_kd_effort_friction_need_no_dedicated_measurem   (4733 bytes)
  tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_   (9394 bytes)
Each carries `qualityReasons: ["body-under-120-chars", "no-source-marker", "generic-only-tags"]` on a
body of thousands of bytes with sources. The cause is visible in the last page's final block, which is
its entire scored content: "2026-07-23 curation: status set to resolved -- two corrections converge on
a settled verdict, no open items remain." -- 113 characters, so 100 - 30 (under 120) - 20 (no source
marker) - 10 (generic tags) = 40. All three were demoted by the same 2026-07-23 curation sweep that
closed them, which is the exact opposite of what a curation pass should do to a settled page.

[CONSEQUENCE] `low-quality` cannot be read as "this page is weak" on this corpus; check whether the
final append is a housekeeping line before acting. It also means a curator is penalised for closing
leads tersely -- the incentive runs backwards.

[WORKAROUND until fixed] When closing a lead or making a housekeeping update, write the update block
with at least 120 characters, one numeric token, and a source marker. That costs a sentence and keeps
the page's score honest.

[STATUS] proposed

RELATED: how to read omx wiki lint on this corpus.

---

## Update (2026-08-14T07:25:54.068364)

[STATUS] implemented 2026-08-14 in omx-core v0.11.2 (commits 3e8147d, 9ef2487) -- this spec is closed,
and the [WORKAROUND] above is retired: a terse close no longer costs the page anything.

WHAT LANDED: `ingest_knowledge` recomputes the score from the MERGED body (`score_page(appended,
merged_tags, title=existing.title)`) whenever a score is supplied, instead of storing the caller's
chunk score. The spec's minimal alternative (`max(existing, incoming)`) was NOT taken -- recomputing is
the same number of lines and is correct rather than merely monotone.

ONE THING THE SPEC DID NOT ANTICIPATE, found by verifying live: the CLI computed its OWN chunk score
and printed that, so after the fix it advertised a number the page did not have. Measured before the
follow-up commit -- a one-line close printed `quality_score: 50` while the page on disk carried 80.
`ingest_knowledge` now returns `quality_score`/`quality_reasons` from the WikiPage it wrote and the CLI
prints those. `quality_forced_low` still derives from the incoming chunk, because that gate is about
what is being written, not about what the page already holds.

VERIFICATION: `test_quality_score_reflects_the_merged_body_not_the_new_chunk` and
`test_returns_the_score_the_page_actually_carries`, both watched failing first. End-to-end on a scratch
root, all three CLI lines agree with the file at 80 / ["no-source-marker"]: created, unchanged
(identical re-add), and updated (one-line close, no demotion). This page's own update is the
dogfood case -- it was written through the fixed CLI and scored 100.

CONSEQUENCE FOR THE THREE FLAGGED PAGES: `engine_gap_heavy_tail_json_pct_peak_gt_thresh_exceeds_100_at_ood`,
`joint_dr_params_kp_kd_effort_friction_need_no_dedicated_measurem` and
`tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_` still carry their stale 40 on disk,
because nothing rescores a page that is not re-added. They will correct themselves on the next update
to each; until then, read `low-quality` on those three as an artifact of the old scorer, not a verdict.

---

## Update (2026-08-14T07:32:37.370003)

POINTER CORRECTION 2026-08-14. The commit SHAs cited in the block above (3e8147d, 9ef2487) were the
BRANCH commits and no longer exist: PR #13 was squash-merged, so neither is reachable from main
(verified with `git merge-base --is-ancestor`). The fix now lives in ONE commit.

RELEASED: omx-core v0.11.2, commit 385bb81 on main, tagged v0.11.2, merged from
https://github.com/luckkim123/oh-my-experiments/pull/13. CI green on both required checks --
`test` pass and `tag-drift` pass. CI additionally proves the 4 local `wandb` failures were purely a
missing optional dependency here: the same suite is fully green on the runner.

Cite 385bb81, not the branch SHAs. This correction is itself an instance of the rule this curation
pass wrote down -- a pointer ages independently of the knowledge it points at, and a squash merge is
one of the ways it ages within the hour.

