# Institutional TimesFM 3.0 Engine (`v2/INSTITUTIONAL`)

An honest, point-in-time, leakage-audited forecasting and screening stack built on the real
`google/timesfm-3.0-pytorch` checkpoint plus an anonymised LLM analyst layer.

This directory supersedes `v2/MULTI_AGENT_SANDBOX`. Everything below was measured on a Colab
T4; nothing is asserted that was not run.

---

## The headline result, stated plainly

**TimesFM 3.0 does not beat a naive random walk on Indian equity price levels.**

Across a 192-run walk-forward study (34 names × 3 cutoffs × 2 horizons):

| metric | TimesFM 3.0 | naive (last price) | drift | seasonal-naive |
| :--- | ---: | ---: | ---: | ---: |
| mean MAPE, 60d | **9.41%** | 9.48% | 10.71% | 12.68% |
| mean MAPE, 252d | 17.26% | **16.62%** | 32.95% | 39.07% |
| pooled mean MAPE | 13.34% | **13.05%** | – | – |

It beats naive on 51% of runs — a coin flip. It crushes the *trend-following* baselines at
long horizons (17.3% vs 32.9% drift, 39.1% seasonal), so it is not useless; it simply cannot
beat the specific hypothesis "price stays where it is".

**Two things do work:**

1. **Direction.** Pooled directional accuracy is **57.8%** on n=192 (z=2.17, two-sided
   p=0.030 against 50%). Modest, but measurable, and it is what feeds position sizing.
2. **Calibrated uncertainty.** The model's native 80% band covers only **75.3%** of outcomes;
   point-in-time conformal calibration in log space lifts pooled coverage to **77.9%**
   (60d 76.5%, 252d 79.3%) against a nominal 80% band, with every bound strictly positive.

**What does not work:** the anonymised LLM conviction score showed **no cross-sectional
predictive power** in this sample — mean Spearman rank-IC **+0.009** across six
(horizon, cutoff) panels, positive in only 2 of 6. It did not find the multi-baggers: CUPID
returned +415% over 252 days from the 2024-12-31 cutoff and the screener scored it 38/100.
That is reported rather than hidden, and it is why the engine never lets the LLM touch the
price path.

Live forward predictions: [`FORWARD/FORWARD_REPORT.md`](FORWARD/FORWARD_REPORT.md).
Full numbers: [`VALIDATION.md`](VALIDATION.md). Configuration evidence:
[`ABLATION.md`](ABLATION.md). Verified model contract: [`TIMESFM3_API.md`](TIMESFM3_API.md).

---

## Architecture

```
universe.py        rule-based universe as of each cutoff (no survivorship selection)
pit_data.py        PIT prices, 7 past covariates, 3 calendar covariates, PIT fundamentals
timesfm3_adapter.py  hard-fail wrapper: real TimesFM 3.0 or an exception, never a heuristic
calibration.py     split-conformal calibration of the native quantiles, in log space
anonymizer.py      entity/date scrubbing + adversarial identity probe verdicts
llm_agents.py      Exa PIT evidence, multi-bagger conviction scoring, identity probe
risk_sizing.py     horizon-matched stop, non-circular Kelly, VaR/CVaR
engine.py          composes one (ticker, cutoff, horizon) run
run_validation.py  resumable walk-forward harness  ->  artifacts/ledger.json
precompute_llm.py  parallel LLM pass (the serial version took an hour)
analyze_validation.py  ledger -> VALIDATION.md
run_forward.py     live forward predictions -> FORWARD_REPORT.md
tests/test_units.py  16 CPU-only tests
```

## How TimesFM 3.0 is actually used

Verified on the T4 (see `TIMESFM3_API.md` for the probe transcript):

* **Long context** — up to 4096 trading days per name (the model accepts 16384; Indian
  listings do not have that much history).
* **Native multivariate** — context is `(V, T)` with targets `[stock, NIFTY 50, sector index]`,
  so cross-asset structure is handled by the model's variate attention in one forward pass.
  This was the single best configuration change (mean MAPE 11.15 → 10.58).
* **Native quantiles** — all 9 quantile heads are consumed; `quantiles[:,0]` and
  `quantiles[:,8]` are the reported 80% band, then conformally calibrated. Nothing is
  substituted from historical volatility.
* **Covariates are supported but switched OFF** — 7 past + 3 past-future covariates are built
  and shape-validated as `(k,T)`/`(k,T+H)`, but measurement showed they *hurt* (coverage
  72.4% → 65.4%). They stay behind a flag so the finding is reproducible.
* **No fallback** — `TimesFMUnavailable` is raised if the checkpoint cannot load. Every result
  record carries `neural_points == horizon` and `extrapolated_points == 0`.

## How the LLM is actually used

* **PIT evidence** via Exa with a hard `end_published_date` ceiling, then post-filtered for
  any post-cutoff year token (3 of 6 retrieved snippets were dropped as future-dated in the
  smoke test).
* **Anonymised packet** — no ticker, no company name, no index names, no absolute dates
  (only `[T]`, `[T-1]`, …), and only unit-free ratios, because yfinance reports some NSE names
  in USD while the price is INR.
* **Structured conviction** — five multi-bagger axes (earnings acceleration, margin expansion,
  capacity/order-book, balance-sheet repair, re-rating headroom), multi-sample
  self-consistency with median aggregation and sample disagreement recorded as uncertainty.
