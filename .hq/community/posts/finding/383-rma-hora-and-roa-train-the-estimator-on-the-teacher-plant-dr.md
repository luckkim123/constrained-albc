# RMA, HORA and ROA train the estimator on the teacher plant, drive with z_hat from a random init, and use a fixed 0.2-1.5 s window; ALBC C3 differed on plant and memory, and the R3 probes are the driver and the window

- id: finding/383 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- topic: reference
- confidence: high · status: needs-experiment
- verified: none · keywords: RMA, HORA, ROA, adaptation-module, phase-2, dagger, beta, windowed-estimator, tcn, gru, plant, decision-021, finding-380, finding-381, R3
- summary: Four-axis comparison: plant (RMA/HORA/ROA/Lee/NORBC all = teacher DR; ALBC violated it, finding/381), driver (RMA/HORA beta=0; Lee/NORBC DAgger student-driven; ALBC select 0.5), estimator memory (RMA/HORA/ROA windowed, Lee TCN-100 > GRU on steps, NORBC GRU; ALBC GRU drifting per finding/380), actor (Lee/NORBC trainable end-to-end vs ALBC frozen). Student budget: 1/3 of teacher in both lineages vs 1/50 here. Probes R3a beta0, R3b tcn, R4a budget10x, R4b trainable actor.
**Read against RMA (arXiv 2107.04034), HORA (2210.04887) and ROA (2210.10044, "Deep Whole-Body Control"), ALBC stage 2 now differs on three axes, and the two that the 2026-09-05 failure exposed -- the rollout plant and the estimator's memory -- are exactly where the literature is uniform and ALBC was not. Sources: the papers' method sections and algorithms, pulled 2026-09-05 (RMA 3.2 / 4.2 / Alg. 1; HORA 3.2 / 9; ROA 2.2 / Alg. 1). decision/021 (2026-07-21) described the pre-DAgger runner; this page supersedes its axis-1 statement.**

| axis | RMA | HORA | ROA | ALBC C3 (as run 2026-09-05) | ALBC R1/R2 (queued) |
|:--|:--|:--|:--|:--|:--|
| phase-2 plant | same envs as phase 1 (Alg. 1 reuses `envs[i]`) | "the same object initialization and dynamics randomization setting" as phase 1 | single phase, same envs | DORAEMON initial Beta, SimToReal fields reverted (finding/381) | task DR, uniform over the teacher's box |
| who drives the rollout | base policy on the student's z_hat from a RANDOM init, iterated to convergence (beta = 0 throughout) | same (pi(o, z_hat)) | pi on z^phi every H=20 iterations, on z^mu otherwise | DAgger `select`, beta 0.5 fixed: half the env-steps execute the teacher's action | unchanged |
| labels / loss | MSE(z_hat, z) only; actor frozen | l2(z_hat, z) only; actor frozen | z^phi <- sg[z^mu]; z^mu <- sg[z^phi] with lambda 0->1; policy trained jointly | MSE(actor(o, z_hat), a_t) + 1.0 x MSE(z_hat, l_t), frozen actor (decision/021 axis 2) | unchanged |
| estimator memory | 1-D CNN over a FIXED window, k = 50 steps = 0.5 s | 1-D conv over 30 steps = 1.5 s | window 10 steps | GRU, hidden carried for the whole episode (unbounded) | GRU (R2: episodes 155 s) |
| estimator input | state + action history | joint pos + action history | state + action history | normalized policy obs (69/72D incl. 2-step action history) | unchanged |
| phase-2 budget | 1000 it x 80k = 80M steps, 3 h | "until the loss converges" | continuous | 1000 it x 2048 x 24 = 49M steps, 12 min; loss still falling (-6 % over the last 200 it) | 1000 it |
| deployment | phi async at 10 Hz, pi at 100 Hz | -- | -- | np_policy GRU at the board rate (finding/198 open) | -- |

