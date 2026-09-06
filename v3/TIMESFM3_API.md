# TimesFM 3.0 — Verified API Contract (probed on Colab T4, 2026-09-06)

Everything below was measured by running the real model on a Tesla T4 (15360 MiB, driver 580.82.07,
torch 2.11.0+cu128, python 3.13). Probe scripts: `probe_timesfm_contract.py`, `bench_timesfm.py`.
Raw output: `TIMESFM3_PROBE.json`, `TIMESFM3_BENCH.json`.

## Package and loader

```python
import timesfm
fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cuda")
```

* Installed via `pip install git+https://github.com/google-research/timesfm.git`
* Exposed symbols: `TimesFM3Forecaster`, `TimesFM3Torch`, `TimesFM_2p5_200M_torch`, `ForecastConfig`
* Weights: `model.safetensors` 1.32 GB; cold load **24.7 s** on T4
* `TimesFM3Forecaster` members: `from_pretrained`, `predict`, `predict_batch`, `global_context`

## predict signature (verified)

```python
fc.predict(
    context,                      # np.ndarray  (T,) univariate  OR  (V, T) multivariate
    horizon,                      # int, single forward pass (663 verified)
    past_only_covariates=None,    # np.ndarray (k, T)      <-- (k, T), NOT (T, k)
    past_future_covariates=None,  # np.ndarray (k, T + H)  <-- (k, T+H), NOT (T+H, k)
    ts_id=None,
    return_quantiles=False,
    use_symmetric_averaging=False,
    make_positive=False,
    sort_quantiles=True,
    use_znorm=False,
    padding_mode="none",
) -> ForecastOutput
```

`predict_batch(contexts: list[np.ndarray], horizon, past_only_covariates: list, past_future_covariates: list, ...) -> Iterator[ForecastOutput]`

## ForecastOutput

| field | shape (univariate) | shape (V targets) |
| :--- | :--- | :--- |
| `forecast` | `[H]` | `[V, H]` |
| `quantiles` | `[H, 9]` | `[V, H, 9]` |
| `ts_id` | passthrough | passthrough |

**Quantile layout (verified monotone increasing along the last axis):**
index `0 → q10`, `1 → q20`, … `4 → q50 (median)`, … `8 → q90`.
So `q[:, 0]` is the 10th percentile and `q[:, 8]` is the 90th percentile.

## Shape rules learned the hard way

| attempt | result |
| :--- | :--- |
| `past_only_covariates` as `(T, k)` | `RuntimeError: size of tensor a (2) must match tensor b (512) at dim 2` |
| `past_only_covariates` as `(k, T)` | OK |
| `past_future_covariates` as `(T+H, k)` | `ValueError: Decode function requires horizon > 0.` |
| `past_future_covariates` as `(k, T+H)` | OK |
| `context` as `(V, T)` | OK → forecast `[V, H]` (true multivariate, one pass) |
| `context` as `(T, V)` | "accepted" but silently treats T as the variate axis → forecast `[512, 32]`. **Never pass this.** |

## Measured cost on T4 (all `ok: true`)

| config | context | horizon | past cov | past-future cov | targets | secs | peak GPU MB |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| uni | 512 | 60 | 0 | 0 | 1 | 0.20 | 1333 |
| uni | 2048 | 252 | 0 | 0 | 1 | 0.31 | 1337 |
| uni | 8192 | 252 | 0 | 0 | 1 | 0.76 | 1351 |
| uni | 2048 | 663 | 0 | 0 | 1 | 0.41 | 1338 |
| cov | 2048 | 252 | 7 | 3 | 1 | 0.41 | 1380 |
| cov | 4096 | 252 | 7 | 3 | 1 | 0.64 | 1423 |
| multi | 2048 | 252 | 0 | 0 | 3 | 0.28 | 1348 |
| multi+cov | 2048 | 252 | 4 | 0 | 3 | 0.32 | 1363 |

Context lengths 512 / 1024 / 2048 / 4096 / 8192 / 16384 all accepted.

## Production settings chosen for this repo

* `context = min(4096, len(pit_history))` — 4096 trading days ≈ 16 years, covers the full listed
  history of every name in our universe; 8192/16384 buys nothing for Indian equities.
* Multivariate targets `(V, T)` = `[stock, NIFTY 50, sector index]` so cross-asset structure is
  handled by the model's variate attention instead of being bolted on afterwards.
* 7 past-only covariates + 3 past-future covariates (see `pit_data.build_covariates`).
* `return_quantiles=True` always; `q[:,0]`/`q[:,8]` become the reported 80% interval.
* `sort_quantiles=True` to guarantee no quantile crossing.
* A T4 run costs <1 s of GPU per (ticker, cutoff, horizon), so the walk-forward harness is
  bounded by yfinance/LLM latency, not by the model.
