# `pairDR` covers the 23 DR dims the eval actually records, and `thrust_coefficien

- id: finding/356 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: pairdr-covers-the-23-dr-dims-the-eval-actually-records-and-thrust_coefficien · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: `pairDR` covers the 23 DR dims the eval actually records, and `thrust_coefficient_scale` is not one of them, so the two 

`pairDR` covers the 23 DR dims the eval actually records, and `thrust_coefficient_scale` is not one of them, so the two arms share the section-5 band by construction rather than by measurement — `p4_runner.sh` passes the identical `DELTA` override to both. The scorer's `pairing()` computes `max|dr_* difference|` over exactly those recorded keys, so a discrepancy in an unrecorded dim would not raise `pairDR`.

[EVIDENCE: `np.load('.hq/work/p4c/p3b_finalC/healthy/data_hard.npz')` gives 23 `dr_*` keys (added_mass_0-5, body_mass, cob_x/y/z, cog_x/y/z, lin_damp_0-5, payload_cog_x/y/z, payload_mass) and zero containing `thrust`; `p4_score.py` `pairing(a, b)`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

`pairDR` covers the 23 DR dims the eval actually records, and `thrust_coefficient_scale` is not one of them, so the two arms share the section-5 band by construction rather than by measurement — `p4_runner.sh` passes the identical `DELTA` override to both. The scorer's `pairing()` computes `max|dr_* difference|` over exactly those recorded keys, so a discrepancy in an unrecorded dim would not raise `pairDR`.

[EVIDENCE: `np.load('.hq/work/p4c/p3b_finalC/healthy/data_hard.npz')` gives 23 `dr_*` keys (added_mass_0-5, body_mass, cob_x/y/z, cog_x/y/z, lin_damp_0-5, payload_cog_x/y/z, payload_mass) and zero containing `thrust`; `p4_score.py` `pairing(a, b)`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge
