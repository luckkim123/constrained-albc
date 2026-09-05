# The DR dim the robot most needs is the one that cannot reach physics: measured pitch inertia 0.49 against an effective 0.12

- id: finding/354 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-dr-dim-the-robot-most-needs-is-the-one-that-cannot-reach-physics-measured-pi · supersedes: none
- topic: reference
- confidence: high · status: needs-experiment
- verified: none · keywords: inertia, dr, set_inertias, sim2real, gap
- summary: Measured 2026-09-05 from the as-run engine readout of trpo_p3b_lb200_s30_r2050_260904_163518 (analysis diagnose-20260905

Measured 2026-09-05 from the as-run engine readout of trpo_p3b_lb200_s30_r2050_260904_163518 (analysis diagnose-20260905-060354). analyze_training.py [TIER 3] DR prints buoy_F=76.45 I_roll=0.12 I_pitch=0.12 payload=1.63 current=0.22, while DORAEMON reports inertia_scale mean 1.1834 std 0.4585 SATURATED - i.e. the curriculum believes it is randomizing inertia while the effective value never moves off 0.12. finding/312 records the measured assembly pitch inertia as 0.49 against a nominal sim DR ceiling of 0.39, and the finding/149 correction (program note 2026-09-04 03:4x) established the mechanism: set_inertias is absent so inertia_scale never reaches physics. So the retrained teacher trained with an effective pitch inertia roughly 4x below the real vehicle and no curriculum coverage of the gap. This is carried into deployment as-is. NEXT PROBE: implement set_inertias and re-measure the effective I_pitch under a nonzero inertia_scale before trusting any inertia-related sim-to-real margin.
## Comments
