"""Pure-function time-series analysis library for RL training metrics.

All functions accept numpy arrays and return plain Python types.
Dependencies: numpy, scipy, ruptures, hmmlearn.
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

try:
    import ruptures as rpt
    HAS_RUPTURES = True
except ImportError:
    HAS_RUPTURES = False

try:
    from hmmlearn.hmm import GaussianHMM
    HAS_HMMLEARN = True
except ImportError:
    HAS_HMMLEARN = False


def _clean(vals):
    """Remove non-finite values."""
    vals = np.asarray(vals, dtype=np.float64)
    return vals[np.isfinite(vals)]


def _least_squares_slope(seg):
    """Compute least-squares slope for a 1D segment."""
    if len(seg) < 2:
        return 0.0
    x = np.arange(len(seg), dtype=np.float64)
    xm, ym = x.mean(), seg.mean()
    denom = ((x - xm) ** 2).sum()
    if denom < 1e-12:
        return 0.0
    return float(((x - xm) * (seg - ym)).sum() / denom)


def quartile_slopes(vals):
    """Compute linear slope in each of 4 equal-length quartiles.

    Returns list of 4 slopes (units: change per index step).
    Returns None if fewer than 20 points.
    """
    vals = _clean(vals)
    if len(vals) < 20:
        return None
    n = len(vals)
    return [_least_squares_slope(vals[i * n // 4:(i + 1) * n // 4]) for i in range(4)]


def quartile_arrows(slopes, scale=None):
    """Convert 4 slopes to a 4-character arrow string.

    Symbols: ^ (rising), / (slight rise), = (flat), \\\\ (slight fall), v (falling)

    Args:
        slopes: list of 4 slope values.
        scale: normalization denominator. If None, uses max(abs(slopes)).
    """
    if slopes is None:
        return "    "
    if scale is None or scale < 1e-12:
        scale = max((abs(s) for s in slopes), default=0)
    if scale < 1e-12:
        return "===="
    chars = []
    for s in slopes:
        ns = s / scale
        if ns > 0.4:
            chars.append("^")
        elif ns > 0.1:
            chars.append("/")
        elif ns < -0.4:
            chars.append("v")
        elif ns < -0.1:
            chars.append("\\")
        else:
            chars.append("=")
    return "".join(chars)


def detect_phase(vals):
    """Detect training phases with adaptive merging.

    Splits into 8 segments, classifies each as warmup/learning/plateau/unstable,
    then merges alternating patterns and limits to max 3 transitions.

    Returns string like ``warmup(1)->learning(5)->plateau(2)`` or None if <80 points.
    """
    vals = _clean(vals)
    if len(vals) < 80:
        return None
    n = len(vals)
    data_range = vals.max() - vals.min()
    if data_range < 1e-8:
        return "plateau(8)"

    n_seg = 8
    phases = []
    for i in range(n_seg):
        seg = vals[i * n // n_seg:(i + 1) * n // n_seg]
        if len(seg) < 3:
            phases.append("plateau")
            continue
        slope = _least_squares_slope(seg)
        cv = seg.std() / abs(seg.mean()) if abs(seg.mean()) > 1e-8 else 0.0
        norm_slope = abs(slope) * len(seg) / data_range

        if cv > 0.5 and norm_slope > 0.3:
            phases.append("warmup")
        elif norm_slope > 0.15:
            phases.append("learning")
        elif cv > 0.3:
            phases.append("unstable")
        else:
            phases.append("plateau")

    # Step 1: Compress consecutive identical phases
    compressed = []
    current, count = phases[0], 1
    for p in phases[1:]:
        if p == current:
            count += 1
        else:
            compressed.append((current, count))
            current, count = p, 1
    compressed.append((current, count))

    # Step 2: Merge alternating patterns (A->B->A->B -> noisy_A)
    if len(compressed) >= 4:
        merged = []
        i = 0
        while i < len(compressed):
            # Check for alternating: A B A pattern
            if (i + 2 < len(compressed)
                    and compressed[i][0] == compressed[i + 2][0]
                    and compressed[i][0] != compressed[i + 1][0]):
                dominant = compressed[i][0]
                total = compressed[i][1] + compressed[i + 1][1] + compressed[i + 2][1]
                j = i + 3
                while (j + 1 < len(compressed)
                       and compressed[j][0] != dominant
                       and compressed[j + 1][0] == dominant):
                    total += compressed[j][1] + compressed[j + 1][1]
                    j += 2
                if j < len(compressed) and compressed[j][0] != dominant:
                    total += compressed[j][1]
                    j += 1
                merged.append((f"noisy_{dominant}", total))
                i = j
            else:
                merged.append(compressed[i])
                i += 1
        compressed = merged

    # Step 3: Limit to max 3 transitions (4 phases)
    while len(compressed) > 4:
        min_idx = 0
        min_total = compressed[0][1] + compressed[1][1]
        for k in range(1, len(compressed) - 1):
            total = compressed[k][1] + compressed[k + 1][1]
            if total < min_total:
                min_total = total
                min_idx = k
        a_name, a_cnt = compressed[min_idx]
        b_name, b_cnt = compressed[min_idx + 1]
        winner = a_name if a_cnt >= b_cnt else b_name
        compressed = (compressed[:min_idx]
                      + [(winner, a_cnt + b_cnt)]
                      + compressed[min_idx + 2:])

    return "->".join(f"{name}({cnt})" for name, cnt in compressed)


def fit_convergence(vals):
    """Fit exponential convergence model to latter 60% of data.

    Model: ``y = A + B * exp(-k * t)``

    Returns dict with keys: asymptote, rate, pct_converged, r2.
    Returns None if <50 points or fit fails (r2 < 0.3).
    """
    vals = _clean(vals)
    if len(vals) < 50:
        return None

    start = int(len(vals) * 0.4)
    seg = vals[start:]
    t = np.arange(len(seg), dtype=np.float64)

    first_q = seg[: len(seg) // 4].mean()
    last_q = seg[-len(seg) // 4 :].mean()

    def model(x, A, B, k):
        return A + B * np.exp(-k * x)

    try:
        popt, _ = curve_fit(
            model,
            t,
            seg,
            p0=[last_q, first_q - last_q, 3.0 / len(seg)],
            bounds=([-np.inf, -np.inf, 1e-6], [np.inf, np.inf, 1.0]),
            maxfev=5000,
        )
        A, B, k = popt
        y_pred = model(t, *popt)
        ss_res = ((seg - y_pred) ** 2).sum()
        ss_tot = ((seg - seg.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        if r2 < 0.3:
            return None
        total_change = abs(B)
        if total_change < 1e-8:
            pct = 100.0
        else:
            remaining = abs(B * np.exp(-k * len(seg)))
            pct = (1 - remaining / total_change) * 100
        return {
            "asymptote": float(A),
            "rate": float(k),
            "pct_converged": min(100.0, float(pct)),
            "r2": float(r2),
        }
    except (RuntimeError, ValueError):
        return None


def detect_plateau(vals, window_frac=0.25):
    """Detect plateau using normalized slope of trailing window.

    Checks if slope magnitude / data_range < 0.05 in the last window_frac.

    Returns:
        dict with keys: plateaued (bool), last_slope_norm (float), since_pct (float).
        Returns None if <30 points.
    """
    vals = _clean(vals)
    if len(vals) < 30:
        return None

    data_range = vals.max() - vals.min()
    if data_range < 1e-8:
        return {"plateaued": True, "last_slope_norm": 0.0, "since_pct": 0.0}

    w = max(10, int(len(vals) * window_frac))
    tail = vals[-w:]
    slope = _least_squares_slope(tail)
    slope_norm = abs(slope) * len(tail) / data_range

    plateaued = slope_norm < 0.05

    since_pct = 100.0
    if plateaued:
        step = max(5, len(vals) // 20)
        for start in range(len(vals) - w, -1, -step):
            seg = vals[start:start + w] if start + w <= len(vals) else vals[start:]
            if len(seg) < 5:
                break
            s = _least_squares_slope(seg)
            sn = abs(s) * len(seg) / data_range
            if sn >= 0.05:
                since_pct = 100.0 * start / len(vals)
                break
        else:
            since_pct = 0.0

    return {
        "plateaued": plateaued,
        "last_slope_norm": float(slope_norm),
        "since_pct": float(since_pct),
    }


def detect_changepoints(vals):
    """Detect changepoints using CUSUM on residuals from linear trend.

    Returns list of changepoint indices (into original array).
    Returns empty list if <50 points.
    """
    vals = _clean(vals)
    if len(vals) < 50:
        return []
    n = len(vals)

    # Remove linear trend
    x = np.arange(n, dtype=np.float64)
    residuals = vals - np.polyval(np.polyfit(x, vals, 1), x)

    # CUSUM on residuals
    cusum = np.cumsum(residuals - residuals.mean())
    abs_cusum = np.abs(cusum)

    std_r = residuals.std()
    if std_r < 1e-12:
        return []

    prominence = std_r * np.sqrt(n) * 0.3
    peaks, _ = find_peaks(abs_cusum, prominence=prominence, distance=max(1, n // 10))
    return sorted(int(p) for p in peaks)


def detect_oscillation(vals, window=20):
    """Detect periodic oscillation in a time series.

    Uses zero-crossing rate of first derivative to detect oscillating signals,
    and autocorrelation to estimate period.

    Args:
        vals: time series array.
        window: rolling window for envelope (max-min amplitude).

    Returns:
        dict with keys: oscillating (bool), period (float), amplitude (float),
        amplitude_trend (str: "growing"/"shrinking"/"stable").
        Returns None if <40 points.
    """
    vals = _clean(vals)
    if len(vals) < 40:
        return None

    # First derivative (diff)
    dv = np.diff(vals)
    if len(dv) < 10:
        return None

    # Zero-crossing rate: sign changes in first derivative
    signs = np.sign(dv)
    # Remove zeros (flat regions)
    signs = signs[signs != 0]
    if len(signs) < 10:
        return {"oscillating": False, "period": 0.0, "amplitude": 0.0, "amplitude_trend": "stable"}

    sign_changes = np.sum(np.abs(np.diff(signs)) > 0)
    sign_change_rate = float(sign_changes) / len(signs)

    high_sign_change = sign_change_rate > 0.3

    # Estimate period from autocorrelation
    period = 0.0
    has_periodic_peak = False
    if high_sign_change:
        centered = vals - vals.mean()
        n = len(centered)
        # Compute autocorrelation for lags up to n//2
        max_lag = min(n // 2, 200)
        autocorr = np.correlate(centered, centered, mode="full")
        autocorr = autocorr[n - 1:]  # positive lags only
        if autocorr[0] > 1e-12:
            autocorr = autocorr / autocorr[0]
        # Find first peak after lag 5 (skip trivial peak at 0)
        if max_lag > 10:
            ac_seg = autocorr[5:max_lag]
            peaks, _ = find_peaks(ac_seg, prominence=0.1)
            if len(peaks) > 0:
                period = float(peaks[0] + 5)  # offset by starting lag
                has_periodic_peak = True

    # Require BOTH high sign change rate AND a periodic autocorrelation peak.
    is_oscillating = high_sign_change and has_periodic_peak

    # Rolling envelope amplitude
    amplitude = 0.0
    amplitude_trend = "stable"
    if len(vals) >= window:
        envelopes = []
        for i in range(window - 1, len(vals)):
            w = vals[i - window + 1: i + 1]
            envelopes.append(w.max() - w.min())
        envelopes = np.array(envelopes)
        amplitude = float(envelopes[-len(envelopes) // 4:].mean())
        # Trend: compare first half vs second half
        mid = len(envelopes) // 2
        if mid > 0:
            first_half = envelopes[:mid].mean()
            second_half = envelopes[mid:].mean()
            if first_half > 1e-8:
                ratio = second_half / first_half
                if ratio > 1.2:
                    amplitude_trend = "growing"
                elif ratio < 0.8:
                    amplitude_trend = "shrinking"

    return {
        "oscillating": is_oscillating,
        "period": period,
        "amplitude": amplitude,
        "amplitude_trend": amplitude_trend,
    }


def rolling_cv(vals, window=None):
    """Compute rolling coefficient of variation.

    Args:
        vals: time series.
        window: window size (default: len//10, min 10).

    Returns:
        (cv_array, final_cv): rolling CV array and final window CV.
        Returns (None, None) if <20 points.
    """
    vals = _clean(vals)
    if len(vals) < 20:
        return None, None
    if window is None:
        window = max(10, len(vals) // 10)
    window = min(window, len(vals))

    cv_arr = np.full(len(vals), np.nan)
    for i in range(window - 1, len(vals)):
        w = vals[i - window + 1 : i + 1]
        m = w.mean()
        cv_arr[i] = w.std() / abs(m) if abs(m) > 1e-8 else 0.0

    valid = cv_arr[~np.isnan(cv_arr)]
    final_cv = float(valid[-1]) if len(valid) > 0 else 0.0
    return cv_arr, final_cv


def summarize(vals):
    """Run all analyses and return a summary dict.

    Keys: quartile_slopes, quartile_arrows, phase, plateau,
    changepoints, final_cv, stability, oscillation.

    Uses detect_plateau (normalized-slope based) instead of fit_convergence.
    fit_convergence is still available as a standalone function.
    """
    vals = _clean(vals)
    slopes = quartile_slopes(vals)
    _, final_cv = rolling_cv(vals)
    stability = None
    if final_cv is not None:
        if final_cv < 0.05:
            stability = "stable"
        elif final_cv < 0.15:
            stability = "moderate"
        else:
            stability = "volatile"
    osc = detect_oscillation(vals)
    plateau = detect_plateau(vals)
    return {
        "quartile_slopes": slopes,
        "quartile_arrows": quartile_arrows(slopes),
        "phase": detect_phase(vals),
        "plateau": plateau,
        "oscillation": osc,
        "changepoints": detect_changepoints(vals),
        "final_cv": final_cv,
        "stability": stability,
    }


# ==================================================================
# Multi-metric deep analysis (PELT, Lag Analysis, HMM)
# ==================================================================

# Key metric tags for cross-metric analysis, ordered by diagnostic priority.
# NOTE: These are defaults for hero_agent. Use resolve_key_metrics(data) for
# environment-aware resolution (constrained_full_albc uses different tag names).
KEY_METRICS = [
    "Train/mean_reward",
    "Attitude_Error/roll_deg",
    "Attitude_Error/pitch_deg",
    "Constraint/barrier_penalty",
    "Encoder/z_std",
    "Encoder/grad_norm",
    "Policy/mean_noise_std",
    "Policy/entropy",
    "Policy/line_search_success",
    "TRPO/step_norm",
    "DORAEMON/success_rate",
    "Action/size_mean",
    "Action/rate_mean",
    "Dynamics/joint_vel_abs_max",
]

# Diagnostically meaningful pairs for lag analysis.
LAG_PAIRS = [
    ("Constraint/barrier_penalty", "Train/mean_reward"),
    ("Encoder/z_std", "Attitude_Error/roll_deg"),
    ("Encoder/z_std", "Attitude_Error/pitch_deg"),
    ("Constraint/barrier_penalty", "Attitude_Error/roll_deg"),
    ("Action/size_mean", "Attitude_Error/roll_deg"),
    ("Policy/mean_noise_std", "Train/mean_reward"),
    ("Dynamics/joint_vel_abs_max", "Train/mean_reward"),
    ("TRPO/step_norm", "Train/mean_reward"),
    ("DORAEMON/success_rate", "Train/mean_reward"),
]

# Backwards-compatible alias
CORR_PAIRS = LAG_PAIRS


def _resolve_tag(data, *candidates):
    """Return first tag from candidates that exists in data, or first candidate."""
    for tag in candidates:
        if tag in data:
            return tag
    return candidates[0]


def resolve_key_metrics(data):
    """Return KEY_METRICS with environment-specific tags resolved.

    Handles tag name differences between hero_agent and constrained_full_albc:
        - Attitude_Error/* vs Attitude/*
        - Action/size_mean vs Action/arm_norm
        - Action/rate_mean vs Action/arm_rate
    Also adds constrained_full_albc-specific metrics when available.
    """
    r = lambda *tags: _resolve_tag(data, *tags)
    metrics = [
        "Train/mean_reward",
        r("Attitude/roll_deg", "Attitude_Error/roll_deg"),
        r("Attitude/pitch_deg", "Attitude_Error/pitch_deg"),
        "Constraint/barrier_penalty",
        "Encoder/z_std",
        "Encoder/grad_norm",
        "Policy/mean_noise_std",
        "Policy/entropy",
        "Policy/line_search_success",
        "TRPO/step_norm",
        "DORAEMON/success_rate",
        r("Action/arm_norm", "Action/size_mean"),
        r("Action/arm_rate", "Action/rate_mean"),
        "Dynamics/joint_vel_abs_max",
    ]
    # Add constrained_full_albc-specific metrics if available
    for tag in ["Action/thruster_norm", "Thruster/utilization_mean",
                "Episode_Termination/too_fast_ang"]:
        if tag in data:
            metrics.append(tag)
    return metrics


def resolve_lag_pairs(data):
    """Return LAG_PAIRS with environment-specific tags resolved."""
    r = lambda *tags: _resolve_tag(data, *tags)
    roll = r("Attitude/roll_deg", "Attitude_Error/roll_deg")
    pitch = r("Attitude/pitch_deg", "Attitude_Error/pitch_deg")
    arm_act = r("Action/arm_norm", "Action/size_mean")
    pairs = [
        ("Constraint/barrier_penalty", "Train/mean_reward"),
        ("Encoder/z_std", roll),
        ("Encoder/z_std", pitch),
        ("Constraint/barrier_penalty", roll),
        (arm_act, roll),
        ("Policy/mean_noise_std", "Train/mean_reward"),
        ("Dynamics/joint_vel_abs_max", "Train/mean_reward"),
        ("TRPO/step_norm", "Train/mean_reward"),
        ("DORAEMON/success_rate", "Train/mean_reward"),
    ]
    # Add constrained_full_albc-specific lag pairs
    if "Action/thruster_norm" in data:
        pairs.append(("Action/thruster_norm", "Train/mean_reward"))
    if "Episode_Termination/too_fast_ang" in data:
        pairs.append(("Episode_Termination/too_fast_ang", "Train/mean_reward"))
    return pairs


def rank_metrics_by_interest(data, reward_tag="Train/mean_reward", min_points=20):
    """Rank all TB tags by diagnostic interest score.

    Scoring (each 0-1, equal weight):
      - CV: high variance relative to mean
      - Trend: large shift between first and last 20%
      - Changepoints: number of structural breaks (PELT)
      - |Reward correlation|: strength of relationship with reward

    Args:
        data: dict of {tag: [(step, value), ...]} from TensorBoard.
        reward_tag: tag to correlate against.
        min_points: minimum data points required.

    Returns:
        list of (tag, score) sorted by score descending.
    """
    reward_vals = None
    if reward_tag in data and len(data[reward_tag]) >= min_points:
        reward_vals = np.array([v for _, v in data[reward_tag]], dtype=np.float64)

    raw = {}
    for tag in data:
        if len(data[tag]) < min_points:
            continue
        vals = np.array([v for _, v in data[tag]], dtype=np.float64)
        vals = vals[np.isfinite(vals)]
        if len(vals) < min_points:
            continue

        mean = abs(vals.mean())
        cv = float(vals.std() / mean) if mean > 1e-8 else 0.0

        n = len(vals)
        k = max(1, n // 5)
        trend_abs = abs(float(vals[-k:].mean() - vals[:k].mean()))
        val_range = float(vals.max() - vals.min())
        trend_norm = trend_abs / val_range if val_range > 1e-8 else 0.0

        # Fast changepoint proxy: count significant slope sign changes
        w = max(5, len(vals) // 20)
        slopes = np.array([
            vals[min(i + w, len(vals) - 1)] - vals[i]
            for i in range(0, len(vals) - w, w)
        ])
        sign_ch = int(np.sum(np.abs(np.diff(np.sign(slopes))) > 0)) if len(slopes) > 1 else 0

        reward_corr = 0.0
        if reward_vals is not None and tag != reward_tag:
            nc = min(len(vals), len(reward_vals))
            if nc >= min_points:
                try:
                    c = abs(float(np.corrcoef(vals[:nc], reward_vals[:nc])[0, 1]))
                    if np.isfinite(c):
                        reward_corr = c
                except Exception:
                    pass

        raw[tag] = (cv, trend_norm, sign_ch, reward_corr)

    if not raw:
        return []

    max_cv = max(r[0] for r in raw.values()) or 1.0
    max_tr = max(r[1] for r in raw.values()) or 1.0
    max_cp = max(r[2] for r in raw.values()) or 1

    scored = []
    for tag, (cv, tr, cp, rc) in raw.items():
        score = (
            0.25 * min(cv / max_cv, 1.0)
            + 0.25 * min(tr / max_tr, 1.0)
            + 0.25 * min(cp / max_cp, 1.0)
            + 0.25 * rc
        )
        scored.append((tag, round(score, 4)))
    scored.sort(key=lambda x: -x[1])
    return scored


def detect_changepoints_pelt(vals, pen=None):
    """Detect changepoints using PELT (Pruned Exact Linear Time).

    Penalty is computed from original series length (not downsampled),
    so longer series naturally produce fewer changepoints.

    For series > 500 points, downsamples to ~500 via block-averaging.
    Final-point filter uses working-array bounds before scale mapping.

    Args:
        vals: 1D time series.
        pen: penalty parameter (higher = fewer changepoints).
             Default: 3 * log(n_original) (BIC-inspired).

    Returns:
        list of changepoint indices (excluding final point).
        Empty list if <30 points or ruptures not available.
    """
    if not HAS_RUPTURES:
        return detect_changepoints(vals)  # fallback to CUSUM
    vals = _clean(vals)
    if len(vals) < 30:
        return []

    # Downsample long series to ~500 points via block-averaging
    scale = 1
    working = vals
    if len(vals) > 500:
        scale = len(vals) // 500
        n_blocks = len(vals) // scale
        working = vals[:n_blocks * scale].reshape(n_blocks, scale).mean(axis=1)

    if pen is None:
        pen = 3.0 * np.log(len(vals))  # original length, not downsampled
    algo = rpt.Pelt(model="l2", min_size=max(5, len(working) // 20), jump=5).fit(working)
    cps = algo.predict(pen=pen)
    # Filter in working-array space before mapping back
    return [int(c * scale) for c in cps if c < len(working)]


def multi_metric_changepoints(data, metrics=None):
    """Run PELT on all key metrics and return changepoints ordered by time.

    Args:
        data: dict of {tag: [(step, value), ...]} from TensorBoard.
        metrics: list of tags to analyze. Defaults to KEY_METRICS.

    Returns:
        list of (iteration, tag_short, direction) sorted by iteration.
        direction: "up" or "down" (mean shift direction at changepoint).
    """
    if metrics is None:
        metrics = KEY_METRICS
    all_cps = []
    for tag in metrics:
        if tag not in data or len(data[tag]) < 30:
            continue
        vals = np.array([v for _, v in data[tag]], dtype=np.float64)
        tag_steps = [s for s, _ in data[tag]]
        cps = detect_changepoints_pelt(vals)
        short = tag.split("/")[-1]
        for cp in cps:
            # Determine direction: mean after vs mean before
            before = vals[max(0, cp - 10):cp].mean()
            after = vals[cp:min(len(vals), cp + 10)].mean()
            direction = "up" if after > before else "down"
            iter_num = tag_steps[min(cp, len(tag_steps) - 1)]
            all_cps.append((iter_num, short, direction))
    all_cps.sort(key=lambda x: x[0])
    return all_cps


def filter_coincident_changepoints(all_cps, tolerance=15):
    """Filter changepoints to only keep groups where 2+ metrics change together.

    Args:
        all_cps: list of (iteration, tag_short, direction) from multi_metric_changepoints.
        tolerance: max iteration gap to consider changepoints coincident.

    Returns:
        list of groups, each group is a list of (iteration, tag_short, direction).
        Only groups with 2+ metrics are returned.
    """
    if not all_cps:
        return []

    groups = []
    current_group = [all_cps[0]]
    for cp in all_cps[1:]:
        if cp[0] - current_group[-1][0] <= tolerance:
            current_group.append(cp)
        else:
            groups.append(current_group)
            current_group = [cp]
    groups.append(current_group)

    # Only keep groups with 2+ distinct metrics
    significant = []
    for g in groups:
        unique_tags = set(tag for _, tag, _ in g)
        if len(unique_tags) >= 2:
            significant.append(g)
    return significant


def rolling_correlation(x, y, window=50):
    """Compute rolling Pearson correlation between two time series.

    Constant segments produce NaN (not 0.0) since correlation is undefined.

    Args:
        x, y: 1D arrays of equal length.
        window: rolling window size.

    Returns:
        (corr_array, flip_rate): rolling correlation array (NaN-padded)
        and flip_rate (sign changes normalized by length).
        Returns (None, 0.0) if <window points.
    """
    x, y = _clean(x), _clean(y)
    n = min(len(x), len(y))
    if n < window:
        return None, 0.0
    x, y = x[:n], y[:n]

    corr = np.full(n, np.nan)
    for i in range(window - 1, n):
        wx = x[i - window + 1:i + 1]
        wy = y[i - window + 1:i + 1]
        sx, sy = wx.std(), wy.std()
        if sx > 1e-12 and sy > 1e-12:
            corr[i] = float(np.corrcoef(wx, wy)[0, 1])
        # else: leave as NaN (constant segment, correlation undefined)

    valid = corr[~np.isnan(corr)]
    flip_rate = 0.0
    if len(valid) > 1:
        signs = np.sign(valid)
        signs = signs[signs != 0]
        if len(signs) > 1:
            sign_changes = int(np.sum(np.abs(np.diff(signs)) > 0))
            flip_rate = float(sign_changes) / len(signs)

    return corr, flip_rate


def cross_correlation_lag(x, y, max_lag=30):
    """First-differenced cross-correlation for lead-lag detection.

    Differencing removes shared trends, isolating timing relationships.

    Args:
        x, y: 1D arrays.
        max_lag: maximum lag to test in each direction.

    Returns:
        dict with best_lag (positive = x leads y), best_corr,
        x_leads (bool), significant (bool: |corr| >= 0.3).
        Returns None if insufficient data.
    """
    x, y = _clean(x), _clean(y)
    n = min(len(x), len(y))
    if n < max_lag * 2 + 10:
        return None
    x, y = x[:n], y[:n]

    # First-difference to remove trends
    dx = np.diff(x)
    dy = np.diff(y)

    # Normalize
    sx, sy = dx.std(), dy.std()
    if sx < 1e-12 or sy < 1e-12:
        return None
    dx = (dx - dx.mean()) / sx
    dy = (dy - dy.mean()) / sy

    best_lag = 0
    best_corr = 0.0
    n_d = len(dx)

    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            cx = dx[:n_d - lag] if lag > 0 else dx
            cy = dy[lag:] if lag > 0 else dy
        else:
            cx = dx[-lag:]
            cy = dy[:n_d + lag]
        if len(cx) < 10:
            continue
        c = float(np.dot(cx, cy) / len(cx))
        if abs(c) > abs(best_corr):
            best_corr = c
            best_lag = lag

    return {
        "best_lag": int(best_lag),
        "best_corr": float(best_corr),
        "x_leads": best_lag > 0,
        "significant": abs(best_corr) >= 0.3,
    }


def lag_profile(x, y, max_lag=30):
    """Compute first-differenced correlation at each lag.

    Returns array of correlations for lags from -max_lag to +max_lag,
    or None if insufficient data.
    """
    x, y = _clean(x), _clean(y)
    n = min(len(x), len(y))
    if n < max_lag * 2 + 10:
        return None
    x, y = x[:n], y[:n]

    dx = np.diff(x)
    dy = np.diff(y)
    sx, sy = dx.std(), dy.std()
    if sx < 1e-12 or sy < 1e-12:
        return None
    dx = (dx - dx.mean()) / sx
    dy = (dy - dy.mean()) / sy

    n_d = len(dx)
    corrs = []
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            cx = dx[:n_d - lag] if lag > 0 else dx
            cy = dy[lag:] if lag > 0 else dy
        else:
            cx = dx[-lag:]
            cy = dy[:n_d + lag]
        if len(cx) < 10:
            corrs.append(0.0)
            continue
        corrs.append(float(np.dot(cx, cy) / len(cx)))
    return np.array(corrs)


def multi_metric_lag_analysis(data, pairs=None):
    """Compute lead-lag relationships for metric pairs.

    Args:
        data: dict of {tag: [(step, value), ...]}
        pairs: list of (tag_a, tag_b). Defaults to LAG_PAIRS.

    Returns:
        list of dicts with: pair, best_lag, best_corr, x_leads, significant.
    """
    if pairs is None:
        pairs = LAG_PAIRS
    results = []
    for tag_a, tag_b in pairs:
        if tag_a not in data or tag_b not in data:
            continue
        va = np.array([v for _, v in data[tag_a]], dtype=np.float64)
        vb = np.array([v for _, v in data[tag_b]], dtype=np.float64)
        n = min(len(va), len(vb))
        if n < 70:
            continue
        lag_info = cross_correlation_lag(va[:n], vb[:n])
        if lag_info is None:
            continue
        short_a = tag_a.split("/")[-1]
        short_b = tag_b.split("/")[-1]
        results.append({
            "pair": (short_a, short_b),
            **lag_info,
        })
    return results


def multi_metric_correlations(data, window=50, pairs=None):
    """Compute rolling correlation for diagnostically meaningful metric pairs.

    Args:
        data: dict of {tag: [(step, value), ...]} from TensorBoard.
        window: rolling window size.
        pairs: list of (tag_a, tag_b) tuples. Defaults to LAG_PAIRS.

    Returns:
        list of dicts with keys: pair (tuple), corr_array, last_corr,
        mean_corr, flip_rate, regime_shift (bool).
    """
    if pairs is None:
        pairs = LAG_PAIRS
    results = []
    for tag_a, tag_b in pairs:
        if tag_a not in data or tag_b not in data:
            continue
        va = np.array([v for _, v in data[tag_a]], dtype=np.float64)
        vb = np.array([v for _, v in data[tag_b]], dtype=np.float64)
        n = min(len(va), len(vb))
        if n < window:
            continue
        corr, flip_rate = rolling_correlation(va[:n], vb[:n], window)
        if corr is None:
            continue
        valid = corr[~np.isnan(corr)]
        if len(valid) == 0:
            continue
        last_corr = float(valid[-1])
        mean_corr = float(valid.mean())
        # Regime shift: first half mean vs second half mean differ significantly
        mid = len(valid) // 2
        regime_shift = False
        if mid > 0:
            first_mean = valid[:mid].mean()
            second_mean = valid[mid:].mean()
            if abs(first_mean - second_mean) > 0.3:
                regime_shift = True

        short_a = tag_a.split("/")[-1]
        short_b = tag_b.split("/")[-1]
        results.append({
            "pair": (short_a, short_b),
            "corr_array": corr,
            "last_corr": last_corr,
            "mean_corr": mean_corr,
            "flip_rate": flip_rate,
            "regime_shift": regime_shift,
        })
    return results


def detect_regimes(data, max_states=4, metrics=None):
    """Detect training regimes using Gaussian HMM on metric change rates.

    Uses first-differences of key metrics as features. Selects optimal
    number of states (2-max_states) by BIC. Excludes binary metrics
    (Constraint/mode). Filters states with mean duration < 5.

    Args:
        data: dict of {tag: [(step, value), ...]} from TensorBoard.
        max_states: maximum number of HMM states to test.
        metrics: list of tags to use as features. Defaults to KEY_METRICS.

    Returns:
        dict with keys: states (array), n_states, valid_states (list),
        state_means, state_durations, transitions, feature_names.
        Returns None if hmmlearn unavailable or <50 points.
    """
    if not HAS_HMMLEARN:
        return None
    if metrics is None:
        metrics = KEY_METRICS

    # Exclude binary metrics from HMM features
    _binary_tags = {"Policy/line_search_success", "DORAEMON/reverted"}

    # Select features: use metrics that exist and have enough data
    feature_tags = []
    for tag in metrics:
        if tag in _binary_tags:
            continue
        if tag in data and len(data[tag]) >= 50:
            feature_tags.append(tag)
    if len(feature_tags) < 3:
        return None

    # Build feature matrix from first-differences (change rates)
    min_len = min(len(data[tag]) for tag in feature_tags)
    if min_len < 50:
        return None

    raw = np.column_stack([
        np.array([v for _, v in data[tag][:min_len]], dtype=np.float64)
        for tag in feature_tags
    ])
    # First differences (change rates)
    features = np.diff(raw, axis=0)
    # Z-score normalize each feature
    std = features.std(axis=0)
    std[std < 1e-12] = 1.0
    features = (features - features.mean(axis=0)) / std

    d = features.shape[1]
    T = len(features)

    # Select best n_states by BIC
    best_model, best_bic, best_n = None, np.inf, 2
    for n in range(2, max_states + 1):
        try:
            model = GaussianHMM(
                n_components=n, covariance_type="diag",
                n_iter=200, random_state=42,
            )
            model.fit(features)
            # BIC = -2*LL + k*log(T)
            ll = model.score(features)
            # Corrected n_params: means(n*d) + variances(n*d) + transitions(n*(n-1)) + initial(n-1)
            n_params = n * 2 * d + n * (n - 1) + (n - 1)
            bic = -2 * ll + n_params * np.log(T)
            if bic < best_bic:
                best_model, best_bic, best_n = model, bic, n
        except Exception:
            continue

    if best_model is None:
        return None

    states = best_model.predict(features)
    # State means in original (non-differenced) feature space
    state_means = {}
    for s in range(best_n):
        mask = states == s
        if mask.sum() > 0:
            # Use raw values (offset by 1 due to diff)
            state_means[s] = {
                tag.split("/")[-1]: float(raw[1:][mask, i].mean())
                for i, tag in enumerate(feature_tags)
            }

    # State durations
    state_durations = {}
    for s in range(best_n):
        runs = []
        count = 0
        for st in states:
            if st == s:
                count += 1
            elif count > 0:
                runs.append(count)
                count = 0
        if count > 0:
            runs.append(count)
        state_durations[s] = float(np.mean(runs)) if runs else 0.0

    # Identify valid states (mean duration >= 5)
    valid_states = [s for s in range(best_n) if state_durations.get(s, 0) >= 5]

    return {
        "states": states,
        "n_states": best_n,
        "valid_states": valid_states,
        "state_means": state_means,
        "state_durations": state_durations,
        "transitions": best_model.transmat_.tolist(),
        "feature_names": [t.split("/")[-1] for t in feature_tags],
    }
