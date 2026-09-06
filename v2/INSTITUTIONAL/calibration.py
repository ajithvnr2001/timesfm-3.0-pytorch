"""
calibration.py
==============
Point-in-time conformal calibration of TimesFM 3.0's native quantiles.

Why this exists: probing the raw model on Indian equities showed the native 80% band
(q10..q90) covering only 0-5% of realised prices at a 60-day horizon - the foundation
model's uncertainty is calibrated for its pretraining corpus, not for a single equity at
a multi-month horizon. Reporting that band as "80%" would be dishonest.

Method (split conformal, PIT-safe):
  1. Choose `n_origins` origin dates strictly before the cutoff, spaced so that each
     origin's full horizon of ground truth is ALSO before the cutoff.
  2. At each origin, rebuild the PIT bundle (context, covariates - identical machinery to
     production) and run the model.
  3. Standardise each step's error by the model's own half-width:
         e = (actual - median) / max(halfwidth, eps)
     where halfwidth = (q90 - q10) / 2.
  4. The calibrated multiplier is the empirical `target` quantile of |e| (symmetric) or of
     the positive/negative sides separately (asymmetric).
  5. Forward band = median +/- k * halfwidth, using only pre-cutoff information.

Nothing after the cutoff is touched, so the multiplier is legitimately available at
decision time. `n_calibration_points` is reported so thin calibration is visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd


@dataclass
class CalibrationResult:
    k_low: float = 1.0
    k_high: float = 1.0
    k_symmetric: float = 1.0
    n_origins_used: int = 0
    n_calibration_points: int = 0
    raw_coverage_pct: Optional[float] = None
    calibrated_coverage_pct: Optional[float] = None
    target_coverage: float = 0.80
    status: str = "identity"
    detail: dict = field(default_factory=dict)

    def apply(self, median: np.ndarray, q10: np.ndarray, q90: np.ndarray):
        """Widen (or tighten) a band using the fitted multipliers, in LOG space.

        Working in log space is not cosmetic: price-space widening with a large multiplier
        produced negative lower bounds (a -4125 rupee floor for a 5193 rupee stock) and
        absurd upper bounds. In log space the band is strictly positive and asymmetric in the
        way prices actually are.
        """
        med = np.maximum(np.asarray(median, dtype=float), 1e-9)
        lo = np.maximum(np.asarray(q10, dtype=float), 1e-9)
        hi = np.maximum(np.asarray(q90, dtype=float), 1e-9)
        half_log = np.maximum((np.log(hi) - np.log(lo)) / 2.0, 1e-9)
        low = med * np.exp(-self.k_low * half_log)
        high = med * np.exp(self.k_high * half_log)
        return low, high


def _standardised_errors(actual, median, q10, q90):
    """Log-space standardised error: log(actual/median) / log-half-width."""
    act = np.maximum(np.asarray(actual, dtype=float), 1e-9)
    med = np.maximum(np.asarray(median, dtype=float), 1e-9)
    lo = np.maximum(np.asarray(q10, dtype=float), 1e-9)
    hi = np.maximum(np.asarray(q90, dtype=float), 1e-9)
    half_log = np.maximum((np.log(hi) - np.log(lo)) / 2.0, 1e-9)
    return np.log(act / med) / half_log


def calibrate_pit(
    predict_fn: Callable[[pd.Timestamp, int], Optional[dict]],
    origin_dates,
    horizon: int,
    target_coverage: float = 0.80,
    asymmetric: bool = True,
    min_points: int = 40,
    max_multiplier: float = 12.0,
) -> CalibrationResult:
    """Fit conformal multipliers from rolling origins that are entirely pre-cutoff.

    `predict_fn(origin, horizon)` must return a dict with keys
    `median`, `q10`, `q90`, `actual` (all 1-D, equal length, all strictly pre-cutoff),
    or None if that origin is unusable.
    """
    errs = []
    used = 0
    raw_hits, raw_total = 0, 0
    for origin in origin_dates:
        try:
            got = predict_fn(pd.Timestamp(origin), horizon)
        except Exception:
            got = None
        if not got:
            continue
        actual = np.asarray(got["actual"], dtype=float)
        n = len(actual)
        if n < max(5, horizon // 4):
            continue
        median = np.asarray(got["median"], dtype=float)[:n]
        q10 = np.asarray(got["q10"], dtype=float)[:n]
        q90 = np.asarray(got["q90"], dtype=float)[:n]
        errs.append(_standardised_errors(actual, median, q10, q90))
        raw_hits += int(np.sum((actual >= q10) & (actual <= q90)))
        raw_total += n
        used += 1

    if not errs:
        return CalibrationResult(status="no_origins", target_coverage=target_coverage)

    e = np.concatenate(errs)
    res = CalibrationResult(
        n_origins_used=used,
        n_calibration_points=int(len(e)),
        raw_coverage_pct=round(100.0 * raw_hits / max(1, raw_total), 2),
        target_coverage=target_coverage,
    )
    if len(e) < min_points:
        res.status = f"insufficient_points({len(e)})"
        return res

    if asymmetric:
        neg = -e[e < 0]
        pos = e[e >= 0]
        tail = 1.0 - (1.0 - target_coverage) / 2.0  # 0.90 for 80% central coverage
        k_low = float(np.quantile(neg, tail)) if len(neg) >= 10 else float(np.quantile(np.abs(e), tail))
        k_high = float(np.quantile(pos, tail)) if len(pos) >= 10 else float(np.quantile(np.abs(e), tail))
    else:
        k_low = k_high = float(np.quantile(np.abs(e), target_coverage))

    k_sym = float(np.quantile(np.abs(e), target_coverage))
    res.k_low = float(np.clip(k_low, 0.25, max_multiplier))
    res.k_high = float(np.clip(k_high, 0.25, max_multiplier))
    res.k_symmetric = float(np.clip(k_sym, 0.25, max_multiplier))
    res.calibrated_coverage_pct = round(
        100.0 * float(np.mean((-res.k_low <= e) & (e <= res.k_high))), 2
    )
    res.status = "fitted"
    res.detail = {
        "err_p10": round(float(np.quantile(e, 0.10)), 3),
        "err_p50": round(float(np.quantile(e, 0.50)), 3),
        "err_p90": round(float(np.quantile(e, 0.90)), 3),
        "err_std": round(float(np.std(e)), 3),
        "asymmetric": asymmetric,
    }
    return res


def rolling_origins(dates: pd.DatetimeIndex, cutoff, horizon: int, n_origins: int = 8, spacing: int = None):
    """Origins o_i such that o_i and o_i + horizon rows are all <= cutoff.

    Walks backwards from the last usable origin so the most recent (most relevant) regime
    is always included.
    """
    cut = pd.Timestamp(cutoff).normalize()
    idx = dates[dates <= cut]
    if len(idx) < horizon * 2 + 260:
        return []
    last_pos = len(idx) - horizon - 1
    if spacing is None:
        spacing = max(horizon // 2, 10)
    out = []
    pos = last_pos
    while pos > 260 and len(out) < n_origins:
        out.append(idx[pos])
        pos -= spacing
    return out
