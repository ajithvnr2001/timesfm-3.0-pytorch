"""
risk_sizing.py
==============
Risk and position sizing that does not collapse to zero at long horizons.

Two defects in the previous engine are fixed here explicitly:

  1. **Stop-loss horizon mismatch.** The old code anchored the stop at the *terminal*
     10th percentile of the forecast, so a 663-day band produced a -33% stop, an RRR of
     0.30 and a 0% allocation on a position that actually returned +49%. A stop is a
     short-horizon invalidation trigger, so here it is derived from a `stop_window`
     (default 20 trading days) using the calibrated band and an ATR-style volatility floor,
     independent of the forecast horizon.

  2. **Circular Kelly.** The old code derived `p_win` from RRR and then fed the same RRR
     into the Kelly formula. Here `p_win` comes from an externally supplied empirical
     estimate (walk-forward directional hit-rate) and defaults to 0.50 - a coin flip -
     when no evidence exists. No evidence, no leverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

ROUNDTRIP_FRICTION_PCT = 0.25  # STT + exchange + stamp + slippage, India


@dataclass
class RiskResult:
    horizon: int
    stop_window: int
    last_price: float
    stop_level: float
    stop_distance_pct: float
    expected_move_pct: float
    net_expected_move_pct: float
    risk_reward: float
    ann_vol_pct: float
    var95_1d_pct: float
    var95_horizon_pct: float
    cvar95_horizon_pct: float
    max_drawdown_pct: float
    p_win_source: str
    p_win: float
    kelly_fraction_pct: float
    vol_parity_pct: float
    recommended_alloc_pct: float
    recommended_capital: float
    recommended_shares: int
    directive: str
    notes: list = field(default_factory=list)


def _atr_proxy(close: np.ndarray, window: int = 14) -> float:
    if len(close) < window + 2:
        return float(np.std(np.diff(close) / close[:-1]) if len(close) > 2 else 0.02)
    rets = np.abs(np.diff(close[-(window + 1):]) / close[-(window + 1):-1])
    return float(np.mean(rets))


def compute_risk(
    history: np.ndarray,
    last_price: float,
    forecast_median: np.ndarray,
    band_low: np.ndarray,
    band_high: np.ndarray,
    horizon: int,
    stop_window: int = 20,
    p_win_empirical: Optional[float] = None,
    portfolio_capital: float = 1_000_000.0,
    macro_multiplier: float = 1.0,
    max_single_name_pct: float = 12.0,
) -> RiskResult:
    hist = np.asarray(history, dtype=float)
    notes = []

    rets = np.diff(hist) / hist[:-1]
    win = rets[-252:] if len(rets) >= 252 else rets
    daily_vol = float(np.std(win)) if len(win) > 2 else 0.02
    ann_vol = daily_vol * np.sqrt(252)

    running_max = np.maximum.accumulate(hist)
    max_dd = float(np.min((hist - running_max) / running_max) * 100.0)

    var_1d = 1.645 * daily_vol * 100.0
    var_h = 1.645 * daily_vol * np.sqrt(horizon) * 100.0
    tail = win[win <= np.quantile(win, 0.05)] if len(win) > 20 else win
    cvar_h = float(abs(np.mean(tail)) * np.sqrt(horizon) * 100.0) if len(tail) else var_h * 1.25

    # --- Stop: short-window band floor OR volatility floor, whichever is nearer to price
    k = min(max(stop_window, 1), len(band_low)) - 1
    band_stop = float(band_low[k])
    atr = _atr_proxy(hist)
    vol_stop = float(last_price * (1.0 - 2.5 * atr * np.sqrt(stop_window)))
    stop_level = float(max(band_stop, vol_stop))
    if stop_level >= last_price:
        stop_level = last_price * (1.0 - max(0.03, 2.0 * daily_vol * np.sqrt(stop_window)))
        notes.append("band lower bound above spot at stop window; fell back to volatility stop")
    stop_dist = float((last_price - stop_level) / last_price * 100.0)
    stop_dist = float(min(max(stop_dist, 1.5), 35.0))
    stop_level = float(last_price * (1 - stop_dist / 100.0))

    expected_move = float((forecast_median[-1] - last_price) / last_price * 100.0)
    net_move = round(expected_move - ROUNDTRIP_FRICTION_PCT, 2)
    rr = round(max(0.0, net_move) / stop_dist, 2) if stop_dist > 0 else 0.0

    # --- Kelly with an honest, external win probability
    if p_win_empirical is None:
        p_win = 0.50
        p_src = "default_coinflip_no_evidence"
        notes.append("no empirical hit-rate supplied; Kelly uses p_win=0.50")
    else:
        p_win = float(min(0.70, max(0.30, p_win_empirical)))
        p_src = "walkforward_directional_hit_rate"

    b = max(0.05, (max(0.0, net_move) / stop_dist)) if stop_dist > 0 else 0.05
    full_kelly = (p_win * (b + 1.0) - 1.0) / b
    kelly_pct = float(max(0.0, full_kelly) * 0.5 * 100.0)

    vol_parity_pct = float(np.clip((1.75 / max(0.08, ann_vol)) * 10.0, 0.0, 100.0))

    raw_alloc = min(kelly_pct, vol_parity_pct)
    alloc = float(round(min(max_single_name_pct, raw_alloc * macro_multiplier), 2))
    capital = round(alloc / 100.0 * portfolio_capital, 2)
    shares = int(capital // last_price) if last_price > 0 else 0

    # Labels describe the RISK/REWARD geometry only. They deliberately do not say
    # "conviction", because conviction is the LLM's separate, independently reported score.
    if net_move >= 10.0 and rr >= 1.8:
        directive = "FAVOURABLE RISK/REWARD"
    elif net_move >= 4.0 and rr >= 1.1:
        directive = "MILDLY FAVOURABLE"
    elif net_move > -3.0:
        directive = "NEUTRAL / MONITOR"
    else:
        directive = "UNFAVOURABLE / AVOID"

    return RiskResult(
        horizon=horizon, stop_window=stop_window, last_price=float(last_price),
        stop_level=round(stop_level, 2), stop_distance_pct=round(stop_dist, 2),
        expected_move_pct=round(expected_move, 2), net_expected_move_pct=net_move,
        risk_reward=rr, ann_vol_pct=round(ann_vol * 100, 2),
        var95_1d_pct=round(var_1d, 2), var95_horizon_pct=round(var_h, 2),
        cvar95_horizon_pct=round(cvar_h, 2), max_drawdown_pct=round(max_dd, 2),
        p_win_source=p_src, p_win=round(p_win, 3),
        kelly_fraction_pct=round(kelly_pct, 2), vol_parity_pct=round(vol_parity_pct, 2),
        recommended_alloc_pct=alloc, recommended_capital=capital, recommended_shares=shares,
        directive=directive, notes=notes,
    )
