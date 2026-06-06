---
title: "report completeness gate must run BEFORE writing, not after"
tags: ["exp-analyze", "report", "completeness", "workflow"]
created: 2026-06-06T09:43:37.013233
updated: 2026-06-06T09:43:37.013233
sources: ["diagnose-20260606-183657"]
links: []
category: debugging
confidence: high
schemaVersion: 1
---

# report completeness gate must run BEFORE writing, not after

Hard-won 2026-06-06 (dr_harder teacher report failed 3x for the SAME reason): I picked 'what looked important' (reward, constraint, eval) by feel and wrote the report, THEN ran the metrics.yaml group coverage check afterwards -- which found 4 of 7 diagnostic groups missing (trpo line_search/surrogate/grad, critic value_loss/cost_value, encoder z_std/z_min/z_max, doraemon success_rate/entropy_before/kl_step + per-param mean/std). The data was already aggregated in /tmp -- I just never transcribed it into the report body. ROOT CAUSE: completeness was treated as a post-hoc audit, not a pre-write gate. CORRECT WORKFLOW: (1) expand metrics.yaml 'groups' FIRST and turn each group into a TodoWrite checklist item; (2) write each section to satisfy its group; (3) run 'omx report-coverage' (or the python group-token self-check) and prove 7/7 BEFORE declaring done. The lint exists precisely to force this; running it after writing instead of before makes the tool useless. This is the same pattern as the engine-skip (1st) and partial-coverage (2nd) failures: 'enforce completeness as an output gate, never verify it after the fact.' Self-check snippet: load metrics.yaml groups, for each group assert >=1 token (bare name, prefix-stripped) appears in report.md.lower().
