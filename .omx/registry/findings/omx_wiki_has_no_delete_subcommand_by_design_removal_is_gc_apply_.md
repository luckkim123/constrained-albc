---
title: "omx wiki has no delete subcommand by design: removal is gc-apply, duplicates come from add-with-new-title"
tags: ["wiki", "gc", "delete", "convention", "discoverability"]
created: 2026-06-14T07:37:55.125761
updated: 2026-07-23T07:42:44.788055
sources: ["omx-core/omx_core/wiki/gc.py", "omx-core/omx_core/wiki/ingest.py", "exp-analyze/SKILL.md"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# omx wiki has no delete subcommand by design: removal is gc-apply, duplicates come from add-with-new-title

There is NO `omx wiki delete` subcommand, and that is intentional, not a missing feature. A session reading only the project rules or `omx wiki --help` can wrongly conclude 'delete does not exist' -- that happened in a 2026-06-14 session.
WHY no delete: omx wiki is append-merge (INV-2, 'knowledge accrues without loss'). `add` derives the slug from the title (storage.title_to_slug) and on a slug collision MERGES into the existing page (appends a timestamped `## Update` section), never overwrites. So a normal 'edit' (re-add under the SAME title) does NOT create a duplicate.
WHERE duplicates actually come from: re-adding the SAME knowledge under a DIFFERENT (evolved) title forks the slug, leaving two coexisting pages. Example seen on disk: engine_gap_eval_adapter_covers_static_segmented_periodic_* vs engine_gap_eval_adapter_only_covers_static_periodic_*.
HOW to remove/dedup (the real delete path): never rm/Edit/Write the .md (bypasses lock + index regen + git-recovery guard). Use the git-guarded two-phase gc path: `omx wiki gc` (read-only diagnosis) -> write a `kind: wiki-gc` proposal with `## DELETE` / `## MERGE` sections + one-line reasons -> human edits/approves the proposal -> `omx wiki gc-apply --proposal <f>`. gc-apply validates every slug exists + is git-tracked + no self-merge, then deletes/merges atomically (partial apply impossible). Full procedure: exp-analyze/SKILL.md '## Wiki maintenance (gc)'. Contrast: omc wiki exposes wiki_delete (immediate, no git guard) as a first-class op; omx deliberately did NOT copy that, choosing safe two-phase gc instead.

---

## Update (2026-07-23T07:42:44.788055)

2026-07-23 curation: CORRECTION -- `omx wiki delete` now exists as a deprecation-redirect stub (.claude/rules/02-operations.md: the slug argument is ignored, it always returns {"error": "deprecated", ...} pointing at the gc path). The page's central claim 'no delete subcommand exists' is now false; the underlying removal mechanism it describes (git-guarded gc / gc-apply) remains accurate. Note: confidence recalibration to medium was attempted but the wiki CLI's merge policy only allows confidence to increase (max-rank), never decrease (omx_core/wiki/ingest.py), so confidence stays high -- flagging the mismatch here instead.
