---
title: "How to read omx wiki lint on this corpus: oversized means accumulated updates, and contradiction-candidate is a tag-collision heuristic that never reads a claim"
tags: ["omx", "wiki", "lint", "curation", "triage", "meta", "omx-0.11.2"]
created: 2026-08-14T06:50:44.128488
updated: 2026-08-14T07:26:12.915857
sources: ["wiki-curation-2026-08-14", "omx-core 3e8147d", "omx-core 9ef2487"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# How to read omx wiki lint on this corpus: oversized means accumulated updates, and contradiction-candidate is a tag-collision heuristic that never reads a claim

Two of the six lint signals on this wiki are dominated by false positives, and a session that triages
them literally will burn a lot of reading for nothing. Measured on the post-curation corpus (264 pages,
2026-08-14).

OVERSIZED = A LONG-LIVED PAGE, NOT A VERBOSE ONE.
The lint fires above 10240 bytes. Across the 34 pages it flags, 373,591 of the 589,926 bytes -- 63% --
sit in APPENDED `## Update` blocks rather than in the original body. The worst offenders are 81-93%
update mass over 6 to 12 append cycles:
  93%  11 updates  on_policy_dagger_correction_for_the_buoyfix_student
  87%  12 updates  stonefish_yaw_gap_claim_review_main_body_hydro_yaw_torque_
  86%   6 updates  experiment_idea_latency_transport_delay_dr_sensor_obs_cont
  85%   8 updates  roll_transient_is_worst_at_none_dr_and_improves_monotonica
So oversized is measuring HOW OFTEN A TOPIC WAS REVISITED. On an append-only wiki that is a signal of
importance, not of bloat, and it is not fixable by editing -- the body cannot be rewritten, only
appended to. Do NOT open an oversized page expecting to trim it.
HOW TO READ ONE: the LAST update block is the current state; earlier blocks are history and are
frequently superseded by later ones. Read bottom-up.

CONTRADICTION-CANDIDATE NEVER COMPARES CLAIMS.
All 113 flags come from exactly two tag-collision heuristics, neither of which reads any page body:
  69  "N high-confidence <category> pages share tag <t>"
  44  "tag <t> appears across categories [...]"  (2 to 5 categories)
A shared tag is what a controlled tag vocabulary is FOR, and a tag legitimately spanning `reference`
and `decision` is the normal shape of a fact that drove a decision. The flag says two pages are about
the same subject; it says nothing about whether they disagree.
PRACTICAL RULE: treat contradiction-candidate as a topic INDEX, not a defect list. Real contradictions
in this wiki have been found by reading bodies -- the stonefish duplicate pair and the superseded-R2
pages were both caught that way, and the lint had flagged them under `near-duplicate`, not here.

WHICH SIGNALS ARE WORTH ACTING ON: `near-duplicate` (slug jaccard -- 10 flagged pre-curation, all
genuine), `broken-ref` (always real, and never repairable in place), `low-quality` (quality_score < 50),
and `open-lead` (the actionable-status roster, which is the launch gate's only input). `orphan` and
`stale` are informational -- an orphan is often a correctly-standalone reference page, and a page can be
untouched for 60 days because it is settled.

---

## Update (2026-08-14T07:26:12.915857)

AMENDMENT 2026-08-14, same day: `low-quality` is now trustworthy going forward but NOT on the three
pages currently flagged. omx-core v0.11.2 fixed the scorer -- `qualityScore` is computed on the merged
body instead of the incoming chunk, so a one-line close no longer demotes a rich page. Nothing
rescores a page that is not re-added, so the three historical victims keep their stale 40 on disk
until each is next updated:
  engine_gap_heavy_tail_json_pct_peak_gt_thresh_exceeds_100_at_ood   (2404 bytes, sourced)
  joint_dr_params_kp_kd_effort_friction_need_no_dedicated_measurem   (4733 bytes, sourced)
  tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_   (9394 bytes, sourced)
Read a `low-quality` flag by checking the page's SIZE first: thousands of bytes with sources means the
old scorer, not a weak page. A genuinely thin page is short.

The `oversized` and `contradiction-candidate` readings above are unaffected -- both are structural
properties of an append-only store, and neither was a scorer bug.

DETAIL: engine-gap qualityScore is computed on the incoming append only (now [STATUS] implemented).

