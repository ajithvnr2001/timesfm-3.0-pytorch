# Evidence Mode Experiment — does anonymised pre-cutoff evidence add skill or leak identity?

LLM blocks: {'numbers_only': 247, 'with_evidence': 247}. Forecasts are identical across modes (494 runs), so any difference comes purely from what the LLM was shown.

## 1. Adversarial identity probe by mode

| mode | clean | suspected | confirmed | any leak |
| :--- | ---: | ---: | ---: | ---: |
| `numbers_only` | 205 (83%) | 37 (15%) | 5 (2%) | **17%** |
| `with_evidence` | 118 (48%) | 38 (15%) | 91 (37%) | **52%** |

## 2. Rank-IC of conviction vs realised forward return, same forecasts

| horizon | cutoff | n | IC numbers_only | IC with_evidence | delta |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 60d | 2022-12-30 | 27 | -0.132 | -0.203 | -0.071 |
| 60d | 2023-06-30 | 27 | -0.171 | -0.148 | +0.023 |
| 60d | 2023-12-29 | 32 | -0.103 | +0.265 | +0.368 |
| 60d | 2024-03-28 | 33 | -0.130 | -0.105 | +0.025 |
| 60d | 2024-06-28 | 33 | +0.254 | +0.231 | -0.022 |
| 60d | 2024-09-30 | 33 | +0.351 | +0.218 | -0.132 |
| 60d | 2024-12-31 | 31 | -0.043 | +0.113 | +0.156 |
| 60d | 2025-06-30 | 31 | -0.010 | +0.023 | +0.033 |
| 252d | 2022-12-30 | 27 | +0.044 | -0.176 | -0.220 |
| 252d | 2023-06-30 | 27 | -0.130 | +0.146 | +0.276 |
| 252d | 2023-12-29 | 32 | +0.109 | +0.240 | +0.131 |
| 252d | 2024-03-28 | 33 | +0.158 | +0.357 | +0.199 |
| 252d | 2024-06-28 | 33 | -0.097 | +0.016 | +0.113 |
| 252d | 2024-09-30 | 33 | +0.185 | +0.058 | -0.127 |
| 252d | 2024-12-31 | 31 | -0.069 | -0.077 | -0.008 |
| 252d | 2025-06-30 | 31 | -0.169 | -0.033 | +0.136 |

* `numbers_only`: mean IC **+0.003**, median -0.056, sd 0.162 across k=16 panels, se 0.041, t=0.07, normal-approx p=0.942, positive in 6/16 panels
* `with_evidence`: mean IC **+0.058**, median +0.040, sd 0.174 across k=16 panels, se 0.043, t=1.33, normal-approx p=0.183, positive in 10/16 panels

## 3. The decisive split: with_evidence IC on probe-clean vs probe-identified runs

| horizon | subset | n | rank-IC | top-quintile fwd | bottom-quintile fwd |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 60d | probe-clean | 118 | +0.011 | +4.2% | +2.9% |
| 60d | probe-identified | 129 | +0.072 | -2.5% | +2.4% |
| 252d | probe-clean | 118 | -0.003 | +38.7% | +44.9% |
| 252d | probe-identified | 129 | -0.072 | +18.8% | +51.8% |

## 4. How much did the evidence move the score?

* 247 paired scores. Mean conviction 33.5 (numbers_only) vs 39.2 (with_evidence); mean absolute change **7.8 points**; rank correlation between modes +0.636.
* Score change is 9.3 points on probe-identified runs versus 6.2 on probe-clean runs.

## Interpretation

Panels: k=16. 252-day panels from adjacent quarterly cutoffs overlap, so the effective sample is smaller than k suggests; treat the 252d rows as correlated.

**History of this result, stated plainly.** An earlier run with only three cutoffs (k=6 panels) measured with_evidence mean IC +0.132 with t=2.32, p=0.021, and the probe-clean subset carried the signal - which looked like genuine, non-leaked skill. Expanding to eight cutoffs (k=16) pulled that to the value in the table above and removed its significance. The earlier figure was a small-sample artefact.

Evidence mode moved mean rank-IC from **+0.003** to **+0.058** while raising the probe leak rate from 17% to 52%.

