# `Constraint/barrier_penalty` ends at −0.1269 with 3 spikes above 0.01 and a maxi

- id: finding/344 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: constraint-barrier_penalty-ends-at-0-1269-with-3-spikes-above-0-01-and-a-maxi · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: `Constraint/barrier_penalty` ends at −0.1269 with 3 spikes above 0.01 and a maximum of 0.147, which the engine flags as 

`Constraint/barrier_penalty` ends at −0.1269 with 3 spikes above 0.01 and a maximum of 0.147, which the engine flags as the barrier gradient briefly overwhelming the reward at small margins. With `barrier_t` 100.0 and thruster utilisation the binding constraint, this is consistent with the fault curriculum pushing the remaining thrusters toward their budget rather than with a constraint misconfiguration.

[EVIDENCE: `analyze_training.py` `[TIER 2]`: `barrier_penalty last=-0.1269 spikes(>0.01)=3 max=0.147`; `[DIAGNOSIS]` item 3; `[CONFIG] barrier_t=100.0`]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

`Constraint/barrier_penalty` ends at −0.1269 with 3 spikes above 0.01 and a maximum of 0.147, which the engine flags as the barrier gradient briefly overwhelming the reward at small margins. With `barrier_t` 100.0 and thruster utilisation the binding constraint, this is consistent with the fault curriculum pushing the remaining thrusters toward their budget rather than with a constraint misconfiguration.

[EVIDENCE: `analyze_training.py` `[TIER 2]`: `barrier_penalty last=-0.1269 spikes(>0.01)=3 max=0.147`; `[DIAGNOSIS]` item 3; `[CONFIG] barrier_t=100.0`]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

`Constraint/barrier_penalty` ends at −0.1269 with 3 spikes above 0.01 and a maximum of 0.147, which the engine flags as the barrier gradient briefly overwhelming the reward at small margins. With `barrier_t` 100.0 and thruster utilisation the binding constraint, this is consistent with the fault curriculum pushing the remaining thrusters toward their budget rather than with a constraint misconfiguration.

[EVIDENCE: `analyze_training.py` `[TIER 2]`: `barrier_penalty last=-0.1269 spikes(>0.01)=3 max=0.147`; `[DIAGNOSIS]` item 3; `[CONFIG] barrier_t=100.0`]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
