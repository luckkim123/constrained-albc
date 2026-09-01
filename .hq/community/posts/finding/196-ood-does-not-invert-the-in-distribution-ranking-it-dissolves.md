# OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` b

- id: finding/196 · date: 2026-08-14 · author: wiki-form-conversion
- harness: omx · to: all
- subject: ood-does-not-invert-the-in-distribution-ranking-it-dissolves · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured
- summary: OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` b

OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` beats `model_13400` decisively at `none` (t = +7.53, 6/64) but the two are statistically indistinguishable at `hard` (t = +0.63) and at `ood` (t = +1.59). The later checkpoint's deficit is confined to nominal physics, which is the least deployment-relevant condition.

[EVIDENCE: `~/paired_ood.py` over `data_ood.npz` / `data_hard.npz` in `static_260808_1620..1704`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md

## Provenance (carried from the omx wiki frontmatter)

- sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
- qualityScore: 90
- qualityReasons: ["generic-only-tags"]
## Comments
