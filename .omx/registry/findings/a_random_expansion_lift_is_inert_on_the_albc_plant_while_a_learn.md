---
title: "A random expansion lift is inert on the ALBC plant while a learned dictionary is not, and the learned one saturates at about 12 effective dimensions"
tags: ["koopman", "lifting", "random-expansion", "effective-rank", "latent-dim"]
created: 2026-08-05T10:17:27.637731
updated: 2026-08-05T10:17:27.637731
sources: [".omx/programs/koopman-lifting/PLAN.md#12.8", ".omx/programs/koopman-lifting/step2_fit/fit_none.json"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# A random expansion lift is inert on the ALBC plant while a learned dictionary is not, and the learned one saturates at about 12 effective dimensions

SOURCE: .omx/programs/koopman-lifting/step2_fit/fit_none.json, 2026-08-05, PLAN 12.8. At DR none on the full-length static protocol, a frozen random lift scores H25 RMSE 0.4651 / 0.4624 / 0.4632 / 0.4685 at added widths 16 / 32 / 64 / 128, against 0.4680 with NO lift at all -- every one inside the 3-seed spread. Expansion width alone buys nothing on this plant; only a LEARNED dictionary moves the number, and it does so by 7.8 to 12.0 pct RMSE (2.1 to 2.9 sigma) at the same widths. This is also what makes the step-2 kill gate a real gate rather than a rubber stamp: a dead pipeline would have put the learned lift in that same inert band, and it did not. Two design numbers follow. First, m from the plateau as PLAN section 6 required: learned-linear goes 0.4288 (w=16), 0.4189 (32), 0.4122 (64), 0.4123 (128), so about 64 added dimensions and nothing past it. Second, participation-ratio effective rank of psi saturates at 11 to 12 for the learned lift no matter how wide it is, while the random lift's rank keeps climbing 9.3 to 19.5 -- the learned dictionary concentrates rather than spreads, and its per-dim std falls from 0.689 to 0.334 as width grows.
