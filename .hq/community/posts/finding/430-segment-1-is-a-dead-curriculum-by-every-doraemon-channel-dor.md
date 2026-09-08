# Segment 1 is a dead curriculum by every DORAEMON channel: `DORAEMON/success_rate

- id: finding/430 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: segment-1-is-a-dead-curriculum-by-every-doraemon-channel-doraemon-success_rate · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Segment 1 is a dead curriculum by every DORAEMON channel: `DORAEMON/success_rate` 0.000 → 0.0008 (maximum 0.003 at itera

Segment 1 is a dead curriculum by every DORAEMON channel: `DORAEMON/success_rate` 0.000 → 0.0008 (maximum 0.003 at iteration 1311) against α = 0.5, `DORAEMON/entropy_before` −55.98 → −58.52 (it *contracted*), `DORAEMON/kl_step` 0 on every update but one (0.12 at 1500), `DORAEMON/ess_ratio` 1.0 → 0.39, `DORAEMON/mode` −3 then −2 for the rest of the segment. The six paced dims sat at their initial 0.01 (`control_delay_strength` 0.0127, `fault_severity` 0.0113, `fz_disturbance_strength` 0.0133, `obs_noise_scale` 0.0104, `ocean_current_strength` 0.0081, `payload_cog_offset_xy_u` 0.0098 — 0.8–1.3 % of range), and the engine's per-dim verdicts are `STALLED` for 17 of 23 dims. `performance_lb` 200 was unreachable: the buffer's mean return at iteration 4350 was −7 (median −1.8, 40th percentile −19.3).

[EVIDENCE: `tbread.py` seg 1 windows; `analyze_training.py` `[TIER 2] DORAEMON` (seg 1: `success=5.0e-04 ess_ratio=0.39 mode=-2.00`, verdict column); buffer-return percentiles from the resume script header `p5_teacher_resume.sh` (read from `doraemon_state.pt` at 4350)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
