"""Pure-numpy forward pass of the albc student policy (board runtime).

Mirrors student_inference.py's torch modules exactly, but depends ONLY on numpy
so it runs on the Jetson TX2 (Python 3.5, numpy 1.11.0, no torch). Every op here
is checked against torch-produced golden vectors to atol=1e-5 (see test_npforward.py).

numpy-1.11.0 / Python 2.7 compatibility: uses np.dot (NOT @, which is py3.5+
only -- ROS lunar rospy runs the board node on py2.7), np.maximum/np.expm1/np.tanh,
np.abs, broadcasting, as_strided. No np.einsum-only paths, no newer kwargs.
"""
import numpy as np


# ---------------------------------------------------------------- primitives
def linear(x, w, b):
    """torch nn.Linear: y = x.dot(w.T) + b. w is (out, in), x is (..., in)."""
    return np.dot(x, w.T) + b


def elu(x, alpha=1.0):
    """torch ELU: x if x>0 else alpha*(exp(x)-1). expm1 for numerical parity."""
    return np.where(x > 0, x, alpha * np.expm1(x))


def softsign(x):
    """torch F.softsign: x / (1 + |x|)."""
    return x / (1.0 + np.abs(x))


def layer_norm(x, gamma, beta, eps=1e-5):
    """torch nn.LayerNorm over the last dim. Default eps=1e-5 (torch default).

    NOTE: keepdims= on ndarray.mean/.var is SILENTLY IGNORED on numpy < 1.12.0
    (the board has 1.11.0), so we reshape explicitly to keep the (..., 1) axis.
    """
    kept = x.shape[:-1] + (1,)
    mean = x.mean(axis=-1).reshape(kept)
    var = x.var(axis=-1).reshape(kept)   # population variance (torch uses biased)
    return (x - mean) / np.sqrt(var + eps) * gamma + beta


def conv1d(x, w, b, stride=1):
    """torch nn.Conv1d (cross-correlation, no kernel flip), no padding, dilation 1.

    x: (batch, in_ch, L)   w: (out_ch, in_ch, k)   b: (out_ch,)
    returns (batch, out_ch, L_out) with L_out = (L - k)//stride + 1
    """
    batch, in_ch, L = x.shape
    out_ch, in_ch_w, k = w.shape
    assert in_ch == in_ch_w, (in_ch, in_ch_w)
    L_out = (L - k) // stride + 1
    # explicit sliding-window sum-of-products (numpy 1.11 safe, clear over fast)
    y = np.zeros((batch, out_ch, L_out), dtype=x.dtype)
    for t in range(L_out):
        s = t * stride
        window = x[:, :, s:s + k]                     # (batch, in_ch, k)
        # (batch, in_ch, k) * (out_ch, in_ch, k) summed over in_ch,k -> (batch, out_ch)
        y[:, :, t] = np.tensordot(window, w, axes=([1, 2], [1, 2])) + b
    return y


