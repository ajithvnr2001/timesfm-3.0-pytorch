# Evidence Mode Experiment — does anonymised pre-cutoff evidence add skill or leak identity?

LLM blocks: {'numbers_only': 96, 'with_evidence': 96}. Forecasts are identical across modes (192 runs), so any difference comes purely from what the LLM was shown.

## 1. Adversarial identity probe by mode

| mode | clean | suspected | confirmed | any leak |
| :--- | ---: | ---: | ---: | ---: |
| `numbers_only` | 69 (72%) | 24 (25%) | 3 (3%) | **28%** |
| `with_evidence` | 47 (49%) | 13 (14%) | 36 (38%) | **51%** |

## 2. Rank-IC of conviction vs realised forward return, same forecasts

| horizon | cutoff | n | IC numbers_only | IC with_evidence | delta |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 60d | 2023-12-29 | 32 | -0.103 | +0.265 | +0.368 |
| 60d | 2024-06-28 | 33 | +0.254 | +0.231 | -0.022 |
| 60d | 2024-12-31 | 31 | -0.043 | +0.113 | +0.156 |
| 252d | 2023-12-29 | 32 | +0.109 | +0.240 | +0.131 |
| 252d | 2024-06-28 | 33 | -0.097 | +0.016 | +0.113 |
| 252d | 2024-12-31 | 31 | -0.069 | -0.077 | -0.008 |

* `numbers_only`: mean IC **+0.009**, median -0.056, sd 0.143 across k=6 panels, se 0.058, t=0.15, normal-approx p=0.884, positive in 2/6 panels
* `with_evidence`: mean IC **+0.132**, median +0.172, sd 0.139 across k=6 panels, se 0.057, t=2.32, normal-approx p=0.021, positive in 5/6 panels

## 3. The decisive split: with_evidence IC on probe-clean vs probe-identified runs

| horizon | subset | n | rank-IC | top-quintile fwd | bottom-quintile fwd |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 60d | probe-clean | 47 | +0.091 | -1.7% | +0.5% |
| 60d | probe-identified | 49 | +0.068 | -4.2% | +3.5% |
| 252d | probe-clean | 47 | +0.114 | +18.5% | +15.0% |
| 252d | probe-identified | 49 | -0.138 | -1.2% | +4.6% |

## 4. How much did the evidence move the score?

* 96 paired scores. Mean conviction 34.5 (numbers_only) vs 39.6 (with_evidence); mean absolute change **7.2 points**; rank correlation between modes +0.630.
* Score change is 8.9 points on probe-identified runs versus 5.5 on probe-clean runs.

## Interpretation

Read this cautiously: k=6 panels is a small sample, the panels overlap in time (adjacent 252-day windows share most of their return path), and this is a single pre-specified test rather than a survey. The result is suggestive, not established. The natural check is more, non-overlapping cutoffs.

Evidence mode moved mean rank-IC from **+0.009** to **+0.132** while raising the probe leak rate from 28% to 51%.

