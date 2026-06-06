---
title: "DR-harder campaign synthesis: speed kills attitude, center-shift overfits"
tags: ["dr-harder", "campaign", "kl_ub", "ocean_current", "attitude", "ss_error", "synthesis", "doraemon"]
created: 2026-06-06T02:15:02.504780
updated: 2026-06-06T02:15:02.504780
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
---

# DR-harder campaign synthesis: speed kills attitude, center-shift overfits

DR-harder campaign (2026-06-06, autonomous overnight) — 3 single-knob treatments vs deterministic baseline. SETUP: teacher 260525_232805 baseline; E4 reproduces it to +-0.0% (training AND eval) -> pipeline deterministic -> all treatment differences are CAUSAL, not seed. RESULTS: E1 (kl_ub 0.06->0.12, curriculum SPEED): expands DR 3.6x (ocean mean 0.12->0.42) but attitude SS error +30-70% WORSE (roll/pitch every level), vx/yaw better. entropy LOW-alive. E2 (ocean nominal 0.0->0.3, distribution CENTER): reaches SAME ocean coverage 0.41 but attitude KEPT (roll hard +8%, pitch hard -17%), translation BEST of three (vx/vy/yaw all better). HOWEVER entropy COLLAPSED -0.63 + reward highest 257 = overfit; eval confirms vz none/soft +46/+103% WORSE (weak-current starvation). SYNTHESIS (answers speed-vs-tail): E1 vs E2 reach identical ocean coverage by different means but opposite attitude outcomes => the FAST curriculum (kl_ub) is the attitude-killer, the strong-current TAIL itself is NOT. Neither knob is a clean win for the user's #1 SS-error priority: kl_ub-up trades attitude for translation; ocean-nominal-up keeps attitude+translation but overfits weak DR (vz). RECOMMENDATION: to get hard-current robustness without either harm, WIDEN DORAEMON variance from nominal=0 (don't shift the center, don't speed the curriculum) — i.e. a variance/range knob at baseline kl_ub and nominal=0. E3 (both kl_ub+ocean) would compound both harms; low priority. The decisive enabler was E4 the deterministic control (made every claim causal).
