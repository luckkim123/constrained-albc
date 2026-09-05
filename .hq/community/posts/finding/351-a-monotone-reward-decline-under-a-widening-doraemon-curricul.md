# A monotone reward decline under a widening DORAEMON curriculum is the difficulty tax, not divergence

- id: finding/351 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: a-monotone-reward-decline-under-a-widening-doraemon-curriculum-is-the-difficulty · supersedes: none
- topic: pattern
- confidence: high · status: none
- verified: none · keywords: doraemon, reward, diagnosis, false-positive, engine
- summary: analyze_training.py [DIAGNOSIS] item 2 fires -Reward declining in all 4 quarters. Training diverged.- on a purely monoto

analyze_training.py [DIAGNOSIS] item 2 fires -Reward declining in all 4 quarters. Training diverged.- on a purely monotone test, which a working run under a widening curriculum will trip. Measured 2026-09-05 (analysis diagnose-20260905-060354): reward fell 235.34 (it 2092) to 171.24 (it 9999) and DIAGNOSIS called divergence, while the SAME engine [TRENDS] module reported phase plateau(8), plateau YES since ~50 percent, stability cv=0.049 stable, changepoints 2226/5279/8210. Over the identical window fault_severity went 0.0132 to 0.4782 and obs_noise_scale to 0.4811. The held-out exam settled it: the final policy beats the incumbent 64/64 on pair34 pitch, which a diverged policy does not do. APPLY: when DIAGNOSIS says diverged, cross-read (1) the TREND cv and plateau verdict, (2) whether DR widened over the same window, (3) any held-out eval. Only a decline with rising cv AND flat difficulty is divergence.
## Comments
