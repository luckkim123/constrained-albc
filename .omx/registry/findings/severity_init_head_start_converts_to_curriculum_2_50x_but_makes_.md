---
title: "Severity-init head start converts to curriculum (2.50x) but makes m4-dead fault rejection 2.9-5.5x WORSE -- raising trained fault severity is not a route to fault tolerance on this plant"
tags: ["fault-tolerant-control", "ftc", "fault_severity", "doraemon", "curriculum", "m4", "thruster-fault", "e-ftc1", "screening", "single-seed", "correction"]
created: 2026-07-29T08:25:27.751562
updated: 2026-07-29T08:25:55.051979
sources: ["diagnose-20260729-171553", "trpo_ftc1sevinit_s30_260729_105510", "trpo_faultdr_agnostic_s30_260725_183121"]
links: ["ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Severity-init head start converts to curriculum (2.50x) but makes m4-dead fault rejection 2.9-5.5x WORSE -- raising trained fault severity is not a route to fault tolerance on this plant

[FINDING] E-ftc1 (fault_severity nominal init 0.0771, the ONLY change vs Arm A) reached 2.50x Arm A's curriculum endpoint yet its policy rejects the m4-dead fault 2.9x-5.5x WORSE at every DR level. Pre-registered verdict H1-WEAK (0.1929 in [0.15,0.20), 0.0071 under the H1 gate). [EVIDENCE: compare.py paired, delta att_norm ss_error deg = m4dead minus healthy -- none +0.834 vs +0.285 (2.93x), soft +0.922 vs +0.241 (3.83x), medium +1.372 vs +0.251 (5.47x), hard +1.416 vs +0.432 (3.28x); every cell REAL against the 0.10 deg floor in BOTH runs; reproduces on roll (+0.685..+1.028 vs +0.241..+0.309) and pitch (+0.372..+0.756 vs +0.095..+0.259) separately] [CONFIDENCE: HIGH] [WHY THE none CELL IS ADMISSIBLE] soft/medium/hard are self-graded (--doraemon-dr default True, each run on its own learned box) so their absolute values are inadmissible cross-run, but  applies no learned box and the eval drops the learned fault_severity dim entirely ([WARN] DomainRandomizationCfg has no field 'fault_severity'), so the fault condition is identical across runs and levels. [MECHANISM RULED OUT] Not reward regression (E-ftc1 leads on all 7 Reward/* terms and Train/mean_reward 263.98 vs 250.63); not encoder collapse (z_std 0.409, |z|max 0.729, grad 0.0295 -- all pass); not critic divergence (Loss/value_function 0.430, Loss/cost_value 0.728); NOT thruster-budget saturation -- thruster_util J_C/d_k moved AWAY from binding, 0.902 -> 0.890, so the proposal's stated hazard did not fire. [SHAPE] Uniform mean shift, not heavy tail:  m4-dead att_norm CV 0.35 (E-ftc1) vs 0.36 (Arm A), and E-ftc1 has FEWER extreme roll envs (n_gt40 1.67 vs 4.33). [LEADING UNEXPLAINED MECHANISM] Revives FTC composition-risk 3 from [[ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti]] -- a continuous 9D latent is the wrong prior for a discrete actuator dropout (Xu et al. arXiv:2606.02280) -- since severity exposure scaled 2.5x with no robustness gain. [CAVEAT] Single seed (30), paired screening; never a paper number. [WHERE] analysis diagnose-20260729-171553, sections 'tracking' and 'verdict'.

---

## Update (2026-07-29T08:25:55.051979)

[CORRECTION to the entry above] Two words were lost to shell backtick substitution when the entry was first written. Read those two clauses as: (1) "...inadmissible cross-run, but the none LEVEL applies no learned box and the eval drops the learned fault_severity dim entirely..."; (2) "[SHAPE] Uniform mean shift, not heavy tail: at the none LEVEL under m4-dead, att_norm CV 0.35 (E-ftc1) vs 0.36 (Arm A)...". No number changed; only the level name none was dropped. [EVIDENCE: analysis diagnose-20260729-171553 sections tracking and generalization carry both statements intact] [CONFIDENCE: HIGH]
