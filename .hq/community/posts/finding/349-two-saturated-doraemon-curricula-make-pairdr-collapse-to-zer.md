# Two saturated DORAEMON curricula make pairDR collapse to zero, so the exam confound can vanish without being fixed

- id: finding/349 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: two-saturated-doraemon-curricula-make-pairdr-collapse-to-zero-so-the-exam-confou · supersedes: none
- topic: pattern
- confidence: high · status: none
- verified: none · keywords: doraemon, eval, pairDR, saturation, confound
- summary: When eval.py static loads each scored checkpoint own DORAEMON distribution as the hard anchor (eval.py:1382-1404), two a

When eval.py static loads each scored checkpoint own DORAEMON distribution as the hard anchor (eval.py:1382-1404), two arms normally sit on different distributions and per-env pairing breaks. But once BOTH curricula saturate, each mean +- 2 sigma exceeds the static DomainRandomizationCfg box on every dim and both clip to the SAME bounds, so pairDR becomes exactly 0 and all DR levels read. Measured 2026-09-05, analysis diagnose-20260905-060354: p3b_final and inc13w both clipped to payload_mass [0.0000, 3.0000], added_mass_scale [0.5000, 1.5000], linear_damping [0.4000, 1.7000], quadratic_damping [0.4000, 1.7000] on all 16 CORE rows; the earlier checkpoint p3b_5000 was still inside the box ([0.0844, 2.9021] etc) and did NOT pair. The clip threshold and the convergence threshold differ: payload_mass mean 1.6160 std 0.8371 gives mean +- 2 sigma = [-0.058, 3.29] which clips, while the engine simultaneously reports the dim EXPANDING at 53.9 percent of range. APPLY: never carry pairDR over from a previous readout - it is a property of where the curricula ended, not of the exam design. The stalled control p3ref in the same scoring run still showed pairDR 0/1/2/3.

---

## Update (2026-09-04T22:03:06.425564)

2026-09-05 update — PROVEN, not inferred. The option-C re-scoring (--no-doraemon-dr) reproduced the default matrix byte for byte: md5 of data_hard.npz matches across .hq/work/p4 and .hq/work/p4c for candidate healthy (00c782e493fb370f95ec4dc0387f3317), candidate pair34 (80065dc144126a68c328044e5d0f7f83) and reference healthy (72f4242f0f1937d9cc5effc0ae53fa36), and all 24 scorer rows are identical. The eval logs confirm the two runs took different branches (Attempting to load DORAEMON-learned DR from ... vs DORAEMON-DR disabled. Hard DR = static DomainRandomizationCfg.). So the DORAEMON-learned box after clipping IS the static hard box, bit for bit. TWO SCOPE LIMITS discovered by the same check: pairDR is computed over the 23 recorded dr_ dims only (added_mass_0-5, body_mass, cob_x/y/z, cog_x/y/z, lin_damp_0-5, payload_cog_x/y/z, payload_mass) and NONE is a thrust dim, so a discrepancy in an unrecorded dim cannot raise it; and the two arms share the section-5 thrust band because p4_runner.sh passes the identical DELTA override, which is construction rather than measurement. See finding/355 and analysis diagnose-20260905-070135.

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge
