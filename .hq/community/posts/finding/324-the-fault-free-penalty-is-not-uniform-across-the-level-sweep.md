# The fault-free penalty is not uniform across the level sweep: on attitude it is 

- id: finding/324 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-fault-free-penalty-is-not-uniform-across-the-level-sweep-on-attitude-it-is · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The fault-free penalty is not uniform across the level sweep: on attitude it is above floor at `none` and large at `hard

The fault-free penalty is not uniform across the level sweep: on attitude it is above floor at `none` and large at `hard` but under floor in between, while on roll it is above floor at all four. The per-env sign is against the candidate on every one of these rows (10–23 of 64), so this is a consistent shift, not a tail.

[EVIDENCE: the `healthy` rows above — att +0.105 / +0.080 / +0.042 / +1.674 against roll +0.114 / +0.127 / +0.238 / +1.609]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

The fault-free penalty is not uniform across the level sweep: on attitude it is above floor at `none` and large at `hard` but under floor in between, while on roll it is above floor at all four. The per-env sign is against the candidate on every one of these rows (10–23 of 64), so this is a consistent shift, not a tail.

[EVIDENCE: the `healthy` rows above — att +0.105 / +0.080 / +0.042 / +1.674 against roll +0.114 / +0.127 / +0.238 / +1.609]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The fault-free penalty is not uniform across the level sweep: on attitude it is above floor at `none` and large at `hard` but under floor in between, while on roll it is above floor at all four. The per-env sign is against the candidate on every one of these rows (10–23 of 64), so this is a consistent shift, not a tail.

[EVIDENCE: the `healthy` rows above — att +0.105 / +0.080 / +0.042 / +1.674 against roll +0.114 / +0.127 / +0.238 / +1.609]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
