# Fault ranking on the section-5 teacher: thruster 0 dominates, m3 is second, and the deployed pair34 is mid-table

- id: finding/350 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: fault-ranking-on-the-section-5-teacher-thruster-0-dominates-m3-is-second-and-the · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: none · keywords: fault, thruster, fault-map, pair34, deployment
- summary: Candidate-only EXTRA readout, p3b_final model_9999, 64 envs seed 42, hard level mean per-env ss_error deg (analysis diag

Candidate-only EXTRA readout, p3b_final model_9999, 64 envs seed 42, hard level mean per-env ss_error deg (analysis diagnose-20260905-060354, extra_read.py over .hq/work/p4/p3b_final). Worst first: m0m3 10.576, m0m5 8.280, m0 7.935, m0m4 7.619, m0m2 6.803, m1m3 6.449, m3 6.104, m0m1 5.825, m3m5 5.698, m2m3 5.588, m1m5 5.505, m2m4 5.401, m4m5 5.078, m2m5 4.615, m4 4.398, m1m4 4.391, m1m2 4.340, m5 4.181, m1 4.055, m2 3.939. Same-arm anchors: healthy 3.663, pair34 6.326. Every one of the five worst configs contains m0. AXIS SPLIT: m0 is a roll-authority loss (hard roll 6.359 vs pitch 3.364), m3 a pitch one (none pitch 0.539 vs healthy 0.298). m0+m3 is superadditive at none where no DR applies: healthy 0.511, m0 0.700, m3 0.833, m0m3 3.350. SURVIVAL: 100 percent in 17 of 20 configs; exceptions m2m4 96.9 and m4 98.4, both only at hard, shallower than the delay configs healthy_d1/d2 at 96.9. Thruster loss degrades accuracy, it does not cost control; delay is the sharper survival threat.
## Comments
