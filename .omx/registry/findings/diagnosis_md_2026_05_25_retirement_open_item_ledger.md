---
title: "DIAGNOSIS.md 2026-05-25 retirement: open-item ledger"
tags: ["backlog", "diagnosis", "cleanup", "debt"]
created: 2026-07-12T14:35:29.998767
updated: 2026-07-12T14:35:29.998767
sources: ["diagnosis-audit-2026-07-12"]
links: ["constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# DIAGNOSIS.md 2026-05-25 retirement: open-item ledger

DIAGNOSIS.md (root, 2026-05-25 audit snapshot) was retired 2026-07-12 after a full re-audit: 11 items DONE, 3 OBSOLETE (resolved by NORBC paper cross-check, see [[constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1]]), 14 genuinely open. The file is deleted (recoverable via git history); this page is the surviving ledger of the open items.

Open items (severity as originally triaged; file:line as of commit c5a8a08):

MEDIUM:
- Ocean-current OU clamp exceeds max_velocity by 5% (clamp_bound = max_vel * 1.05) — envs/main/albc_env.py:883-884 and envs/full_dof/albc_env.py:765-766. Decide: intentional headroom (document) or tighten.
- ConstraintTRPO minor math hygiene: cost-returns clamp(min=0) at constraint_trpo.py:457, a missing detach, a disabled assert, CG damping constant — analysis before change (rules/03 no-fix-without-evidence).
- TDC test gap: no TDE delay/rate-limit/OOD/update_gains tests (tests/test_tdc_controller.py has 19 tests, none of these; test_delay_buffer_behavior.py covers latency-DR DelayBuffer, not TDC's TDE buffer).
- Analysis layer: no MetricsConfig centralization (metric definitions still duplicated; matplotlib.use("Agg") scattered across 12 files); matplotlib figure leaks (no save_and_close helper) + YAML exception swallowing.

PHASE-C (user-gated by DIAGNOSIS's own rule — do not action without approval):
- Added-mass clamp uses DR'd inertia — envs/main/mdp/events.py:268-276 (physics-behavior change).
- (companion Phase-C physics items as listed in the original §2 batch.)

LOW:
- quat-align gradient concern — envs/main/albc_env.py:1044-1057; verified visualization-only call path (_update_payload_viz_markers), so LOW stands.
- LOW batch never actioned: integral accumulation, yaw wrap, manipulability norm, control-decimation doc, euler cache (albc_env.py:300, :689-693, :133-136).
- actor-critic duplication: PolicyBase._init_base now shares construction, but act/act_inference/update_normalization/load_state_dict still duplicated (encoder/actor_critic_encoder.py:272-296+ vs actor_critic_asym_constrained.py:121-139+).
- Runner helper duplication (_should_log/_save_aux_state/_load_aux_state) in constraint_encoder_runner.py:199-214 and on_policy_doraemon_runner.py:49-58.
- print-vs-logger ratio improved 7:1 -> 4:1 (351 print / 88 logger), not resolved.
- pyproject dependencies have no version bounds ("marinelab", "gymnasium", "torch", "numpy").

OPTIONAL / conditional (never committed to):
- TDC controller C++/CUDA migration (Phase D).
- Promotion candidates to marinelab: TDC controller, ConstraintTRPO+IPO, BetaDistribution (marinelab/algorithms/ has only doraemon.py).

