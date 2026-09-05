# Episode return fell 235.34 (end of segment 1, it 2092) → 171.24 (it 9999), and t

- id: finding/337 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: episode-return-fell-235-34-end-of-segment-1-it-2092-171-24-it-9999-and-t · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Episode return fell 235.34 (end of segment 1, it 2092) → 171.24 (it 9999), and the engine's `[DIAGNOSIS]` reads that as 

Episode return fell 235.34 (end of segment 1, it 2092) → 171.24 (it 9999), and the engine's `[DIAGNOSIS]` reads that as divergence. The engine's own `[TREND]` module contradicts it: `phase: plateau(8)`, `plateau: YES since ~50%`, `stability: cv=0.049 (stable)`, with changepoints at iterations 2226, 5279 and 8210. The reconciling fact is that difficulty rose monotonically over the same window — `fault_severity` 0.0132 (it 1056) → 0.4782, `obs_noise_scale` → 0.4811 — so a mild decline at cv 0.049 under a widening curriculum is the difficulty tax, not divergence. The held-out exam settles it: a diverged policy does not beat the incumbent 64/64 on `pair34` pitch.

[EVIDENCE: `analyze_training.py` `[TIER 1]` on both segments, `[TRENDS] reward`, `[DIAGNOSIS]` item 2; `p4_score.py` `pair34` pitch `none` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Episode return fell 235.34 (end of segment 1, it 2092) → 171.24 (it 9999), and the engine's `[DIAGNOSIS]` reads that as divergence. The engine's own `[TREND]` module contradicts it: `phase: plateau(8)`, `plateau: YES since ~50%`, `stability: cv=0.049 (stable)`, with changepoints at iterations 2226, 5279 and 8210. The reconciling fact is that difficulty rose monotonically over the same window — `fault_severity` 0.0132 at it 1056 (the 1000-iteration readout recorded in the program note of 2026-09-04 15:0x) → 0.4782 at it 9999, `obs_noise_scale` → 0.4811 — so a mild decline at cv 0.049 under a widening curriculum is the difficulty tax, not divergence. The held-out exam settles it: a diverged policy does not beat the incumbent 64/64 on `pair34` pitch.

[EVIDENCE: `analyze_training.py` `[TIER 1]` on both segments, `[TRENDS] reward`, `[DIAGNOSIS]` item 2; `p4_score.py` `pair34` pitch `none` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Episode return fell 235.34 (end of segment 1, it 2092) → 171.24 (it 9999), and the engine's `[DIAGNOSIS]` reads that as divergence. The engine's own `[TREND]` module contradicts it: `phase: plateau(8)`, `plateau: YES since ~50%`, `stability: cv=0.049 (stable)`, with changepoints at iterations 2226, 5279 and 8210. The reconciling fact is that difficulty rose monotonically over the same window — `fault_severity` 0.0132 at it 1056 (the 1000-iteration readout recorded in the program note of 2026-09-04 15:0x) → 0.4782 at it 9999, `obs_noise_scale` → 0.4811 — so a mild decline at cv 0.049 under a widening curriculum is the difficulty tax, not divergence. The held-out exam settles it: a diverged policy does not beat the incumbent 64/64 on `pair34` pitch.

[EVIDENCE: `analyze_training.py` `[TIER 1]` on both segments, `[TRENDS] reward`, `[DIAGNOSIS]` item 2; `p4_score.py` `pair34` pitch `none` row]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
