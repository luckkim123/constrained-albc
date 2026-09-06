#!/usr/bin/env python3
"""N-arm comparison figure + table from existing eval summary.json files.

Sibling of tools/paper_figures.py: that module has one hardcoded subcommand per
paper figure, each with its own baked-in arm set. This one takes the arm set as
data (a manifest) so a comparison can grow an arm without a code change --
which is the whole point of a baseline-comparison line.

Reuses paper_figures' RA-L rcParams, provenance manifest, CSV and LaTeX writers
verbatim rather than restating them.

    /isaac-sim/python.sh tools/compare_arms.py --manifest arms.json --out-dir OUT
    python3 tools/compare_arms.py --check          # no Isaac needed

Manifest (paths relative to repo root, or absolute):

    {
      "caption": "...", "label": "table:...",
      "axis": "att_norm", "field": "ss_error",
      "levels": ["none", "soft", "medium", "hard"],
      "arms": [{"name": "full_method", "label": "Full method",
                "summary": "logs/.../summary.json"}]
    }

`axis`/`field`/`levels` are optional and default as shown.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.getcwd()
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
# _analyze lives under the analysis package; paper_figures adds this too, but our
# imports of it are lazy so the path has to be here for the --common-set path.
_ANALYSIS_DIR = os.path.join(REPO_ROOT, "constrained_albc", "analysis")
if _ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, _ANALYSIS_DIR)

DEFAULT_LEVELS = ["none", "soft", "medium", "hard"]
DEFAULT_AXIS = "att_norm"
DEFAULT_FIELD = "ss_error"

# Plant fields that `--doraemon-dr-from` / `--env-dr-anchor` change but that the
# eval npz does NOT sample-log today, so check_anchor cannot see a difference
# confined to them (finding/396). Listed rather than assumed absent: the moment a
# later eval.py writes either one, the gate compares it like any dr_ field.
_PLANT_SCALARS = ("thrust_coefficient_scale", "control_delay_steps")

# Distinct enough to survive greyscale printing; extended past paper_figures'
# 4-colour ARM_COLORS because a baseline comparison runs more arms than an
# ablation does.
_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
    "#CCB974", "#64B5CD",
]


def _rel(path: str) -> str:
    """Resolve a manifest path against the repo root, leaving absolutes alone."""
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def collect(manifest: dict) -> tuple[list[dict], list[str], str, str]:
    """Read every arm's summary.json into rows of per-level values.

    Returns (rows, levels, axis, field). A level an arm never evaluated comes
    back as None rather than raising: an arm that skipped a tier should show a
    gap in the figure, not sink the whole run.
    """
    levels = manifest.get("levels") or DEFAULT_LEVELS
    axis = manifest.get("axis") or DEFAULT_AXIS
    field = manifest.get("field") or DEFAULT_FIELD
    std_field = f"{field}_std"

    from paper_figures import _load_summary, _val

    rows = []
    for arm in manifest["arms"]:
        summary_path = _rel(arm["summary"])
        summary = _load_summary(summary_path)
        surv = []
        for lvl in levels:
            s = summary.get(lvl, {}).get("survival_pct")
            surv.append(s.get("value") if isinstance(s, dict) else s)
        rows.append({
            "name": arm["name"],
            "label": arm.get("label", arm["name"]),
            "summary_path": summary_path,
            "values": [_val(summary, lvl, axis, field) for lvl in levels],
            "stds": [_val(summary, lvl, axis, std_field) for lvl in levels],
            "survival": surv,
        })
    return rows, levels, axis, field


def collect_common_set(manifest: dict, stat: str = "mean") -> tuple[list[dict], list[str], str, str, dict]:
    """Same rows as collect(), but every level restricted to the environments
    that EVERY arm completed.

    This exists because summary.json cannot answer the question. Its ss_error is
    each arm's own average over its own surviving environments, so an arm that
    holds a hard draw for 54 s before capsizing is charged for 54 s of its own
    pre-capsize excursion while an arm that capsizes at 4.9 s is not -- the
    late-failing arm takes the penalty. Measured on the 5000-iteration ablation
    at the hard tier: reading summary.json verbatim ranks the full method (1.656)
    BELOW no-encoder (1.172) and PPO (1.515); restricted to the 62 environments
    all arms complete, the full method is 0.953. The ranking inverts.

    Only att_norm is supported: it is the one axis _compute_enhanced_metrics
    exposes a per-env vector for, and it is the manuscript's primary metric.

    Verified 2026-09-06 against the manuscript's own stated pair for the full
    method at hard: 1.6565 unrestricted (== summary.json) and 0.9532 restricted
    (manuscript: 0.953).
    """
    levels = manifest.get("levels") or DEFAULT_LEVELS
    axis = manifest.get("axis") or DEFAULT_AXIS
    field = manifest.get("field") or DEFAULT_FIELD
    if axis != "att_norm" or field != "ss_error":
        raise SystemExit(
            f"--common-set supports only axis=att_norm field=ss_error "
            f"(got {axis}/{field}); the per-env vector exists for no other axis."
        )

    import numpy as np
    from _analyze.recompute_metrics import _compute_enhanced_metrics

    per_arm: dict[str, dict[str, tuple]] = {}
    for arm in manifest["arms"]:
        eval_dir = os.path.dirname(_rel(arm["summary"]))
        per_level = {}
        for lvl in levels:
            npz = os.path.join(eval_dir, f"data_{lvl}.npz")
            if not os.path.isfile(npz):
                continue
            out = _compute_enhanced_metrics(npz, with_per_env=True)
            pe = np.asarray(out["per_env"]["att_norm"], dtype=float)
            # Same completion criterion _compute_enhanced_metrics uses for
            # survival_pct -- terminated at the FINAL step, not terminated ever.
            term = np.load(npz, allow_pickle=True)["terminated"]
            per_level[lvl] = (pe, ~term[-1])
        per_arm[arm["name"]] = per_level

    common: dict[str, "np.ndarray"] = {}
    for lvl in levels:
        masks = [pl[lvl][1] for pl in per_arm.values() if lvl in pl]
        if masks:
            common[lvl] = np.logical_and.reduce(masks)

    rows = []
    for arm in manifest["arms"]:
        pl = per_arm[arm["name"]]
        values, stds = [], []
        for lvl in levels:
            if lvl not in pl or lvl not in common:
                values.append(None)
                stds.append(None)
                continue
            pe = pl[lvl][0][common[lvl]]
            reduce = {"mean": np.nanmean, "median": np.nanmedian,
                      "p90": lambda a: np.nanpercentile(a, 90)}[stat]
            values.append(float(reduce(pe)) if np.isfinite(pe).any() else None)
            # A standard deviation is the dispersion around the MEAN. Pairing it
            # with a median or a P90 draws an error bar that is not the spread of
            # the plotted statistic, so leave it off and let build_figure fall
            # back to plain markers.
            stds.append(float(np.nanstd(pe))
                        if stat == "mean" and np.isfinite(pe).any() else None)
        rows.append({
            "name": arm["name"],
            "label": arm.get("label", arm["name"]),
            "summary_path": _rel(arm["summary"]),
            "values": values,
            "stds": stds,
            "survival": [
                (float(pl[lvl][1].sum()) / len(pl[lvl][1]) * 100.0) if lvl in pl else None
                for lvl in levels
            ],
        })

    # How many arms actually constrained each mask. An arm with no data_<lvl>.npz
    # silently sits the intersection out, so "common to all arms" is only true
    # when this equals the arm count -- say which, rather than claim the stronger
    # thing unconditionally.
    n_arms = len(manifest["arms"])
    sizes = {lvl: (int(m.sum()), int(m.size), sorted(map(int, (~m).nonzero()[0])),
                   sum(1 for pl in per_arm.values() if lvl in pl), n_arms)
             for lvl, m in common.items()}
    return rows, levels, axis, field, sizes


def check_anchor(manifest: dict, levels: list[str]) -> dict:
    """Verify every arm sat the SAME exam, by comparing the sampled DR values.

    decision/392 makes anchor identity the table-admission rule: only arms
    sharing one `--doraemon-dr-from` anchor may appear in one table. Reading
    that claim off RUN_CONDITIONS.txt is not enough -- the TDC and PID eval
    dirs carry no RUN_CONDITIONS.txt at all (measured 2026-09-06), so a
    text-file gate would either pass them vacuously or reject a run that is
    in fact fine. The npz carries the DR values actually sampled, so compare
    those: same anchor + same seed + same env count => identical draws.

    Two things this compares that a cheaper version would not, both because a
    cheaper version was measured to fail on 2026-09-06:

    - ELEMENTWISE, not (min, max, mean). Those three moments are invariant
      under a PERMUTATION of the same draws, and both collect_common_set and
      build_paired_figure pair arms BY ENVIRONMENT INDEX. A permuted draw
      would clear a moment gate and then silently mis-pair every environment.
    - `vacuous` when fewer than two arms carried a data_<level>.npz, or when
      the npz has no dr_ fields at all. Without it the gate reported ok for a
      level no arm had, and main() wrote "the arms sat the same exam" into the
      figure's provenance having read zero files.

    KNOWN BLIND SPOT (finding/396, peer session, 2026-09-07). This gate reasons
    forward -- same anchor => identical draws -- but USES the converse: identical
    draws => same anchor. The converse is false for any plant field the npz does
    not sample-log, and `--env-dr-anchor` changes exactly two such fields:
    `thrust_coefficient_scale` and `control_delay_steps`. Measured on one student
    checkpoint, the anchored and unanchored exams were bit-identical across all 23
    dr_ arrays while the hard-tier error moved by up to 1.03 deg. So this check
    can only certify the axes the npz carries, and it now says so in its own
    caveat rather than claiming "the arms sat the same exam" outright. It picks
    up the two scalars automatically if a later eval.py starts logging them.

    Returns {level: {"ok": bool, "vacuous": bool, "n_fields": int,
                     "n_compared": int, "differing": [...], "missing": [...],
                     "blind_to": [...]}}.
    `ok` means VERIFIED ON THE LOGGED AXES, and is False when the check was vacuous.
    """
    import numpy as np

    verdict = {}
    for lvl in levels:
        ref_name = ref_keys = ref_arrays = None
        differing, missing, compared, blind = [], [], [], set(_PLANT_SCALARS)
        for arm in manifest["arms"]:
            npz = os.path.join(os.path.dirname(_rel(arm["summary"])), f"data_{lvl}.npz")
            if not os.path.isfile(npz):
                missing.append(arm["name"])
                continue
            d = np.load(npz, allow_pickle=True)
            keys = sorted([k for k in d.files if k.startswith("dr_")]
                          + [k for k in _PLANT_SCALARS if k in d.files])
            blind -= set(d.files)
            arrays = {k: np.asarray(d[k]) for k in keys}
            compared.append(arm["name"])
            if ref_arrays is None:
                ref_name, ref_keys, ref_arrays = arm["name"], keys, arrays
                continue
            if keys != ref_keys:
                differing.append(f"{arm['name']}:FIELDSET")
                continue
            bad = [k for k in keys if not np.array_equal(ref_arrays[k], arrays[k])]
            if bad:
                differing.append(f"{arm['name']}:{','.join(bad[:4])}")
        n_fields = len(ref_keys or [])
        vacuous = len(compared) < 2 or n_fields == 0
        verdict[lvl] = {"ok": (not differing) and not vacuous,
                        "vacuous": vacuous, "reference": ref_name,
                        "n_fields": n_fields, "n_compared": len(compared),
                        # The NAMES, not just the count: main() has to check that
                        # every arm contributing a NUMBER to the table was one of
                        # the arms actually compared. Two matching arms plus a
                        # third with no npz used to read as a clean pass over a
                        # three-row table.
                        "compared": compared,
                        "differing": differing, "missing": missing,
                        "blind_to": sorted(blind) if compared else sorted(_PLANT_SCALARS)}
    return verdict


def _anchor_refusal(lvl: str, v: dict) -> str:
    """Why the anchor gate is stopping this run. The two reasons are different
    failures and must not print the same sentence: one says the arms are known
    to differ, the other says nothing was checked at all."""
    if v["vacuous"]:
        return (
            "ANCHOR NOT VERIFIED at %s: only %d arm(s) carried a data_%s.npz "
            "(%d dr_ fields). Nothing was compared, so no same-exam claim is "
            "supported -- this is not a pass.\n"
            "Evaluate the arms at this tier, or pass --allow-mixed-anchor to "
            "publish anyway (the manifest will record that it was unverified)."
            % (lvl, v["n_compared"], lvl, v["n_fields"])
        )
    return (
        "ANCHOR MISMATCH at %s: %s -- arms did not sit the same exam, and "
        "decision/392 forbids putting them in one table.\n"
        "Re-evaluate the odd arms against one --doraemon-dr-from, or pass "
        "--allow-mixed-anchor to override (the manifest will say so)."
        % (lvl, v["differing"])
    )


def _anchor_caveat(anchor: dict) -> str:
    """One sentence describing what the anchor gate actually established.

    Three states, because collapsing them is how a figure ends up carrying
    "the arms sat the same exam" on the strength of zero files read.
    """
    ok = {lvl: v for lvl, v in anchor.items() if v["ok"]}
    vac = {lvl: v for lvl, v in anchor.items() if v["vacuous"]}
    mism = {lvl: v for lvl, v in anchor.items() if not v["ok"] and not v["vacuous"]}
    parts = []
    if ok:
        parts.append(
            "Anchor VERIFIED at " + ", ".join(
                "%s (%d dr_ fields elementwise-identical across %d arms)"
                % (lvl, v["n_fields"], v["n_compared"]) for lvl, v in ok.items()))
    if vac:
        parts.append(
            "Anchor NOT VERIFIED at " + ", ".join(
                "%s (only %d arm(s) had data; nothing compared)"
                % (lvl, v["n_compared"]) for lvl, v in vac.items()))
    if mism:
        parts.append(
            "Anchor MISMATCH at " + ", ".join(
                "%s (%s)" % (lvl, v["differing"]) for lvl, v in mism.items())
            + " -- cross-arm differences there are confounded by the plant")
    # What "VERIFIED" does not cover. Without this the sentence above reads as a
    # same-exam guarantee, which it is not: an anchor difference confined to a
    # field the npz never sampled is invisible here (finding/396).
    #
    # Reported PER TIER. A union over every tier would attach one tier's blindness
    # to another tier that did log the field -- a false qualifier is as wrong as a
    # missing one, and this sentence goes into the paper.
    blind_by_tier = {lvl: v["blind_to"] for lvl, v in ok.items() if v.get("blind_to")}
    if blind_by_tier:
        parts.append(
            "Verified ONLY over the sample-logged DR axes at " + ", ".join(
                "%s (%s not recorded in the npz)" % (lvl, ", ".join(b))
                for lvl, b in blind_by_tier.items())
            + " -- an anchor difference confined to those fields would not be "
              "detected there (finding/396)")
    return "; ".join(parts) + "."


def needs_log_scale(rows: list[dict], threshold: float = 20.0) -> bool:
    """True when the arms span enough orders that a linear axis hides the small ones.

    A classical-controller arm can sit 20-40x above the RL arms (PID/TDE-off
    measured 14.7-18.4 deg against a teacher's 0.51-0.81), which flattens every
    RL arm onto the x-axis on a linear scale.
    """
    vals = [v for r in rows for v in r["values"] if v is not None and v > 0]
    if len(vals) < 2:
        return False
    return (max(vals) / min(vals)) > threshold


def build_figure(rows: list[dict], levels: list[str], axis: str, field: str, logy: bool | None):
    import matplotlib.pyplot as plt
    from paper_figures import RAL_RC

    try:
        from _analyze.recompute_metrics import unit_for
        unit = unit_for(axis, field) or ""
    except Exception:
        unit = ""

    use_log = needs_log_scale(rows) if logy is None else logy
    with plt.rc_context(RAL_RC):
        fig, ax = plt.subplots()
        for i, r in enumerate(rows):
            colour = _PALETTE[i % len(_PALETTE)]
            xs = [j for j, v in enumerate(r["values"]) if v is not None]
            if not xs:
                continue
            ys = [r["values"][j] for j in xs]
            errs = [r["stds"][j] for j in xs]
            if all(e is not None for e in errs):
                ax.errorbar(xs, ys, yerr=errs, label=r["label"], color=colour,
                            marker="o", markersize=3, capsize=2, elinewidth=0.6)
            else:
                ax.plot(xs, ys, label=r["label"], color=colour, marker="o", markersize=3)
        ax.set_xticks(list(range(len(levels))))
        ax.set_xticklabels([lvl.capitalize() for lvl in levels])
        ax.set_xlabel("Domain-randomization tier")
        ax.set_ylabel(f"{axis} {field}" + (f" ({unit})" if unit else ""))
        if use_log:
            ax.set_yscale("log")
        ax.legend(frameon=False, ncol=2)
        ax.grid(True, which="both", axis="y", linewidth=0.3, alpha=0.4)
    return fig, use_log



def build_paired_figure(manifest: dict, levels: list[str], baseline: str, level: str):
    """Per-environment scatter of every arm against one baseline, at one tier.

    The aggregate table hides WHERE an arm's advantage comes from. This shows
    it per environment: points below the diagonal are environments the baseline
    handles better, above are ones it handles worse, and an environment nobody
    completes is drawn as an open marker on the axis edge so a reader can see
    that the common-set correction dropped it rather than that it scored zero.

    Hard-tier environments 43 and 45 are exactly the pair the two IPO-carrying
    arms lose; this is the figure that makes that visible instead of stated.

    Returns (fig, dropped) where `dropped` is PER ARM, not per baseline. An
    earlier version reported only the baseline's own failures, so running with
    --paired ppo (ppo completes 64/64 at hard) wrote "none dropped" into the
    provenance while silently dropping environments 43 and 45 from the two arms
    that do fail there. Measured 2026-09-06.
    """
    import numpy as np
    from paper_figures import RAL_RC
    import matplotlib.pyplot as plt

    from _analyze.recompute_metrics import _compute_enhanced_metrics

    per = {}
    for arm in manifest["arms"]:
        npz = os.path.join(os.path.dirname(_rel(arm["summary"])), f"data_{level}.npz")
        if not os.path.isfile(npz):
            continue
        out = _compute_enhanced_metrics(npz, with_per_env=True)
        pe = np.asarray(out["per_env"]["att_norm"], dtype=float)
        term = np.load(npz, allow_pickle=True)["terminated"]
        per[arm["name"]] = (pe, ~term[-1], arm.get("label", arm["name"]))

    if baseline not in per:
        raise SystemExit(f"baseline {baseline!r} not among arms: {sorted(per)}")
    bx, bdone, blabel = per[baseline]

    # Colour by position in the manifest, the same key build_figure enumerates,
    # so an arm keeps one colour across both figures of the same paper.
    order = {a["name"]: i for i, a in enumerate(manifest["arms"])}

    dropped: dict[str, list[int]] = {}
    with plt.rc_context(RAL_RC):
        fig, ax = plt.subplots(figsize=(3.45, 3.2))
        vals = [v for pe, done, _ in per.values() for v in pe[done] if np.isfinite(v) and v > 0]
        lo, hi = min(vals) * 0.7, max(vals) * 1.4
        ax.plot([lo, hi], [lo, hi], color="0.6", lw=0.8, zorder=0)
        for name, (pe, done, label) in ((k, v) for k, v in per.items() if k != baseline):
            both = done & bdone & np.isfinite(pe) & np.isfinite(bx)
            ax.scatter(bx[both], pe[both], s=9, alpha=0.75, linewidths=0,
                       color=_PALETTE[order.get(name, 0) % len(_PALETTE)], label=label)
            miss = sorted(int(j) for j in (~both).nonzero()[0])
            if miss:
                dropped[name] = miss
        union = sorted({j for miss in dropped.values() for j in miss})
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel(f"{blabel} steady-state error (deg)")
        ax.set_ylabel("Arm steady-state error (deg)")
        ax.set_title(f"{level} tier, per environment"
                     + (f" (env {', '.join(map(str, union))} dropped)" if union else ""),
                     fontsize=7)
        ax.legend(frameon=False, fontsize=5, loc="upper left")
        fig.tight_layout()
    # Measured, so the provenance can state the span instead of asserting it. The
    # axes are log-log unconditionally; the caveat used to claim "the arms span
    # more than an order of magnitude" whether or not they did.
    span = max(vals) / min(vals)
    return fig, dropped, span


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", help="arm manifest JSON")
    p.add_argument("--out-dir", help="output directory (created if absent)")
    p.add_argument("--stem", default="compare_arms", help="output file stem")
    p.add_argument("--logy", dest="logy", action="store_true", default=None,
                   help="force log y-axis (default: auto when the span exceeds 20x)")
    p.add_argument("--no-logy", dest="logy", action="store_false",
                   help="force linear y-axis")
    p.add_argument("--stat", choices=("mean", "median", "p90"), default="mean",
                   help="how to reduce the per-env vector under --common-set. "
                        "mean is what the manuscript reports; at hard it is a TAIL "
                        "statistic -- PPO's median beats the full method's while its "
                        "mean is 1.5x worse (finding/395)")
    p.add_argument("--paired", metavar="BASELINE_ARM",
                   help="per-environment scatter of every arm against BASELINE_ARM")
    p.add_argument("--paired-level", default="hard",
                   help="DR tier for --paired (default hard)")
    p.add_argument("--allow-mixed-anchor", action="store_true",
                   help="publish even though the arms sat different exams (recorded in the manifest)")
    p.add_argument("--common-set", action="store_true",
                   help="restrict every level to the environments EVERY arm completed, "
                        "recomputed from data_{level}.npz. Without this the numbers are "
                        "each arm's own average over its own survivors, which inverts the "
                        "hard-tier ranking (see collect_common_set).")
    p.add_argument("--check", action="store_true",
                   help="run the self-check on synthetic data and exit")
    args = p.parse_args()

    if args.check:
        _self_check()
        return
    if not args.manifest or not args.out_dir:
        p.error("--manifest and --out-dir are required unless --check is given")

    with open(args.manifest) as f:
        manifest = json.load(f)

    if args.paired:
        levels = manifest.get("levels") or DEFAULT_LEVELS
        anchor = check_anchor(manifest, [args.paired_level])
        v = anchor[args.paired_level]
        if not v["ok"] and not args.allow_mixed_anchor:
            raise SystemExit(_anchor_refusal(args.paired_level, v))
        os.makedirs(args.out_dir, exist_ok=True)
        from paper_figures import _savefig, _write_manifest
        fig, dropped, span = build_paired_figure(manifest, levels, args.paired, args.paired_level)
        outputs = _savefig(fig, args.out_dir, args.stem)
        _write_manifest(
            args.out_dir,
            [_rel(a["summary"]) for a in manifest["arms"]],
            outputs,
            caveats=[
                "Per-environment paired scatter against %s at the %s tier; the "
                "diagonal is parity. A point ABOVE the line is an environment "
                "where that arm is worse than the baseline." % (args.paired, args.paired_level),
                # Per arm, because the baseline is not always the worst completer:
                # a baseline that finishes every environment used to make this
                # read "none dropped" while other arms silently lost theirs.
                "Only environments BOTH that arm and the baseline completed are "
                "plotted; dropped per arm: %s."
                % ("; ".join("%s %s" % (k, v) for k, v in sorted(dropped.items()))
                   if dropped else "none for any arm"),
                "Log-log axes; the plotted values span %.1fx." % span,
                _anchor_caveat(anchor),
            ],
            extra={"generator": "tools/compare_arms.py --paired",
                   "baseline": args.paired, "level": args.paired_level,
                   "value_span": span,
                   "dropped_envs": dropped, "anchor_check": anchor,
                   "anchor_override": (not v["ok"]) and args.allow_mixed_anchor},
        )
        print("wrote %d outputs + manifest.json to %s" % (len(outputs), args.out_dir))
        return

    # Gate BEFORE computing. collect_common_set intersects per-environment masks
    # across arms, so two arms with different env counts raise an opaque numpy
    # broadcast error -- burying the very condition the anchor gate exists to
    # report clearly. The levels come from the manifest, so the gate needs nothing
    # that collect() produces.
    levels = manifest.get("levels") or DEFAULT_LEVELS
    anchor = check_anchor(manifest, levels)
    bad = {lvl: v for lvl, v in anchor.items() if not v["ok"]}
    if bad and not args.allow_mixed_anchor:
        for lvl, v in bad.items():
            print(_anchor_refusal(lvl, v), file=sys.stderr)
        raise SystemExit("anchor gate refused %d of %d tiers; nothing written."
                         % (len(bad), len(anchor)))

    sizes = None
    if args.common_set:
        rows, levels, axis, field, sizes = collect_common_set(manifest, args.stat)
    else:
        rows, levels, axis, field = collect(manifest)

    # An arm can carry a NUMBER at a tier (summary.json has it) while having no
    # data_<tier>.npz to anchor-check. The gate above passes on the arms it could
    # compare, and the table then publishes the unchecked arm beside them under a
    # caveat that says VERIFIED -- which is the thing decision/392 forbids.
    unverified = {}
    for i, lvl in enumerate(levels):
        checked = set(anchor.get(lvl, {}).get("compared", ()))
        rogue = [r["name"] for r in rows
                 if r["values"][i] is not None and r["name"] not in checked]
        if rogue:
            unverified[lvl] = rogue
    if unverified and not args.allow_mixed_anchor:
        for lvl, names in unverified.items():
            print("ANCHOR UNCHECKED at %s: %s contribute a value to the table but "
                  "carry no data_%s.npz, so their exam was never compared."
                  % (lvl, ", ".join(names), lvl), file=sys.stderr)
        raise SystemExit(
            "arms in the table were never anchor-checked; nothing written.\n"
            "Evaluate them at those tiers, or pass --allow-mixed-anchor (the "
            "manifest will record exactly which arms went unchecked).")
    os.makedirs(args.out_dir, exist_ok=True)

    from paper_figures import _savefig, _write_csv, _write_latex_table, _write_manifest

    fig, use_log = build_figure(rows, levels, axis, field, args.logy)
    outputs = _savefig(fig, args.out_dir, args.stem)

    header = ["Arm"] + [lvl.capitalize() for lvl in levels]
    table_rows = [
        [r["label"]] + [("--" if v is None else f"{v:.3f}") for v in r["values"]]
        for r in rows
    ]
    csv_path = os.path.join(args.out_dir, f"{args.stem}.csv")
    tex_path = os.path.join(args.out_dir, f"{args.stem}.tex")
    _write_csv(csv_path, header, table_rows)
    _write_latex_table(
        tex_path,
        manifest.get("caption", f"{axis} {field} by arm and DR tier"),
        manifest.get("label", "table:compare_arms"),
        header, table_rows,
    )
    outputs += [os.path.basename(csv_path), os.path.basename(tex_path)]

    # Every caveat below is a property of the inputs, not of this script -- they
    # travel with the figure so a reader never sees the numbers without them.
    if sizes is not None:
        provenance = [
            "Values are RECOMPUTED from data_{level}.npz over the environments completed by "
            "every arm MEASURED at that level (the per-level lines below say how many that "
            "was), via _compute_enhanced_metrics(with_per_env=True). They therefore "
            "differ from summary.json, which averages each arm over its own survivors and "
            "so penalises an arm for failing LATE.",
        ] + [
            f"{lvl}: {n}/{tot} environments completed by all {k} arms measured "
            f"at this tier" + (f" (of {tot_arms} in the table)" if k != tot_arms else "")
            + (f"; excluded {ex}" if ex else "")
            for lvl, (n, tot, ex, k, tot_arms) in sizes.items()
        ]
    else:
        provenance = [
            "Values are read verbatim from each arm's summary.json; nothing is recomputed here.",
            "NOT common-set corrected: each arm is averaged over its OWN surviving "
            "environments, which charges a late-failing arm for its pre-failure excursion. "
            "Re-run with --common-set for the cross-arm comparison.",
        ]
    unchecked_line = ([
        "ANCHOR OVERRIDE: %s appear in this table with a value but were never "
        "anchor-checked (no data_<tier>.npz), so their comparability to the rest "
        "is asserted, not measured."
        % "; ".join("%s at %s" % (", ".join(n), lvl) for lvl, n in unverified.items())
    ] if unverified else [])
    caveats = [_anchor_caveat(anchor)] + unchecked_line + provenance + [
        "Exams run before 2026-09-06 were graded on the DomainRandomizationCfg CLASS "
        "DEFAULT, not the run's own env cfg (finding/391). Arms remain comparable to "
        "each other; the graded plant is not the designed plant.",
        f"y-axis is {'logarithmic' if use_log else 'linear'}.",
    ]
    # Caveats that belong to THIS arm set rather than to the script -- e.g. a
    # mixed-training-budget set, or a known-stale anchor. The manifest describes
    # the inputs, so it is where an input-specific caveat has to live.
    caveats += list(manifest.get("caveats", []))
    _write_manifest(
        args.out_dir,
        source_files=[r["summary_path"] for r in rows],
        outputs=outputs,
        caveats=caveats,
        extra={"generator": "tools/compare_arms.py",
               "arms": [r["name"] for r in rows],
               "levels": levels, "axis": axis, "field": field,
               "log_y": use_log,
        # Name the field actually read. This used to say "ss_error" whatever the
        # manifest asked for, so a peak_rate table carried provenance claiming a
        # steady-state error was computed.
        "stat": args.stat if sizes is not None else "summary.json %s" % field,
        "anchor_check": anchor,
        "anchor_override": (bool(bad) or bool(unverified)) and args.allow_mixed_anchor,
        "anchor_unchecked_arms": unverified or None,
               "common_set": (
                   {lvl: {"n": n, "of": tot, "excluded_envs": ex,
                          "arms_measured": k, "arms_in_table": tot_arms}
                    for lvl, (n, tot, ex, k, tot_arms) in sizes.items()}
                   if sizes is not None else None),
               },
    )
    print(f"wrote {len(outputs)} outputs + manifest.json to {args.out_dir}")
    for r in rows:
        vals = ", ".join("--" if v is None else f"{v:.3f}" for v in r["values"])
        print(f"  {r['name']:<20} {vals}")


def _self_check() -> None:
    """Smallest thing that fails if level/axis picking or scale selection breaks."""
    tight = {"values": [0.5, 0.6, 0.7, 0.8]}
    assert needs_log_scale([tight]) is False, "single tight arm must stay linear"
    assert needs_log_scale([tight, {"values": [14.7, 15.9, 16.9, 18.4]}]) is True, \
        "a 20x+ span must switch to log"
    assert needs_log_scale([{"values": [None, None]}]) is False, "all-missing must not raise"
    assert needs_log_scale([{"values": [0.0, 0.0]}]) is False, "zeros must not divide"

    import tempfile
    summary = {lvl: {"att_norm": {"ss_error": v, "ss_error_std": 0.1},
                     "survival_pct": 100.0}
               for lvl, v in zip(DEFAULT_LEVELS, [0.5, 0.6, 0.7, 0.8])}
    summary["hard"]["att_norm"].pop("ss_error")          # a tier an arm never finished
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "summary.json")
        with open(path, "w") as f:
            json.dump(summary, f)
        rows, levels, axis, field = collect({"arms": [{"name": "a", "summary": path}]})
    assert (levels, axis, field) == (DEFAULT_LEVELS, DEFAULT_AXIS, DEFAULT_FIELD)
    assert rows[0]["values"] == [0.5, 0.6, 0.7, None], rows[0]["values"]
    assert rows[0]["stds"] == [0.1] * 4
    assert rows[0]["survival"] == [100.0] * 4
    assert rows[0]["label"] == "a", "label must fall back to name"

    # check_anchor decides whether a table may be published, so it gets its own
    # check. Both failures below were real: the moment signature passed a
    # permuted draw, and a tier no arm had reported a verified anchor.
    import numpy as np
    with tempfile.TemporaryDirectory() as d:
        def _arm(nm, vals):
            os.makedirs(os.path.join(d, nm), exist_ok=True)
            np.savez(os.path.join(d, nm, "data_x.npz"),
                     dr_a=np.asarray(vals, dtype=float),
                     terminated=np.zeros((3, len(vals)), dtype=bool))
            with open(os.path.join(d, nm, "summary.json"), "w") as fh:
                fh.write("{}")
            return {"name": nm, "summary": os.path.join(d, nm, "summary.json")}

        same = _arm("a", [1.0, 2.0, 3.0])
        dup = _arm("b", [1.0, 2.0, 3.0])
        perm = _arm("c", [3.0, 1.0, 2.0])     # identical min/max/mean, reordered
        diff = _arm("d", [1.0, 2.0, 9.0])

        v = check_anchor({"arms": [same, dup]}, ["x"])["x"]
        assert v["ok"] and not v["vacuous"] and v["n_compared"] == 2, v
        v = check_anchor({"arms": [same, perm]}, ["x"])["x"]
        assert not v["ok"], "a permuted draw shares min/max/mean and must NOT pass"
        v = check_anchor({"arms": [same, diff]}, ["x"])["x"]
        assert not v["ok"] and v["differing"], v
        v = check_anchor({"arms": [same, dup]}, ["nosuchtier"])["nosuchtier"]
        assert v["vacuous"] and not v["ok"], "a tier nobody has is not a verified anchor"
        assert len(v["missing"]) == 2, v
        v = check_anchor({"arms": [same]}, ["x"])["x"]
        assert v["vacuous"] and not v["ok"], "one arm is not a cross-arm verification"

        # The refusal text must name WHICH failure; conflating them is how an
        # unverified run reads as a mismatch and gets waved through.
        assert "NOT VERIFIED" in _anchor_refusal("x", {"vacuous": True, "n_compared": 1,
                                                       "n_fields": 0, "differing": []})
        assert "MISMATCH" in _anchor_refusal("x", {"vacuous": False, "n_compared": 2,
                                                   "n_fields": 3, "differing": ["b:dr_a"]})
        assert "NOT VERIFIED" in _anchor_caveat(
            {"x": {"ok": False, "vacuous": True, "n_compared": 1, "n_fields": 0,
                   "differing": []}})
        # A VERIFIED verdict must carry its blind spot with it, or the sentence
        # reads as a same-exam guarantee it cannot make (finding/396).
        v = check_anchor({"arms": [same, dup]}, ["x"])["x"]
        assert v["blind_to"] == sorted(_PLANT_SCALARS), v["blind_to"]
        assert v["compared"] == ["a", "b"], v["compared"]
        line = _anchor_caveat({"x": v})
        assert "VERIFIED" in line and "thrust_coefficient_scale" in line, line

        # The blind spot is per tier. A union would hang one tier's blindness on
        # another tier that did log the field -- a false qualifier in the paper.
        seeing = {"ok": True, "vacuous": False, "n_fields": 3, "n_compared": 2,
                  "differing": [], "blind_to": []}
        line = _anchor_caveat({"none": dict(v), "hard": dict(seeing)})
        assert "hard" not in line.split("Verified ONLY")[1], \
            "a tier that logged the scalars must not be tagged blind: " + line
    print("self-check OK")


if __name__ == "__main__":
    main()
