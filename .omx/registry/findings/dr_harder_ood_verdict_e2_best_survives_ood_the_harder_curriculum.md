---
title: "DR-harder OOD verdict: E2-best survives OOD; the harder curriculum (E1) generalizes WORST"
tags: ["dr-harder", "ood", "generalization", "overfit", "doraemon", "attitude"]
created: 2026-06-06T13:27:54.764400
updated: 2026-06-06T13:27:54.764400
sources: ["trpo_main_teacher_260525_232805/eval/static_260606_215248", "trpo_e1_kl_ub_012_260605_193501/eval/static_260606_220436", "trpo_e2_ocean_shift_260606_055938/eval/static_260606_220436"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# DR-harder OOD verdict: E2-best survives OOD; the harder curriculum (E1) generalizes WORST

The decisive dr-harder OOD eval was run (held-out thruster x1.4 past the fixed
training range + cog/cob offsets at the DORAEMON ceiling mean+2std x1.5, appended
as a 5th `ood` level via `eval.py static --ood`, 64 env). It RESOLVES the question
the in-distribution reports could not.

OOD attitude (att_norm) ss_error, lower = better generalization:
- teacher : OOD 2.00 deg (in-dist hard 1.28) -- BEST OOD
- E2 ocean-shift : OOD 2.27 deg (in-dist hard 1.33) -- 2nd, near teacher
- E1 kl_ub 0.12 : OOD 3.18 deg (in-dist hard 1.82) -- WORST OOD

Two findings overturn the prior in-dist hypothesis ("E2 overfit -> worst OOD"):

1. **E2 is NOT worst OOD; it is 2nd and the most UNIFORM.** Despite the entropy
   collapse (-0.60) and none-level CV ~0%, E2's OOD att is near the teacher's and
   its OOD att CV is the LOWEST of the three (189% vs teacher 216%, E1 223%). Its
   OOD roll worst-env (ss_max 19.87 deg) is the best of the three. So "best
   in-dist tracker" (reward 254, hard roll 1.19) does NOT collapse out-of-dist.
   The overfit flags (entropy collapse, bad HMM regime) remain real concerns but
   did NOT manifest as OOD fragility.

2. **The aggressive curriculum (E1, kl_ub 0.12) generalizes WORST.** It pushed DR
   ~3.6x harder (ocean mean 0.118 -> 0.421) but paid for it in-dist (hard att 1.82
   vs teacher 1.28) AND that penalty AMPLIFIES OOD: OOD att 3.18 deg, worst-env
   roll diverges to 33 deg (teacher/E2 ~20). Preserved exploration (entropy +0.16,
   not collapsed) did NOT buy better OOD generalization -- the opposite.

Common to all three: the OOD gap is an ATTITUDE-ONLY (roll) gap (+56/71/75% on
att_norm; lin_vel and yaw generalize cleanly), and OOD turns the in-dist DC-bias
dispersion into a genuine roll heavy-tail -- roll pct_peak_gt_thresh goes 0% (all
3 in-dist hard) -> 3.1% (all 3 OOD). Physics: cog/cob offset -> restoring torque
-> roll DC-bias is the dominant OOD failure mode, matching the design rationale.

Net: dr-harder's "push DR harder" lever (E1) HURT OOD generalization; the
center-shift overfit (E2) did not help OOD beyond the plain teacher. The teacher
baseline generalizes best. Supersedes the "OOD is the missing test" page
(that gap is now closed).

