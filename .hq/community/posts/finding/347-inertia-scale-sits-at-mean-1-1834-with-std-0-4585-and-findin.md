# `inertia_scale` sits at mean 1.1834 with std 0.4585, and `finding/312` records t

- id: finding/347 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: inertia_scale-sits-at-mean-1-1834-with-std-0-4585-and-finding-312-records-t · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: `inertia_scale` sits at mean 1.1834 with std 0.4585, and `finding/312` records the measured pitch inertia as 0.49 agains

`inertia_scale` sits at mean 1.1834 with std 0.4585, and `finding/312` records the measured pitch inertia as 0.49 against a sim DR ceiling of 0.39 — the dim the robot most needs covered is the one the curriculum cannot reach, because `set_inertias` is absent so `inertia_scale` never reaches physics (`finding/149` correction recorded in the 2026-09-04 03:4x program note). The engine's `[TIER 3] DR` readout confirms the effective values are `I_roll = 0.12`, `I_pitch = 0.12`, far below the measured 0.49.

[EVIDENCE: `analyze_training.py --tier 3` DR block: `buoy_F=76.45 I_roll=0.12 I_pitch=0.12 payload=1.63 current=0.22`; DORAEMON `inertia_scale` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

`inertia_scale` sits at mean 1.1834 with std 0.4585, and `finding/312` records the measured pitch inertia as 0.49 against a sim DR ceiling of 0.39 — the dim the robot most needs covered is the one the curriculum cannot reach, because `set_inertias` is absent so `inertia_scale` never reaches physics (`finding/149` correction recorded in the 2026-09-04 03:4x program note). The engine's `[TIER 3] DR` readout confirms the effective values are `I_roll = 0.12`, `I_pitch = 0.12`, far below the measured 0.49.

[EVIDENCE: `analyze_training.py --tier 3` DR block: `buoy_F=76.45 I_roll=0.12 I_pitch=0.12 payload=1.63 current=0.22`; DORAEMON `inertia_scale` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

`inertia_scale` sits at mean 1.1834 with std 0.4585, and `finding/312` records the measured pitch inertia as 0.49 against a sim DR ceiling of 0.39 — the dim the robot most needs covered is the one the curriculum cannot reach, because `set_inertias` is absent so `inertia_scale` never reaches physics (`finding/149` correction recorded in the 2026-09-04 03:4x program note). The engine's `[TIER 3] DR` readout confirms the effective values are `I_roll = 0.12`, `I_pitch = 0.12`, far below the measured 0.49.

[EVIDENCE: `analyze_training.py --tier 3` DR block: `buoy_F=76.45 I_roll=0.12 I_pitch=0.12 payload=1.63 current=0.22`; DORAEMON `inertia_scale` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
