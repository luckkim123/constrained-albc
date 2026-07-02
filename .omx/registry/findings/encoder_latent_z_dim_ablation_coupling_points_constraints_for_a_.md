---
title: "Encoder latent z_dim ablation: coupling points + constraints for a future sweep (from-scratch, student sync, verify via z_sweep)"
tags: []
created: 2026-07-01T10:14:00.708833
updated: 2026-07-01T10:14:00.708833
sources: []
links: ["encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har.md", "teacher_encoder_0_dead_latent_dims_keys_on_lateral_cog_cob_offse.md"]
category: reference
confidence: high
schemaVersion: 1
---

# Encoder latent z_dim ablation: coupling points + constraints for a future sweep (from-scratch, student sync, verify via z_sweep)

Planning notes for a FUTURE encoder latent z_dim ablation (envs/main). Code-verified 2026-07-01, NO code change made -- this records the coupling points and constraints so the experiment can be launched cleanly later. Current z_dim = encoder_latent_dim = 9.

WHY IT IS A CLEAN SWEEP: z_dim is fully parameterized off a single config value encoder_latent_dim (rsl_rl_ppo_cfg.py:143 = 9). All downstream shapes reference the variable, no scattered literal 9: actor_critic_encoder.py:175 num_actor_obs = policy_obs_dim + encoder_latent_dim, :104 num_critic_obs += encoder_latent_dim, :162 encoder MLP output dim, :164 LayerNorm(encoder_latent_dim). Changing the one config value reconstructs the network consistently.

CONSTRAINT 1 -- FROM-SCRATCH ONLY, no resume. Changing z_dim changes actor/critic/encoder input/output tensor shapes, so existing model_*.pt checkpoints (saved at z_dim=9) CANNOT load. Each z_dim value = a fresh random-init 0->5000 iter run (same class of change as dr-derived-norm-bounds / branch-consolidation: not byte-identical). One GPU training run per swept value.

CONSTRAINT 2 -- STUDENT latent_dim MUST TRACK TEACHER (silent-break trap). Student distillation regresses proprioception-history -> l_hat against the TEACHER's z as target. student/config.py:34 latent_dim: int = 9 "# must match teacher encoder output". Also hard-wired in student/teacher.py:96 (encoder_latent_dim=cfg.latent_dim), student/collector.py (l_gt_flat buffer sized cfg.latent_dim), student/models.py (TCN/GRU head final Linear -> cfg.latent_dim). If teacher is retrained at z_dim!=9 but student config stays 9, the student regresses a wrong-width target -> shape mismatch or silent mislearning. Any z_dim sweep that goes to deployment must re-run the whole distill+export pipeline per value.

NON-COUPLING (verified, safe) -- priv_obs_bounds is INDEPENDENT of z_dim. derive_priv_obs_bounds_from_dr (utils/priv_obs_bounds.py, the dr-derived-norm-bounds work) normalizes the encoder INPUT (privileged 27D). z_dim is the encoder OUTPUT. Changing z_dim does NOT touch priv_obs_bounds. See [[encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har]].

DO NOT ASSUME "bigger z_dim = better". Current encoder is near-saturated: teacher z-sweep shows 0/9 dead dims, mean active_dims 8.4/9 (z[7]=0.441, dead threshold max-range<0.1) -- see [[teacher_encoder_0_dead_latent_dims_keys_on_lateral_cog_cob_offse]]. So SHRINKING (e.g. 6D) tests whether all 9 are truly needed (information-bottleneck ablation, meaningful); GROWING (e.g. 12D) may just collapse the spare dims to dead OR may use them -- unknown, must be run, not assumed. Per rules/03 "No Generic Solutions Without Evidence": do not claim capacity helps without this codebase's data.

VERIFICATION METHOD (rules/03, non-negotiable). Judge z_dim effect with encoder_tools.py sweep per-dimension z-sensitivity heatmap (OLD 9D vs NEW), NOT with TB aggregates (enc_added>0 / z_std). enc_added>0 means "an update was applied", not "meaningful learning". Compare each swept run's active_dims and per-dim |z_range| against the 9D baseline.

SUGGESTED DESIGN (git-native isolation per rules/02). Highest-information framing is NOT "maximize performance" but "is 9D justified?": branch exp/z-dim-ablation off a baseline tag, retrain z_dim in {6,9,12} from the SAME baseline, then z_sweep-compare. run_id via make_run_id with a z-dim tag; one wandb project for the campaign (--log_project_name). Fold into or after the sim-to-real audit retrain batch (docs/plans/2026-06-29-sim-to-real-audit-before-baseline-retrain.md) since both need from-scratch retrains anyway.