* **The LLM never sets the price path.** It produces a conviction score for ranking and a
  separate percentage re-rating range. A hallucination cannot corrupt the forecast.

## The leakage problem, and what was done about it

Locking retrieved evidence to the cutoff is not enough: GLM-5.3 already knows what these
companies did after 2024 from pretraining. So every backtest run also carries an
**adversarial identity probe** — an independent LLM call that is asked to name the company
from the anonymised packet. If it succeeds, the run is marked `valid_for_backtest=false`.

Measured, and this is the reason for the design:

| mode | probe outcome |
| :--- | :--- |
| `numbers_only` (headline) | could not identify MODISONLTD or CUPID (self-confidence 0.1) |
| `with_evidence` | named **"Cupid Limited", confidence 0.92** → run auto-invalidated |

In `with_evidence` mode the Modison thesis also volunteered "silver electrical contacts" —
business descriptions are identifying even after names are scrubbed. Headline validation
therefore runs `numbers_only`. Across 96 LLM blocks: 72% probe-clean, 3% confirmed leak,
25% "suspected" (a distinctive token appeared in the model's reasoning prose but no parsable
guess). `VALIDATION.md` reports the screener numbers both including and excluding these.

## Defects carried over from the previous engine, and their fixes

| defect (previous `MULTI_AGENT_SANDBOX`) | fix here | pinned by |
| :--- | :--- | :--- |
| Silent heuristic fallback; every committed result had `neural_points: 0` | `TimesFMUnavailable`, no fallback path | `test_adapter_refuses_to_predict_without_model` |
| Stop-loss anchored to the *terminal* forecast quantile → −33% stop, 0% allocation on a +49% move | stop derived from a 20-day window + ATR floor, independent of horizon | `test_stop_is_horizon_independent` |
| `p_win` derived from RRR then fed into Kelly using the same RRR (circular) | `p_win` supplied externally from the measured 57.8% hit-rate; defaults to 0.50 | `test_no_evidence_means_coinflip_pwin` |
| Band widening in price space produced a **negative** lower bound (−4125 for a 5193 stock) | conformal calibration in log space | `test_log_space_band_stays_positive` |
| Covariates built, shipped, never consumed | covariates wired in for real, then switched off on evidence | `ABLATION.md` |
| `sanitize_text` defined but never called; audit that could not fail | anonymiser applied to all LLM input + fail-closed packet audit + identity probe | `test_audit_packet_catches_leak` |
| Cherry-picked CUPID as multi-bagger proof | rule-based universe at each cutoff including later losers | `universe.py` |

## Reproducing

```bash
# 1. GPU session
colab --auth=oauth2 new -s timesfm-gpu --gpu T4
colab install -s timesfm-gpu "git+https://github.com/google-research/timesfm.git" exa_py

# 2. CPU-only unit tests (no GPU, no network)
python3 v2/INSTITUTIONAL/tests/test_units.py     # 16 passed

# 3. Walk-forward validation (resumable; ledger survives a lost VM)
export AKASHML_API_KEY=... EXA_API_KEY=... NVIDIA_NIM_API_KEY=...
#   stage 1: parallel LLM pass, stage 2: GPU forecast pass
TIME_BUDGET_S=1500 python3 v2/INSTITUTIONAL/precompute_llm.py
TIME_BUDGET_S=1700 python3 v2/INSTITUTIONAL/run_validation.py
python3 v2/INSTITUTIONAL/analyze_validation.py    # -> VALIDATION.md

# 4. Live forward predictions
HORIZONS=60,252 P_WIN=0.578 python3 v2/INSTITUTIONAL/run_forward.py
```

Credentials are read from the environment only. Nothing is hardcoded and nothing is written
into the repository.

## Known limitations

* **The candidate pool is hand-specified** (36 NSE names, deliberately including later
  losers). Selection *within* the pool is rule-based and point-in-time, but the pool is not a
  survivorship-free census of the market — historical index membership is not available
  through yfinance. Results are evidence about this pool only.
* **PIT fundamentals are thin.** yfinance gives 5 annual periods and often no quarterly income
  statement, so the LLM frequently sees a single reporting period and says so ("single-period
  data" appears in many theses). A vendor with real PIT financials would change this layer
  materially.
* **Single-asset risk only.** No portfolio covariance, no factor exposure, no liquidity
  constraint beyond the universe screen. Frictions are a flat 25 bp round trip.
* **Coverage is right on average, not per name.** Pooled coverage is 77.9% versus 80% nominal,
  but the per-run spread is wide (mean |coverage-80| is 20pp), so an individual band should be
  read as an order-of-magnitude risk range, not a precise interval.
* **Three cutoffs is a small sample.** Six (horizon, cutoff) panels cannot resolve a rank-IC
  of ±0.10. The negative screener result is "no evidence of skill", not "proof of no skill".
* **Backtests use adjusted close** from yfinance, which is itself restated over time.
* The 252-day horizon spans a regime the model never saw in training; treat long-horizon bands
  as scenario ranges, not forecasts.

## Not investment advice

This is research code. It produces probabilistic projections whose headline finding is that
the price-level forecast has no edge over assuming today's price. Do not trade it.
