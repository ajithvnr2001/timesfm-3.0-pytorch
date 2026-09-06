"""
universe.py
===========
Survivorship-bias-free candidate universe, defined by rule *as of* each cutoff.

The previous repo demonstrated "multi-bagger detection" on CUPID - a name chosen because
we already knew it multiplied. That is selection on the outcome and proves nothing. Here:

  * `CANDIDATE_POOL` is a fixed, hand-specified list of NSE names that were all already
    listed before the earliest backtest cutoff. It deliberately includes names that
    subsequently did badly, so hit-rate is measurable in both directions.
  * At each cutoff, membership is decided only by data available then: minimum listed
    history, minimum median traded value, and a price floor. No forward information.
  * The resulting list is persisted so every run is reproducible and auditable.

Limitation, stated plainly: the pool is hand-specified rather than reconstructed from
historical NSE index membership (that data is not available through yfinance). Selection
*within* the pool is rule-based and point-in-time, but the pool itself is not a survivorship-
free census of the market. Results should be read as evidence about this pool only.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np
import pandas as pd

# Mix of large caps, mid caps, small caps, later-winners and later-losers.
CANDIDATE_POOL = [
    # large / mega cap
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
    "ITC.NS", "BHARTIARTL.NS", "HEROMOTOCO.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS",
    # mid cap
    "HAL.NS", "BEL.NS", "BHEL.NS", "TATAPOWER.NS", "PERSISTENT.NS", "COFORGE.NS",
    "POLYCAB.NS", "APLAPOLLO.NS", "CGPOWER.NS", "SUZLON.NS",
    # small cap / potential multi-baggers and their failures
    "MODISONLTD.NS", "CUPID.NS", "NETWEB.NS", "STLTECH.NS", "AETHER.NS", "MTARTECH.NS",
    "VENUSREM.NS", "WHEELS.NS", "RAYMONDREL.NS", "ARROWGREEN.NS", "KPITTECH.NS",
    "IDEA.NS", "YESBANK.NS", "RPOWER.NS", "JPPOWER.NS", "SOUTHBANK.NS",
]

DEFAULT_RULES = {
    "min_listed_days": 750,          # ~3 years of history before the cutoff
    "min_median_turnover_inr": 2.0e7,  # 2 crore median daily traded value over last 60d
    "min_price": 10.0,
    "max_price": 1.0e6,
}


def screen_universe(
    cutoff: str,
    pool: Optional[list] = None,
    rules: Optional[dict] = None,
    verbose: bool = True,
) -> dict:
    """Apply point-in-time liquidity/history rules. Returns members plus per-name reasons."""
    from pit_data import load_full_history, pit_slice

    pool = pool or CANDIDATE_POOL
    rules = {**DEFAULT_RULES, **(rules or {})}
    members, rejected = [], {}

    for tk in pool:
        try:
            full = load_full_history(tk)
        except Exception as exc:
            rejected[tk] = f"no_data: {type(exc).__name__}"
            continue
        hist = pit_slice(full, cutoff)
        if len(hist) < rules["min_listed_days"]:
            rejected[tk] = f"short_history({len(hist)}d)"
            continue
        close = hist["Close"].to_numpy(dtype=float)
        vol = hist["Volume"].to_numpy(dtype=float) if "Volume" in hist else np.zeros_like(close)
        turnover = float(np.median((close * vol)[-60:])) if len(close) >= 60 else 0.0
        price = float(close[-1])
        if not (rules["min_price"] <= price <= rules["max_price"]):
            rejected[tk] = f"price_out_of_range({price:.1f})"
            continue
        if turnover < rules["min_median_turnover_inr"]:
            rejected[tk] = f"illiquid(median_turnover={turnover:.3g})"
            continue
        members.append({
            "ticker": tk,
            "listed_days_at_cutoff": int(len(hist)),
            "price_at_cutoff": round(price, 2),
            "median_turnover_60d_inr": round(turnover, 0),
        })

    out = {
        "cutoff": str(cutoff),
        "rules": rules,
        "pool_size": len(pool),
        "n_members": len(members),
        "members": members,
        "rejected": rejected,
        "selection_note": (
            "Membership decided using only data at or before the cutoff. Pool is hand-specified "
            "and intentionally includes names that later underperformed."
        ),
    }
    if verbose:
        print(f"[universe] {cutoff}: {len(members)}/{len(pool)} pass; "
              f"rejected {len(rejected)}")
    return out


def save_universe(u: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"universe_{u['cutoff']}.json")
    with open(path, "w") as f:
        json.dump(u, f, indent=2)
    return path


def forward_return_pct(ticker: str, cutoff: str, horizon: int) -> Optional[float]:
    """Realised forward return - for scoring the screener AFTER the fact only."""
    from pit_data import load_full_history, pit_slice, forward_actuals

    try:
        full = load_full_history(ticker)
        hist = pit_slice(full, cutoff)
        fwd = forward_actuals(full, cutoff, horizon)
        if len(hist) == 0 or len(fwd) == 0:
            return None
        last = float(hist["Close"].iloc[-1])
        return float((float(fwd["Close"].iloc[-1]) - last) / last * 100.0)
    except Exception:
        return None
