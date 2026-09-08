# Student beats teacher in the delay cells: decompose the student latent error per dimension before crediting the margin

- id: finding/439 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: student-beats-teacher-in-the-delay-cells-decompose-the-student-latent-error-per · supersedes: none
- topic: decision
- confidence: medium · status: needs-experiment
- verified: none · keywords: student, latent, control_delay, p5
- summary: From analysis diagnose-20260908-142536. sd_p5_r3a beats model_9999 on all 7 cells at every DR level, by 5.6-6.9 deg in t

From analysis diagnose-20260908-142536. sd_p5_r3a beats model_9999 on all 7 cells at every DR level, by 5.6-6.9 deg in the d1/d2 cells (5.34 vs 11.21 medium) and 0.5-1.6 deg without lag. The margin sits where the privileged control_delay_strength input of the teacher was least trained (paced dim mean 0.06 of range) while the DAgger rollouts of the student sampled control_delay_steps uniformly over (0,13). The 2026-09-06 lesson: a student can beat its teacher through a constant latent error acting as damping. Experiment: per-dimension latent MSE of the student on the exam cells (student_latent analysis) and a teacher exam with the delay latent clamped to the true value; zero training.
## Comments
