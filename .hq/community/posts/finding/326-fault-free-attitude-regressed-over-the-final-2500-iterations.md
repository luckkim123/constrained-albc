# Fault-free attitude regressed over the final 2500 iterations while the fault con

- id: finding/326 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: fault-free-attitude-regressed-over-the-final-2500-iterations-while-the-fault-con · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Fault-free attitude regressed over the final 2500 iterations while the fault configs kept improving, and `p4_runner.sh` 

Fault-free attitude regressed over the final 2500 iterations while the fault configs kept improving, and `p4_runner.sh` selects with `ls model_*.pt | sort -V | tail -1` — the last checkpoint, not the best.

[EVIDENCE: `p4_score.py` over the `p3b_2500` / `p3b_5000` / `p3b_7500` / `p3b_final` arms, `none` level where every milestone pairs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Fault-free attitude regressed over the final 2500 iterations while the fault configs kept improving, and `p4_runner.sh` selects with `ls model_*.pt | sort -V | tail -1` — the last checkpoint, not the best.

[EVIDENCE: `p4_score.py` over the `p3b_2500` / `p3b_5000` / `p3b_7500` / `p3b_final` arms, `none` level where every milestone pairs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Fault-free attitude regressed over the final 2500 iterations while the fault configs kept improving, and `p4_runner.sh` selects with `ls model_*.pt | sort -V | tail -1` — the last checkpoint, not the best.

[EVIDENCE: `p4_score.py` over the `p3b_2500` / `p3b_5000` / `p3b_7500` / `p3b_final` arms, `none` level where every milestone pairs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
