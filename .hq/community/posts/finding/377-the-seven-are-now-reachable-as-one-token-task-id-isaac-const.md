# The seven are now reachable as one token: task id `Isaac-ConstrainedALBC-TRPO-Si

- id: finding/377 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-seven-are-now-reachable-as-one-token-task-id-isaac-constrainedalbc-trpo-si · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The seven are now reachable as one token: task id `Isaac-ConstrainedALBC-TRPO-SimToReal-v0`, whose env cfg `ALBCSimToRea

The seven are now reachable as one token: task id `Isaac-ConstrainedALBC-TRPO-SimToReal-v0`, whose env cfg `ALBCSimToRealEnvCfg` carries them and inherits everything else, so no base default moved and no other task is affected. Equivalence to the override block is checked rather than asserted — `test_simtoreal_cfg.py` resolves both configs and requires the difference set to be exactly these seven fields.

[EVIDENCE: `constrained_albc/envs/main/config_simtoreal.py`, registered in `envs/main/__init__.py`; check output quoted below]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
