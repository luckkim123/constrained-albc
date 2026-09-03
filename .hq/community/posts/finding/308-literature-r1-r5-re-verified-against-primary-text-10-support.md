# Literature R1-R5 re-verified against primary text: 10 supported, 3 partly, 1 contradicted (2512.13359 is not a UVMS and has no dead band) -- no plan decision moves

- id: finding/308 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: history
- confidence: medium · status: resolved
- verified: yes · keywords: literature, retrain-simtoreal-2026-09, deadband, latency, ftc, doraemon
- summary: Re-verification 2026-09-03 of the 13 external sources cited by the frozen retrain plan. Full-text passages, not abstracts: R1-c (arXiv 2512.13359 fixed +/-5 N band) is contradicted -- the paper abstracts to body forces and defers actuators to deployment; R1-d (2508.19164) is adaptive control not RL but its failed deadband compensation is real; MMDR +90 pct should read nearly 100 pct moving distance; Gangapurwala Table I confirms 50 ms at 50 Hz vs 90 ms at 10 Hz. No decision in PLAN v3.1 changes; four text corrections owed to section 12.

Re-verification (2026-09-03) of the 13 external sources the 2026-09-02 frozen plan cited under "Traceability R1-R5" and PLAN v3.1 §12 carried as "not re-verified". Method: arXiv abstract for every id (arxiv MCP), full-text passage for every numeric claim (arxiv HTML via WebFetch, or pdftotext on the downloaded PDF), vendor pages for the two non-arXiv sources. Verdict per source, with the sentence the verdict rests on.

## Ledger

