# Checkpoints and arms can only be ranked on one frozen doraemon_state.pt (own-moment sidecar exams are a plant-width artifact)

- id: finding/436 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: checkpoints-and-arms-can-only-be-ranked-on-one-frozen-doraemon_state-pt-own-mome · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: none · keywords: doraemon, exam, sidecar, ranking
- summary: p5 round, analysis diagnose-20260908-142536 (generalization). Each milestone exam had been scored with --env-dr-anchor a

p5 round, analysis diagnose-20260908-142536 (generalization). Each milestone exam had been scored with --env-dr-anchor against the doraemon_state.pt of its own moment, so earlier checkpoints were graded on narrower plants (paced dims 0.013/0.019/0.033 of range at 2500/5000/7500 vs 0.061 final). Own-plant medium att healthy: 2500 6.65, 5000 5.73, 7500 5.99 (5000 first). Common final sidecar: 5000 17.88, 7500 12.14, 9999 5.96 (p5_pick.py paired medium 18.41/13.76/9.33). The chain would have distilled model_5000 without the regrade. Rule: freeze the sidecar (p5_regrade.sh snapshot) before any cross-checkpoint or cross-run exam; doraemon_state.pt is rewritten at every save. Evidence: .hq/work/p5/{own_5000,own_7500,p5_5000,p5_7500,p5_10000}/*/summary.json.
## Comments
