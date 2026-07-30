---
title: "The roll transient regression is plant-wide, not a nominal-corner artifact: roll"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The roll transient regression is plant-wide, not a nominal-corner artifact: roll

The roll transient regression is plant-wide, not a nominal-corner artifact: roll os_env_mean is elevated at every DR level and roll n_gt20 re-opens a heavy tail the E-int family had closed. The known family pattern (roll transient worst at `none`, improving as DR hardens) replicates in shape from none to medium, then hard bounces back up. | level | roll os_env_mean (pp) HydroRC vs E-int | roll n_gt20 (envs) HydroRC vs E-int | roll ss_error (deg) HydroRC vs E-int | |:--|--:|--:|--:| | none | 17.96 vs 8.18 | 18.67 vs 0.00 | 0.436 vs 0.428 | | soft | 14.43 vs 7.63 | 12.00 vs 0.33 | 0.420 vs 0.399 | | medium | 12.23 vs 8.68 | 9.33 vs 1.33 | 0.478 vs 0.395 | | hard | 13.93 vs 10.41 | 15.00 vs 5.67 | 1.380 vs 0.600 |

[EVIDENCE: roll os_env_mean / n_gt20 / ss_error at all four levels of the two healthy summary.json files; family history in wiki roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md — pre-buoyfix runs sat at 17-21 pp at none (A3 21.49, old anchor 17.02), E-int had brought this to 8.18 pp, HydroRC returns to 17.96 pp]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

The roll transient regression is plant-wide, not a nominal-corner artifact: roll os_env_mean is elevated at every DR level and roll n_gt20 re-opens a heavy tail the E-int family had closed. The known family pattern (roll transient worst at `none`, improving as DR hardens) replicates in shape from none to medium, then hard bounces back up. | level | roll os_env_mean (pp) HydroRC vs E-int | roll n_gt20 (envs) HydroRC vs E-int | roll ss_error (deg) HydroRC vs E-int | |:--|--:|--:|--:| | none | 17.96 vs 8.18 | 18.67 vs 0.00 | 0.436 vs 0.428 | | soft | 14.43 vs 7.63 | 12.00 vs 0.33 | 0.420 vs 0.399 | | medium | 12.23 vs 8.68 | 9.33 vs 1.33 | 0.478 vs 0.395 | | hard | 13.93 vs 10.41 | 15.00 vs 5.67 | 1.380 vs 0.600 |

[EVIDENCE: roll os_env_mean / n_gt20 / ss_error at all four levels of the two healthy summary.json files; family history in wiki roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md — pre-buoyfix runs sat at 17-21 pp at none (A3 21.49, old anchor 17.02), E-int had brought this to 8.18 pp, HydroRC returns to 17.96 pp]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

The roll transient regression is plant-wide, not a nominal-corner artifact: roll os_env_mean is elevated at every DR level and roll n_gt20 re-opens a heavy tail the E-int family had closed. The known family pattern (roll transient worst at `none`, improving as DR hardens) replicates in shape from none to medium, then hard bounces back up. | level | roll os_env_mean (pp) HydroRC vs E-int | roll n_gt20 (envs) HydroRC vs E-int | roll ss_error (deg) HydroRC vs E-int | |:--|--:|--:|--:| | none | 17.96 vs 8.18 | 18.67 vs 0.00 | 0.436 vs 0.428 | | soft | 14.43 vs 7.63 | 12.00 vs 0.33 | 0.420 vs 0.399 | | medium | 12.23 vs 8.68 | 9.33 vs 1.33 | 0.478 vs 0.395 | | hard | 13.93 vs 10.41 | 15.00 vs 5.67 | 1.380 vs 0.600 |

[EVIDENCE: roll os_env_mean / n_gt20 / ss_error at all four levels of the two healthy summary.json files; family history in wiki roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md — pre-buoyfix runs sat at 17-21 pp at none (A3 21.49, old anchor 17.02), E-int had brought this to 8.18 pp, HydroRC returns to 17.96 pp]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
