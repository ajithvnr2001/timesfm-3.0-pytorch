# Forward Predictions (live, no cutoff)

Generated 2026-09-06 17:46 UTC | model `google/timesfm-3.0-pytorch` on `cuda` | Kelly win probability = 0.58 (walk-forward directional hit-rate)

> These are probabilistic projections, not advice. The walk-forward study found this model has **no edge over a random walk on price level** and only a modest directional edge, so the calibrated band matters more than the median path.

## Horizon 60 trading days

| ticker | spot | median | 80% band | exp. move | stop | R:R | conviction | alloc | directive |
| :--- | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| HEROMOTOCO.NS | 4838.7 | 4868.8 | 4256 – 6380 | +0.6% | 4504.2 (-6.9%) | 0.05 | 62.0 | 0.0% | NEUTRAL / MONITOR |
| MODISONLTD.NS | 295.4 | 242.2 | 162 – 471 | -18.0% | 221.6 (-25.0%) | 0.00 | 56.5 | 0.0% | UNFAVOURABLE / AVOID |
| CGPOWER.NS | 905.0 | 880.6 | 733 – 1115 | -2.7% | 804.6 (-11.1%) | 0.00 | 56.5 | 0.0% | NEUTRAL / MONITOR |
| HAL.NS | 4491.6 | 4642.5 | 3940 – 5243 | +3.4% | 4131.9 (-8.0%) | 0.39 | 53.5 | 0.0% | NEUTRAL / MONITOR |
| POLYCAB.NS | 8862.0 | 9025.7 | 6926 – 10668 | +1.9% | 7532.5 (-15.0%) | 0.11 | 53.5 | 0.0% | NEUTRAL / MONITOR |
| CUPID.NS | 214.8 | 255.8 | 178 – 522 | +19.1% | 197.5 (-8.0%) | 2.35 | 45.0 | 12.0% | FAVOURABLE RISK/REWARD |
| NETWEB.NS | 5193.0 | 4779.1 | 3803 – 9520 | -8.0% | 4489.3 (-13.6%) | 0.00 | 43.5 | 0.0% | UNFAVOURABLE / AVOID |
| ARROWGREEN.NS | 814.1 | 776.0 | 501 – 1373 | -4.7% | 629.5 (-22.7%) | 0.00 | 36.5 | 0.0% | UNFAVOURABLE / AVOID |
| TCS.NS | 2304.0 | 2391.9 | 1685 – 2690 | +3.8% | 2001.5 (-13.1%) | 0.27 | 36.0 | 0.0% | NEUTRAL / MONITOR |
| INFY.NS | 1130.0 | 1180.4 | 813 – 1299 | +4.5% | 973.1 (-13.9%) | 0.30 | 30.0 | 0.0% | NEUTRAL / MONITOR |

## Horizon 252 trading days

| ticker | spot | median | 80% band | exp. move | stop | R:R | conviction | alloc | directive |
| :--- | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| HEROMOTOCO.NS | 4838.7 | 4885.0 | 3455 – 9400 | +1.0% | 4458.8 (-7.8%) | 0.09 | 62.0 | 0.0% | NEUTRAL / MONITOR |
| MODISONLTD.NS | 295.4 | 195.8 | 106 – 764 | -33.7% | 221.6 (-25.0%) | 0.00 | 56.5 | 0.0% | UNFAVOURABLE / AVOID |
| CGPOWER.NS | 905.0 | 838.5 | 579 – 1335 | -7.3% | 817.3 (-9.7%) | 0.00 | 56.5 | 0.0% | UNFAVOURABLE / AVOID |
| HAL.NS | 4491.6 | 5116.0 | 4182 – 8138 | +13.9% | 4266.6 (-5.0%) | 2.73 | 53.5 | 12.0% | FAVOURABLE RISK/REWARD |
| POLYCAB.NS | 8862.0 | 9815.5 | 6071 – 18623 | +10.8% | 7166.9 (-19.1%) | 0.55 | 53.5 | 0.0% | NEUTRAL / MONITOR |
| CUPID.NS | 214.8 | 265.8 | 120 – 1146 | +23.8% | 192.5 (-10.4%) | 2.27 | 45.0 | 12.0% | FAVOURABLE RISK/REWARD |
| NETWEB.NS | 5193.0 | 4034.6 | 907 – 14364 | -22.3% | 3781.0 (-27.2%) | 0.00 | 43.5 | 0.0% | UNFAVOURABLE / AVOID |
| ARROWGREEN.NS | 814.1 | 692.8 | 369 – 2104 | -14.9% | 681.3 (-16.3%) | 0.00 | 36.5 | 0.0% | UNFAVOURABLE / AVOID |
| TCS.NS | 2304.0 | 2545.1 | 1419 – 3420 | +10.5% | 2001.5 (-13.1%) | 0.78 | 36.0 | 1.8% | NEUTRAL / MONITOR |
| INFY.NS | 1130.0 | 1199.8 | 734 – 1597 | +6.2% | 1001.0 (-11.4%) | 0.52 | 30.0 | 0.0% | NEUTRAL / MONITOR |

