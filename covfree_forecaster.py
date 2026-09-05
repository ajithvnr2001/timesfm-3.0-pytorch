"""
covfree_forecaster.py  --  FIX for Weakness #2
Replaces the target-anchored sigmoid covariate cheat
(last_price + sigmoid(t)*(target-last_price)) with an honest
volatility-scaled fundamental blend + Monte-Carlo CI.

The forecast is NOT forced to hit the target; it converges toward
it with a confidence weight, and the CI comes from simulated paths.
"""
import numpy as np

def sigmoid_path_OLD(last, target, horizon, k=0.18, t0=None):
    """The old cheat: endpoint is mathematically pinned to `target`."""
    t0 = horizon/2 if t0 is None else t0
    return np.array([last + (1/(1+np.exp(-k*(h+1-t0))))*(target-last) for h in range(horizon)])

def monte_carlo_paths(last, annual_vol, horizon, n_sims=500, seed=11):
    rng = np.random.default_rng(seed)
    daily_vol = annual_vol*np.sqrt(1/252)
    rets = rng.normal(0.0, daily_vol, (n_sims, horizon))
    return last*np.exp(np.cumsum(rets, axis=1))

def forecast_covfree(last, target, annual_vol, horizon, target_reach=0.62,
                     n_sims=500, seed=11):
    """
    Honest hybrid:
      - simulate vol-scaled paths from `last`
      - blend the median path toward the fundamental `target` with a
        linearly increasing confidence weight capped at `target_reach`
      - CI from the actual distribution of simulated paths (not +/-10%)
    Returns (point_forecast, q10, q90).
    """
    paths = monte_carlo_paths(last, annual_vol, horizon, n_sims, seed)
    med = np.median(paths, axis=0)
    w = np.linspace(0, target_reach, horizon)
    point = (1-w)*med + w*target
    q10 = np.percentile(paths, 10, axis=0)
    q90 = np.percentile(paths, 90, axis=0)
    return point, q10, q90

def annualized_vol(close_series):
    r = close_series.pct_change().dropna()
    return float(r.std()*np.sqrt(252))
