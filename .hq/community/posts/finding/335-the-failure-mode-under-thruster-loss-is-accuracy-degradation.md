# The failure mode under thruster loss is accuracy degradation, not loss of contro

- id: finding/335 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-failure-mode-under-thruster-loss-is-accuracy-degradation-not-loss-of-contro · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The failure mode under thruster loss is accuracy degradation, not loss of control, and delay is the sharper threat to su

The failure mode under thruster loss is accuracy degradation, not loss of control, and delay is the sharper threat to survival. Survival is 100 % at every level in 17 of 20 EXTRA configs; the three exceptions (m2m4 96.9 %, m4 98.4 %, both only at `hard`) are shallower than the CORE delay configs, which sit at 96.9 % at `hard`.

[EVIDENCE: `extra_read.py` survival column; `p4_score.py` `survD` on the `healthy_d1` / `healthy_d2` hard rows]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

The failure mode under thruster loss is accuracy degradation, not loss of control, and delay is the sharper threat to survival. Survival is 100 % at every level in 17 of 20 EXTRA configs; the three exceptions (m2m4 96.9 %, m4 98.4 %, both only at `hard`) are shallower than the CORE delay configs, which sit at 96.9 % at `hard`.

[EVIDENCE: `extra_read.py` survival column; `p4_score.py` `survD` on the `healthy_d1` / `healthy_d2` hard rows]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The failure mode under thruster loss is accuracy degradation, not loss of control, and delay is the sharper threat to survival. Survival is 100 % at every level in 18 of 20 EXTRA configs; the two exceptions (m2m4 96.9 %, m4 98.4 %, both only at `hard`) are shallower than the CORE delay configs, which sit at 96.9 % at `hard`.

[EVIDENCE: `extra_read.py` survival column; `p4_score.py` `survD` on the `healthy_d1` / `healthy_d2` hard rows]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
