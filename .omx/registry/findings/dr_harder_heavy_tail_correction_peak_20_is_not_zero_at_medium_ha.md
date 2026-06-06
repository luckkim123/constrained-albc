---
title: "dr-harder heavy-tail correction: %peak>20 is NOT zero at medium/hard"
tags: ["heavy-tail", "roll", "dr-harder", "correction"]
created: 2026-06-06T09:14:24.251618
updated: 2026-06-06T09:14:24.251618
sources: ["diagnose-20260606-180317"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# dr-harder heavy-tail correction: %peak>20 is NOT zero at medium/hard

An earlier dr-harder summary claimed '%peak>20=0 all (DC-bias not heavy-tail)'. The engine-driven re-work CORRECTS this: a real heavy tail exists at medium/hard. From heavy_tail.json aggregate (max pct_peak_gt_thresh across axes, roll dominant): teacher medium=18.75% / hard=14.06% (peak_max 11.36 deg); E1 hard=15.62% (peak_max 13.60); E2 hard=14.06% (peak_max 11.08). none/soft are 0%. So roll DOES go heavy-tail under medium+ DR in a ~9-19% minority of envs, ON TOP OF the DC-bias dispersion (hard roll CV ~2.65). Both failure modes coexist; do not call it 'DC-bias only'. Re-visit: analysis diagnose-20260606-180317, all 3 runs section 3.
