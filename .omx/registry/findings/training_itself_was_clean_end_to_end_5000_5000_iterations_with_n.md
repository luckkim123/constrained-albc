---
title: "Training itself was clean end to end: 5000/5000 iterations with no crash (unlike"
tags: ["auto-captured", "correction", "e-int", "hydrorc", "withdrawn-draft"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T09:11:06.751628
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md", "diagnose-20260728-081953"]
links: []
category: session-log
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Training itself was clean end to end: 5000/5000 iterations with no crash (unlike

Training itself was clean end to end: 5000/5000 iterations with no crash (unlike E-int, no resume seam), final reward 260.38 vs E-int 260.5 — the iter-300 gap (110.14 vs 144.35, HydroRC learning active damping the old plant provided passively) fully closed by the end; reward plateaus from ~10% with cv 0.009; fps 65627; zero NaN lines in the launch log.

[EVIDENCE: launch.log iteration blocks at 100/200/300 and 4999 for both runs; analyze_training.py TRENDS section (plateau since ~10 percent, stability cv=0.009) and Perf line fps=65627; grep -ci nan on launch.log = 0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

Training itself was clean end to end: 5000/5000 iterations with no crash (unlike E-int, no resume seam), final reward 260.38 vs E-int 260.5 — the iter-300 gap (110.14 vs 144.35, HydroRC learning active damping the old plant provided passively) fully closed by the end; reward plateaus from ~10% with cv 0.009; fps 65627; zero NaN lines in the launch log.

[EVIDENCE: launch.log iteration blocks at 100/200/300 and 4999 for both runs; analyze_training.py TRENDS section (plateau since ~10 percent, stability cv=0.009) and Perf line fps=65627; grep -ci nan on launch.log = 0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

Training itself was clean end to end: 5000/5000 iterations with no crash (unlike E-int, no resume seam), final reward 260.38 vs the E-int true final 263.98 (-1.4%) — the iter-300 gap (110.14 vs 144.35, -23.7%, HydroRC learning active damping the old plant provided passively) narrowed to -1.4% by the end, mostly but not fully closed; reward plateaus from ~10% with cv 0.009; fps 65627; zero NaN lines in the launch log.

[EVIDENCE: iteration blocks 100/200/300 from the E-int PRE-resume segment launch.log (trpo_eint_s30_260727_160913) and from the HydroRC launch.log; iteration-4999/5000 blocks from the HydroRC launch.log (Mean reward 260.38) and the E-int RESUMED-segment launch.log (trpo_eint_s30_rs2350_260727_195102, Mean reward 263.98 / ep_len 1426.46); analyze_training.py TRENDS section (plateau since ~10 percent, stability cv=0.009) and Perf line fps=65627; grep -ci nan on launch.log = 0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md

---

## Update (2026-07-28T09:11:06.751628)

# CORRECTION 2026-07-28: the E-int reward referent in the two EARLIER blocks is a withdrawn draft figure

Same defect as on the sibling page `the_per_step_reward_decomposition_is_essentially_unchanged_by_th`.
Two of the three reports this page was auto-captured from (`diagnose-20260728-081212`,
`diagnose-20260728-081242`) were DRAFTS withdrawn during independent review, and their blocks above
cite E-int's final reward as **260.5** — the reward at E-int's CRASH point (iter ~2390 of the
original `trpo_eint_s30_260727_160913` segment), not its final value.

The value of record is **263.98**, from the iteration-4999/5000 block of the RESUMED segment
`trpo_eint_s30_rs2350_260727_195102`. It already appears in the third (latest) block above.

The consequence is not cosmetic: against 260.5 the HydroRC final reward 260.38 looks like a dead
heat, while against the true 263.98 it is **-1.4%**, and the iter-300 gap (110.14 vs 144.35, -23.7%)
narrows to -1.4% rather than closing fully. The withdrawn blocks state "fully closed by the end";
that claim does not survive the correction.

[EVIDENCE: independent report-reviewer round 1 on diagnose-20260728-081953 flagged the 260.5 referent as a major defect; fixed by re-authoring from the generator, round 2 APPROVE with 0 findings. PLAN teacher-final-closeout section 12.2, HydroRC row, records the same correction]
[CONFIDENCE: HIGH]

