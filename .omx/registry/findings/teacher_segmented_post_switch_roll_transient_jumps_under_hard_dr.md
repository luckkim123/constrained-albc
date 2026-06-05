---
title: "teacher segmented: post-switch roll transient jumps under hard DR"
tags: ["segmented", "post-switch", "roll", "hard-dr", "transient", "teacher"]
created: 2026-06-05T11:00:33.092719
updated: 2026-06-05T11:00:33.092719
sources: ["diagnose-20260605-195846"]
links: []
category: pattern
confidence: medium
schemaVersion: 1
---

# teacher segmented: post-switch roll transient jumps under hard DR

Teacher (260525_232805) segmented eval via the NEW eval_adapter segmented subcommand: post-switch peak after each mid-episode DR switch (segs 1..N, env x seg, _sw_all_post_switch delegation). roll post-switch none mean 0.03deg/max 0.37 -> hard mean 6.45deg/max 28.29; yaw none 0.32/2.35 -> hard 1.72/7.87. The DR-switch ADAPTATION cost is real, roll-dominated, and grows ~200x none->hard in mean. Consistent with the static-eval CV finding (roll most dispersed: hard CV 2.65). This coverage was invisible to the static heavy-tail adapter -- it needed the segmented subcommand (post-switch transient, not steady-state). cf the static hard-DR CV-explosion-without-heavy-tail finding (same run, DC-bias dispersion).
