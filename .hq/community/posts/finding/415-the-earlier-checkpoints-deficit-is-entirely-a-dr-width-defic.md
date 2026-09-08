# The earlier checkpoints' deficit is entirely a DR-width deficit. At `none` the t

- id: finding/415 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-earlier-checkpoints-deficit-is-entirely-a-dr-width-deficit-at-none-the-t · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The earlier checkpoints' deficit is entirely a DR-width deficit. At `none` the three checkpoints are within 0.2 deg of e

The earlier checkpoints' deficit is entirely a DR-width deficit. At `none` the three checkpoints are within 0.2 deg of each other on `healthy` (8.14 / 8.20 / 8.07) and at `soft` within 2.6 deg; at `medium` they split 17.88 / 12.14 / 5.96 and at `hard` 24.39 / 19.56 / 6.14, with 5000 and 7500 losing 1.6–4.7 pp of survival at `hard`. The final plant's DR box is what 5000 and 7500 never trained on.

[EVIDENCE: `exam_table.csv` rows tag ∈ {`p5_5000`, `p5_7500`, `p5_10000`}, cell `healthy`, all four levels; survival 96.9 / 98.4 / 100 at hard]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
