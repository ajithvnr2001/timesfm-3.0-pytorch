# V3 Usage Guide

How to install, run, and read the output of the institutional TimesFM 3.0 engine — plus a
blunt section on what to trust and what to ignore.

Read [`README.md`](README.md) first for the measured results. Short version: the calibrated
uncertainty band works; the price forecast and the LLM conviction score have **no demonstrated
predictive skill**. Use this as a risk instrument, not a stock picker.

---

## 1. What each script is for

| script | what it does | needs GPU | needs LLM keys |
| :--- | :--- | :---: | :---: |
| `tests/test_units.py` | 17 CPU-only correctness tests | no | no |
| `run_ablation.py` | reproduces the configuration ablation | yes | no |
| `precompute_llm.py` | LLM conviction + identity probe, parallel, cached per (ticker, cutoff) | no | yes |
| `run_validation.py` | walk-forward forecasts + metrics into a resumable ledger | yes | no (uses cache) |
| `analyze_validation.py` | ledger → `VALIDATION.md` | no | no |
| `analyze_evidence.py` | ledger → `EVIDENCE_EXPERIMENT.md` (leak vs value) | no | no |
| `run_forward.py` | live forecasts, no cutoff → `FORWARD/` | yes | yes |

Library modules: `timesfm3_adapter.py` (model), `pit_data.py` (data), `calibration.py`
(conformal), `anonymizer.py` + `llm_agents.py` (LLM layer), `risk_sizing.py` (stops/sizing),
`universe.py` (point-in-time screen), `engine.py` (composes one run).

---

## 2. Setup

### Credentials

Everything is read from the environment. Nothing is hardcoded; never commit these.

```bash
export AKASHML_API_KEY="..."      # primary LLM (zai-org/GLM-5.3)
export NVIDIA_NIM_API_KEY="..."   # fallback LLM
export EXA_API_KEY="..."          # only needed for EVIDENCE_MODE=with_evidence
```

Without any LLM key the forecast layer still runs; the conviction block reports
`status: llm_unavailable`.

### Local, CPU only — verify correctness in 10 seconds

```bash
python3 v3/tests/test_units.py     # expect: 17 passed, 0 failed
```

### GPU (Colab T4)

```bash
colab --auth=oauth2 new -s timesfm-gpu --gpu T4
colab install -s timesfm-gpu "git+https://github.com/google-research/timesfm.git" exa_py
```

The model is `google/timesfm-3.0-pytorch`, ~1.32 GB, first load ~25 s, then ~3 s from cache.
Peak GPU memory is ~1.4 GB of 15 GB and a forecast takes <1 s, so the T4 is never the
bottleneck — yfinance and the LLM are.

---

## 3. Running it

### A. One live forecast (the common case)

```bash
export HORIZONS=60,252
export P_WIN=0.5                  # see the warning in section 5
export TICKERS=MODISONLTD.NS,CUPID.NS,INFY.NS,TCS.NS
export OUT_DIR=./v3/FORWARD
python3 v3/run_forward.py
```

Produces `FORWARD/forward_predictions.json` and `FORWARD/FORWARD_REPORT.md`.

### B. Full walk-forward validation

Three stages. The LLM stage is separate because it does not depend on horizon, so it is
computed once per (ticker, cutoff) and reused.

```bash
# stage 1 - LLM blocks (parallel, no GPU). Repeat until "REMAINING:0".
TIME_BUDGET_S=800 MAX_BLOCKS=30 EVIDENCE_MODE=numbers_only \
  LEDGER=./v3/artifacts/ledger.json python3 v3/precompute_llm.py

# stage 2 - GPU forecasts. Repeat until "REMAINING:0".
TIME_BUDGET_S=800 EVIDENCE_MODE=numbers_only \
  LEDGER=./v3/artifacts/ledger.json OUT_DIR=./v3/artifacts python3 v3/run_validation.py

# stage 3 - reports
python3 v3/analyze_validation.py ./v3/artifacts/ledger.json ./v3/VALIDATION.md
python3 v3/analyze_evidence.py   ./v3/artifacts/ledger.json ./v3/EVIDENCE_EXPERIMENT.md
```

Both stages are **resumable**: they skip anything already in the ledger, so re-running after a
crash costs nothing. Cutoffs and horizons are defined at the top of `run_validation.py`.

### C. Surviving a lost Colab VM (important)

Free-tier Colab recycles the VM while the session *name* persists — `exec` then returns
404/401 and `/content` is empty. Downloading the ledger only at the end of a long pass loses
everything, which happened three times during development.

Both stages therefore stream each finished record to stdout as
`##BLOCK##{json}` / `##RUN##{json}`. Capture the full stdout to a file and merge it locally:

```bash
colab exec -s timesfm-gpu -f driver.py --timeout 900 > pass.log 2>&1
python3 merge_stream.py pass.log        # folds ##BLOCK##/##RUN## lines into the local ledger
```

