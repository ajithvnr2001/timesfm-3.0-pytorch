# Configuration Ablation — how the production settings were chosen

Every number here was measured on a Colab **T4 with the real `google/timesfm-3.0-pytorch`
checkpoint**. No heuristic fallback was involved: the adapter raises `TimesFMUnavailable`
rather than silently substituting a drift line, and every run reports
`neural_points == horizon`, `extrapolated_points == 0`.

## Stage A — representation, context length, covariates

44 cases = 6 tickers (INFY, TCS, MODISONLTD, CUPID, HEROMOTOCO, NETWEB)
× 4 cutoffs (2024-03-28, 2024-06-28, 2024-12-31, 2025-06-30) × 2 horizons (21d, 60d).
Baselines: naive (last price carried forward), drift (60-day slope extrapolated),
seasonal-naive (last H observations rescaled).

| config | mean MAPE | median MAPE | directional acc | q10–q90 coverage | vs naive | beats naive |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **naive** | **9.97** | **6.03** | – | – | +0.00 | – |
| drift | 11.35 | 8.48 | – | – | +1.38 | – |
| seasonal-naive | 13.76 | 8.53 | – | – | +3.79 | – |
| uni_raw_4096 | 11.15 | 6.61 | 38.6% | 69.1% | +1.18 | 14/44 |
| **multi_raw_4096** | **10.58** | 7.20 | 45.5% | **72.4%** | **+0.61** | 17/44 |
| uni_raw_ctx512 | 11.71 | 6.55 | 36.4% | 68.2% | +1.74 | 14/44 |
| uni_raw_ctx1024 | 11.77 | 6.60 | 34.1% | 69.2% | +1.80 | 14/44 |
| uni_raw_ctx2048 | 11.32 | 7.16 | 40.9% | 66.9% | +1.35 | 16/44 |
| uni_raw_noscale_2048 | 11.32 | 7.16 | 40.9% | 66.9% | +1.35 | 16/44 |
| uni_log_2048 | 13.13 | 7.76 | 34.1% | 66.2% | +3.16 | 12/44 |
| multi_log_2048 | 12.21 | 7.93 | **54.5%** | 71.4% | +2.24 | **20/44** |
| uni_raw_cov_z_2048 | 11.12 | 7.23 | 45.5% | 63.5% | +1.15 | 15/44 |
| multi_raw_cov_z_2048 | 11.27 | 7.62 | 43.2% | 65.4% | +1.30 | 14/44 |

### What this says

1. **No configuration beats a naive random walk on price level.** The best (multivariate raw,
   4096 context) is still +0.61pp worse on mean MAPE and beats naive on only 17 of 44 cases.
   Anyone claiming a foundation model produces price alpha on Indian equities out of the box
   is not measuring against the right baseline.
2. **Covariates hurt.** Even z-scored, 7 past + 3 past-future covariates degraded coverage
   (72.4% → 65.4%) and did not improve mean MAPE. Raw (un-normalised) covariates were much
   worse: an earlier 12-case run measured mean coverage of 48.2% with raw covariates versus
   74.6% without. Production therefore runs **without covariates**, and the covariate builder
   is retained behind `RunConfig.use_covariates` purely so the finding stays reproducible.
3. **Multivariate helps a little.** Adding NIFTY 50 and the sector index as extra *targets*
   (context `(V,T)`, which TimesFM 3.0 handles natively via variate attention) is the single
   best change: mean MAPE 11.15 → 10.58 and coverage 69.1% → 72.4%.
4. **Log-space is worse on MAPE but better on direction.** `multi_log_2048` had the best
   directional accuracy (54.5%) and beats-naive count (20/44) while being worse on mean MAPE.
   Production keeps raw space for the level forecast; the log-space variant is a documented
   alternative rather than a silent ensemble.
5. **Longer context is mildly better.** 4096 ≥ 2048 > 1024 ≈ 512. Beyond that there is no
   Indian equity history to use, so 16384 buys nothing.

### Production configuration

```python
RunConfig(
    max_context=4096,      # truncated to available history
    multivariate=True,     # targets: [stock, NIFTY 50, sector index]
    use_covariates=False,  # measured to hurt
    calibrate=True,        # PIT conformal, log space
    stop_window=20,        # stop decoupled from forecast horizon
)
```

## Interval calibration

The model's native 80% band (`quantiles[:,0]` to `quantiles[:,8]`) is not calibrated for
single-equity, multi-month horizons. A 12-case run at H=60 measured **48.2%** mean coverage
with covariates and 74.6% after conformal correction; the full 192-run walk-forward measured
**75.3% raw → 79.0% calibrated** against an 80% nominal band. See `VALIDATION.md`.

Calibration is split-conformal on rolling origins that are entirely pre-cutoff, and operates
in **log space** — an earlier price-space implementation produced a negative lower bound
(-4125 for a 5193-rupee stock) once the multiplier grew large. `tests/test_units.py::
test_log_space_band_stays_positive` pins that fix.

## Data traps found while building this

* `Ticker.quarterly_income_stmt` is **empty** for several NSE names (e.g. INFY.NS); only the
  annual `income_stmt` (5 periods) is populated. The fundamentals layer uses annual statements
  with a 90-day publication lag, and the quarterly balance sheet with a 45-day lag.
* **Currency mismatch:** yfinance reports INFY.NS financials in USD (Diluted EPS ≈ 0.80) while
  the price series is INR (≈1470). Any absolute P/E built from those two numbers is wrong by
  the FX rate. The engine therefore exposes only **unit-free ratios** to the LLM and asks for
  a *percentage* re-rating, never an absolute price target.
* Covariates must be passed as `(k, T)` / `(k, T+H)`. Passing `(T, k)` raises; passing context
  as `(T, V)` is silently misinterpreted (T becomes the variate axis).
