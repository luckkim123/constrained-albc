# fault_koopman: Verification of Ocean Engineering vol.348 (2026) art. 123965 — Koopman-based Actuator FDI for UUV

## Q1 — Does it exist as described (venue, platform, fault axis)?

**Yes, confirmed at abstract-adjacent depth**, with the venue/volume/article-number/author details matching exactly.

- Full title: **"Actuator fault-tolerant control of underwater vehicle using koopman framework"**
- Authors: **Ravi Kiran Akumalla, Jagadeesh Kadiyam, Tushar Jain** (T. Jain — IIT Mandi, School of Computing and Electrical Engineering)
- Venue: **Ocean Engineering, Volume 348 (2026), Article 123965**
- This exact venue/volume/article-number/author triple was independently confirmed via a Google-Scholar-profile fetch for T. Jain (structured "Publications 2025–2026" listing), which is a stronger signal than a search snippet alone since it lists it as a discrete, dated entry (citation count: 1) rather than paraphrased search-engine text.
- Platform and fault axis match the brief exactly: demonstrated on a **fixed 8-thruster underwater vehicle**, targeting **actuator (thruster) faults**, using **trajectory tracking via a backstepping controller** to collect the identification data.

Verification depth: **abstract-level (recurring, near-identical abstract text surfaced by the search engine across 4+ independent queries) + structured bibliographic confirmation (Google Scholar author page)**. Full text was NOT reached — see routes-tried below.

## Q2 — Known-library faults vs. unknown faults; how is the fault parameter estimated?

The recurring abstract text is explicit that the framework targets **unknown** actuator faults, not a pre-enumerated fault library:

> "Underwater Vehicles (UVs) face a high risk of mission failure ... due to **unknown** onboard component faults ... a novel, data-driven, active fault-tolerant control framework [addresses] the challenge of **unknown actuator faults** in UVs."

Mechanism as described: a single linear **Koopman operator** is identified from operational input-output data collected during nominal (backstepping-controlled) trajectory tracking. This linear Koopman model is then used to design a **linear observer** that performs **real-time fault detection and isolation (FDI)** — i.e., the fault is estimated as a discrepancy/residual between the Koopman-observer's prediction and the true measured output, not selected from a discrete bank of pre-modeled fault types. Once estimated, the fault estimate is fed into a **controller reconfiguration** step (active FTC) that adjusts the existing backstepping controller rather than switching to a separate fault-specific controller.

This reads as a **residual/observer-based estimation** scheme (estimate the fault magnitude online from the observer residual), consistent with classical FDI-via-observer designs, just built on a Koopman-linearized plant model instead of a first-principles linear model. I could not confirm from the available text whether the fault representation is scalar-per-thruster (e.g., an efficiency/loss-of-effectiveness coefficient per thruster) or a richer parameterization — that level of detail sits in the methods section, which was not reachable.

## Q3 — Single global K vs. per-regime/switched — does it confirm or contradict the doc's blocker?

**Best-available evidence points to a single global (offline-identified) Koopman operator, not a switched/multi-model bank** — which would mean this paper does **not** directly falsify the doc's "single-K cannot cover fault-scale regime change" blocker, and may even be read as consistent with it (with an important caveat below).

Reasoning from the repeated abstract text: "the Koopman operator ... identifies the UV's system dynamics directly from operational input-output data collected during trajectory tracking via a backstepping controller. This data yields **a** linear Koopman operator used to design **a** linear observer" — singular phrasing throughout, with no mention of multiple operators, regime-switching, gain-scheduling, or a model bank. The FTC action is described as "reconfiguring the existing controller" (singular, one controller), not switching among several pre-trained controllers/operators.

