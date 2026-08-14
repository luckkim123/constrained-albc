---
title: "engine-gap: qualityScore is computed on the incoming append only, so a one-line housekeeping update permanently downgrades a rich page"
tags: ["engine-gap", "omx", "wiki", "quality", "lint", "scoring"]
created: 2026-08-14T06:51:35.841507
updated: 2026-08-14T06:51:35.841507
sources: ["wiki-curation-2026-08-14"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

