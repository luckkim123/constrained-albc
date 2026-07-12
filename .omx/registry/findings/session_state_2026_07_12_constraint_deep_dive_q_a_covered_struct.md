---
title: "Session state 2026-07-12: constraint deep-dive (Q&A) -- covered structure/prob-avg/reward-cost-parallel/classification/thresholds; 2 wiki pages + constraints.md 3.2/3.4/4.3/4.6 + 1 PROMPT; pending 5/9"
tags: ["session-log", "constraint", "deep-dive", "resume-marker", "2026-07-12"]
created: 2026-07-12T08:29:32.109454
updated: 2026-07-12T09:25:32.086868
sources: []
links: ["reward_md_deep_dive_session_2026_07_11_4_review_fix_prompts_queu.md", "reward_cost_parallel_structure_mostly_mirroring_two_real_couplin.md", "constraint_threshold_budget_tuning_thresholds_split_into_hard_ph.md", "constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Session state 2026-07-12: constraint deep-dive (Q&A) -- covered structure/prob-avg/reward-cost-parallel/classification/thresholds; 2 wiki pages + constraints.md 3.2/3.4/4.3/4.6 + 1 PROMPT; pending 5/9

Interactive constraint deep-dive (Q&A mode, user asks / assistant explains from code; fixes go
to .sp/plans PROMPTs, knowledge goes to docs + omx wiki). Sister to the 2026-07-11 reward.md
deep-dive [[reward_md_deep_dive_session_2026_07_11_4_review_fix_prompts_queu]]. This page is the
resume marker so a post-compaction session knows what was covered and what remains.

## Covered (constraints.md walked section by section)

- §1 structure: 3-layer (definitions / IPO optimization / wiring), optimizer has ZERO prob-vs-avg
  branches.
- §2 prob/avg taxonomy: theoretically a correct CMDP reduction (prob = average constraint on a
  {0,1} indicator). "No distinction" true only at optimizer-logic level; numerical layer
  (std floor min=1.0) is implicitly binary-aware; prob constraints are gradient-dark in deep slack
  (explains §9 inert attitude/cumul_yaw).
- reward/cost PARALLEL structure: justified mirroring, NOT lazy reuse. Two real couplings found ->
  [[reward_cost_parallel_structure_mostly_mirroring_two_real_couplin]] + PROMPT (triage).
- §3 classification + hard-rail vs soft-shaping thresholds + actuator hard-cap layering ->
  [[constraint_threshold_budget_tuning_thresholds_split_into_hard_ph]].
- avg-max = time-averaged soft-peak (theoretically fine).

## Artifacts produced this session (all persisted)

1. omx wiki (2 new pages, both quality 100):
   `reward_cost_parallel_structure_mostly_mirroring_two_real_couplin.md`,
   `constraint_threshold_budget_tuning_thresholds_split_into_hard_ph.md`.
2. docs/reference/constraints.md (+ .ko mirror): §3.2 (max soft-peak), §3.4 NEW (threshold
   provenance / actuator layering), §4.3 (feasibility = GAE-return estimator coupling), §4.6
   (separate critics + shared grad-clip coupling).
3. .sp/plans/PROMPT_constraint_reward_cost_parallel_coupling_triage.md (confirm-then-fix work
   order for the two couplings; NOT git-tracked, /workspace is not a repo).

## Pending / not yet done

- constraints.md §5 (margin normalization J_C/d_k) and §9 (which constraints actually bind) were
  NOT yet walked in Q&A -- natural next topics if the deep-dive resumes.
- cumul_yaw 8*pi -> 6*pi: user intent = cosmetic (a). Recorded as a behavioral NO-OP (peak ~1.22
  rev << 3 rev); NO fix-prompt created, NO functional change queued. Rides a future config touch.
- The two reward/cost couplings are (C)-tentative; the PROMPT gates any code change on runtime
  evidence (value-group grad-norm split; GAE-return vs raw-MC feasibility).

## Branch / commit state

Work done on branch exp/latency-dr. constraint_trpo.py / _policy_base.py cites verified against
disk (exp/latency-dr) this session; the reward.md branch-stale caveat is rewards.py-specific and
does NOT affect the constraint_trpo.py cites. Doc + wiki changes committed at compaction-prep.

---

## Update (2026-07-12T09:25:32.086868)

## UPDATE (later same day 2026-07-12): §4 optimization walked + theoretical review DONE

After the original marker above, the Q&A continued into §4 (ConstraintTRPO optimization) and
then a theoretical-soundness review with web research + an independent critic + the NORBC paper.

**Covered now (beyond the original marker):**
- §4 optimization explained (update() 6-step flow, combined surrogate = reward - barrier -
  entropy, IPO log-barrier + adaptive threshold, TRPO natural-gradient CG/line-search, Fisher =
  pure KL Hessian, separate value update).
- Theoretical review: independent critic (oh-my-claudecode:critic, Opus) confirmed two "soft
  spots" -- then reading the NORBC paper RESOLVED both as design, not bugs.

**Key resolution -- ConstraintTRPO = FAITHFUL NORBC "Modified IPO" (Kim et al., arXiv:2308.12517v4,
2024; docstring L16-18).** Code<->NORBC Eq.(8)/(10)/(11) + multi-head cost value map 1:1. The
raw-J_C-vs-standardized-A_C barrier asymmetry is NORBC Eq.(10) verbatim (zero-mean => always
feasible; std half = multi-constraint gradient conditioning; permissive effect dormant unless a
constraint's cost-adv std>1). Soft (non-CPO) feasibility is NORBC's acknowledged trade-off. Full
detail: [[constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1]].

**Corrections logged (retractions):**
- "barrier diverges to +inf and auto-rejects the step" -> WRONG. `margin.clamp(min=1e-8)` (`:464`)
  CAPS the barrier at -log(1e-8)/100 ~= 0.184 per constraint; a reward gain above that crosses the
  boundary. The clamp is a numerical guard NOT in NORBC Eq.(9)/(10).
- "NORBC is an unverifiable/possibly-fabricated citation" -> RETRACTED (real, Kim et al. 2024).

**Artifacts this segment (all persisted):**
1. omx wiki new page `constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1` (quality 100).
2. docs/reference/constraints.md (+ .ko): §4 intro NEW provenance para; §4.1 barrier-cap 0.184
   correction; §4.3 standardization = NORBC-design resolution.
3. .sp/plans/PROMPT_barrier_clamp_comment.md (comment-only code follow-up for `:464`; NOT tracked).
4. Commit **f3efe80** on exp/latency-dr (5 files: 2 docs + wiki page + registry index/log).

**Code-fix verdict: NO functional fix required.** Standardization + soft feasibility are NORBC
design; the only code-level item is the barrier-clamp comment (PROMPT above). The one empirical
follow-up is a runtime probe (does any constraint's cost-adv std exceed 1; is the 0.184 cap hit).

**Pending UNCHANGED:** constraints.md §5 (margin normalization J_C/d_k) and §9 (which constraints
actually bind) were still NOT walked in Q&A -- natural next topics if the deep-dive resumes.