| # | Source as cited | Verdict | What the primary text says |
|:--|:--|:--|:--|
| R1-a | BlueRobotics T200 guide, neutral 1475-1525 us | SUPPORTED | Basic ESC / T200 guide: "1500 us (+/- 25 us of deadband) is stopped"; forward >1525 us, reverse <1475 us |
| R1-b | MarineGym arXiv 2503.09203 "models a dead-zone" | SUPPORTED | Sec. III-D: "thrust generation model of propellers is represented as a quadratic function with a dead zone" |
| R1-c | "6-DOF UVMS paper arXiv 2512.13359 uses a fixed +/-5 N band" | **CONTRADICTED** | Tuncay/Andres/Carlucho: a free-floating AUV with NO manipulator; the agent "operates in terms of body-fixed forces and torques rather than individual thruster commands"; thruster constraints are "deferred to deployment". No dead band of any width appears. The citation supports the *deployment-lane* choice, not a fixed band |
| R1-d | "spacecraft RL arXiv 2508.19164 measured a failed deployment-side deadband compensation" | PARTLY | Not RL: a Lyapunov adaptive controller with integral concurrent learning. The deadband fact is true and stronger than cited: reaction wheels have "a current deadband of around 300 mA"; kick-starting and sign-times-deadband offset both "proved unsuccessful"; they switched to velocity commands |
| R1-e | Whitcomb & Yoerger 1999 "links dead-zones to limit cycles" | PARTLY (unread) | The 1999 IEEE JOE paper is "Preliminary experiments in model-based thruster control for underwater vehicle positioning" (24(4):495-506). The dead-zone -> limit-cycle statement is how later citing work frames it; I did not read the paper, so the attribution is unverified |
| R2-a | Tan et al. 2018 arXiv 1804.10332 "obs latency 3-19 ms at 150-200 Hz" | SUPPORTED | "The PD servo running on the microcontroller has a lower latency (3ms) while the locomotion controller executed on TX2 has a higher latency (typically 15-19ms)"; control frequency "approximately 150-200Hz" |
| R2-b | MMDR arXiv 2109.14549 "proprio delay DR [0, 40 ms] at 25 Hz, per-modality independent, +90 % real-world" | SUPPORTED except the % | Table: Proprioception Latency (s) [0, 0.04]; control 25 Hz (PD at 400 Hz); "we randomize the observation from different modalities independently". Real-world: "improves the Moving Distance by nearly 100%, and reduces the Collision Steps by 475% to the No-Delay baseline" -- the plan's "+90 %" should read "nearly 100 % moving distance" |
| R2-c | Learning to Swim arXiv 2410.00120 "skipped action-delay DR citing instability" | SUPPORTED | "we do not model motor action delays which can lead to instabilities in deployment"; compensated with quaternion slerp at deployment |
| R3-a | Satellite RL arXiv 2505.00165 "dedicated underactuated-case policy" | SUPPORTED | Abstract: nominal case and "the underactuated case, where an actuator failure is simulated randomly along with one of the axes" |
| R3-b | Quadrotor RL-FTC arXiv 2505.08223 "infers faults from history" | SUPPORTED | Transformer "to infer latent representations in real time" under loss-of-effectiveness faults (sim only, PyBullet) |
| R3-c | arXiv 2603.10714 "infers faults from history" | SUPPORTED | MAVEN: "predictive context encoder ... infer a latent representation of the system dynamics from interaction history"; single-rotor thrust loss up to 70 %, real flights |
| R4 | Gangapurwala ICRA 2023 arXiv 2209.14887 "50 ms @ 50 Hz vs 90 ms @ 10 Hz; 10 Hz not worse; resampling 200 Hz history at 10 Hz -> near-zero gradients" | SUPPORTED | Table I (max actuation delay before failure, 5 ms resolution): 5 Hz 90, 10 Hz 90, 25 Hz 65, 50 Hz 50, 100 Hz 30, 200 Hz 20 ms. Fig. 7: "Sampling joint state history at 10 Hz for pi_b:4 resulted in near-zero gradients for history terms". Table II compares 10 Hz vs 200 Hz perceptive success over 100 runs |
| R5-a | HuB arXiv 2505.07294 "OU-colored noise beat uniform in sim (67.18 vs 69.45 mm)" | SUPPORTED, weaker than it reads | Table 9 (Bruce Lee's Kick, sim): independent uniform 105.21, independent OU 99.22, coupled uniform 69.45, coupled OU 67.18 mm. The large effect is *coupled vs independent* injection (105 -> 69); OU vs uniform is 2.3 mm. Sim only |
| R5-b | DORAEMON arXiv 2311.01885 "alpha 0.5, best-checkpoint tracking, infeasible ranges destabilize" | SUPPORTED | "the value of alpha=0.5 generalizes sufficiently well ... selected this value for all our experiments"; "we track the best-performing policy during training in terms of global success rate"; "exposure to harder/infeasible parameters, which destabilize training"; fixed wide DR "unable to learn any meaningful behavior" |

Tally: 10 SUPPORTED, 3 PARTLY (R1-d label, R1-e attribution, R2-b percentage; R5-a magnitude), 1 CONTRADICTED (R1-c).

## Does any verdict change the plan?

No decision moves. R1's conclusion ("no RL work does both sim-model and deployment-inverse; this program takes the deployment lane") is *strengthened* by the corrected R1-c, which defers actuator constraints to deployment explicitly. R1-d loses its "RL" label but keeps the fact the plan uses it for (a deployment-side deadband compensation that failed on hardware). R2 still supports a narrow (0,1)-class delay range with a paired gate. R5-a is cited nowhere in the v3.1 knob table (noise is held as-run), so its weaker reading costs nothing.

Text corrections owed to PLAN §12: R1-c rewritten; R1-d "spacecraft RL" -> "spacecraft adaptive control (not RL)"; R2-b "+90 %" -> "nearly 100 % moving distance"; R1-e marked unread.

## Method note

The three older PDFs (1804.10332, 2109.14549, 2209.14887) have no arXiv HTML rendering; WebFetch returned binary and the numbers above come from `pdftotext` on the saved PDFs. arXiv abstracts alone would have passed R1-c and R1-d -- the mislabels live in the body, which is why abstract-level verification is not verification.
## Comments
