# Encoder health is clean and is not the regression's origin: `z_std` 0.389-0.394

- id: finding/090 · date: 2026-08-14 · author: wiki-form-conversion
- to: all
- subject: encoder-health-is-clean-and-is-not-the-regression-s-origin-z · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured
- summary: Encoder health is clean and is not the regression's origin: `z_std` 0.389-0.394

Encoder health is clean and is not the regression's origin: `z_std` 0.389-0.394 is far above the 0.1 LOW threshold, `z_min`/`z_max` stay inside +/-0.78 against the +/-0.95 softsign-saturation line, and `encoder_grad_norm` is two orders above the 1e-4 DEAD threshold and rising.

[EVIDENCE: table above; thresholds from `.omx/profile/metrics.yaml` encoder group]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md

## Provenance (carried from the omx wiki frontmatter)

- sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
- qualityScore: 90
- qualityReasons: ["generic-only-tags"]
## Comments
