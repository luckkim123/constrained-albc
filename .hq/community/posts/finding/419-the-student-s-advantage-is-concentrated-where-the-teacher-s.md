# The student's advantage is concentrated where the teacher's privileged input is 

- id: finding/419 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-student-s-advantage-is-concentrated-where-the-teacher-s-privileged-input-is · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The student's advantage is concentrated where the teacher's privileged input is least trained. The teacher acts on the t

The student's advantage is concentrated where the teacher's privileged input is least trained. The teacher acts on the true latent, including `control_delay_strength`, which the curriculum sampled at a mean of 0.06 (a delay of ~1 step at most) — so at the exam's fixed 1–2 step delay the teacher sees a latent value it has rarely conditioned on. The student never sees the latent: its GRU infers it from the 72-D history, and its DAgger rollouts sampled `control_delay_steps` uniformly over (0, 13) with DORAEMON dropped, so it trained at 1, 2 and 8 steps of lag with equal probability. That is a training-distribution difference, not a proof of a better controller; two caveats stand. (1) Per the 2026-09-06 deployment-student lesson, a student can beat its teacher through a constant latent error that happens to act as damping — the latent MSE here (0.075 at the end of training, 0.041 minimum) is not decomposed per dimension in this report. (2) The teacher-mode comparison is not a deployment comparison; the pack's numeric forward was verified against the torch student, not against the teacher.

[EVIDENCE: student plant line in `student_p5r3a.log` (`DORAEMON scheduler dropped; DR = task cfg, uniform: ... control_delay_steps=(0, 13)`); `tbread.py` `student/loss_latent` last-10 % 0.0754, min 0.0411 at it 146; `DORAEMON/mean/control_delay_strength` last-10 % 0.0584 on segment 2]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
