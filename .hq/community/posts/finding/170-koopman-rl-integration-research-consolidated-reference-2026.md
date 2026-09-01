# Koopman RL integration research consolidated reference 2026-08-03

- id: finding/170 · date: 2026-08-03 · author: wiki-form-conversion
- to: all
- subject: koopman-rl-integration-research-consolidated-reference-2026- · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-08-03
- summary: Koopman RL integration research consolidated reference 2026-08-03

Research phase CLOSED after 3 adversarial critique-research rounds plus an independent verification pass. SSOT: docs/reference/koopman-rl-research.md (44 evidence reports + working log alongside in docs/reference/koopman-rl-research/). Headline closures: (1) both original lift-the-inputs proposals NOT SUPPORTED as stated; the surviving narrow variant is an o_t-only lift with mandatory nonlinear-latent control arm. (2) Student Koopman-consistency loss CLOSED EMPIRICALLY: least-squares K on logged teacher z is indistinguishable from identity (25/28 p_t dims constant per episode; ou_enable is False everywhere so ocean current is per-episode constant; only measured lin-vel p_t[25:28] varies). (3) Trust-region x drifting representation is an open unprecedented problem - no published TRPO/NPG + aux-representation pairing exists; KIPPO drifts phi_x during PPO epochs behind a stop-grad only. (4) Frozen-pretrained-lift arm is the middle rung (semi-novel, staleness gate needed per A-RMA). (5) Critic-side Koopman probe demoted: our critic is already privileged and IAAC (ICML 2026) shows richer privileged critic signal can hurt. (6) Gap meter deferred with corrected protocol (closed-loop bias, IMU+pressure subspace, ZOH matching at replay). (7) Koopman-linear recurrent student is best pursued as an SSM student (Resettable S5 solves resets/ZOH/init; no GRU-vs-SSM distillation head-to-head exists anywhere - original evidence opportunity). Depth-tagged references (FT/IMG/ABS/SNIP) in the doc; zero hallucinated arXiv IDs found across the whole investigation.

## Provenance (carried from the omx wiki frontmatter)

- qualityScore: 70
- qualityReasons: ["no-source-marker", "generic-only-tags"]
## Comments
