---
title: "Track/cmd_att/*_deg logs the env-mean of |command|, not the command range (13.5 deg = uniform +-30 x 0.9)"
tags: []
created: 2026-07-13T05:55:24.505691
updated: 2026-07-13T05:55:24.505691
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Track/cmd_att/*_deg logs the env-mean of |command|, not the command range (13.5 deg = uniform +-30 x 0.9)

TB tag semantics gotcha (user asked 2026-07-13 on trpo_baseline_260713_031325: 'commands should be uniform +-30 deg but the tag only shows 11-16'). VERIFIED: (1) sampling IS uniform +-30 deg — albc_env.py:756 uniform_(-1,1) * att_max(pi/6) * scale(permanently 1.0), with vel_cmd_zero_prob=0.1 (config.py:465) giving 10% of envs a zero command. (2) The tag Track/cmd_att/roll|pitch_deg (albc_env.py:1260-1261) records rad2deg(cmd).abs().mean() over the logging env subset — an ABSOLUTE-VALUE MEAN, not a range. Expected value: E|U(-30,30)| * (1-0.1) = 15 * 0.9 = 13.5 deg. Baseline TB measured: mean 13.51 (roll) / 13.51 (pitch), std 0.82, min-max 10.7-16.9 over 5000 iters — exact match; the 11-16 band is finite-sample noise of the mean (|U| std 8.66 / sqrt(~100 resetting envs) ~= 0.87). CONSEQUENCE: do not read this scalar as the command range; to see the +-30 box use eval trajectory plots or an _ang_cmd histogram. Related open item: eval's step commands are ATT_AMP_DEG=15 (analysis/_eval_dr/trajectory.py:14), only the inner half of the trained box — the A2 command-box coverage gap in the p7_tail post-e1/e2 plan.
