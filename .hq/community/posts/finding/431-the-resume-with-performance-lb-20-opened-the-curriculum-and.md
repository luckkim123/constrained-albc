# The resume with `performance_lb` −20 opened the curriculum and it was still open

- id: finding/431 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-resume-with-performance_lb-20-opened-the-curriculum-and-it-was-still-open · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The resume with `performance_lb` −20 opened the curriculum and it was still opening at the last update. `DORAEMON/succes

The resume with `performance_lb` −20 opened the curriculum and it was still opening at the last update. `DORAEMON/success_rate` jumped to 0.99 at 4450 (nearly every buffered episode clears −20), decayed to the 0.77 first-tenth window and reached the α = 0.5 boundary around iteration 8000, ending at 0.48; `DORAEMON/entropy_before` rose −56.98 → −35.27 (`entropy_after` maximum −33.34 at 9999); `DORAEMON/kl_step` hit the `kl_ub` 0.12 cap at 4499 and averaged 0.0006 in the last tenth; `DORAEMON/ess_ratio` fell to a minimum of 0.147 at 4749 and ended at 0.44; `DORAEMON/mode` was 0 (feasible) on 21 of 22 updates and 1 (inverted step, success < α) at 8749 and after. Every one of the 23 dims widened: the Beta standard deviation grew ×1.75–×2.73 on the 17 physical dims and ×4.9–×9.6 on the six paced dims between the first (4499) and last (9999) records, and 23 of 23 were still widening between 9749 and 9999. The paced dims ended at 5–8 % of range (`control_delay_strength` 0.0607, `fault_severity` 0.0662, `fz_disturbance_strength` 0.0758, `obs_noise_scale` 0.0568, `ocean_current_strength` 0.0734, `payload_cog_offset_xy_u` 0.0531) — the curriculum is far from its ceiling, and the p3b precedent (`finding/403`: 9 of 21 dims still widening at 9999) is milder than this one.

[EVIDENCE: `tbread.py` seg 2 windows and `DORAEMON/mean/*` first/last; `misc.py` on `curriculum_trajectory.json` (23 records 4499–9999, Beta sd per dim first → last, widening count 23/23 at the last step); `analyze_training.py` `[TIER 2] DORAEMON` seg 2 (`success=0.45 ess_ratio=0.15 mode=1.00`, `EXPANDING` on 22 of 23 dims, `body_mass_scale` STALLED at 50.7 %), `[DIAGNOSIS]` item 3]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
