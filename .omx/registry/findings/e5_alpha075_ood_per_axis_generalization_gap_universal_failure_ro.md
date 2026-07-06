---
title: "E5 alpha075 OOD per-axis generalization gap (universal failure = roll DC-bias doubles OOD)"
tags: ["dr-harder", "E5", "alpha", "OOD", "generalization-gap", "roll", "per-axis"]
created: 2026-07-06T02:12:29.437680
updated: 2026-07-06T02:12:29.437680
sources: ["trpo_260606_225859"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# E5 alpha075 OOD per-axis generalization gap (universal failure = roll DC-bias doubles OOD)

E5 (dr_harder, DORAEMON alpha 0.50->0.75) OOD eval per-axis generalization-gap table. Preserved here because E5's canonical exp-analyze report.md no longer exists on disk (the dr_harder run tree was reorganized after the campaign), so this per-axis OOD gap breakdown is now the only surviving copy. The E5 in-distribution verdict (alpha is a feasibility floor, no curriculum effect) is already in wiki `doraemon_alpha_is_a_feasibility_floor_*`; this page adds only the OOD generalization detail.

OOD DEFINITION: held-out thruster (thrust_coeff/time_const x1.4 past the fixed training range = less control authority) + magnitude OOD (cog/cob offset = DORAEMON ceiling x1.5 = more disturbance torque). 5 levels none/soft/medium/hard/ood + generalization_gap = ood - hard. Survival 100% at OOD (no divergence). model_4999, num_envs 64.

OOD ss_error + generalization gap (E5 vs teacher/E1/E2):
| axis | run | hard | ood | gap (ood-hard) |
|---|---|---|---|---|
| roll (deg) | teacher | 1.101 | 1.918 | +0.82 (+74%) |
| roll (deg) | E1 | 1.474 | 2.964 | +1.49 (+101%) |
| roll (deg) | E2 | 1.191 | 2.205 | +1.01 (+85%) |
| roll (deg) | E5 | 1.032 | 2.000 | +0.97 (+94%) |
| pitch (deg) | teacher | 0.352 | 0.239 | -0.11 (-32%) |
| pitch (deg) | E5 | 0.238 | 0.278 | +0.04 (+17%) |
| vz (m/s) | teacher | 0.017 | 0.008 | -0.01 (-52%) |
| vz (m/s) | E5 | 0.033 | 0.009 | -0.02 (-73%) |
| yaw (rad/s) | E5 | 0.0045 | 0.0021 | -52% |

READING:
- UNIVERSAL OOD failure mode = roll attitude DC-bias ~DOUBLES (every run +74-101%). The held-out thruster cut + beyond-ceiling cog/cob offset directly induce the roll restoring-torque bias (`hydrodynamics.py:483` CoB-CoG offset moment) — the attitude weakness the dr-harder reports flagged, amplified OOD. E5's OOD roll (2.00 deg) is 2nd-best absolute of the 4 (only teacher 1.92 lower; E1 2.96 worst, E2 2.20). E5's gap +94% is mid-pack.
- TRANSLATION IMPROVES under OOD (vz -73%, yaw -52%, vx -46%): the OOD axes stress attitude, not translation, and reduced thruster authority settles translation closer to target. So E5's in-dist weak-DR vz overfit (vz none +213%) does NOT carry into OOD — OOD vz is fine (0.009).
- NET: E5 generalizes to OOD comparably to teacher (survives 100%, best-of-4 pitch, 2nd-best roll). The alpha=0.75 change neither helped nor hurt OOD robustness materially, consistent with "alpha had no curriculum effect".

VERIFIED: E5 eval `eval/static_260607_041900/` (--ood path, generalization_gap object), independently re-derived and agreed with the (now-deleted) canonical report at analysis time. Source run trpo_260606_225859 (wandb dr_harder_e5_alpha075). Related: `dr_harder_ood_verdict_e2_best_survives_ood_*`, `doraemon_alpha_is_a_feasibility_floor_*`.

