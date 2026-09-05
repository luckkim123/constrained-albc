# Option C is byte-identical to the default scoring: the saturation claim is proven and the section-5 thrust band is untestable by this route

- id: finding/355 · date: 2026-09-05 · author: claude-opus5-mac
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: measured · keywords: albc, phase4, option-c, pairDR, doraemon, thrust-band, fault-delay
- summary: The --no-doraemon-dr re-scoring reproduced the default matrix byte for byte (three md5 matches, all 24 rows identical) while the eval logs show the two runs genuinely taking different DR branches. That proves the DORAEMON-clipped box IS the static hard box. It also means option C did not achieve its purpose: no thrust dim is recorded among the 23 dr_ keys and the section-5 band has never reached any Phase 4 exam on either branch, which --deterministic-dr would not fix. Two reading consequences: pairDR covers recorded dims only, and the shared band rests on the identical runner override rather than on measurement. Separately, fault and delay were never scored together despite the robot having both.

# Option C is byte-identical to the default scoring, which proves the saturation claim and retires the section-5 band as a testable quantity

The operator ruled on 2026-09-04 22:4x that the Phase 4 CORE matrix be re-scored with
`--no-doraemon-dr`, so both arms would sit on the static hard `DomainRandomizationCfg` and the
section-5 thrust band (0.5, 2.0) would finally apply. That run finished 2026-09-05 06:56
(`.hq/work/p4c`, 8 evals, ~8 min each — faster than p4's 9m41s because it skips the DORAEMON
load). Here is what it returned.

## The two runs took different branches and produced the same bytes

| file | `.hq/work/p4` | `.hq/work/p4c` |
|:--|:--|:--|
| candidate `healthy/data_hard.npz` | `00c782e493fb370f95ec4dc0387f3317` | **same** |
| candidate `pair34/data_hard.npz` | `80065dc144126a68c328044e5d0f7f83` | **same** |
| reference `healthy/data_hard.npz` | `72f4242f0f1937d9cc5effc0ae53fa36` | **same** |

All 24 scorer rows match digit for digit. And this is **not** the flag failing to take effect —
the eval logs show the branches diverging exactly where they should:

- `p4`: `[INFO] Attempting to load DORAEMON-learned DR from: …trpo_p3b_lb200_s30_r2050_260904_163518`,
  then `payload_mass_range mean=1.6160 std=0.8371 -> [0.0000, 3.0000]` and the rest.
- `p4c`: `[INFO] DORAEMON-DR disabled. Hard DR = static DomainRandomizationCfg.`

**So the DORAEMON-learned box, after clipping, *is* the static hard box — bit for bit.**
`finding/321` inferred that from printed ranges agreeing to four decimals; this proves it over
the full trajectory data, through the opposite code path. It is the strongest form the claim
can take.

## The cost: option C's stated purpose was not achieved and cannot be by this route

The band was supposed to apply once DORAEMON was out of the way. It did not — the numbers are
unchanged. Two measurements say why:

1. **No `thrust` dim is recorded at all.** `data_hard.npz` carries 23 `dr_*` keys
   (`added_mass_0-5`, `body_mass`, `cob_x/y/z`, `cog_x/y/z`, `lin_damp_0-5`,
   `payload_cog_x/y/z`, `payload_mass`) and not one contains `thrust`. Neither eval log prints
   a thrust line.
2. **`debugging/319` already showed the same thing from the other side** — adding the band to
   the incumbent arm produced an `inc13w` byte-identical to `inc13`.

`--deterministic-dr` will not fix this either: the band is not being *drawn differently*, it is
not reaching the eval at all. **The section-5 thrust band has never been exercised by any
Phase 4 exam, on either branch.** If the designed plant is to be tested, that needs a different
mechanism, not a different flag.

## Two consequences for how `pairDR` should be read

**`pairDR` covers the recorded dims only.** `p4_score.py`'s `pairing(a, b)` computes
`max|dr_* difference|` over exactly those 23 keys. A discrepancy in an unrecorded dimension
would not raise it. So `pairDR = 0` means "the two arms agree on the 23 dims the eval writes
down", not "the two arms saw the same plant in every respect".

**The shared thrust band rests on construction, not measurement.** `p4_runner.sh` passes the
identical `DELTA` override to both arms, so they have the same band by how the runner was
written. That is a sound argument, but it is an argument, and the distinction matters when the
next reader asks what `pairDR = 0` licensed.

## A separate gap the same check surfaced

**Fault and delay were never scored together.** The deployed robot has both — m3 dead with m4
excluded, and observations 1.2 to 4.7 control steps stale — but no config combines them:
`pair34` is the fault at zero delay, `healthy_d1`/`healthy_d2` are the delay with all six
thrusters healthy, and no `pair34_d*` directory exists in either matrix. Every claim about
"the real robot's condition" in the Phase 4 reporting is an argument joining two separately
measured axes.

## Verdict on the queued run

Option C was queued as the repair for a broken comparison and is retired as a **confirmation**:
it changed nothing because there was nothing left to change, and the way it changed nothing is
itself the proof. The 78 minutes bought a stronger claim than the one it was meant to rescue.
Full analysis in `experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md`.
## Comments
