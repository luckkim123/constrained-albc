# The stated purpose of option C was therefore not achieved, and cannot be by this

- id: finding/359 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-stated-purpose-of-option-c-was-therefore-not-achieved-and-cannot-be-by-this · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The stated purpose of option C was therefore not achieved, and cannot be by this route: the section-5 thrust band (0.5, 

The stated purpose of option C was therefore not achieved, and cannot be by this route: the section-5 thrust band (0.5, 2.0) was never exercised by any Phase 4 exam, on either branch. That is consistent with `debugging/319`, where adding the band to the incumbent arm produced a byte-identical `inc13w`. `--deterministic-dr` would not fix it either, since the band does not reach the eval at all rather than being drawn differently.

[EVIDENCE: the byte-identity above, plus the absence of any `thrust` key among the 23 recorded `dr_*` dims and of any thrust line in either eval log]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The stated purpose of option C was therefore not achieved, and cannot be by this route: the section-5 thrust band (0.5, 2.0) was never exercised by any Phase 4 exam, on either branch. That is consistent with `debugging/319`, where adding the band to the incumbent arm produced a byte-identical `inc13w`. `--deterministic-dr` would not fix it either, since the band does not reach the eval at all rather than being drawn differently.

[EVIDENCE: the byte-identity above, plus the absence of any `thrust` key among the 23 recorded `dr_*` dims and of any thrust line in either eval log. It is not unique: both eval logs also emit `[WARN] DomainRandomizationCfg has no field 'ocean_current_strength'` while TB carries `DORAEMON/mean/ocean_current_strength` as a live, expanding curriculum dim]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge
