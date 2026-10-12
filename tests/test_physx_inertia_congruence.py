"""G5 congruence check: I' = S^(1/2) I S^(1/2) is what randomize_physx_inertia applies.

Pure torch, no Kit -- this checks the MATH only. The wiring (that set_inertias actually
moves PhysX's rigid-body inertia for this articulation) needs a live env and is NOT
covered here; run it on an idle GPU before trusting the feature.

Run:  python3 test_physx_inertia_congruence.py
"""
import torch

def congruence(default_flat: torch.Tensor, scales: torch.Tensor) -> torch.Tensor:
    """Mirror of randomize_physx_inertia's core, on (N, 9) x (N, 3) -> (N, 9)."""
    root = scales.clamp_min(1e-9).sqrt()
    c = root.unsqueeze(-1) * root.unsqueeze(-2)
    return (default_flat.view(-1, 3, 3) * c).reshape(-1, 9)


def _sym_pd(n, gen):
    """n random symmetric positive-definite 3x3 tensors with real off-diagonal products."""
    a = torch.rand(n, 3, 3, generator=gen) - 0.5
    return a @ a.transpose(-1, -2) + 3.0 * torch.eye(3).expand(n, 3, 3)


g = torch.Generator().manual_seed(0)
N = 64
I0 = _sym_pd(N, g)
flat = I0.reshape(N, 9)

# 1. scale 1.0 is a bit-identical no-op -- the incumbent must not move when DR is off.
out = congruence(flat, torch.ones(N, 3))
assert torch.equal(out, flat), "scales=1 changed the tensor; incumbent is not bit-identical"

# 2. the diagonal scales by exactly s_i, which is what `inertia_scale` means.
s = 0.4 + 1.6 * torch.rand(N, 3, generator=g)          # the configured (0.4, 2.0) band
out = congruence(flat, s).view(N, 3, 3)
diag_got = torch.diagonal(out, dim1=-2, dim2=-1)
diag_want = torch.diagonal(I0, dim1=-2, dim2=-1) * s
assert torch.allclose(diag_got, diag_want, rtol=1e-6, atol=1e-8), "diagonal is not I_ii * s_i"

# 3. symmetry survives -- PhysX rejects a non-symmetric inertia tensor.
assert torch.allclose(out, out.transpose(-1, -2), atol=1e-7), "result is not symmetric"

# 4. positive-definiteness survives. This is why the congruence is used instead of
#    scaling the three diagonal entries in place, which can drive a tensor indefinite.
assert (torch.linalg.eigvalsh(out) > 0).all(), "result is not positive definite"

# 5. Why the congruence rather than "just multiply the three diagonal entries".
#    Corrected 2026-09-07: the first version of this check asserted the naive form always
#    breaks positive-definiteness. It does not -- on the diagonally-dominant fixture above
#    it stays PD, and this test caught that overclaim. The true statement is weaker and is
#    what the code comment should say: diagonal-only scaling preserves the diagonal but is
#    NOT guaranteed to preserve PD, while the congruence is. One concrete counter-example
#    is enough to justify the choice; tuning the fixture until the stronger claim passed
#    would be fitting the test to the rhetoric.
ill = torch.tensor([[[1.0, 0.99, 0.0], [0.99, 1.0, 0.0], [0.0, 0.0, 1.0]]])   # thin body
s_bad = torch.tensor([[0.4, 2.0, 1.0]])                                       # inside (0.4, 2.0)

naive = ill.clone()
naive[:, torch.arange(3), torch.arange(3)] *= s_bad
assert not (torch.linalg.eigvalsh(naive) > 0).all(), \
    "the counter-example no longer demonstrates the failure; re-derive it"

cong = congruence(ill.reshape(1, 9), s_bad).view(1, 3, 3)
assert (torch.linalg.eigvalsh(cong) > 0).all(), "congruence lost PD on the counter-example"
assert torch.allclose(torch.diagonal(cong, dim1=-2, dim2=-1),
                      torch.diagonal(ill, dim1=-2, dim2=-1) * s_bad, rtol=1e-6), \
    "congruence did not scale the counter-example's diagonal by s_i"

print("PASS  congruence: no-op at 1.0, diagonal exact, symmetric, PD;")
print("      and on an ill-conditioned tensor where diagonal-only scaling goes indefinite,")
print("      the congruence stays PD with the same diagonal.")
