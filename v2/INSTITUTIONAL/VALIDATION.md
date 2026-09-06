# Walk-Forward Validation — TimesFM 3.0 + Anonymised LLM Screener

Runs completed: **192**  |  errored: 0  |  cutoffs: ['2023-12-29', '2024-06-28', '2024-12-31']  |  horizons: [60, 252]  |  names: 34
Model: `google/timesfm-3.0-pytorch` on `cuda`, context 3154, targets ['stock', 'nifty', 'sector'], neural points = full horizon (no extrapolation).

## 1. Point-forecast skill vs baselines

| horizon | n | TimesFM MAPE (mean / median) | naive | drift | seasonal | beats naive | directional acc |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 60d | 96 | **9.41 / 7.89** | 9.48 / 7.97 | 10.71 | 12.68 | 53% | 57% |
| 252d | 96 | **17.26 / 13.65** | 16.62 / 14.59 | 32.95 | 39.07 | 49% | 58% |

Pooled: TimesFM mean MAPE 13.34% vs naive 13.05% (**+0.29pp**), beats naive on 51% of runs.

Directional accuracy **57.8%** on n=192 runs (z=2.17, two-sided p=0.030 against a 50% coin flip). This is the one component with measurable edge; the level forecast has none.

Against the *trend-following* baselines the model is far ahead at long horizons: 252d mean MAPE 17.3% vs drift 32.9% and seasonal 39.1%. It is the flat random walk specifically that it cannot beat.

## 2. Interval calibration (nominal 80%)

| horizon | n | raw q10-q90 coverage | PIT-conformal coverage | median k_low | median k_high | calibration status |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| 60d | 96 | 74.3% | **76.5%** | 0.84 | 1.35 | 96/96 fitted |
| 252d | 96 | 76.2% | **79.3%** | 0.74 | 1.37 | 96/96 fitted |

Pooled coverage: raw **75.3%** -> calibrated **77.9%** against an 80% nominal band. Absolute miscalibration |coverage-80| improves from 22.4pp to 20.1pp.

## 3. Multi-bagger screener: does the anonymised LLM conviction rank anything?

| horizon | cutoff | n | rank-IC (conviction vs forward return) | top-quintile mean fwd | bottom-quintile mean fwd | spread |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 60d | 2023-12-29 | 32 | -0.103 | +1.4% | +10.7% | -9.3pp |
| 60d | 2024-06-28 | 33 | 0.254 | +10.7% | -4.2% | +14.9pp |
| 60d | 2024-12-31 | 31 | -0.043 | -14.7% | -10.7% | -4.0pp |
| 252d | 2023-12-29 | 32 | 0.109 | +28.5% | +17.3% | +11.1pp |
| 252d | 2024-06-28 | 33 | -0.097 | -4.2% | +9.1% | -13.3pp |
| 252d | 2024-12-31 | 31 | -0.069 | +5.5% | +12.2% | -6.7pp |

Mean rank-IC across 6 (horizon, cutoff) panels: **+0.009** (median -0.056, sd 0.131). Panels with positive IC: 2/6.

## 4. Leakage audit (adversarial identity probe)

LLM blocks: 96. Probe verdicts -> **clean**: 69 (72%), **confirmed**: 3 (3%), **suspected**: 24 (25%)

* `confirmed` = the probe returned a parsed guess containing a distinctive token of the real company name. Those runs are marked `valid_for_backtest=false`.
* `suspected` = no parsable JSON, but a distinctive token appeared in the model's reasoning prose. Conservative, may include false positives.
* `clean` = the probe could not name the company.

Screener recomputed on probe-clean runs only (n=138):

| horizon | n | rank-IC | top-quintile fwd | bottom-quintile fwd |
| :--- | ---: | ---: | ---: | ---: |
| 60d | 69 | -0.110 | -10.4% | -0.7% |
| 252d | 69 | 0.041 | +4.2% | +5.1% |

## 5. Did it find the big winners?

| ticker | cutoff | realised fwd return | conviction | probe | TimesFM predicted move | directive |
| :--- | :--- | ---: | ---: | :--- | ---: | :--- |
| CUPID.NS | 2024-12-31 | **+415.2%** | 38 | clean | -13.7% | UNFAVOURABLE / AVOID |
| RPOWER.NS | 2024-06-28 | **+126.5%** | 25 | clean | -4.7% | UNFAVOURABLE / AVOID |
| ARROWGREEN.NS | 2023-12-29 | **+84.8%** | 30 | clean | 1.2% | NEUTRAL / MONITOR |
| RPOWER.NS | 2023-12-29 | **+81.9%** | 22 | clean | -9.9% | UNFAVOURABLE / AVOID |
| COFORGE.NS | 2024-06-28 | **+79.4%** | 32 | clean | 3.0% | NEUTRAL / MONITOR |
| PERSISTENT.NS | 2023-12-29 | **+69.6%** | 35 | suspected | 13.8% | MILDLY FAVOURABLE |
| SOUTHBANK.NS | 2024-12-31 | **+60.9%** | 48 | clean | 1.1% | NEUTRAL / MONITOR |
| MARUTI.NS | 2024-12-31 | **+59.7%** | 50 | confirmed | 3.8% | NEUTRAL / MONITOR |
| SUZLON.NS | 2023-12-29 | **+57.1%** | 25 | clean | 0.2% | NEUTRAL / MONITOR |
| BHARTIARTL.NS | 2023-12-29 | **+55.8%** | 30 | suspected | -0.7% | NEUTRAL / MONITOR |

