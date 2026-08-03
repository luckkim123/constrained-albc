## Axis C: History-Window Lifting and Teacher-Side History in Teacher-Student RL

### C1 — Does the RMA-family teacher ever consume long proprio history, or is privileged-info + short obs standard?

**Finding: privileged-info + short-obs teacher is the norm; history is the *substitute* the student uses when privileged info isn't available, not a complement the teacher also gets.**

| Work | Teacher input | Student/adapter input | Verified |
|---|---|---|---|
| **RMA** (Kumar et al., arXiv:2107.04034) | Current state $x_t \in \mathbb{R}^{30}$ + $a_{t-1}$ + extrinsics $z_t\in\mathbb{R}^8$ (from privileged $e_t$). No history. | Adaptation module: $k=50$ steps (0.5s @100Hz) of $(x_{t-k:t-1}, a_{t-k:t-1})$ through a 1D CNN → $\hat z_t$. | Fetched, quoted directly: base policy is an MLP on current-step-only input; the history lives *only* in the adapter that must estimate what privileged access already gives the teacher. |
| **HORA** (Qi et al., CoRL'22, arXiv:2210.04887) | Stage-1 (teacher/base) policy takes privileged object properties directly, no history. | Stage-2 (student) policy takes proprioceptive+action **history** in place of privileged info. | Confirmed via search of paper/GitHub — same two-stage privileged-vs-history split as RMA. |
| **Distillation-PPO** (arXiv:2503.08299) | Teacher: Conv1D over clean simulator scan-dots → 32D latent, no temporal history. | Student: 50-frame history state → 32D latent via a separate encoder; downstream MLP is *inherited* from the teacher (parameter-shared trunk). | Fetched and quoted directly. |
| **CTS** (arXiv:2405.10830, "Concurrent Teacher-Student RL") | Teacher and student trained *concurrently* in one PPO run sharing the **same downstream policy/critic trunk**; only the front-end encoder differs (privileged encoder vs. proprioceptive/history encoder feeding the shared trunk). | — | Confirmed via search summaries + project page (PDF text-extraction was garbled, so the exact belief-encoder equations are unverified — flag). |

No paper found in this search claiming teacher-side history helps *in addition to* privileged access — the RMA/HORA design choice (base policy = current state + extrinsics only, explicitly *not* history) is itself the strongest evidence: when $p_t$-equivalent info is available, the field's revealed preference is to drop history from the teacher, not add it.

### C2 — Window-lifting encoders producing a Koopman-linear latent from an obs-history window (distinct from KOAP)

Four candidates found; **none operate in an RL-with-privileged-teacher setting** — all are classical/MPC system-ID on low-dimensional or single-system problems:

- **Yang & Bhounsule, "Koopman Operator Based Time-Delay Embeddings and State History Augmented LQR"** (arXiv:2507.14455, confirmed abstract + fetched body). Classical (non-neural) Hankel-matrix + EDMD: stacks $[x_i,\dots,x_{i+m}]$ history into a Hankel matrix, recovers a linear Koopman operator by least-squares, then runs a **state-history-augmented LQR**: $\hat U_i = -K_{LQR}\hat X_i$ where $\hat X_i$ is the full past window. Window lengths are large relative to RL contexts — N=110/M=90 (~200 steps) for a bouncing pendulum, N=300/M=600 (~900 steps) for a simplest walker — spanning multiple hybrid-mode cycles. No neural network, no RL, no policy network at all; it's LQR gain synthesis on a linearized augmented state.
- **Deep Recurrent Koopman Operators (DRKO)**, "Robust Learning and Control of Time-Delay Nonlinear Systems" (IEEE TII 2024, 10.1109/TII.2023.10311059, PDF at xiangyin.sjtu.edu.cn/Paper/24TII.pdf, fetched). A recurrent encoder ingests a **window of time-delayed observations** and outputs mean/variance of a probabilistic Koopman embedding, propagated linearly, used for **robust MPC** on a chemical process. Confirms delay-embedding + deep + recurrent lifting exists, but exact window length was not extractable from the fetch (flag: unverified number) and the application is process control, not legged/manipulator RL.
- **MAKO** (arXiv:2510.09042, 2025, fetched). Meta-adaptive Koopman lifting that appears to consume delay-embedded history (confirmed by fetch) and meta-learns the lifting/operator per system parameters, for MPC under parametric uncertainty. Architecturally closest in spirit to a "history + parameter-conditioned lifting," but again MPC not policy-gradient RL, and exact window length wasn't extractable (flag: unverified number).
- **CKNet/DCKNet/VCKNet** (arXiv:2102.10205). Combines delay embedding with a Koopman autoencoder for pixel-based latent dynamics; general description confirmed via search summaries, but the PDF fetch was garbled so window-length specifics are **unverified** — cite with caveat only.

Structural gap: every window-lifting-Koopman precedent found is classical-control/MPC-flavored (LQR/MPC, offline system ID, single or few systems), not large-batch on-policy/TRPO-style RL with a privileged teacher. None benchmark against a privileged-parameter encoder baseline the way our $p_t\to z$ encoder does.

### C3 — Precedent for blurring the teacher/student split via shared history

**CTS is the one clear precedent**, and it blurs the split by *sharing the downstream trunk*, not by giving the teacher its own history window: teacher and student are trained concurrently, sharing one policy/critic body, and differ only in whether a privileged-encoder or a proprioceptive/history-encoder produces the latent fed into that shared trunk. Distillation-PPO similarly makes the two encoders *interchangeable by design* (matched 32D output, inherited downstream MLP weights) without literally adding history to the teacher.

I found **no paper where the teacher consumes $o_{t-H:t}$ while still retaining full privileged $p_t$ access** — i.e., no precedent for the exact configuration your question poses (redundant-by-construction: both a ground-truth privileged channel *and* a self-estimated history channel in the same teacher). The absence is explainable from C1: privileged $p_t$ is strictly stronger information than anything a history window can reconstruct about the same underlying physics, so nobody in this corpus bothered building it — it reads as solving an already-solved estimation problem with a noisier tool.

### C4 — Applicability to our stack

Teacher $o_t$ (72D) already carries a **hand-engineered, sparse-stride history**: 20D current proprio + 30D tracking history (10 features × 3 past steps, stride 3) + 16D action history (8D × 2) + 3D leaky integral + 3D bias-EMA — on top of the privileged $p_t(28D)\to z(9D)$ encoder that gives the actor ground-truth physical parameters no history could recover. The student GRU/TCN already integrates a much longer horizon over the same $o_t$ stream, DAgger-distilled to match teacher $z$ and actions.

Mapping C1–C3 onto this:

1. **C1 says teacher-side history is the field's *substitute* for privileged access, not a complement.** Since our teacher already has $p_t\to z$ (ground truth), a $\phi_x(o_{t-H:t})$ on the actor path competes with the $z$ encoder's job (both try to characterize "what kind of dynamics am I in"), and $z$ wins on information content by construction.
2. **C2 says no window-lifting-Koopman precedent operates at our scale/setting** — nothing transfers as a ready recipe; all evidence is MPC/LQR on toy or single-plant systems.
3. **C3 says no precedent for keeping full privileged access *and* adding teacher-side history** — you'd be piloting an untested configuration, not applying an established one.
4. **On our stack specifically, the one place this isn't pure duplication:** the teacher's existing 30D tracking-history feature is *sparse-stride* (3 steps, stride 3) — a dense $\phi_x$ over a denser window could in principle resolve finer near-term dynamics the current stride-3 sampling misses. But this can't be cleanly ablated without disturbing the byte-identical-toggle discipline the ablation suite depends on, and there's no literature evidence (C2) that the gain from denser windowing is worth the added machinery.
5. **Deployment path is broken by design**: the teacher's $\phi_x$ is training-only unless distilled into the student. But the student's GRU/TCN is already a temporal encoder converting $o_t$-history into a compact latent for the policy — folding $\phi_x$ into the student duplicates that job. If instead $\phi_x$'s output becomes a new DAgger-matching target alongside $z$ and actions, that's a second learned-representation target with no established composition, and its aux losses (recon/latent-prediction, per KIPPO-style) risk the same failure class already documented for the $p_t\to z$ encoder (reconstruction → collapse) on a *different* encoder path — the settled "no aux losses on the encoder" ceiling doesn't literally cover $\phi_x$, but the mechanism risk transfers.

**Blockers**: (a) checkpoint/obs-contract geometry — adding a windowed-history input to the actor changes the observation contract, breaking existing 72D-obs checkpoints/eval scripts, requiring the same versioning discipline as the obs4-extraobs precedent; (b) DAgger consistency — no existing distillation target for $\phi_x$, so either it's ignored (teacher/student actor computations silently diverge) or added to the loss (new aux-loss risk); (c) deployment — zero benefit unless re-implemented in the student, at which point it's redundant with the GRU/TCN.

**Verdict: NOT-APPLICABLE** (as scoped — window-lifting $\phi_x(o_{t-H:t})$ on the teacher's actor path, alongside the existing $p_t\to z$ encoder). The literature treats history as privileged-info's substitute, not its complement (C1); no window-lifting-Koopman precedent operates at our RL scale (C2); no precedent exists for the specific "keep full privileged access + add teacher history" configuration (C3); and on our stack it would add a third temporal encoder with no deployment payoff unless duplicated into the student, competing with rather than complementing the $z$ encoder.

One adjacent note, out of this axis's literal scope but worth flagging: replacing the **student's** GRU/TCN with a Koopman-linear delay-embedding encoder (à la DRKO) has real precedent (deep + recurrent + delay-embedding + Koopman-linear latent is exactly DRKO's recipe) and would be deployment-relevant since the student is what ships — that's a different question than "teacher-side history," but is the one place this axis's C2 evidence is directly actionable.

## Sources

- [RMA: Rapid Motor Adaptation for Legged Robots (ar5iv full text)](https://ar5iv.labs.arxiv.org/html/2107.04034)
- [RMA: Rapid Motor Adaptation for Legged Robots (arXiv abs)](https://www.arxiv-vanity.com/papers/2107.04034/)
- [In-Hand Object Rotation via Rapid Motor Adaptation (HORA) — GitHub](https://github.com/HaozhiQi/hora)
- [In-Hand Object Rotation via Rapid Motor Adaptation (arXiv:2210.04887)](https://arxiv.org/pdf/2210.04887)
- [Distillation-PPO: A Novel Two-Stage RL Framework for Humanoid Perceptive Locomotion (arXiv:2503.08299)](https://arxiv.org/html/2503.08299)
- [CTS: Concurrent Teacher-Student RL for Legged Locomotion (arXiv:2405.10830)](https://arxiv.org/pdf/2405.10830)
- [CTS project page](https://clearlab-sustech.github.io/concurrentTS/)
- [Koopman Operator Based Time-Delay Embeddings and State History Augmented LQR (arXiv:2507.14455)](https://arxiv.org/html/2507.14455)
- [Koopman Operator Based Time-Delay Embeddings — abstract page](https://arxiv.org/abs/2507.14455)
- [Robust Learning and Control of Time-Delay Nonlinear Systems With Deep Recurrent Koopman Operators (IEEE TII 2024, PDF)](https://xiangyin.sjtu.edu.cn/Paper/24TII.pdf)
- [Robust Learning and Control of Time-Delay Nonlinear Systems — IEEE Xplore](https://ieeexplore.ieee.org/document/10311059/)
- [MAKO: Meta-Adaptive Koopman Operators for Learning-based MPC (arXiv:2510.09042)](https://arxiv.org/pdf/2510.09042)
- [CKNet: A Convolutional Neural Network Based on Koopman Operator (arXiv:2102.10205)](https://arxiv.org/abs/2102.10205)

---

**Note on tool/research process** (not part of the deliverable): DreamWaQ (arXiv:2301.10602) was targeted for C1 but both the PDF and abstract-page fetch failed to yield readable architectural text (corrupted/garbled extraction) — its history-length claim ("history length of 10...") surfaced only as an unattributed search snippet and could not be confirmed to belong to DreamWaQ specifically, so it was dropped rather than reported as fact. CKNet, DRKO, and MAKO's exact window-length numbers are similarly flagged unverified above where the PDF fetch degraded — reported qualitatively only, per the no-fabrication constraint.