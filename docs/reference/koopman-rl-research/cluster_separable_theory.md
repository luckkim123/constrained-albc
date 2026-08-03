## Sources

- Survey (primary, directly read): Y. Shi et al., "Koopman Operators in Robot Learning," *IEEE Trans. Robotics*, vol. 42, 2026 — bibliography pp. 1104–1107 (PDF pp. 17–20), Sec. II-C (PDF p. 5), Sec. V-B (PDF pp. 13–14), Table I (PDF p. 6). Local file: `/workspace/references/Koopman Operators in Robot Learning.pdf`
- [36] M. Haseli and J. Cortés, "Modeling nonlinear control systems via Koopman control family: Universal forms and subspace invariance proximity," *Automatica*, vol. 185, 2026. [arXiv:2307.15368](https://arxiv.org/abs/2307.15368)
- [105] M. Korda and I. Mezić, "Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control," *Automatica*, vol. 93, pp. 149–160, 2018. [arXiv:1611.03537](https://arxiv.org/abs/1611.03537)
- [161] S. Peitz and S. Klus, "Koopman operator-based model reduction for switched-system control of PDEs," *Automatica*, vol. 106, pp. 184–191, 2019. [arXiv:1710.06759](https://arxiv.org/abs/1710.06759)
- [162] M. Haseli, I. Mezić, and J. Cortés, "Two roads to Koopman operator theory for control: Infinite input sequences and operator families," arXiv:2510.15166, Oct. 2025. [arXiv:2510.15166](https://arxiv.org/abs/2510.15166) (PDF read directly, pp. 8–12)

**Verification notes**: The survey bibliography and [162] pp. 8–12 were read directly (Read tool, verbatim). [36], [105], [161] content below was obtained via WebFetch/ar5iv-mediated extraction (AI-summarized from HTML), not my own verbatim multi-page read — equation/theorem numbers are reported as extracted and flagged where confidence is lower.

---

## Reference resolution (survey → exact citation)

Confirmed against the survey's in-text usage (Sec. V-B, PDF pp. 13–14), which matches the task's paraphrase almost verbatim:

| # | Citation | Survey's role for it |
|---|---|---|
| [36] | Haseli & Cortés, *Automatica* 2026, "Koopman control family: Universal forms and subspace invariance proximity" | Input-state separable model, Th. 4.3, Lemmas 4.4–4.5 |
| [105] | Korda & Mezić, *Automatica* 2018, "Linear predictors…" | Infinite-input-sequence framework, linear predictor eq. (24), "Discussion after Corollary 1" |
| [161] | Peitz & Klus, *Automatica* 2019, "…switched-system control of PDEs" | Cited example of "linear switched models" |
| [162] | Haseli, Mezić & Cortés, arXiv 2025, "Two roads to Koopman operator theory for control" | Proves [105]≅[36] equivalence |

---

## [36] Haseli & Cortés — Koopman Control Family (KCF), *Automatica* 2026

**Mechanism.** KCF is a family of operators $\{\mathcal{K}_{u^*}: \mathcal{F}\to\mathcal{F}\}_{u^*\in\mathcal{U}}$, one Koopman operator per constant-input autonomous subsystem $\mathcal{T}_{u^*}(x):=\mathcal{T}(x,u\equiv u^*)$. A trajectory under an actual (possibly time-varying) input sequence is recovered by composing the family members in order: $g(x_{m+1})=[\mathcal{K}_{u_0}\mathcal{K}_{u_1}\cdots\mathcal{K}_{u_m}g](x_0)$ — the input never has to be lifted into a single fixed operator.

**Central result (Th. 4.3 / "input-state separable model").** A finite-dimensional common invariant subspace of the KCF exists iff there exist $\Psi:\mathcal{X}\to\mathbb{C}^s$ and a matrix-valued $\mathcal{A}:\mathcal{U}\to\mathbb{C}^{s\times s}$ with
$$\Psi(x^+) = \mathcal{A}(u)\,\Psi(x).$$
This is **linear in the lifted state, but $\mathcal{A}(u)$ may be an arbitrary (not necessarily affine) function of $u$** — this is the key point for the design question below.

**Special cases (Lemmas 4.4–4.5).** Linear/bilinear = $\mathcal{A}(u)$ **affine** in $u$ ($\mathcal{A}(u)=A+\sum_i u_i B_i$, plus an augmented row for the pure-linear inhomogeneous $Cu$ term). Linear switched (the [161] case) = $\mathcal{A}(u)$ **piecewise-constant**, selecting one of finitely many fixed matrices from a discrete input alphabet. The paper's framing is explicit: these are the two narrow, commonly-used special cases of a strictly larger family.

**Assumptions / scope.** $\mathcal{T}(x,u)$ is treated as a single, fully known, fixed function — no discussion of parameter uncertainty in $\mathcal{A}(u)$, actuator faults, or a *family* of dynamics indexed by a hidden/DR parameter. Data-driven identification of $\Psi,\mathcal{A}$ is named as future work; the theory itself is model-based, not a robustness/uncertainty theory.

**Error analysis.** When the chosen lifted subspace is not exactly KCF-invariant, the paper's "subspace invariance proximity" machinery (built on the consistency-index tool from the authors' own prior EDMD work) quantifies the approximation gap — but no closed-form finite bound was surfaced in the excerpted sections; treated qualitatively/asymptotically, echoing the general Koopman-approximation literature (survey Fig. 3, consistency index $\mathcal{I}_C=\lambda_{\max}(I-K_FK_B)$).

**Maturity.** Accepted for *Automatica* (2026), UCSD authors (Cortés group), ONR/NSF funded, v4 preprint July 2025 — mature, peer-reviewed theory paper, no numerical/robotic experiments.

---

## [105] Korda & Mezić — Linear predictors, *Automatica* 2018

**Mechanism.** Classic EDMDc-style construction: lift the state with $\psi(x)$, but keep the control input structurally simple by choosing observables of the *joint* form $\phi_i(x,u)=\psi_i(x)+\mathcal{L}_i(u)$ with $\mathcal{L}_i$ **linear** in $u$. This directly yields the affine-in-raw-input predictor
$$z^+ = Az+Bu,\qquad \hat x = Cz,$$
fit by two sequential least-squares problems (Moore–Penrose pseudoinverse) — exactly the classical "affine input form in the lifted space" the survey describes in Sec. II-C-2, and structurally identical to the KIPPO aux model's skeleton (minus the learned action encoder $\phi_u$).

**Error analysis / the key caveat.** The paper's finite-horizon convergence guarantee ("Corollary 1": $K_N\to$ the true operator projected onto the observable subspace as data $N\to\infty$) **requires an orthonormal basis**. The joint-lifting structure $\phi_i(x,u)=\psi_i(x)+\mathcal{L}_i(u)$ needed to get the clean affine-in-$u$ form **breaks orthonormality**, so the convergence guarantee does *not* transfer to the linear predictors actually used for control — this is precisely the "discussion after Corollary 1" the survey flags. The authors state directly that a linear-predictor trajectory should not be expected to track the true nonlinear trajectory accurately over long horizons; their mitigation is that MPC re-solves every step (closed-loop, short-horizon use), not that the model is globally accurate.

**Bilinear alternative, explicitly declined.** They also present a bilinear predictor $z^+=Az+(Bz)u$ and note it is **asymptotically exact (tight) as lifting dimension $\to\infty$, but only under the assumption that the underlying continuous-time plant is control-affine** ($\dot x=f(x)+g(x)u$) and the discrete model comes from sampling it. They deliberately choose the *affine* (not bilinear) form for control synthesis anyway, trading away this conditional guarantee for QP/MPC solver compatibility — an engineering choice, not a claim that affine is theoretically preferable.

**Numerical evidence.** Only qualitative claims surfaced ("superior to Carleman/local linearization"); no quantitative error table was available in the extracted content — flagged as unverified rather than asserted.

**Maturity.** Extremely high — foundational, thousands of citations, the standard baseline for Koopman-MPC in both PDE and robotic control.

---

## [161] Peitz & Klus — Switched-system K-ROM, *Automatica* 2019

**Mechanism.** Input is restricted to a finite set of $n_c$ constant values $\hat u=\{u^0,\dots,u^{n_c-1}\}$; a **separate autonomous Koopman operator $\mathcal{K}_{u^j}$ is built per fixed input value** (not one augmented operator on $(x,u)$) — this is a concrete, pre-KCF instantiation of exactly the "linear switched" special case [36] later formalizes (Lemma 4.4). Optimal control becomes a switching-*time* optimization over $\tau_1,\dots,\tau_p$ given the fixed discrete input alphabet.

**Convergence guarantee.** Theorem 3.3: as basis size $k\to\infty$ and samples $m\to\infty$, the K-ROM objective converges to the true PDE-constrained objective for all control sequences in $\hat u^p$ and a.e. initial condition, built on a general EDMD strong-convergence result (their Thm. 2.6) plus assumptions that the basis functions don't vanish on positive-measure sets, the Koopman operator is bounded, and the basis is orthonormal in $L^2$ — again an **orthonormal-basis condition**, echoing [105]'s caveat.

**Evidence.** 1D Burgers ($q{=}4$ obs, $k{=}35$, ~100× integration speedup) and 2D Navier–Stokes cylinder flow at Re=100 ($q{=}8$ obs, $k{=}45$, ~7.5×10⁴× speedup); good open-loop tracking with noted divergence at high reference lift attributed to control bounds and insufficient training-data richness. No closed-form finite-$k$/finite-$m$ error bound was surfaced.

**Stated limitations.** Restriction to a *finite, fixed* constant-input alphabet fundamentally caps expressivity (no continuous-parameter fault DR); the brute-force switching-sequence search is $O(n_c^p)$, explicitly flagged as infeasible for larger horizons without relaxation/DP; accuracy decays after several steps for richer PDEs when data is not "rich enough."

**Maturity.** Solidly published, moderate citation count, PDE-control focused — no robotic/actuator-fault application.

---

## [162] Haseli, Mezić & Cortés — Two roads to Koopman control theory, arXiv 2025

**Mechanism (directly verified, pp. 8–12).** Builds three parallel function-space/operator frameworks and an *intermediary* single-step augmented framework $\mathcal{F}^{\mathrm{aug}}$ on $\mathcal{X}\times\mathcal{U}$ (with dynamics $\mathcal{T}^{\mathrm{aug}}$) to connect (i) the infinite-input-sequence framework $\mathcal{F}^\infty$ on $\mathcal{X}\times\ell(\mathcal{U})$ with left-shift $S$ and operator $\mathcal{K}^\infty$, and (ii) the KCF $\mathcal{F}$ with $\{\mathcal{K}_{u^*}\}$. Restriction/extension maps $R,E$ (Defs. 7.1, 7.4) move functions between the three domains.

**Main equivalence results.** Under closure conditions (Ci)–(Cii) — the function spaces must be closed under the restriction/extension operators $R,E$ — Props. 7.3/7.6 give well-defined *linear* operators connecting $\mathcal{F}^\infty\leftrightarrow\mathcal{F}^{\mathrm{aug}}\leftrightarrow\mathcal{F}$, and Thms. 8.2/8.4 give exact operator-level identities (e.g. $\mathcal{R}^{\mathcal{F}^{\mathrm{aug}}}_{\mathcal{F}^\infty}\mathcal{K}^\infty=\mathcal{K}^{\mathrm{aug}}\mathcal{R}^{\mathcal{F}^{\mathrm{aug}}}_{\mathcal{F}^\infty}$). Restricted to **control-independent functions**, Prop. 7.7/7.9/Cor. 7.10 show $\mathcal{F}$, $\mathcal{F}^{\mathrm{aug}}_{\mathrm{CI}}$, $\mathcal{F}^\infty_{\mathrm{CI}}$ are **isomorphic** — the two "roads" carry identical information there. In general, $\mathrm{card}(\mathcal{F})\le\mathrm{card}(\mathcal{F}^\infty)$: $\mathcal{F}^\infty/\mathcal{F}^{\mathrm{aug}}$ embed input-sequence effects *inside* the function space, while KCF keeps input information *outside* $\mathcal{F}$, in the operator-family index (Fig. 1 in the paper).

**The practically decisive result (Thm. 8.6).** For any $f\in\mathcal{F}$, along the *actual* trajectory driven by a realized input sequence $\mathbf u=(u_0,u_1,\dots)$: $f(x_k)=[\mathcal{K}_{u_0}\mathcal{K}_{u_1}\cdots\mathcal{K}_{u_{k-1}}f](x_0) = [(\mathcal{K}^\infty)^k(\text{lift of }f)](x_0,\mathbf u)$ — composing per-mode KCF operators along the realized input sequence exactly reproduces the infinite-sequence operator's prediction. The two frameworks are exactly equivalent as **representations**; they differ only in *where* input-dependence is stored, not in expressive power.

**What it does NOT do.** No numerical examples (pure operator theory). Explicitly does not address actuator faults, degradation, or parameter-varying/structurally-changing dynamics — like [36], it treats $\mathcal{T}(x,u)$ as one fixed, fully known map. Preprint only (Oct. 2025), not yet journal-accepted as far as verifiable.

---

## Implications for the KIPPO aux-model design question

**1. The proposed form is not "merely affine" — it inherits [36]'s general theorem, conditionally.** $\phi_x(o_{t+1})\approx K\,\phi_x(o_t)+B\,\phi_u(a_t)$ is [105]'s linear-predictor skeleton with the raw input $u$ replaced by a *learned nonlinear* lift $\phi_u(a_t)$. Read through [36]'s Th. 4.3, the composite map $\mathcal{A}(u):=K+B\,\phi_u(u)$ is **only** the narrow "affine-in-input" special case (Lemma 4.5) if $\phi_u$ itself is affine in $u$. If $\phi_u$ is a genuinely nonlinear NN encoder, $\mathcal{A}(u)$ can approximate an *arbitrary* continuous function of $u$ (universal approximation), which is exactly what Th. 4.3's fully general input-state separable model asks for. So the design is closer to the general KCF theorem than to the restrictive "bilinear" case the survey worried about — **provided $\phi_u$ has enough capacity and the right invariances to fit the deadband/quadratic thrust-command nonlinearity.** That static nonlinearity, on its own, is not a reason to move to bilinear or switched forms — a rich-enough $\phi_u$ subsumes it per [36]'s own taxonomy.

**2. None of the four papers give a theory for actuator-fault DR — this is the real gap, not the affine-vs-bilinear question.** [36] and [162] both explicitly fix $\mathcal{T}(x,u)$ (hence $\mathcal{A}(u)$) as one *known* function; [105]'s linear predictor is for one fixed nonlinear plant; [161]'s switched operators are indexed by a fixed, known discrete input alphabet, not by unknown fault modes. Thruster-fault DR changes the true dynamics $T_\theta(x,u)$ across episodes for a hidden $\theta$ — none of these frameworks model a *family* of $\mathcal{T}_\theta$. A single fixed $(K,B)$ pair implicitly assumes one lifted subspace is jointly invariant across the *entire* DR distribution simultaneously — a much stronger requirement than any of the cited existence theorems guarantee, and plausibly false for structurally different fault regimes (e.g., a stuck/degraded thruster). **Actionable implication**: condition $(K,B)$ on the privileged encoder's latent $z_t$ (e.g. $K(z_t), B(z_t)$ via a small hypernetwork, or concatenate $z_t$ into $\phi_x$'s input) rather than trying to make $\phi_u$ alone absorb fault-dependent behavior — $\phi_u$ only ever sees $a_t$, never the fault parameter, so it structurally cannot represent $\theta$-dependent dynamics no matter how expressive it is.

**3. Switched forms are the right tool only if faults are categorical, not continuous.** [161]/[36]-Lemma-4.4's piecewise-constant $\mathcal{A}(u)$ is a natural match if the fault DR is a small set of discrete regimes (e.g., "thruster $i$ nominal / stuck / reversed"): a mixture-of-affine-experts gated by an inferred discrete mode is the theoretically grounded upgrade path there. If the DR instead sweeps continuous parameters (ESC time constant, deadband width, latency), the switched/discrete-mode view is the wrong fit — Th. 4.3's continuous $\mathcal{A}(u,\theta)$-style conditioning (i.e., $z$-conditioned $K,B$, point 2 above) is the correct generalization, not a finite bank of switched matrices.

**4. The ESC filter and control latency are a Markovity problem, not an affine-vs-bilinear problem.** Every framework here (Th. 4.3, the [105] predictor, KCF) implicitly assumes the one-step recursion is Markov in the *lifted state itself* — i.e., $x_t$ (hence $\phi_x(o_t)$) must already carry whatever memory the true dynamics need. A first-order ESC filter with its own hidden state and a DR'd control-latency buffer are *not* functions of the instantaneous command alone; if $o_t$ is a single frame with no actuator-state history, $\phi_x(o_t)\!\to\!\phi_x(o_{t+1})$ is not well-posed as a one-step map regardless of how the input is lifted. This argues for feeding a short action/observation history (or an explicit ESC-state estimate) into $\phi_x$ — matching the student's own GRU precedent in this codebase — rather than trying to fix a memory problem with a richer instantaneous input encoder.

**5. Precedent on the affine-vs-bilinear tradeoff itself, from the authors who built both.** [105] shows a strictly bilinear form ($z^+=Az+(Bz)u$) is *asymptotically exact* only under a control-affine continuous-time plant assumption — and even its own authors chose the affine form for engineering reasons (linear-solver compatibility), accepting the lost guarantee. Given our plant is not simply control-affine (deadband + quadratic + filtered + latency-DR'd), neither the affine nor the strict-bilinear form of [105]/[36] carries a real accuracy guarantee for us; the literature's own precedent is "pick affine for tractability, rely on short-horizon/closed-loop correction to bound the damage" (matches how KIPPO-style aux losses are typically used — short rollout horizons, policy re-conditions every step) — which supports keeping the affine-in-lifted-action design **as an engineering default**, but only if the DR-conditioning (point 2) and history/memory (point 4) gaps are separately closed; those, not the affine/bilinear choice, are where the cited theory says the design is currently under-specified for this actuator model.

**Bottom line**: the survey's cited works do **not** argue for switching to bilinear or switched forms on nonlinearity grounds alone — a sufficiently expressive learned $\phi_u$ inside an affine composition is theoretically adequate for the static deadband/quadratic nonlinearity per [36]'s own general theorem. What they collectively fail to cover — and what should change in the design — is (a) making $(K,B)$ depend on the DR/fault context $z_t$, since no cited framework admits a *family* of dynamics under one fixed lifted model, and (b) ensuring $\phi_x$'s input carries enough history/actuator-state to make the one-step affine recursion well-posed given the ESC filter and control-latency memory.