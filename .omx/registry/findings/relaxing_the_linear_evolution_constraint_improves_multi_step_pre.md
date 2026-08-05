---
title: "Relaxing the linear-evolution constraint improves multi-step prediction in 10 of 10 offline configurations on the ALBC plant"
tags: ["koopman", "lifting", "linearity", "offline-fit", "prediction", "nested-comparison"]
created: 2026-08-05T10:16:50.220803
updated: 2026-08-05T10:16:59.690180
sources: [".omx/programs/koopman-lifting/PLAN.md#12.8", ".omx/programs/koopman-lifting/step2_fit/fit_hard.json", ".omx/programs/koopman-lifting/step2_fit/excite_excited_hard.json"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Relaxing the linear-evolution constraint improves multi-step prediction in 10 of 10 offline configurations on the ALBC plant

Koopman step 2 offline study, 2026-08-05, zero GPU-h of training. Fitted phi(o) = [o ; psi(o)] with the raw obs always inside the lift, so predicting o is the same linear readout for every model, and rolled the operator forward WITHOUT re-lifting (re-lifting would make every model nonlinear and would not test linearity). Comparing a learned lift under a linear operator against the SAME lift whose operator gains a residual MLP initialised to zero -- a NESTED comparison, so extra capacity cannot be confounded with easier optimization -- relaxing linearity improves H25 (0.5 s) prediction in every one of 10 configurations, 4.6 to 31.9 sigma over 3 seeds. Magnitude 40.7 pct RMSE at DR none and 4.1 pct at DR hard on the full-length static protocol; 16.2 pct and 11.7 pct respectively once action excitation makes B identifiable. The shrinkage under excitation is informative: part of the apparent nonlinear advantage on unexcited data was the model exploiting the confounded closed loop, and part was real. This REFUTES pre-registered prediction 2 in koopman-lifting PLAN 12.4 (arm C and the nonlinear twin do not separate past a decision floor) at the PREDICTION level. It says nothing yet about the CONTROL level, which is what arms 3-5 would buy. Caveat that bounds citation: the nested residual is not arm 4 as specified (same-size K to MLP swap), and every fit is on rollouts of a FROZEN policy, so these are an upper bound on what a pre-frozen operator delivers during RL. Artifacts: .omx/programs/koopman-lifting/step2_fit_lift.py and step2_fit/*.json, PLAN 12.8.

---

## Update (2026-08-05T10:16:59.690180)

SOURCE: .omx/programs/koopman-lifting/step2_fit/*.json produced by step2_fit_lift.py, 2026-08-05, tabulated in PLAN 12.8. Zero GPU-h of training.