## Anonymised LLM theses

* **MODISONLTD.NS** (conviction 56.5, probe leak: False): Genuine earnings accelerator: revenue and EPS both accelerating, margins up ~10pp, ROE 26%. But parabolic 3-month move means multiple expansion is largely spent; forward returns must come from earnings delivery, not rerating.
* **CUPID.NS** (conviction 45.0, probe leak: False): Genuinely accelerating consumer compounder: revenue and EPS accelerating, margins expanding, debt-light 24% ROE. But after ~10x in twelve months near highs, valuation already prices perfection; earnings growth likely offset by multiple compression.
* **INFY.NS** (conviction 30.0, probe leak: True): High-ROE, low-leverage IT business with stable but slow growth and mild margin erosion. Deep 12-month drawdown may overdiscount intact fundamentals, offering mean-reversion value, though no acceleration or expansion catalyst supports multi-bagger upside.
* **TCS.NS** (conviction 36.0, probe leak: False): High-ROE, low-leverage IT business derated ~28% despite only mild fundamental softness. Re-rating case rests on multiple mean-reversion with stable margins, not earnings acceleration; slow-growth profile caps upside.
* **NETWEB.NS** (conviction 43.5, probe leak: False): Hypergrowth compounder (91% revenue, 80% EPS, 28.5% ROE) but margins compressing and price already up 5x in 3 years near highs. Future returns must come from earnings delivery, not multiple expansion.
* **HEROMOTOCO.NS** (conviction 62.0, probe leak: True): Quality compounder: accelerating revenue and EPS, +3pp margin gain, 26.6% ROE on near-zero leverage. 21% drawdown offers entry, but 85% three-year run plus absent valuation and orderbook evidence caps re-rating confidence.
* **HAL.NS** (conviction 53.5, probe leak: False): High-margin, debt-free compounder with 22% ROE and 5.7pp margin gains, but EPS growth is decelerating and capacity/order evidence is absent. Consolidation after a 150% three-year run offers entry only if growth re-accelerates.
* **CGPOWER.NS** (conviction 56.5, probe leak: False): Debt-free compounder with accelerating revenue and EPS; earnings momentum is real but margins compressed over three years and the multiple has already re-rated sharply. Returns must now come from earnings delivery.
* **POLYCAB.NS** (conviction 53.5, probe leak: False): Genuine compounder: ~28% revenue/EPS growth with mild acceleration, 22% ROE, modest leverage. But after a 152% three-year run, multiple expansion is largely spent; forward returns must come from earnings delivery, not rerating.
* **ARROWGREEN.NS** (conviction 36.5, probe leak: False): High-quality ex-compounder (54% EPS CAGR, +11pp margins, debt-free) now in earnings downturn; price at highs after +53% quarter implies recovery pre-priced. Awaiting earnings trough confirmation.