def gru_cell(x_t, h, w_ih, w_hh, b_ih, b_hh):
    """One step of torch nn.GRU (single layer). Gate order in torch: [r, z, n].

    torch GRU equations (with hidden bias INSIDE the n-gate reset term):
        r = sigmoid(W_ir x + b_ir + W_hr h + b_hr)
        z = sigmoid(W_iz x + b_iz + W_hz h + b_hz)
        n = tanh(W_in x + b_in + r * (W_hn h + b_hn))
        h' = (1 - z) * n + z * h

    x_t: (batch, in)   h: (batch, hidden)
    w_ih: (3*hidden, in)   w_hh: (3*hidden, hidden)   b_ih/b_hh: (3*hidden,)
    """
    hidden = h.shape[-1]
    gi = np.dot(x_t, w_ih.T) + b_ih   # (batch, 3*hidden)
    gh = np.dot(h, w_hh.T) + b_hh     # (batch, 3*hidden)
    i_r, i_z, i_n = gi[:, :hidden], gi[:, hidden:2 * hidden], gi[:, 2 * hidden:]
    h_r, h_z, h_n = gh[:, :hidden], gh[:, hidden:2 * hidden], gh[:, 2 * hidden:]
    r = _sigmoid(i_r + h_r)
    z = _sigmoid(i_z + h_z)
    n = np.tanh(i_n + r * h_n)
    return (1.0 - z) * n + z * h


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# ---------------------------------------------------------------- modules
class TeacherActor:
    """obs_normalizer + actor MLP (78 -> 256 -> 128 -> 64 -> 8, ELU between).

    Normalization mirrors rsl_rl EmpiricalNormalization.forward EXACTLY:
        (x - mean) / (std + eps),  eps = 0.01
    The stored _std buffer is sqrt(var) WITHOUT eps folded in, so eps must be
    added at runtime. Verified 2026-06-11 against the live torch normalizer.forward
    (max|err|=0 for (x-mean)/(std+eps); eps-free /std mismatches by 8.12).
    """

    NORM_EPS = 0.01

    def __init__(self, w):
        self.mean = w["normalizer._mean"]   # (1, 69)
        self.std = w["normalizer._std"]     # (1, 69)  -- sqrt(var), eps NOT folded in
        self.layers = [
            (w["actor.0.weight"], w["actor.0.bias"]),
            (w["actor.2.weight"], w["actor.2.bias"]),
            (w["actor.4.weight"], w["actor.4.bias"]),
            (w["actor.6.weight"], w["actor.6.bias"]),
        ]

    def normalize(self, obs):
        return (obs - self.mean) / (self.std + self.NORM_EPS)

    def act(self, obs_normalized, latent):
        x = np.concatenate([obs_normalized, latent], axis=-1)  # (b, 78)
        for i, (wt, b) in enumerate(self.layers):
            x = linear(x, wt, b)
            if i < len(self.layers) - 1:   # ELU between, none after last
                x = elu(x)
        return x


class StudentTCN:
    """channel_transform -> 3x(Conv1d+ELU) -> head(Linear+ELU+LN+Linear) -> softsign."""

    def __init__(self, w):
        self.ct_w = w["channel_transform.0.weight"]   # (32, 69)
        self.ct_b = w["channel_transform.0.bias"]
        self.convs = [
            (w["conv.0.weight"], w["conv.0.bias"]),
            (w["conv.2.weight"], w["conv.2.bias"]),
            (w["conv.4.weight"], w["conv.4.bias"]),
        ]
        self.h0_w, self.h0_b = w["head.0.weight"], w["head.0.bias"]
        self.ln_g, self.ln_b = w["head.2.weight"], w["head.2.bias"]
        self.h3_w, self.h3_b = w["head.3.weight"], w["head.3.bias"]

    def forward(self, win):
        """win: (batch, H, 69) -> latent (batch, 9)."""
        b, h, d = win.shape
        x = elu(linear(win.reshape(b * h, d), self.ct_w, self.ct_b)).reshape(b, h, -1)
        x = np.transpose(x, (0, 2, 1))          # (b, 32, H)
        for cw, cb in self.convs:
            x = elu(conv1d(x, cw, cb, stride=1))
        x = x.reshape(b, -1)                    # flatten (b, 384)
        x = elu(linear(x, self.h0_w, self.h0_b))
        x = layer_norm(x, self.ln_g, self.ln_b)
        x = linear(x, self.h3_w, self.h3_b)
        return softsign(x)


class StudentGRU:
    """stateful GRU -> head(Linear+ELU+LN+Linear) -> softsign. Carry hidden across calls."""

    def __init__(self, w):
        self.w_ih = w["gru.weight_ih_l0"]   # (384, 69)
        self.w_hh = w["gru.weight_hh_l0"]   # (384, 128)
        self.b_ih = w["gru.bias_ih_l0"]
        self.b_hh = w["gru.bias_hh_l0"]
        self.h0_w, self.h0_b = w["head.0.weight"], w["head.0.bias"]
        self.ln_g, self.ln_b = w["head.2.weight"], w["head.2.bias"]
        self.h3_w, self.h3_b = w["head.3.weight"], w["head.3.bias"]
        self.hidden_size = self.w_hh.shape[1]

    def init_hidden(self, batch=1):
        return np.zeros((batch, self.hidden_size), dtype=np.float32)

    def step(self, x_t, hidden):
        """x_t: (batch, 69), hidden: (batch, 128). Returns (latent (batch,9), new hidden)."""
        hidden = gru_cell(x_t, hidden, self.w_ih, self.w_hh, self.b_ih, self.b_hh)
        x = elu(linear(hidden, self.h0_w, self.h0_b))
        x = layer_norm(x, self.ln_g, self.ln_b)
        x = linear(x, self.h3_w, self.h3_b)
        return softsign(x), hidden
