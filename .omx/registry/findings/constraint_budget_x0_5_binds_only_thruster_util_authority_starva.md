---
title: "constraint budget x0.5 binds only thruster_util -> authority starvation"
tags: ["constraint", "thruster_util", "binding", "entropy-collapse", "dr-harder"]
created: 2026-06-07T02:54:26.128107
updated: 2026-06-07T02:54:26.128107
sources: ["diagnose-20260607-113942"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# constraint budget x0.5 binds only thruster_util -> authority starvation

E6 (dr_harder, 10 constraint budgets x0.5) proved the CMDP is NOT globally inert but binds through ONE channel only. Of 10 constraints, only thruster_util reached its discounted budget: J_C/d_k=0.944 (E6) vs 0.869 (teacher), computed as J_C=d_k-margin in the slack regime where d_k=budget/(1-cost_gamma)=20.0 and margin=1.122 (Constraint/margin/thruster_util final-window). The other 9 stayed slack: their margins just tracked the halved budget (attitude/cumul_yaw margin 0.499 = exactly 0.5x teacher 0.997/1.000; yaw_rate 4.23 = 0.5x 8.68), proving cost J_C~0. CONSEQUENCE of that single binding: per-step reward -54% (Reward/total 3.68 vs 7.96), Reward/lin_vel went NEGATIVE -0.262 (only run of 5; teacher +1.89), entropy COLLAPSED to -2.30 crossing 0 at iter 2289 (teacher never; new anomaly), DORAEMON success 0.65 vs 0.97, eval vx ss_error 61x worse at none (0.155 vs 0.0025) as a DR-INDEPENDENT ~0.14 m/s DC bias flat across none->hard. FINGERPRINT: Reward/thruster penalty is the SMALLEST of 5 runs (-0.043 vs teacher -0.091) -> barrier suppresses thrust, removing the authority lin_vel needs. RULE for budget experiments: tightening a control-authority channel (thruster) is destructive; rebalance which channel binds, do not tighten globally. barrier-as-fraction did NOT rise (per-step 1.28% vs teacher 1.52%); detect binding via curve divergence + per-constraint margin, NOT barrier fraction. Revisit: analysis diagnose-20260607-113942 sections 2/6.