Keep passes short (`MAX_BLOCKS=30`, `TIME_BUDGET_S=800`) so a lost VM costs ~10 minutes.
**Always treat the local ledger as the source of truth** and upload it at the start of each
pass, not the copy on the VM.

---

## 4. Reading the output

A run record contains:

```
forecast.median            point path (do not trade this - see section 5)
forecast.raw_q10 / raw_q90 the model's native 80% band, uncalibrated
forecast.calibrated_low/high  USE THIS - PIT-conformal, log space, always positive
calibration.status         "fitted" means the multiplier came from pre-cutoff origins
calibration.k_low/k_high   how much the native band had to be widened
forecast_provenance        model id, context length, targets, neural_points
pit_audit.leakage_checks   all must be true; the run raises if not
llm.conviction_score       0-100 (no demonstrated skill - section 5)
llm.identity_probe.leak    true => this run is NOT valid for backtesting
risk.stop_level            20-day-window stop, independent of forecast horizon
risk.recommended_alloc_pct half-Kelly capped, uses the p_win you supplied
metrics.*                  only present when a cutoff was given (backtest mode)
```

Sanity checks worth running on any new result:

- `forecast_provenance.neural_points == horizon` and `extrapolated_points == 0` — the real
  model ran end to end.
- `calibration.status == "fitted"` — otherwise the band is the raw, under-covering one.
- `llm.identity_probe.leak == false` for any backtest you intend to believe.
- `pit_audit.leakage_checks` all true.

---

## 5. What to trust, and what to ignore

**Trust: `calibrated_low` / `calibrated_high`.** Pooled coverage is 80.0% against an 80%
nominal band across 494 runs. Caveat: it is right *on average*, and per-name dispersion is
wide (mean |coverage − 80| ≈ 20pp), so read a single band as an order-of-magnitude risk range.

**Ignore: `forecast.median` as a trading signal.** 13.23% mean MAPE versus 12.98% for assuming
the price does not move. Directional accuracy 53.2% (p=0.150) — a coin flip.

**Ignore: `llm.conviction_score` as a ranking signal.** Mean rank-IC +0.003 across 16 panels.
It scored CUPID 38/100 immediately before a +415% move.

**`P_WIN` is a claim, not a setting.** `risk.recommended_alloc_pct` is half-Kelly using the win
probability you pass in. The default is 0.50 because no edge replicated. Setting it higher
asserts an edge this validation does not support, and Kelly sizing on a false edge is how
accounts blow up.

**`EVIDENCE_MODE=with_evidence` is not backtest-safe.** It raises the identity-probe leak rate
from 17% to 52% (confirmed identifications 2% → 37%) and produced no significant IC gain. Use
it for live analysis if you want richer commentary; do not use it to claim historical results.

---

## 6. Troubleshooting

| symptom | cause | fix |
| :--- | :--- | :--- |
| `TimesFMUnavailable` | `timesfm` not installed or checkpoint unreachable | reinstall from the git URL; this is deliberate — there is no heuristic fallback |
| `ModuleNotFoundError` on a file you just uploaded | Colab's kernel cached a negative path lookup | `importlib.invalidate_caches()` and `sys.modules.pop(...)` at the top of the driver |
| Your code edits appear to do nothing | the Colab kernel is persistent and reuses imported modules | pop every project module from `sys.modules` before importing |
| `RuntimeError: size of tensor a ... at dim 2` | covariates passed as `(T, k)` | must be `(k, T)`; `(k, T+H)` for past-future — see `TIMESFM3_API.md` |
| Forecast shape is `[512, 32]` instead of `[H]` | context passed as `(T, V)` | must be `(V, T)`; the wrong orientation is silently accepted |
| `upload` returns HTTP 500 | remote directory does not exist | create it with an `exec` first |
| `TooManyAssignmentsError` on `colab new --gpu T4` | a recycled session still holds the assignment | create the session from your own shell, or wait for it to expire |
| Conviction is `llm_unavailable` | no key, or GLM's reasoning exceeded the token budget | check keys; extraction already scans for the last balanced-brace JSON |
| `insufficient_points` from calibration | not enough pre-cutoff history for rolling origins | needs ~260 + 2×horizon rows; use a later cutoff or shorter horizon |

---

## 7. Extending it

The harness is the reusable part. To test a new signal you only need to produce a per-name
score and let the existing machinery grade it:

1. Add your score to the run record (alongside `llm.conviction_score`).
2. `analyze_validation.py` already computes rank-IC, quintile spreads and hit rates from any
   such field — point it at yours.
3. Report it against the naive/drift/seasonal baselines that are already computed.

The highest-value extension identified so far is to stop forecasting price and forecast
**quarterly fundamentals** (revenue, margins) instead, then feed those into a valuation model.
Price at 60–252 days is near-martingale; revenue has genuine autocorrelation and seasonality,
which is what a time-series foundation model is actually good at. The PIT layer, calibration
and ledger all carry over unchanged.

---

## 8. Not investment advice

Research code. Its headline finding is that the price forecast has no edge over assuming
today's price. Do not trade the median path.
