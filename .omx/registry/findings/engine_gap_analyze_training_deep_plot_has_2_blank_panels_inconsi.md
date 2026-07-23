---
title: "ENGINE-GAP: analyze_training deep-plot has 2 blank panels + inconsistent legends; no DORAEMON curriculum plot"
tags: ["engine-gap", "analyze-training", "plot", "doraemon", "legend", "debugging"]
created: 2026-06-06T11:39:51.246514
updated: 2026-07-23T07:42:45.329668
sources: ["diagnose-20260606-202950"]
links: ["engine_gap_omx_cli_gaps_found_re_analyzing_teacher_2026_06_06_ro.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
---

# ENGINE-GAP: analyze_training deep-plot has 2 blank panels + inconsistent legends; no DORAEMON curriculum plot

[ENGINE-GAP] analyze_training.py generate_deep_plots (line ~1258) builds a FIXED 5-panel figure (plt.subplots(5,1)). Panels axes[1]/axes[2] are hardwired to roll_tag/pitch_tag tracking-error TB tags; when those tags are absent from this workspace's TB (they are), the code hits  (line 36-37) and leaves the 2 panels BLANK -> the 01_metrics_changepoints.png the user flagged has 2 empty panels. [WHERE] .omx/profile/analyze_training.py generate_deep_plots ~1258-1340. Also: legend only on panel 4 (noise_std/entropy twin-axis, label= at lines 51/58); single-series panels get no legend -> inconsistent legend presence the user disliked. [SPEC] (a) skip/drop panels whose tag is absent and re-layout to the present panels only (no blank axes), OR fill them with an available metric; (b) make legend policy uniform (either all panels labeled, or rely on y-axis labels and drop the panel-4 legend). [SPEC-2] No DORAEMON curriculum plot exists at all (per-param mean/std vs iter showing how DR widens) — for dr-harder this IS the headline visual (teacher vs E1 vs E2 'how much harder'); add an  view or an engine panel for DORAEMON/mean/* + DORAEMON/std/* trajectories. [STATUS] proposed. Fix in a harness session, not in analysis. cf [[engine_gap_omx_cli_gaps_found_re_analyzing_teacher_2026_06_06_ro]].

---

## Update (2026-06-06T11:40:30.436926)

CORRECTION (shell ate two backtick spans in the first save): the two blank spots read: (1) "the code hits a continue statement (line 36-37)"; (2) "add an omx-plot view or an engine panel". Full restated gap: analyze_training.py generate_deep_plots (~line 1258) builds a FIXED 5-panel figure via plt.subplots(5,1). axes[1]/axes[2] are hardwired to roll_tag/pitch_tag tracking-error TB tags; when those tags are absent from this workspace's TB (they are), the loop does a continue and leaves the 2 panels BLANK -> the 01_metrics_changepoints.png the user flagged shows 2 empty panels. WHERE: .omx/profile/analyze_training.py generate_deep_plots ~1258-1340. Legend inconsistency: only panel 4 (noise_std/entropy twin-axis) sets label= (lines 51/58); single-series panels get no legend -> inconsistent legend presence. SPEC: (a) drop panels whose tag is absent and re-layout to present panels only (no blank axes), or fill them with an available metric; (b) uniform legend policy. SPEC-2: there is NO DORAEMON curriculum plot anywhere (per-param mean/std vs iter showing how DR widens); for dr-harder that is the headline visual (teacher vs E1 vs E2 'how much harder') -> add an omx-plot view or engine panel for DORAEMON/mean/* and DORAEMON/std/* trajectories. STATUS proposed; fix in a harness session.

---

## Update (2026-07-23T07:42:45.329668)

2026-07-23 curation: status moved to resolved -- both gaps (blank panels via dynamic panel count, missing DORAEMON curriculum band plot) are already fixed in analyze_training.py.
