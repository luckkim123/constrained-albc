# DORAEMON SLSQP rejections are invisible in DORAEMON/mode: the signature is kl_step 0 + ess_ratio 1.0 at an update step, confirmed only by the console

- id: finding/437 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: doraemon-slsqp-rejections-are-invisible-in-doraemon-mode-the-signature-is-kl_ste · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: doraemon, slsqp, curriculum, diagnostic
- summary: p5 r4450 segment, analysis diagnose-20260908-142536 (doraemon). Six of 22 updates (4749, 5749, 6749, 6999, 7749, 8749) p

p5 r4450 segment, analysis diagnose-20260908-142536 (doraemon). Six of 22 updates (4749, 5749, 6749, 6999, 7749, 8749) printed [DORAEMON] Entropy opt rejected (Singular matrix E / Positive directional derivative / Iteration limit) while mode stayed 0 because metrics[mode]=0.0 is set on the feasible branch before the optimizer result (marinelab/algorithms/doraemon.py). Check: at an update step read DORAEMON/kl_step and ess_ratio from tfevents (0 and 1.0 = rejected) and grep the console for Entropy opt rejected. A rejection costs one update of widening (27 percent duty loss here). The 6499-6999 live hold was two rejections back to back, first misread as the alpha boundary.
## Comments