**What this says about the failure.**
1. Plant: every one of the three methods trains the estimator on the distribution the teacher was trained on. RMA states the reason explicitly ("would not be robust to deviations from the expert trajectory") and it applies a fortiori to the plant. finding/381 is a violation of the premise all three share, not a recipe choice. R1 restores it.
2. Memory: all three estimators are windowed (0.2-1.5 s). A windowed estimator cannot drift, whatever the episode length; a GRU can, and finding/380 s4 measures it doing so (0.019 -> 0.056 over 155 s). ALBC's windowed option is the TCN (`tcn_history 9` x stride 3 = 27 physical steps = 0.54 s at 50 Hz) and the campaign rejected it in favour of the GRU on latent tracking (decision/145, A0 vs A0g) -- a comparison made on the wrong plant. R2 keeps the GRU and lengthens the training horizon instead; the literature's answer is the window.
3. Driver: RMA/HORA run beta = 0 from a random init and rely on the resulting exploration; ALBC holds beta at 0.5 because C2/C3 found the mix better than beta = 1 (finding/045, decision/145) and never ran the RMA setting on a correct plant. The runner already supports it (`dagger_beta_start 1.0 --dagger_beta_end 0.0 --dagger_anneal_iters 600`, config.py:105).
4. Loss: ALBC's extra action term is a task-aware latent loss through the frozen actor; decision/171 found lambda in [0, 4] control-neutral (on the wrong plant). Not first-order.
5. ROA's realizability gap is the one item that is a TEACHER lever: if the teacher's z carries components proprioception cannot recover (finding/172's d4 collapse at none, the negative in-loop R2 at none of decision/186), no phase-2 recipe closes it; ROA regularizes z^mu toward z^phi during RL. Carries into the next teacher retrain only, under the standing triggers.

**Proposed probes after R1/R2 read (not queued; each 12 min + 25 min exam on the p3b protocol):**
- R3a `gru_beta0`: R1 plant + beta 1.0 -> 0.0 over 600 it, hold 0 for 400 (the RMA/HORA driver). One variable vs R1.
- R3b `tcn_dr5`: R1 plant + `--encoder_type tcn` (windowed estimator, beta 0.5). One variable vs R1; if R2's horizon effect is real, R3b should show no time growth in `latent_none.npz` by construction.
- Longer phase 2 (2000-3000 it) is a free follow-up if R1's loss is still falling at 1000.
Pre-registered readouts: the finding/380 s3 bias^2 at healthy/none and its 0-5 s vs 100-155 s ratio, then the 20-row paired table.

Evidence: arXiv 2107.04034 sections 3.2, 4.2, 9 (Algorithm 1); 2210.04887 sections 3.2, 9; 2210.10044 sections 2.2, 7 (Algorithm 1); `constrained_albc/envs/_core/student/runner.py:188-310` (`_collect_rollout`, `_dagger_action`), `_core/student/config.py:50-68,95-108`.
## Comments

## Update (2026-09-05 23:4x) -- the Lee 2020 / NORBC lineage, and a correction

The user asked for NORBC ("Not Only Rewards But Also Constraints", arXiv 2308.12517, Kim et al., T-RO 2024). Its student pipeline is Lee et al. 2020 (arXiv 2010.11251, Science Robotics) as NORBC 5.1 states ("built based on [lee2020blind, miki2022perception]"). Read from the originals (NORBC 5.3 / 5.5 / 6.1; Lee 2020 4.4 / S8 / S9):

| axis | Lee 2020 | NORBC | ALBC C3 |
|:--|:--|:--|:--|
| who drives the rollout | DAgger: "training data is generated by rolling out trajectories by the student policy", teacher labels every visited state | not stated in the paper; inherits the Lee pipeline | select beta 0.5 |
| labels / loss | (a_bar - a)^2 + (l_bar - l)^2 | identical form, equal weights | identical form, lambda 1.0 |
| actor | the STUDENT has its own actor, trained end-to-end with the encoder | GRU encoder + MLP actor, end-to-end | teacher actor FROZEN; only the encoder trains |
| estimator memory | TCN-100 (100-step window); a GRU variant "between TCN-20 and TCN-100", worse on steps (S8) | GRU, hidden carried | GRU, hidden carried |
| latent loss ablation | dropping the latent term costs success on steps (S9, "naive IL") | -- | decision/171: lambda in [0,4] control-neutral (wrong plant) |
| student budget vs teacher | 4 h vs 12 h (1/3, Table S-times) | 8 h vs 24 h (1/3) | 12 min vs ~10 h (1/50); loss still falling |
| plant | same simulator/curriculum as the teacher | DR "during the training" (5.5), student not separated | fixed in R1 |

**Corrections to the page above.** (1) "All three estimators are windowed ... the literature's answer is the window" holds for the RMA/HORA/ROA family only. The Lee/NORBC family deploys a recurrent estimator with a trainable actor and runs it on the robot indefinitely; Lee 2020 S8 does rank the GRU below TCN-100 on steps, so the window is *favoured* in the one paper that compared, not universal. (2) ALBC C3 is a hybrid nobody published: Lee-style mixed loss and (half) DAgger driver on top of an RMA-style frozen actor. With the actor frozen the encoder must reproduce z exactly for the actor to behave; with a trainable actor (Lee, NORBC) the actor can absorb a biased-but-consistent l_bar. That is a fourth axis the failure mode of finding/380 (shared bias) speaks to directly. (3) Budget: both lineages spend about a third of the teacher's compute on the student; ALBC spends 1/50 and its loss had not converged.

**Added probe candidates (after R1/R2, not queued):**
- R4a `budget10x`: R1 recipe, 10,000 it (~2 h). Free if R1's loss still falls at 1000.
- R4b `trainable_actor`: R1 plant + student actor initialised from the teacher actor and trained end-to-end with the encoder on the same mixed loss (the Lee/NORBC axis). Needs a small runner change (actor copy in the optimizer, saved in the ckpt) and an export path that packs the student actor; the constraint-satisfying behaviour is then inherited by imitation only, as in NORBC.
Ordering after R1/R2: R4a first (no code), then R3a/R3b/R4b by what R1/R2 leave unexplained.

## Comments
- (2026-09-05, omx) 정정: add the Lee 2020 / NORBC lineage (DAgger, trainable actor, 1/3 teacher budget, GRU vs TCN-100) and correct the all-windowed claim; add R4 probes
