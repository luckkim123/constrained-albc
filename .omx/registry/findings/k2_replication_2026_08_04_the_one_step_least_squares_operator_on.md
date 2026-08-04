---
title: "K2 replication 2026-08-04: the one-step least-squares operator on the teacher latent is the identity to within refit noise across 5 run-level pairs, and the reason is structural -- z encodes per-episode CONSTANT parameters"
tags: []
created: 2026-08-04T03:38:22.833590
updated: 2026-08-04T03:38:22.833590
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# K2 replication 2026-08-04: the one-step least-squares operator on the teacher latent is the identity to within refit noise across 5 run-level pairs, and the reason is structural -- z encodes per-episode CONSTANT parameters

## Measurement

Koopman plan Phase 0, item K2. Refit one-step least-squares K on `l_true` over the post-warmup
half, statistic `||K - I||_F` against the split-half refit spread (fit K on each half, take
`||K1 - K2||_F` as the noise scale).

| run | level | `||K-I||_F` | split-half spread | ratio |
|:--|:--|--:|--:|--:|
| a0_tcn | none | 0.0304 | 0.0476 | 0.64 |
| a0_tcn | hard | 0.0001 | 0.0002 | 0.54 |
| a0g_gru | hard | 0.0018 | 0.0005 | 3.83 |
| b2_extraobs | hard | 0.0001 | 0.0002 | 0.43 |
| b2wide_gru256 | hard | 0.0001 | 0.0002 | 0.63 |

Four of five sit BELOW their own refit noise (ratio < 1), i.e. the deviation from identity is not
even resolvable. The one exception has ratio 3.83 but an absolute magnitude of 0.0018, which is
negligible on a latent whose range is about [-0.74, 0.74].

## Reading

J1's negative closure replicates: it was not a one-run artifact. More usefully, the reason is now
explicit rather than empirical. The privileged latent is trained to encode per-episode plant
parameters, and those are CONSTANT within an episode. A one-step transition operator on a constant
signal is the identity by construction. So K approximately I is not weak evidence against Koopman
structure in this latent -- it is the expected reading of a well-behaved parameter encoder, and it
means this particular statistic can never discriminate anything here.

Consequence for any future Koopman work in this repo: do NOT re-run K-vs-I on `l_true` expecting
information. If a lift is to be tested, it must be tested on a signal that actually evolves
(policy obs, or a phi_x on the state), not on the per-episode parameter latent.

