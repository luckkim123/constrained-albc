# Adversarial critique — lens: systemfit (does the design survive contact with the ALBC code?)

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md`
Reviewer stance: senior engineer on this codebase. Every claim below is anchored to `file:line` read
during this critique (2026-08-03). I attack the doc's *design* claims — I do not re-litigate its
literature verdicts except where a code fact reverses one.

Headline: the doc's literature work is solid; its **engineering claims are the weak half**. Four of
them are wrong at the code level, and the two most load-bearing (the KL/trust-region reassurance in
§16.2 and the normalization plan in §11.2) are stated in one sentence each with no contact with the
files they describe. The shortlist item ranked #1 near-term (§9 cat 6, student Koopman-consistency)
is refuted by the doc's *own* §4.2 argument.

---

## THEO-1 (critical) — §16.2: "TRPO's KL constraint already bounds per-update policy shift against representation drift" is false for this implementation

**Claim attacked**: §16.2 step 2, verbatim: *"TRPO's KL constraint already bounds per-update policy
shift against representation drift (Sec 11 homework item 2)."* This is the doc's entire answer to the
"drifting representation under a trust-region algorithm" risk it raised itself in §8.4.3.

**Why it is wrong.** Read `_core/algorithms/constraint_trpo.py`:

1. The KL is evaluated by re-running the **full policy forward**:
   `_kl_divergence` (`:350-352`) calls `self.policy.act(obs)` and compares against `old_mu/old_sigma`.
   `old_mu/old_sigma` are read from storage (`update`, `:443-444`), recorded at **rollout time**
   (`act`, `:247-248`). So the KL is `KL(π_θold,φold(·|s) ‖ π_θnew,φnow(·|s))` — it constrains the
   *composite* of actor and lifting, but only for the φ that exists **at the moment of the TRPO
   step**.
2. The TRPO step is atomic: `_trpo_step` (`:533-591`) computes `g`, CG, step size, and line-searches
   with `kl <= self.max_kl * self.line_search_kl_margin` (`:414, :420`). Once it returns, nothing
   re-checks KL.
3. KIPPO's recipe — which the doc adopts wholesale (§16.2 step 1, §8.1 *"decoupled from the policy
   objective"*) — updates φ_x with a **separate optimizer between policy updates**. That step changes
   `π(·|s)` at fixed `s` by an amount subject to **no KL check whatsoever**. TRPO's monotonic
   improvement bound assumes the only change to π is the parameter step it just line-searched. An
   out-of-band representation step is exactly the assumption violation, not a case the trust region
   covers.
4. Worse, the damage is *upstream* too: the surrogate's importance ratio is
   `exp(log_prob - old_lp)` (`:474`) with `old_lp` from storage (`:442`, recorded under φ_old). If φ
   moved between rollout and update, `old_lp` is not the log-prob of the behavior policy that
   generated the data, so the surrogate is a biased estimator *before* the trust region is even
   applied. The doc's framing ("input distribution shifts under the policy") understates this: the
   *stored behavior-policy statistics* become stale, which is a harder failure than covariate shift.

**Second-order code fact the doc misses.** In this repo the "decoupled optimizer" is not free.
Parameter grouping is by **name prefix** (`:161-184`): anything not starting with
`("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")` is appended to
`self._policy_params`, i.e. the TRPO natural-gradient vector. A `phi_x` submodule registered on the
policy is therefore **silently swept into the TRPO trust region by default**, and then *also* stepped
by the aux Adam — double-updated, and KIPPO's decoupling property (the thing the doc cites as the
mechanism) is silently violated. There is precedent for deliberate double-ownership (the encoder
under `critic_uses_z`, `:186-192`) but it is a documented, argued decision; the doc makes no decision
here at all.

**Verdict**: the reassurance must be withdrawn. Either (a) φ_x lives in `_policy_params` and is
updated *only* by TRPO (then it is not KIPPO, and its aux loss cannot train it), or (b) φ_x is
excluded (add its prefix to `value_prefixes`, `:161`) and trained by the aux optimizer — in which
case **nothing bounds the representation drift** and both the trust region and the importance ratio
degrade. There is no free option. A design that picks (b) needs an explicit stale-φ guard (e.g. φ
frozen during rollout+update, stepped only on a fixed cadence with a re-anchored `old_mu/old_lp`), and
the doc's §16.2 "concurrent decoupled" staging is exactly the option that needs it.

**Research question**: does KIPPO's decoupled-φ result survive when the policy optimizer is a hard
trust-region method rather than clipped PPO? KIPPO is PPO-only; the ratio-clip absorbs mild
mis-specification, a KL line search does not. No cited work tests Koopman-φ + TRPO.

---

## THEO-2 (critical) — §11.2: the normalization plan is not implementable as described; it breaks six consumers, and "DR-derived min-max for o_t" does not exist

**Claim attacked**: §11.2, verbatim: *"the real win is replacing running-stat EmpiricalNorm
non-stationarity with static DR-derived min-max at phi_x input + bounded (tanh) output — the same
remedy already applied to the p_t encoder after the z-drift KL-spike incident."*

Three separate defects.

**(a) "DR-derived" is a category error for `o_t`.** The p_t recipe works because *every* p_t dim IS a
DR-sampled physical parameter with an explicit sampling range — `priv_obs_bounds.py` derives the
bounds from `dr_cfg` + asset SSOT with margin 0 (module docstring `:6-30`;
`derive_priv_obs_bounds_from_dr` `:53+`), and `constraint_encoder_runner.py:101-116` overrides the
cfg literals with the live DR-derived values so they cannot drift. Note what happens for the **only 3
p_t dims that are NOT DR-backed** — measured body lin-vel: they are hardcoded `(-1.0, 1.0)`
(`priv_obs_bounds.py:182-184`), a hand-picked guess, and the file's own invariant comment (`:43`)
segregates them precisely because they cannot be derived.

Now apply that to `o_t`: **zero** of its 72 dims is a DR parameter. It is 20D proprio (euler, ang_vel,
joint pos/vel, manipulability, ESC state), 30D tracking-error history, 16D action history, 3D leaky
integral error, 3D bias-EMA (`albc_env.py:1118-1178`; map in `albc_report.md` §1). Of these only the
3D command block and the 16D action history have a priori bounds (`att_cmd_rp_range`,
`yaw_rate_cmd_range` `config.py:519,521`; actions clamped to [-1,1]). Tracking error, integral error,
and ang_vel have **policy-dependent** ranges — the integral is a leaky gated accumulator
(`albc_env.py:1198-1218`) whose span *is* a function of how badly the current policy tracks. So the
proposal reduces to "hand-pick 72 bounds, or measure them from a prior run and freeze them" — i.e. a
frozen empirical estimate under a different name, extending the file's own acknowledged weak spot
from 3 dims to 72. Calling it "DR-derived" imports a guarantee that does not transfer.

**(b) It breaks six consumers of `actor_obs_normalizer._mean/_std`,** including a frozen deploy
interface:

| Consumer | Anchor | Breakage |
|---|---|---|
| Teacher geometry inference | `_core/student/teacher.py:53` | `state_dict["actor_obs_normalizer._mean"].shape[1]` → `KeyError` if the module is replaced |
| Deploy export contract | `deploy/specs/teacher_actor.py:14-15, 31-32` | `normalizer._mean/_std` are **required** keys with hard `ShapeSpec`; absence = `ExportContractError` |
| Deploy engine | `deploy/engine.py:66, :167` | same key used to infer `policy_obs_dim` |
| Golden parity harness | `deploy/golden.py:166, :179` | reads `_mean.shape` and calls the normalizer |
| Deploy CLI | `deploy/__main__.py:137` | same |
| Student normalizer sharing | `_core/student/runner.py:106`, `analysis/student_policy.py:102` | shares the *instance*; a static-bounds module works only if it keeps the same attribute name and call signature |
| Tests | `tests/deploy/test_teacher_actor_spec.py:11-14` | asserts the exact four normalizer key shapes |

Per project memory the deploy export parity was only just closed (`2f057b9`). Re-opening it for a
*screening arm* is a poor trade the doc never surfaces.

**(c) The premise — that EmpiricalNorm non-stationarity is a live problem on `o_t` — is
unsupported, and the cheap fix already exists in the dependency.** `EmpiricalNormalization.update`
(`rsl_rl/networks/normalization.py:47-62`) uses `rate = count_x / self.count`; at
`num_steps_per_env=64 × 4096 envs` (`agents/rsl_rl_ppo_cfg.py:263`) that is 262,144 samples per
iteration, so `rate = 1/k` at iteration k — the statistics are **asymptotically self-freezing**
(1% per-iteration weight by iter 100, 0.05% by iter 2000). And the constructor already takes
`until: int | None` (`:17`), which hard-freezes the stats after N samples;
`actor_critic_encoder.py:182-184` simply never passes it. So the stated "real win" is available as a
**one-kwarg change** that preserves every checkpoint key, the deploy contract, and all six consumers.

Also, the analogy to the p_t incident is weak: the encoder's normalizer drift moved **z**, a 9D
latent the actor is acutely sensitive to and which is itself the output of a *training* network
(`actor_critic_encoder.py:30` docstring). The actor's o_t normalizer is a per-dim affine on the
actor's own input at 1/k drift. Different mechanism, different severity — the doc transplants the
remedy without transplanting the diagnosis.

**Verdict for the shortlist**: §11.2 as written = **needs-redesign**. The lazy replacement
(`until=N` on the existing normalizer, or nothing at all) achieves the stated goal with a 1-line diff.

---

## THEO-3 (critical) — §9 cat 6 / §10 shortlist item 2: the student Koopman-consistency term is refuted by the doc's own §4.2 argument

**Claim attacked**: §9 priority ranking #1: *"NEAR-TERM training-side probe: student
Koopman-consistency term (cat 6, supervised-only) — smallest diff, rides existing distillation
targets"*, i.e. add `||K ẑ_t − ẑ_{t+1}||²` against logged teacher z sequences.

**The refutation is in the doc itself.** §4.2 kills the p_t-lifting proposal with: *"within an episode
`p_{t+1} = p_t` (trivial identity dynamics), so every function of `p_t` is a Koopman eigenfunction
with eigenvalue 1. There is nothing to linearize."* `z` is a deterministic function of `p_t`
(`actor_critic_encoder.py:209-220`), and 24 of p_t's 28 dims are constant-per-episode: only water
density is fixed while ocean-current velocity `[18:22]` and measured body lin-vel `[25:28]` vary
within an episode (`mdp/observations.py:89-204`, layout table in `albc_report.md` §2; the invariant
comment in `priv_obs_bounds.py:41-45` confirms the split). Therefore the true operator on z is
**K ≈ I**, and the learned K converges to identity: the term degenerates into a **temporal-smoothness
penalty on ẑ**. That may well be useful — student latent jitter is a real deployment concern — but it
is not a Koopman dynamics model, and it does not inherit KOROL/KOAP's precedent, where the latent
encodes *state* whose evolution is nontrivial. The doc applies the eigenvalue-1 argument as a killer
in §4.2 and then silently does not apply it to its own #1 shortlist item.

**Where it would attach (this part checks out).** On the GRU path — the adopted student — it is
genuinely cheap and correctly aligned:
- `_compute_loss_gru` (`_core/student/runner.py:308-325`) already has `l_hat_seq` of shape
  `(envs, T=24, 9)` (`:317`), and `batch.l_t` is `(envs*T, 9)` in **envs-major** order
  (`collector.py:190` with the alignment comment at `:187-188`), so it reshapes back to `(envs, T, 9)`
  exactly. A `K` applied to `l_hat_seq[:, :-1]` vs `l_hat_seq[:, 1:]` is a ~4-line change.
- Episode-boundary masking is **available but currently unused**: `RolloutBatch.dones_seq`
  `(envs, T)` is populated (`collector.py:186`) and never read by either loss. Without it, every
  reset inside the 24-step rollout injects a garbage transition pair. The doc does not mention
  masking.
- **The TCN path does not support it.** `iter_minibatches_tcn` (`collector.py:127-167`) shuffles
  independent `(t, env)` pairs; there is no `t+1` partner in a batch. The doc's "smallest diff"
  framing is GRU-only — fine, since GRU is adopted (memory `albc-deploy-export`), but it should say so.

**Verdict**: **needs-redesign / re-framing**. Implementable on GRU, but the doc must (i) state that
K→I is the expected outcome and therefore justify it as a smoothness prior rather than a Koopman
model, and (ii) specify done-masking. Ranking it #1 on Koopman grounds is not supported.

**Research question**: is student-latent temporal jitter actually a measured problem on the adopted
GRU student (E-int)? If not, this term is a solution without a defect — check the existing
`z_sweep`/latent diagnostics before spending an arm on it.

---

## THEO-4 (major) — §16.2 / §13.1: the aux training loop has no place to live, and K/B/H attached to the policy will crash TRPO

The doc never says *where* the φ_x/K/B/H loop runs. Three code facts constrain it hard:

1. **`torch.autograd.grad(..., allow_unused=False)`.** `_flat_grad` (`:354-366`) defaults
   `allow_unused=False` and is called as `self._flat_grad(loss, self._policy_params)` (`:543`);
   `_fisher_vector_product` does the same for the KL (`:374`). Any parameter in `_policy_params` that
   is **not used in `policy.act()`** raises `RuntimeError: One of the differentiated Tensors appears
   to not have been used in the graph`. K, B, H, the φ_u encoder, and any decoder are used only in
   the aux loss, never in `act()`. So they **cannot be submodules of the policy** unless their names
   are given one of the `value_prefixes` (`:161`) — a naming hack — or the grouping logic is changed.
   This is a hard crash, not a subtlety, and the doc's "the aux model rides alongside the policy"
   framing assumes it away.
2. **Storage is cleared before the runner can see it.** `ConstraintTRPO.update()` ends with
   `self.storage.clear()` (`:526`). `ConstraintEncoderRunner` does not override rsl-rl's inner learn
   loop — it only wraps `learn()` (`:246-251`) and `log()` (`:253-280`), and DORAEMON already
   piggybacks on `log()` (`:274-280`). So the only rsl-rl-friendly hook fires **after** the rollout
   data is nominally gone. The aux step therefore has to be inserted **inside `ConstraintTRPO.update()`
   before `:526`** — i.e. editing the settled algorithm file, which the project treats as a
   settled question.
3. **What is available is right, though.** `storage.observations` is a TensorDict of raw (un-normalized)
   `o_t` recorded at `:249`, `storage.actions` at `:244`, `storage.dones` — so `(o_t, a_t, o_{t+1})`
   triples with correct alignment exist within a rollout (minus the final step, whose successor is
   only passed to `compute_returns`). Done-masking across the 64-step rollout is required and
   unmentioned.

**Verdict**: **implementable, but only with an edit to `constraint_trpo.py`** and an explicit decision
on parameter ownership. Not the drop-in the doc implies.

---

## THEO-5 (major) — §13.2 / §11.1: the z-conditioned K(z)/B(z) hypernetwork leaks aux-loss gradient straight into the p_t encoder — violating the settled rule's *letter*, not just its spirit

**Claim attacked**: §13.2 item 1: *"condition the scaffold on the privileged latent — K(z), B(z) via
small hypernetwork (training-only, scaffold asymmetry principle of Sec 11 preserved)"*; §11.1 stages
it as the *safer* alternative to `phi_x(o,z)`.

The word **`detach` does not appear anywhere in the 639-line document** (verified by grep). Without it,
`L_aux → H/K/B → hypernet → z → encoder MLP → p_t encoder parameters` is a live gradient path. Rule 03
(`.claude/rules/03-analysis-quality.md`, "No Encoder Auxiliary Losses": *"Encoder에 auxiliary loss
(reconstruction, z_bounds, contrastive 등) 추가 절대 금지"*) is unqualified as to *which* loss; this is
a direct violation of the letter, and §8.4.1's "new module, not covered by the rule's letter" defence
does not extend to it — the gradient reaches the old module.

**And it is a latent bug independent of the rule.** The encoder is owned by two optimizers under
`critic_uses_z=True`: it sits in `_policy_params` for TRPO *and* in `value_params` for Adam
(`constraint_trpo.py:186-195`). An aux `backward()` accumulates `.grad` on the encoder leaves. TRPO is
immune (it uses functional `autograd.grad`), but `self.value_optimizer.zero_grad()` (`:622`) runs
inside the value loop, so whether the aux gradient is (a) silently discarded or (b) silently applied
by the Adam step depends purely on where in `update()` the aux step is inserted. Both outcomes are
wrong and neither is loud. Given this repo's history of two-month-silent invalidation
(`student/models.py:26-32`, commit `38d979e`), an ordering-dependent silent gradient is exactly the
failure class to design out, not to leave unspecified.

**Verdict**: **needs-redesign** — the proposal must state `z.detach()` explicitly and site the aux
step relative to `value_optimizer.zero_grad()`, or the "training-only scaffold, encoder untouched"
claim is false.

---

## THEO-6 (major) — §13.1: "H scoped/sparsified" is undefined for a learned φ_x; and the cost is unestimated

§13.1's design update is `phi_x(o+) ≈ K phi_x(o) + B phi_u(a) + H (phi_u(a) ⊗ phi_x(o))`, with
*"H scoped/sparsified to lifted components plausibly carrying hydro/fault information (CCK's 'no
phantom pathway' discipline applied as a structural constraint)"*.

**The sparsification is not well-defined on the branch it is attached to.** CCK's B-sparsity works
because the dictionary entries are *hand-designed and physically named* — you know which observable
is "joint-2 velocity" and can forbid an instantaneous actuation pathway to it. A **learned** φ_x
(KIPPO-style, the doc's §8 arm) produces latent coordinates with **no assigned physical meaning**;
there is no map from latent index j to "hydro/fault information", so "scope H to the components
plausibly carrying it" has no implementable referent. The discipline transfers only to the doc's own
*cheaper route* — `[87]`-style explicit hand-designed cross-terms inside φ_x's dictionary — where the
components *are* named. As written, the sentence combines the learned-φ_x arm with a constraint only
the hand-designed arm can express. That is hand-waving.

**Cost, which the doc never estimates.** Take the doc's own m = 2–4× state dim. With m = 144 and
`phi_u` dim p = 8: H has `m × p × m = 165,888` params (≈2.7× the whole actor MLP, which is
`81·256 + 256·128 + 128·64 + 64·8 ≈ 62k`), and `m·p·m` MACs per sample. That is *fine* — but only if
the aux loop minibatches. The TRPO surrogate runs on the **un-minibatched** flat batch of
`64 × 4096 = 262,144` samples (`update` `:432-454`, `agents/rsl_rl_ppo_cfg.py:263`); if the aux loop
copies that pattern, the Kronecker intermediate alone is `262144 × 1152 × 4 B ≈ 1.2 GB` before the
autograd graph, on a 12 GB RTX 4070 already hosting 4096-env Isaac Sim. So: **implementable with
minibatching, OOM without it** — a constraint worth one sentence in any proposal.

---

## THEO-7 (major) — §8.4.4 "cheap 2000-iter screening": φ_x sits inside 10 CG double-backprops, not one extra forward

The doc prices the KIPPO arm as a screening-cheap addition. Per TRPO iteration the policy forward is
executed on the full 262,144-sample batch roughly 25 times: 1 surrogate for the gradient (`:541`),
**10 `_fisher_vector_product` calls, each a double backprop with `create_graph=True`** (`:368-379`,
`cg_iters=10` `:52`), 1 more surrogate (`:583`), up to 10 line-search iterations each doing a
surrogate **and** a KL forward (`:415-421`), plus the post-step KL (`:515`) and 5×4 = 20 critic
minibatches (`:604-607`, those are minibatched).

A φ_x MLP of 72→256→256→144 is ≈120k MACs/sample against the actor's ≈62k — so inserting it roughly
**triples the per-sample cost of the single most-repeated computation in the update**, and adds ~540 MB
of retained activations to the double-backprop graph (2 × 262,144 × 256 × 4 B). "Same iteration count,
same wall clock" is not a safe assumption for the screening comparison; the arm may need a reduced
`num_steps_per_env` to fit, which would itself confound the comparison against baseline. The doc
should state a measured `ms/iter` gate before committing the arm.

---

## THEO-8 (major) — §8.4.3 / §11: "checkpoint geometry (new track, no reuse)" is right about training and wrong about everything downstream

I verified the doc's claim for the **teacher training path** and it holds: φ_x inside the policy does
not change the env's obs width, so all four consistency checks pass unchanged —
`albc_env.py:199-210` (obs contract validates the env's assembly, not the network),
`sync_policy_obs_dim`/`sync_privileged_dim` (`_core/runners/__init__.py:13-52`, both read
`env.cfg.observation_space`/`state_space`), `_PolicyBase._init_base:75-78` (checks
`obs[policy_key].shape[-1] == policy_obs_dim`, still 72), and `student/runner.py:92-97`. Fresh track
is fine. **Credit where due.**

But the doc stops there, and three downstream consumers hardcode `actor input = obs_dim + latent_dim`:

1. **`FrozenTeacher` hardcodes the whole teacher architecture** (`_core/student/teacher.py:114-136`):
   fixed `encoder_hidden_dims=(256,128,64)`, `critic_uses_z=True`, no φ_x parameter at all. It then
   loads with `nn.Module.load_state_dict(..., strict=False)` (`:143`) and logs unexpected keys at
   **`logger.debug`** (`:156`). A φ_x checkpoint with `m ≠ 72` fails loudly (PyTorch raises on size
   mismatch even under `strict=False`) — but a same-width lift (`m == 72`) would **load silently with
   φ_x dropped**, and the student would then distill against a teacher running the wrong forward pass.
   Same failure class as `38d979e`.
2. **`FrozenTeacher.actor_forward`** (`:186-194`) concatenates `obs_normed(72)` with `latent(9)`. Both
   student losses call it (`runner.py:302, :321`), so a φ_x teacher breaks distillation outright until
   the student path is taught to apply φ_x too — which is itself a design question the doc never
   raises (does the *student* see φ_x(o_t) or raw o_t? `StudentEncoderGRU` is sized
   `policy_obs_dim + extra`, `models.py:126`).
3. **Deploy export** (`deploy/specs/teacher_actor.py:26-42`) asserts
   `actor.0.weight == (256, obs_dim + latent_dim)` as a hard contract; a φ_x actor is an
   `ExportContractError`, and φ_x's own weights have no export spec at all.

Given the stated research focus (sim-to-real gap reduction), an arm that can be trained but neither
distilled nor exported is a screening result with no path to the thesis contribution. That is the
right thing to know **before** launching, not after. The doc should carry it as a staged cost, not a
parenthetical.

---

## THEO-9 (minor→major) — §8.4.1 rule-scope argument contradicts §4.4 of the same document, and uses a scoping axis the codebase does not use

§4.4 item 4(i) says the learned-lift aux objective *"is an auxiliary representation loss — the exact
family the project's settled rule bans after the reconstruction failure."* §8.4.1 reverses this:
*"a separate obs-side lifting module phi_x with its own rec+prediction losses is a NEW module, not
covered by the rule's letter."* Nothing about **the rule** changed between the two sections — only the
literature evidence about whether the method works. Changing the *verdict on efficacy* is legitimate;
silently changing the *reading of the rule* to match is not.

Separately, the codebase already has a precedent for scoping this rule, and it uses a **different
axis**. The omx wiki page on the closest prior idea states: *"Rule 03 (No-Encoder-Auxiliary-Losses):
this is an INPUT change, not an aux loss -- allowed. Do NOT pair it with a
reconstruction/contrastive loss (that path failed)"* (quoted verbatim in `albc_report.md` §6, from
`experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md`). The established test is
**input-change vs aux-loss**, not new-module vs old-module. Under the codebase's own axis, φ_x with
reconstruction + prediction losses lands on the banned side. The doc picks the axis that yields the
permissive answer without noting that a different axis is already in use.

To be fair: §8.4.1 does explicitly say *"flag it to the user"*, and the collapse-mechanism argument
(expansive m > n makes reconstruction easy) is a real distinction from the failed compressive-decoder
path. This is an honesty-of-framing objection, not a claim that the arm must be forbidden. But the
user should be shown both readings, and told that §4.4 already gave the opposite one.

---

## THEO-10 (minor) — a φ_x module will silently corrupt the encoder-health diagnostics

`ConstraintTRPO.__init__` identifies the encoder slice by `name.startswith("encoder")` and assumes
those parameters are **contiguous** in the flat vector (`:179-184`), then slices
`step_dir[offset : offset+count]` for `Grad/enc_step` and computes "actor step" as *everything else*:
`torch.cat([step_dir[sig_e:s], step_dir[e:]])` (`:577-580`). These feed
`Policy/encoder_grad_norm`, `Grad/enc_step`, `Grad/actor_step`
(`constraint_encoder_runner.py:348, 352-353`) — the exact metrics used to diagnose encoder health.

Consequences of inserting φ_x: (i) any name starting with `encoder` (e.g. `encoder_lift`, or a φ_u
called `encoder_u`) is folded into the encoder slice and **breaks contiguity**, producing a garbage
`enc_step` norm; (ii) even with a non-colliding name, φ_x parameters are silently counted as
*actor* step norm. Neither fails loudly. Cheap fix: name the module `lift_*` and add an explicit
slice — but it needs to be in the proposal, since the campaign's diagnosis workflow depends on these
numbers.

---

## THEO-11 (minor) — §8.4.1 / §11.3 / §10-AxisB: the collapse-safety argument and the latent-budget guidance contradict each other

§8.4.1 rests collapse-safety on KIPPO's **expansive** autoencoder (`m > n`, "reconstruction is easy
and collapse-unlikely"). §11.3 then advises *"our 72D obs is partially pre-lifted (52D temporal), so
try smaller m first."* And §10 Axis B proposes lifting only the **20D dynamic block**. These give three
different values of `n` (72 / effective-rank-of-72 / 20) and push `m` in opposite directions: the
collapse-safety argument needs `m > n`, the budget advice needs `m` small. If Axis B's 20D block is
lifted to `m = 40–80`, that is expansive over 20 but the *reconstruction target is only the 20D block*,
so the argument survives — but the doc never states which `n` it means, and under §11.3's "smaller m"
on the full 72D obs it does not. One sentence fixing `n := dim(the block φ_x actually reconstructs)`
resolves it; as written the reader can pick a configuration the safety argument does not cover.

---

## Verdicts on the §15.4 shortlist

| # | Shortlist item | Verdict | What the doc glossed |
|---|---|---|---|
| 1 | KIPPO-style φ_x on o_t (+ block-partitioned targets, bilinear H, z-conditioned scaffold) | **needs-redesign** | THEO-1 (trust-region reassurance false; φ_x auto-joins `_policy_params`), THEO-4 (K/B/H crash `allow_unused=False`; storage cleared before the only runner hook), THEO-5 (K(z) leaks into the p_t encoder — no `detach` in the doc), THEO-6 (H sparsification undefined for a learned φ_x; 1.2 GB Kron if not minibatched), THEO-7 (φ_x rides 10 CG double-backprops on a 262k un-minibatched batch), THEO-8 (FrozenTeacher / actor_forward / deploy contract all block the downstream path) |
| 2 | K_sim vs K_real watertank spectral gap meter | **implementable-as-described** | Genuinely zero training-side risk; my only note is the doc's own caveat that `data/` is host-side. No code coupling. This is the one shortlist item that survives the systemfit lens intact. |
| 3 | Deployment-time online observer | **out of scope for this critique** (no code contact yet); note it inherits THEO-8's export-spec gap — a new observer channel needs an `ExportSpec`, same as obs4 did |
| — | §11.2 normalization plan | **needs-redesign** | THEO-2: not DR-derivable for o_t; breaks 6 consumers incl. the just-closed deploy parity; `EmpiricalNormalization(..., until=N)` already exists (`rsl_rl/networks/normalization.py:17`) and the drift is 1/k-annealing anyway |
| — | §9 cat 6 student Koopman-consistency (ranked #1 near-term) | **needs-redesign / re-frame** | THEO-3: K→I by the doc's own §4.2 argument; it is a smoothness prior, not a Koopman model. Attachment point and alignment do check out on GRU (`runner.py:308-325` + `collector.py:186-190`); TCN cannot support it; done-masking unmentioned though `dones_seq` is already plumbed |

## What the doc got right (verified, not conceded lightly)

- `student reuses the teacher's frozen EmpiricalNormalization **instance**` — true, and it is the
  same object, not a copy (`_core/student/runner.py:106`, mirrored in
  `analysis/student_policy.py:102`).
- Encoder input is `p_t` only; `z` bypasses the actor normalizer and is kept raw
  (`actor_critic_encoder.py:209-220, 249-259`).
- `Isaac-ConstrainedALBC-NoEncoder-v0` exists and is the right control (`envs/main/__init__.py`,
  `agents/rsl_rl_ppo_cfg.py:307-349`).
- "Fresh track, no checkpoint reuse" for the **teacher training** path — all four dim-consistency
  checks are keyed on the env's obs width, which φ_x does not change. Correct as far as it goes
  (see THEO-8 for how far that is).
- §10's clarification that action history inside `o_t` is not the survey's joint-lifting hazard is
  consistent with the code: control latency and ESC filter state are both in the plant
  (`mdp/observations.py:63-64` ESC state in proprio; latency in `p_t[24]`), so past inputs really are
  part of the delay-system state.
