# Walk-Forward Validation — TimesFM 3.0 + Anonymised LLM Screener

Runs completed: **494**  |  errored: 0  |  cutoffs: ['2022-12-30', '2023-06-30', '2023-12-29', '2024-03-28', '2024-06-28', '2024-09-30', '2024-12-31', '2025-06-30']  |  horizons: [60, 252]  |  names: 35
Model: `google/timesfm-3.0-pytorch` on `cuda`, context 3154, targets ['stock', 'nifty', 'sector'], neural points = full horizon (no extrapolation).

## 0. Panel design

60 trading days is roughly one quarter, so quarterly cutoffs give near-independent 60d panels and all of them are used. 252-day windows from adjacent quarterly cutoffs share ~80% of their return path, so for the 252d horizon the **headline** uses only the annually spaced, non-overlapping subset `['2022-12-30', '2023-12-29', '2024-12-31']`; the full overlapping set is reported alongside and flagged, because its panels are correlated and its effective sample size is smaller than n suggests.

## 1. Point-forecast skill vs baselines

| horizon | n | TimesFM MAPE (mean / median) | naive | drift | seasonal | beats naive | directional acc |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 60d | 247 | **8.81 / 6.77** | 8.76 / 6.80 | 10.67 | 12.85 | 51% | 52% |
| 252d non-overlapping | 90 | **17.01 / 15.06** | 16.47 / 14.74 | 25.17 | 25.02 | 48% | 56% |
| 252d all cutoffs (overlapping) | 247 | **17.64 / 14.92** | 17.20 / 14.41 | 31.46 | 36.64 | 49% | 55% |

Pooled: TimesFM mean MAPE 13.23% vs naive 12.98% (**+0.25pp**), beats naive on 50% of runs.

Directional accuracy **53.2%** on n=494 runs (z=1.44, two-sided p=0.150 against a 50% coin flip) - NOT statistically significant.

> An earlier, smaller version of this study (n=192, three cutoffs) measured 57.8% with p=0.030 and the docs described it as the model's one real edge. Expanding to 494 runs across eight cutoffs pulled it back to 53.2% with p=0.150. The original figure was a small-sample artefact. The honest conclusion is that **no component of the point forecast has demonstrated skill** on this data; only the calibrated interval survives scrutiny.


Against the *trend-following* baselines the model is far ahead at long horizons: 252d mean MAPE 17.6% vs drift 31.5% and seasonal 36.6%. It is the flat random walk specifically that it cannot beat.

## 2. Interval calibration (nominal 80%)

| horizon | n | raw q10-q90 coverage | PIT-conformal coverage | median k_low | median k_high | calibration status |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| 60d | 247 | 79.0% | **80.5%** | 0.87 | 1.28 | 247/247 fitted |
| 252d | 247 | 76.6% | **79.5%** | 0.81 | 1.37 | 245/247 fitted |

Pooled coverage: raw **77.8%** -> calibrated **80.0%** against an 80% nominal band. Absolute miscalibration |coverage-80| improves from 20.9pp to 20.2pp.

## 3. Multi-bagger screener: does the anonymised LLM conviction rank anything?

| horizon | cutoff | n | rank-IC (conviction vs forward return) | top-quintile mean fwd | bottom-quintile mean fwd | spread |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 60d | 2022-12-30 | 27 | -0.132 | -15.7% | -9.0% | -6.6pp |
| 60d | 2023-06-30 | 27 | -0.171 | +15.1% | +19.7% | -4.6pp |
| 60d | 2023-12-29 | 32 | -0.103 | +1.4% | +10.7% | -9.3pp |
| 60d | 2024-03-28 | 33 | -0.130 | +12.9% | +13.3% | -0.4pp |
| 60d | 2024-06-28 | 33 | 0.254 | +10.7% | -4.2% | +14.9pp |
| 60d | 2024-09-30 | 33 | 0.351 | -9.1% | -15.1% | +6.0pp |
| 60d | 2024-12-31 | 31 | -0.043 | -14.7% | -10.7% | -4.0pp |
| 60d | 2025-06-30 | 31 | -0.010 | -1.7% | +17.7% | -19.4pp |
| 252d | 2022-12-30 | 27 | 0.044 | +93.2% | +32.5% | +60.7pp |
| 252d | 2023-06-30 | 27 | -0.130 | +102.4% | +96.9% | +5.6pp |
| 252d | 2023-12-29 | 32 | 0.109 | +28.5% | +17.3% | +11.1pp |
| 252d | 2024-03-28 | 33 | 0.158 | -2.3% | -3.0% | +0.6pp |
| 252d | 2024-06-28 | 33 | -0.097 | -4.2% | +9.1% | -13.3pp |
| 252d | 2024-09-30 | 33 | 0.185 | +1.6% | -10.2% | +11.8pp |
| 252d | 2024-12-31 | 31 | -0.069 | +5.5% | +12.2% | -6.7pp |
| 252d | 2025-06-30 | 31 | -0.169 | -17.7% | +212.9% | -230.5pp |

Mean rank-IC across 16 (horizon, cutoff) panels: **+0.003** (median -0.056, sd 0.157). Panels with positive IC: 6/16.

## 4. Leakage audit (adversarial identity probe)

LLM blocks: 494. Probe verdicts -> **clean**: 323 (65%), **confirmed**: 96 (19%), **suspected**: 75 (15%)

* `confirmed` = the probe returned a parsed guess containing a distinctive token of the real company name. Those runs are marked `valid_for_backtest=false`.
* `suspected` = no parsable JSON, but a distinctive token appeared in the model's reasoning prose. Conservative, may include false positives.
* `clean` = the probe could not name the company.

Screener recomputed on probe-clean runs only (n=410):

| horizon | n | rank-IC | top-quintile fwd | bottom-quintile fwd |
| :--- | ---: | ---: | ---: | ---: |
| 60d | 205 | -0.011 | +0.1% | -1.5% |
| 252d | 205 | -0.156 | +15.9% | +58.0% |

## 5. Did it find the big winners?

| ticker | cutoff | realised fwd return | conviction | probe | TimesFM predicted move | directive |
| :--- | :--- | ---: | ---: | :--- | ---: | :--- |
| CUPID.NS | 2025-06-30 | **+824.7%** | 25 | clean | -21.4% | UNFAVOURABLE / AVOID |
| STLTECH.NS | 2025-06-30 | **+448.1%** | 15 | clean | -11.1% | UNFAVOURABLE / AVOID |
| CUPID.NS | 2024-12-31 | **+415.2%** | 38 | clean | -13.7% | UNFAVOURABLE / AVOID |
| MTARTECH.NS | 2025-06-30 | **+343.3%** | 30 | clean | 5.8% | NEUTRAL / MONITOR |
| SUZLON.NS | 2022-12-30 | **+310.8%** | 25 | clean | 0.4% | NEUTRAL / MONITOR |
| BHEL.NS | 2023-06-30 | **+281.1%** | 25 | clean | -2.6% | NEUTRAL / MONITOR |
| SUZLON.NS | 2023-06-30 | **+257.6%** | 30 | clean | 0.1% | NEUTRAL / MONITOR |
| HAL.NS | 2023-06-30 | **+195.8%** | 45 | clean | -7.2% | UNFAVOURABLE / AVOID |
| BEL.NS | 2023-06-30 | **+170.0%** | 45 | clean | -0.7% | NEUTRAL / MONITOR |
| CUPID.NS | 2024-09-30 | **+163.6%** | 35 | clean | -13.9% | UNFAVOURABLE / AVOID |

