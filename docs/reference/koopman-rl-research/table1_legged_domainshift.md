## Sources

**[50]** F. Li, Z. Abuduweili, S. Yun, R. Chen, W. Zhao, and C. Liu, "Continual Learning and Lifting of Koopman Dynamics for Linear Control of Legged Robots," arXiv:2411.14321 (survey cites this preprint id; now published as Li et al., *Proc. Mach. Learn. Res.* vol. 283:1–31, 2025, 7th Conf. on Learning for Dynamics and Control / L4DC 2025). Full text read via [arXiv PDF](https://arxiv.org/pdf/2411.14321) and [NSF PAR mirror](https://par.nsf.gov/servlets/purl/10658794), pp. 1–10 (Sections 1–4.5), code at [github.com/intelligent-control-lab/Incremental-Koopman](https://github.com/intelligent-control-lab/Incremental-Koopman).

**[53]** A. Krolicki, D. Rufino, A. Zheng, S. S. K. S. Narayanan, J. Erb, and U. Vaidya, "Modeling Quadruped Leg Dynamics on Deformable Terrains Using Data-Driven Koopman Operators," *IFAC-PapersOnLine*, vol. 55, no. 37, pp. 420–425, 2022 (MECC 2022). Full text was paywalled ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2405896322028622) and [ResearchGate](https://researchgate.net/publication/362294181_Modeling_Quadruped_Leg_Dynamics_on_Deformable_Terrains_using_Data-driven_Koopman_Operators) both returned HTTP 403) — findings below are from the publisher's indexed abstract via [search synthesis](https://www.sciencedirect.com/science/article/pii/S2405896322028622), not a direct full-text read; flagged accordingly.

**[47]–[49], [131]** — bibliography entries read directly from the survey PDF (pp. 1105, 1107); [131] cross-checked against its own abstract via [arXiv:1909.01419](https://arxiv.org/abs/1909.01419v4) / [ADS](https://ui.adsabs.harvard.edu/abs/2019arXiv190901419H/abstract).

---

## Citation resolution (bibliography, survey pp. 1104–1107)

| Ref | Citation | Legged-Koopman on-topic for this cluster? |
|---|---|---|
| **[50]** | F. Li, Z. Abuduweili, S. Yun, R. Chen, W. Zhao, C. Liu, "Learning and lifting of Koopman dynamics for linear control of legged robots," arXiv:2411.14321, 2024 | **Yes — primary target** |
| **[53]** | A. Krolicki et al., "Modeling quadruped leg dynamics on deformable terrains via data-driven Koopman operators," IFAC-PapersOnLine 55(37):420–425, 2022 | **Yes** |
| [47] | M. Švec, Š. Ileš, J. Matuško, "Predictive direct yaw moment control based on the Koopman operator," IEEE T-CST 31(6):2912–2919, 2023 | **No** — wheeled-vehicle yaw control, not legged |
| [48] | Y. Zhang et al., "Emergency supplies transportation vehicle robot trajectory tracking control based on Koopman operator and improved event-triggered MPC," Int. J. Robust Nonlinear Control 34(13):9089–9111, 2024 | **No** — transportation vehicle, not legged |
| [49] | X. Guan et al., "An online system identification algorithm for spherical robot using the Koopman theory," IEEE RA-L 10(5):4644–4651, 2025 | **No** — spherical rolling robot, not legged |
| [131] | M. Haseli, J. Cortés, "Learning Koopman eigenfunctions and invariant subspaces from data: Symmetric subspace decomposition," IEEE T-AC 67(7):3442–3457, 2022 | **Mismatch** — see note below |

[47]–[49] are false hits from proximity to [50]'s reference number; none involve legged robots, so no deep-read was warranted (per your own gating instruction).

**[131] discrepancy**: the survey's in-text sentence — "Two recent studies [50], [131] focus on modeling the full-body or local leg dynamics of legged robots using Koopman embeddings" — does not match [131]'s actual bibliography entry. [131] (Haseli & Cortés) is a general theoretical paper on data-driven Koopman eigenfunction/invariant-subspace identification (builds on EDMD; proposes the Symmetric Subspace Decomposition, SSD, algorithm), with no legged-robot content in its title or abstract. I could not find a legged-robot application inside it either. This reads as a survey citation error, not a hidden legged-robot result — I'm not asserting a resolution I can't source. One side effect worth keeping: [131] does contain a **Streaming Symmetric Subspace Decomposition (SSSD)**, an online, fixed-memory extension of SSD that incorporates new data as it arrives — genuinely relevant to your design item (2) below, just not to this legged-domain-shift cluster.

---

## [50] — deep read

### Mechanism

**What's lifted**: the robot's full proprioceptive state $x_t$ — joint positions $j_t$, joint velocities $\dot j_t$, root height $p_t^z$, root linear velocity $\dot p_t$, root angular velocity $\dot r_t$, plus root orientation quaternion $r_t$ for humanoids — all normalized to $\mathcal N(0,1)$. This is whole-body state, not per-leg-phase state.

**Dictionary**: a learned neural-network embedding $g'_\theta$, concatenated with the raw state to avoid the trivial degenerate solution ($A{=}B{=}0,\, g\equiv 0$):
$$z_t = g(x_t) = [x_t,\ g'(x_t)]^\top, \qquad z_{t+1} = A z_t + B u_t$$
Control input $u_t$ enters linearly through $B$ (standard Koopman-with-input form, not lifted itself). $\phi$ and $(A,B)$ are trained **jointly, end-to-end** — not decoupled.

**Training loss** — a discounted $k$-step rollout loss combining a *linear* term (multi-step latent-prediction error) and a *reconstruction* term (recovering $x_t$ from $z_t$ via the state-augmentation trick), weighted $\alpha{=}0.1$ toward reconstruction: "slighty emphasizing reconstruction of original state... shows better performance in practice" (Sec. 3.2). This is a single joint objective, not two independently-scheduled auxiliary heads.

**"Domain-shift-robust" refinement — the part the survey highlights.** This is the critical distinction you flagged, and it does **not** mean what "domain shift" means in a DR context. Concretely (Sec. 3, Fig. 1, Algorithm 1):

- Everything happens **offline, before deployment**, in an outer loop that alternates a *Lifting Phase* and a *Learning Phase*.
- *Lifting Phase*: an "Increment Data Collector" runs the **current** MPC controller (built on dynamics $\mathcal T^{(k)}$) to track references drawn from a fixed reference repository $\mathcal R$ (built by adding uniform noise $[-0.05, 0.05]$ to a PPO-generated reference set, so $\mathcal R$ contains some dynamically-infeasible/near-failure references). Failed-tracking rollouts are harvested as $\mathcal D_{incre}$ and appended to the dataset: $\mathcal D^{(k+1)} = \mathcal D^{(k)} \cup \mathcal D_{incre}$. The latent dimension is grown $n^{(k+1)} = n^{(k)} + \Delta n$ ($\Delta n$ a hand-set hyperparameter).
- *Learning Phase*: $(g, A, B)$ are **retrained from the full updated dataset** using the loss above.
- Stopping/trigger criterion: repeat until the survival-steps metric $T_{sur}$ under MPC stops improving iteration-over-iteration — an internal training-curriculum stopping rule, not an external domain-change signal.
- **Crucially, each of the 7 experimental "test suites" (5 robots × 2 terrains) is a fixed, single target domain, trained separately** ("all methods are trained separately on 7 test suites"). There is no deployed model that spans multiple domains, and no re-fitting of $K$ once training ends.

So what the paper calls "domain shift" is a **within-domain data-coverage gap**: an initial behavior-cloning-style collector (PPO policy) doesn't visit the near-failure / corner-case region of state space that closed-loop MPC tracking needs, so the refinement loop is closed-loop self-exploration to fill that coverage gap for **one fixed plant**, not adaptation across a family of plants or across time.

**Theory**: Theorem 1 shows $K \to \mathcal K$ as $m = \Omega(n \ln n) \to \infty$ (i.i.d. samples, bounded latent state, orthogonal/independent embedding functions), with convergence rate $\text{error} \le \mathcal O(\sqrt{\ln n / m}) + \mathcal O(1/\sqrt n)$ under decaying-eigenvalue and ordering assumptions on $\mathcal K$'s eigenfunctions — this motivates growing $n$ and $m$ together, and is architecture-agnostic (useful as a general sizing heuristic independent of the domain-shift question).

### Evidence / numbers

MPC on the lifted linear model, QP-solvable (Eq. 5), horizon $H$, joint-space PD low-level controller at 200 Hz (decimation 4), sim at 50 Hz.

Table 1 (averaged over all 7 test suites; Joint-relative errors $E_{JrPE}/E_{JrVE}/E_{JrAE}$, Root-relative $E_{RPE}/E_{ROE}/E_{RLVE}/E_{RAVE}$, survival $T_{sur}$, upper bound 200):

| Method | $E_{JrPE}\downarrow$ | $E_{JrVE}\downarrow$ | $E_{JrAE}\downarrow$ | $E_{RPE}\downarrow$ | $E_{ROE}\downarrow$ | $T_{sur}\uparrow$ |
|---|---|---|---|---|---|---|
| **Ours (Incremental Koopman) + MPC** | **0.0348** | **0.6499** | 43.15 | **0.1231** | **0.0668** | **188.45** |
| DKRL (Song et al. 2021) + MPC | 0.0823 | 1.1251 | 68.85 | 0.2978 | 0.1561 | 116.95 |
| DKAC (Shi & Meng 2022) + MPC | 0.1816 | 2.0694 | 117.55 | 0.3955 | 0.2749 | 25.03 |
| DKUC (Shi & Meng 2022) + MPC | 0.1576 | 1.0828 | 50.57 | 0.2934 | 0.1989 | 82.46 |
| NNDM (Nagabandi 2017 / Liu 2023) + NMPC | 0.1439 | 2.0220 | 127.45 | 0.4334 | 0.2506 | 35.47 |

Ablation (Table 2, Flat-Unitree-Go2 + Flat-Unitree-G1 average): removing the **dataset-increment** step raises $E_{JrPE}$ ~8.4× (0.0246→0.2061) and drops $T_{sur}$ from 196.6→53.1; removing the **dimension-increment** step raises $E_{JrPE}$ ~4.8× (→0.1189) and drops $T_{sur}$ to 100.9. Both mechanisms matter, and the dataset-coverage mechanism matters more than the dimension-growth mechanism in this ablation.

### Sim/hardware, maturity

**Simulation only** (IsaacLab), 5 robots (ANYmal-D, Unitree A1/Go2/H1/G1), 2 terrain types (flat; rough, 0.005–0.025 m height variation), one task (velocity-tracking walk). No hardware results — the paper's own future-work statement: "tele-operation or retargeted human data will be tested to implement our algorithm in real-world scenarios" (i.e., real-world validation is explicitly not yet done). Peer-reviewed / published at L4DC 2025 (PMLR vol. 283), open-sourced.

---

## [53] — skim

Quadruped leg dynamics over deformable (soft) terrain, framed as a **switched dynamical system**: a Koopman-linear model is fit per gait/contact regime, with the terrain-leg stance-phase interaction as the hard-to-model nonlinearity being linearized. Reported finding (via publisher abstract, not independently read in full — flag accordingly): the learned switched-system model predicts gait trajectories on **unknown terrain**, and — notably — the Koopman generator exhibits a **distinct spectral signature per terrain type**, which the authors use for terrain classification without foot-force sensors. This is architecturally different from [50]: [53] treats terrain identity as something the Koopman spectrum can *reveal* (a passive terrain-classification signal), rather than something a control-facing lifting network is refined against. I did not verify whether validation is hardware or simulated — could not access primary text (403 on both ScienceDirect and ResearchGate); treat platform/terrain specifics as unconfirmed until the primary PDF is obtained.

---

## Implications for the three design items

**(a) per-episode DR (shift every episode) vs (b) slow deployment-time drift — precise answer**: [50]'s refinement recipe transfers to **neither**, cleanly. It is a third category: an **offline, single-fixed-domain data-coverage curriculum** — it never trains one model across a family of distinct plants (each of its 7 domains gets its own separately-trained $(g,A,B)$), and it never updates weights after training ends (no online/deployment-time mechanism at all). The "domain shift" it addresses is the mismatch between an initial behavior-cloning collector's state-space coverage and the corner-case states closed-loop MPC needs *within one plant* — orthogonal to both your per-episode DR setting and your deployment-time drift setting. Do not port its trigger/refinement loop as-is for either.

**(1) KIPPO-style lifting $\phi_x$ (decoupled aux recon + prediction, block-partitioned targets)**: [50] is a useful negative/positive data point on aux-loss design generally, even though its domain-shift claim doesn't transfer. It trains recon + $k$-step prediction **jointly** (not decoupled) and finds a *light* reconstruction weight ($\alpha{=}0.1$) outperforms heavier weighting — some empirical support that reconstruction should be a light regularizer rather than a dominant objective, consistent with your plan to decouple it. Their explicit degeneracy safeguard — concatenating raw state into $z$ so $z=[x,g'(x)]$ can never collapse to $A{=}B{=}0,\,g\equiv0$ — is a cheap, concrete architectural guard worth adopting regardless of the domain-shift question. Theorem 1's $m=\Omega(n\ln n)$ sample-vs-latent-dimension coupling is a general sizing heuristic, not domain-shift-specific.

**(2) deployment-time online Koopman disturbance/current observer**: [50] provides **no** transferable mechanism here — its refinement is explicitly batch/offline, full retraining each iteration, never online. The more relevant primitive surfaced in this search is [131]'s **Streaming Symmetric Subspace Decomposition (SSSD)**: an online, fixed-memory algorithm for incorporating new data into a Koopman eigenfunction/invariant-subspace estimate as it streams in. It's a generic theoretical tool (not legged, not disturbance-specific), but it is a genuine online-update Koopman algorithm, worth a dedicated read if you pursue item (2) — flagged as a lead for follow-up, not verified in depth here since it fell outside this cluster's brief.

**(3) scaffold-side conditioning $K(z)$ for the DR plant family**: [50] argues by contrast rather than support. Its strategy for robustness — keep the domain fixed, aggressively grow data + latent capacity to cover *that* domain's corner cases, and train a **separate** model per domain — is structurally the opposite of a single $K(z)$ conditioned on a context/domain latent that must generalize *across* your DR family. It offers no evidence that within-domain coverage-growth would substitute for or complement explicit domain-conditioning; if anything it suggests that scaling their approach naively to your setting would mean training (and maintaining) one Koopman model per DR condition rather than one conditioned model — the opposite of what item (3) wants.