**Important caveat / how this differs from the doc's threat model**: this paper's Koopman operator is identified **once, from nominal (fault-free) operation**, and then used purely as an **observer/residual generator** for FDI — the "fault-scale regime change" is handled downstream, at the *controller reconfiguration* stage (adjusting the control law to compensate once a fault estimate is available), not by re-lifting or re-fitting the Koopman operator itself across regimes. This is a materially different use of Koopman than "one global lifted linear model that must remain valid as the *plant's* fault-affected dynamics range across regimes" — here the lifted model only needs to stay valid for the *healthy/nominal* regime (since it's the reference the observer compares against), while the fault-*compensation* burden is carried by the reconfigurable backstepping controller, not by the K operator generalizing across fault magnitudes. So: it neither confirms the blocker (no explicit multi-K comparison ablation is described) nor squarely contradicts it (it sidesteps the blocker by not asking a single K to represent post-fault dynamics across regimes at all — only nominal dynamics for residual generation). Whether this decomposition (nominal-only K + reconfigurable controller) is transferable to the ALBC case depends on whether ALBC's downstream controller/policy retains enough authority to reconfigure post-fault without the Koopman-lifted state itself needing to track the faulted regime — a question the doc would need to answer separately, not one this paper resolves.

## Q4 — Validation: simulation only, tank, or field? Fault magnitudes?

**Not confirmed** — none of the reachable sources (search snippets, Scholar profile, WebFetch attempts) specify the validation environment or numerical fault magnitudes. The recurring text says only that faults were "injected" and the framework was "successfully demonstrated ... effectively detecting and compensating for injected actuator faults" — consistent with either a simulation study or a simulated-fault-injection-in-hardware study, but the wording ("fixed 8-thruster underwater vehicle" combined with "injected actuator faults") reads more like a simulation/testbed model than a reported open-water field trial. This is an inference from phrasing, not a confirmed fact — flagged explicitly as unverified.

## Routes tried (for transparency)

- `doi.org/10.1016/j.oceaneng.2026.123965` — guessed DOI, 404 (DOI not confirmed by this route; the correct DOI was never independently verified, only the venue/vol/article-number metadata).
- ScienceDirect abs page (`sciencedirect.com/.../pii/S0029801824015658`) — WebFetch 403 (as flagged in the brief).
- `r.jina.ai` reader-proxy around the ScienceDirect URL — returned a CAPTCHA-gate page, not the article.
- `sciprofiles.com` (MDPI author-profile aggregator, listed T. Jain) — WebFetch 403.
- `api.semanticscholar.org` search endpoint — HTTP 429 (rate-limited) on both attempts; not retried further to avoid burning the budget on a route that had already failed twice.
- Google Scholar author page for T. Jain — **succeeded**, gave the structured bibliographic confirmation used for Q1.
- No PDF was ever reachable (all routes paywalled/blocked before a PDF URL was exposed), so the page-image (`pdftoppm`) rescue route from the brief was never applicable — there was no PDF to fetch.
- ResearchGate/Academia.edu specific-publication pages for this title were searched but did not surface a dedicated page (only tangential co-author papers, e.g. a DRL-based UUV fault-recovery paper by an overlapping author).

## References

1. Akumalla, R.K.; Kadiyam, J.; Jain, T. "Actuator fault-tolerant control of underwater vehicle using koopman framework." *Ocean Engineering*, Vol. 348 (2026), Article 123965. DOI/URL not independently verified (guessed DOI 10.1016/j.oceaneng.2026.123965 returned 404 via doi.org; ScienceDirect landing page pii `S0029801824015658` returned 403 on WebFetch and was not visually confirmed as the same article — the pii-vs-article-number correspondence is inferred, not directly verified). Verification depth: **abstract-level via recurring search-engine text + structured Google Scholar author-page listing**. NOT full-text-read.
2. Akumalla, R.K.; Jain, T. "Online Tuning of Koopman Operator for Fault-Tolerant Control: A Case Study of Mobile Robot Localising on Minimal Sensor Information." *Machines*, Vol. 13(6), 454 (2025). https://www.mdpi.com/2075-1702/13/6/454 — related prior work by the same lead authors on Koopman-based FTC (different platform: mobile robot, not underwater). Verification depth: **snippet/title only**, cited for context, not analyzed in depth (out of scope for this key).

## GitHub repos

None found or searched for — not indicated as open-source in any surfaced material.

## Implications for ALBC

1. **Does not hand the doc a ready refutation of the single-K blocker.** The paper's architecture keeps the Koopman-lifted model scoped to *nominal* dynamics for residual-based FDI, and pushes fault-scale compensation into a separately reconfigurable controller — it does not attempt (and therefore does not demonstrate success at) using one global K to represent the *post-fault* dynamics across a range of fault magnitudes/regimes, which is the specific claim the doc's blocker is about. Citing this paper as "Koopman handles fault regime-change" would overstate what it shows.
2. **It does suggest a decomposition worth naming explicitly in the doc**: separate "detect/estimate the fault via a nominal-regime model" from "compensate for the fault via a reconfigurable downstream controller," rather than requiring one lifted representation to span all fault regimes. If ALBC's ConstraintTRPO+IPO policy/encoder architecture has an analogous "downstream compensation" surface (e.g., the asymmetric privileged critic or the fault-conditioned control head), the blocker might be reframable as "does the *non*-Koopman part of the pipeline have enough authority to compensate," rather than "can a single K span the regime" — but this is a hypothesis this paper does not test for ALBC's setting, only a structural parallel worth flagging as a possible reframing, not a resolution.
3. **Validation strength is unverified**, so this paper should be cited as a **methodological precedent** (single-K-for-nominal-residual + reconfigurable-controller-for-compensation), not as **empirical evidence of scale**, until the actual fault magnitudes and validation environment (sim/tank/field) are confirmed — which was not possible in this pass due to ScienceDirect's access wall on every route attempted.
