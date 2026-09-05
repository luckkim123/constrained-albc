# **Fault and delay were never tested together.** The deployed robot has both — m3

- id: finding/360 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: fault-and-delay-were-never-tested-together-the-deployed-robot-has-both-m3 · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: **Fault and delay were never tested together.** The deployed robot has both — m3 dead with m4 excluded, and observations

**Fault and delay were never tested together.** The deployed robot has both — m3 dead with m4 excluded, and observations 1.2 to 4.7 control steps stale — but no scored config combines them: `pair34` carries the fault at zero delay, `healthy_d1` and `healthy_d2` carry the delay with all six thrusters healthy, and no `pair34_d*` directory exists in either matrix. Every statement in this report about "the real robot's condition" is therefore an argument from two separately measured axes, not from a measurement of their combination.

[EVIDENCE: `ls .hq/work/p4/p3b_final/` returns the 4 CORE and 20 EXTRA configs, none of which pairs a nonzero `--control-delay` with a `--fault_fixed_health` vector; `p4_runner.sh` `CORE` is `("1,1,1,1,1,1 0 healthy" "1,1,1,0,0,1 0 pair34" "1,1,1,1,1,1 1 healthy_d1" "1,1,1,1,1,1 2 healthy_d2")`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md
## Comments
