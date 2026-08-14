---
title: "UTracker diffusion policy is rejected for ALBC on two independent grounds, and its repo disagrees with its own paper on all six axes (do not use it as a comparison axis)"
tags: ["albc", "utracker", "diffusion", "imitation-learning", "distillation", "rma", "transfer", "deployment-budget", "citation-safety"]
created: 2026-08-14T06:01:49.026013
updated: 2026-08-14T06:01:49.026013
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# UTracker diffusion policy is rejected for ALBC on two independent grounds, and its repo disagrees with its own paper on all six axes (do not use it as a comparison axis)

[INVESTIGATION 2026-07-21, read-only -- zero changes to training or deployment code] Asked whether
anything in UTracker's IL + diffusion method transfers to ALBC's 2-stage setup (RL teacher +
proprio-history student). Nine candidates, adversarially screened on three lenses (deployment
feasibility / scientific validity / cost-benefit). The headline answer is NO for the method itself,
and there is a second finding about the SOURCE that matters more than the verdict.

## 1. The diffusion policy is rejected on TWO INDEPENDENT grounds

Either one alone is sufficient; they do not depend on each other.

GROUND A -- THE PROBLEM IT TARGETS DOES NOT EXIST HERE. A diffusion policy earns its cost when one
observation admits several valid trajectories and a deterministic policy collapses to their mean.
Of ALBC's four documented failure families (joint1 integral windup, yaw dynamics gap, buoyancy DR
centring, TAM channel mapping), the number showing that multimodality signature is **zero**.

GROUND B -- THE DEPLOYMENT BUDGET KILLS IT REGARDLESS. Measured from the repo's actual adopted
config: one forward pass of the noise-prediction network is **813 MFLOPs**. Assuming the most
favourable case -- distilling denoising down to a single step -- that is 0.41 to 1.63 s on the TX2
under numpy, against a **20 ms** control budget: 20x to 81x over. No amount of resolving the
multimodality argument moves this.

## 2. Read this before citing UTracker anywhere: the repo disagrees with the paper on all six axes

| axis | paper's account | config actually selected |
|:---|:---|:---|
| horizon / N_obs / N_action | 8 / 5 / 4 | **16 / 2 / 8** |
| scheduler | DDIM, 20 inference steps | **DDPM, 100 steps, no acceleration** |
| beta schedule | linear [1e-4, 0.02] | **cosine (squaredcos_cap_v2)** |
| U-Net channels | [512, 1024, 2048] | **[256, 512, 1024]** |
| vision encoder | ResNet-18 (BN->GN) + TCN fusion | **vendored MultiImageObsEncoder, TCN not wired** |
| epochs | 500 | **100** (or a stale config saying 8000) |

The TCN-fusion encoder the paper presents as central (`diffusion_vision_encoder.py::Encoder`) is
**not referenced as a `_target_` by any hydra config**, and its only caller
(`examples/diffusion/test_policy.py`) uses a kwarg and an attribute that do not exist -- i.e. dead
code. Separately, `diffusion_policy/` is Chi et al.'s original vendored wholesale at a single
commit (78c8fd1) with no attribution in the README, and the LICENSE (GPLv3) contradicts the
README's MIT claim.

THREE CONSEQUENCES.
1. "Port UTracker's method" is an under-specified sentence -- the pipeline as described has never
   existed at the repo head.
2. Any hyperparameter lifted from the paper is disconnected from the code that produced the results.
3. **Do not use this discrepancy as a comparison axis in our own paper.** We could not rule out
   that the paper's numbers came from an unpushed or pre-head branch (unverified). Putting an
   unverified third-party repo state on a review-panel slide invites the first question "did the
   paper claim that, or did you read dead code on GitHub?" -- a question with no good answer.

## 3. "Is our stage 2 imitation learning?" -- half yes, and the half that splits is the point

Both ALBC stage 2 and UTracker stage II are supervised learning on teacher-produced labels with no
reward and no exploration, and the literature does file RMA/HORA-style phase 2 under
privileged-information distillation. What differs is WHAT is imitated:

- **ALBC matches an intermediate node of a function composition.** The student regresses the
  teacher encoder's 9D latent z under ||z_hat - z_gt||^2; the actor MLP and the observation
  normalizer are reused FROZEN from the phase-1 checkpoint. Exactly one module is replaced at
  deployment: the encoder.
- **UTracker reuses none of the teacher network.** It regresses the whole action sequence A_t with a
  new conditional diffusion model (noise-prediction MSE). Explicit L2 action matching exists only in
  a separate BC baseline (`examples/bc/train_bc.py`), which is single-frame -> single-action and
  therefore not architecture-controlled against the diffusion policy.

The consequence is symmetric: ALBC's student inherits the teacher actor's CMDP constraint
satisfaction and inductive bias, but takes on latent-regression error amplified through the actor
Jacobian (A-RMA, arXiv:2205.15299, Table III: RMA MTTF 11.4 s vs phase-3 retrained 14.0 s vs oracle
14.2 s). UTracker's student gains freedom to represent multimodal action distributions and loses the
teacher's safety guarantees entirely.

THREE CORRECTIONS to how this family is usually described:
- RMA/HORA phase 2 is **already on-policy** ("We unroll the base policy pi with the z_hat predicted
  by the randomly initialized policy phi... iteratively until convergence", arXiv:2107.04034). So
  the axis separating these approaches is NOT offline-vs-on-policy; it is **label type**
  (latent-only vs latent+action).
- 'Learning to Walk in Minutes' (arXiv:2109.11978) has NO teacher-student distillation at all --
  do not file it with RMA/HORA.
- The canonical "action distillation" papers are not action-only either: Lee et al.
  (arXiv:2010.11251) use (a_bar - a)^2 + (l_bar - l)^2, Miki et al. (arXiv:2201.08117) use
  L_bc + 0.5 * L_re. The real spectrum is latent-only (RMA/HORA) -> mixed (Lee/Miki) -> action-only
  (UTracker). ALBC sits at the far left end.

## 4. What survived the screen

Rejected: diffusion policy onboard (C1), action chunking (C2, the open-loop window re-accumulates
the joint1 integral path), latent-multimodality generative diagnosis (C3, the existing distillation
loss answers the same question), UTracker-style hierarchy (C6, regression to a superseded design),
and absolute/chunk-aligned action space (C7, deletes the only slew limiter).

Kept: C8 on-policy fact-check (one file to read). Conditional: C4 latent-regression error +
oracle-z ablation, Isaac only (z_gt is undefined in Stonefish); C5 A-RMA phase 3, only after the
oracle gap is measured; C9 evaluation protocol and narrative, reduced to three items.

**The gate for everything conditional is one measurement**: in Isaac, same seed and same initial
conditions, roll out teacher (z_gt) against student (z_hat) and read the performance gap. Until that
number exists, no intervention on the distillation axis has grounds.

SOURCE: vault `0_Project/in_progress/albc/notes/2026-07-21-utracker-transfer-analysis.md` (57 KB,
38-agent workflow: repo measurement + ALBC structure/budget measurement + literature search). The
conditional candidates' detailed designs stay in that note; only the verdicts and the source warning
are reproduced here.
[CONFIDENCE: HIGH on the rejection and the repo discrepancy -- both read directly from code and
config. The "unpushed branch" possibility is explicitly NOT ruled out.]

