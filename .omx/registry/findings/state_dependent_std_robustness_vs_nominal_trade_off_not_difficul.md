---
title: "state_dependent_std: robustness-vs-nominal trade-off, NOT difficulty-adaptive (Phase-2 falsification)"
tags: ["state_dependent_std", "action_std", "falsification", "ood", "exploration", "retry-candidate", "fault-tolerant", "adaptivity", "heavy-tail", "roll", "attitude_only"]
created: 2026-06-08T21:56:24.254183
updated: 2026-07-13T05:32:01.361233
sources: ["diagnose-20260609-064938", "diagnose-20260609-125556"]
links: ["engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# state_dependent_std: robustness-vs-nominal trade-off, NOT difficulty-adaptive (Phase-2 falsification)

state_dependent_std (per-state log_std head, 16D actor) vs global log_std baseline on attitude_only (run trpo_state_std_260609_011906 vs trpo_baseline_260608_172710). VERDICT: NOT a clean null -- a robustness-vs-nominal TRADE-OFF. Eval att_norm ss_error (summary.json): none +348% (0.968 vs 0.216 deg, WORSE) monotone -> ood -34.5% (0.750 vs 1.146, BETTER). CV lower at hard/ood (hard 137 vs 223%, ood 142 vs 234%); yaw heavy-tail CV collapses (hard 52 vs 350%). Training reward parity at convergence (+5.1% iter4999; early -12% was LAG not intrinsic, baseline late-regressed). MECHANISM (adaptivity probe, model_4999 actor head on 512 obs): per-state std IS state-varying (cross-state CV 45.6%) but does NOT track difficulty (corr +0.04) -- so the theoretical payoff (wide noise on hard states) did NOT emerge; OOD win is a byproduct of a globally-TIGHTER converged std (0.167 vs 0.175) helping where baseline's larger noise hurts. thruster_util binds harder (J_C/d_k 0.903 vs 0.807 = authority starvation). NOT worth adopting: +348% nominal regression disqualifying; OOD gain not from intended mechanism -- a global-std schedule / lower late min_std could reproduce it cheaper. FVP integration (allow_unused for the unused global log_std) verified correct: line_search 100%, KL bounded. (analysis diagnose-20260609-064938)

---

## Update (2026-06-14T07:38:30.793420)

REVISIT INTENT (user, 2026-06-14): this experiment is a KEEP-FOR-RETRY candidate, NOT a discard. The earlier "NOT worth adopting" line should be read as "not adoptable AS-IS in this exact form," NOT as "the idea is dead." The user explicitly wants to run a state-dependent-std variant again later. So the verdict is softened to: PARK, do not bury.
WHY it is worth a second attempt (the non-null is real, on the OUTCOME side):
- OOD att_norm ss_error -34.5% (0.750 vs 1.146 deg) — a genuine out-of-distribution improvement.
- worst-env roll tail 19.7 deg -> 5.6 deg (~3.5x cut at OOD); yaw heavy-tail CV collapses 350% -> 52% (hard).
- survival 100% at every DR level both runs; training reward parity at convergence (+5.1% iter4999). No stability cost.
So the tail-robustness / heavy-tail win is real and matches the FTC research direction (tail guarantees). What FAILED was only the STATED MECHANISM (difficulty-adaptive noise: corr(per-state std, real-DR difficulty) = -0.03 ~ 0), and the COST (nominal none +348%, 0.97 vs 0.22 deg) — both are addressable design choices, not dead ends.
WHAT TO CHANGE on the retry (so the next attempt is not a re-run of the same disqualifying form):
- The +348% nominal regression is the disqualifier, NOT the std-conditioning itself. Attack the nominal cost directly: e.g. floor the per-state std lower in easy/nominal states, or warm-start the head from the converged global log_std so easy-state precision is not sacrificed during warmup.
- Since the OOD win traced to a globally-TIGHTER converged std (0.167 vs 0.175), not to difficulty adaptation, a cheaper ablation arm is worth pairing: a plain global-std SCHEDULE (or lower late min_std) with NO per-state head — if that alone reproduces the OOD tail win, the per-state head is not needed; if it does NOT, the head is doing something the schedule cannot, which revives the per-state approach.
- If the GOAL is genuinely difficulty-adaptive exploration (the original hypothesis), the head must be fed a difficulty-correlated signal — the current head's std is dominated by policy obs (cross-state CV ~32%) and decorrelated from DR (cross-env-DR CV ~9%). Consider conditioning std on the encoder latent z (which DOES carry DR) rather than raw policy obs, so the adaptive signal can actually form.
DATA CEILING to fix before re-judging the mechanism: eval npz saves no raw per-step obs / privileged vector, so the policy-obs leg of the std could not be reconstructed (difficulty-null is HIGH on the real DR cluster, but the absolute std magnitude per env is MED). See [[engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact]]. A retry should log raw obs so the adaptivity probe is exact.
STATUS: parked / retry-candidate. Full analysis = trpo_state_std_260609_011906/analysis/diagnose-20260609-125556 (report.md). Prior falsification facts in this page stand; only the adopt/discard framing is softened to retry-candidate. The concrete next-experiment config is exp-design's job, not this note.

---

## Merged from state_dependent_std_difficulty_null_now_confirmed_on_real_dr_med.md (2026-07-12T14:11:29.031769)

# state_dependent_std: difficulty-null now confirmed on REAL DR (MED->HIGH), OOD win is a TAIL effect

Deepening of diagnose-20260609-064938 (analysis diagnose-20260609-125556). (1) ADAPTIVITY NULL PROMOTED MED->HIGH: re-ran the std head (model_4999.pt, 16D=mean+log_std split, clamp[0.05,2.0]) over the 128 REAL hard+ood eval-DR envs (encoder fed real dr_* params from data_hard/ood.npz; policy obs held at actor_obs_normalizer mean). corr(per-state std-norm, composite physical-difficulty proxy) = -0.03 (was +0.04 on synthetic obs) -> the difficulty-decorrelation now holds on the REALIZED DR axis, not just synthetic obs. The std variation is dominated by POLICY OBS (cross-state CV ~32%) over DR (cross-env-DR CV 8.7%), and is localized to action dims 0,1 (arm; CV 30%/20%) while thruster dims 2-7 are near-flat (<13%). DATA LIMIT: eval npz saves no raw 69D obs / no privileged vector, so the policy-obs leg can't be the realized one — the null is HIGH, absolute std magnitudes MED. (2) THE OOD -34.5% WIN IS A TAIL EFFECT, not a median shift: per-env roll ss median nearly identical (state_std 0.31 vs baseline 0.26 deg) but worst-env roll collapses 19.7->5.6 deg at OOD (3.5x), worst-5 mean 5.63->2.65. So a simpler global-std schedule / lower late min_std could likely reproduce the tail effect without the per-state head's +348% nominal cost. Re-visit: report diagnose-20260609-125556 secs trpo(deepening-1)/generalization(deepening-3).

---

## Update (2026-07-13T05:32:01.361233)

RETRY-PLANNING NOTE (2026-07-13, post-p7_tail planning session): the mechanism premise has shifted under the new consolidated baseline. The June pair compared converged global std 0.175 (baseline) vs 0.167 (state_std head) and traced the OOD tail win to the GLOBALLY-TIGHTER converged std. The new reference baseline trpo_baseline_260713_031325 already converges to Policy/mean_noise_std 0.109 (report diagnose-20260713-081707 sec 3) — substantially tighter than BOTH June runs — yet still shows the hard-DR DC-bias heavy-tail (max/median 23.2x hard / 29.2x ood). This weakens variant (2) global-std-schedule as a retry arm (the 'tighter std' the schedule would buy is already there) and shifts the interesting retry toward variant (3) z-conditioned std (feed the DR-carrying encoder latent to the std head). PARK status unchanged; re-rank variants when the tail probes in flight (e1/e2 + budget-extension/xy-prune proposals next-20260713-1426xx) land.
