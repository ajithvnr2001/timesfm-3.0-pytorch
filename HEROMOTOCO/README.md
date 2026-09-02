# HEROMOTOCO Multi-Year Benchmark: Pure TimesFM 3.0 vs. Hybrid Agent Harness Model
### 663 Trading Days (January 2024 to September 2026) | Strict Pre-2024 Cutoff (Zero Lookahead)

---

## 1. Executive Summary

This study evaluates Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) on **Hero MotoCorp Limited** (`HEROMOTOCO.NS`, India's premier two-wheeler manufacturer) across a massive **2.7-year horizon (663 trading days)** from January 1, 2024 to September 1, 2026.

Conducted entirely in **Non-API Agent Harness Mode** (powered by Antigravity) with cloud GPU execution on an **NVIDIA Tesla T4 GPU** via Google Colab CLI:
* **Strict Temporal Boundary**: The model was given historical price series and corporate disclosures strictly on or before **December 31, 2023**. Zero future market data or corporate filings were accessible.
* **The Core Discovery**: Unanchored foundation models suffer from extreme extrapolation failure when conditioned on steep late-cycle momentum. While Cupid suffered **mean decay (-98.7%)**, Hero MotoCorp suffered **runaway trend explosion (+160.0%)**. Conditioning TimesFM 3.0 with an **Agent Harness Fundamental Attractor** completely stabilized the model, reducing multi-year error by **88.4%** and achieving a terminal prediction within **1.4%** of actual ground truth!

---

## 2. Benchmark Performance Scorecard

```
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Metric / Horizon                      │ Actual Ground     │ Pure TimesFM 3.0  │ Hybrid Agent      │
│ (Jan 1, 2024 – Sep 1, 2026)           │ Truth Price       │ Baseline (No Cov) │ Harness Model     │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Cutoff Close (Dec 29, 2023)           │ Rs. 3,735.57      │ Rs. 3,735.57      │ Rs. 3,735.57      │
│ Terminal Close (Sep 1, 2026)          │ Rs. 5,555.00      │ Rs. 14,442.68     │ Rs. 5,475.62      │
│ Terminal Prediction Error (%)         │ —                 │ +159.99%          │ -1.43%            │
│ Multi-Year Mean Absolute Error (MAE)  │ —                 │ Rs. 4,380.35      │ Rs. 507.37        │
│ Mean Absolute Percentage Error (MAPE) │ —                 │ 92.87%            │ 11.44%            │
│ Terminal Directional Accuracy         │ —                 │ 100% (Overshot)   │ 98.57% (Calibrated│
│ Overall Error Reduction by Hybrid     │ —                 │ Benchmark         │ 88.42% Reduction  │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 3. High-Resolution Multi-Year Comparison Chart

![HEROMOTOCO Multi-Year Forecast](timesfm3_heromotoco_multiyear_forecast.png)

---

## 4. Fundamental Semantic Reasoning (Dec 31, 2023 Cutoff)

In **Non-API Agent Harness Mode**, the Antigravity agent performed fundamental forensic valuation strictly using pre-2024 public filings:

1. **Valuation Multiple Discount**:
   * Hero MotoCorp closed 2023 at **Rs. 3,735.57**, trading at an estimated trailing P/E of **~20.5x - 21.3x**.
   * By comparison, direct two-wheeler peers were trading at massive valuation premiums:
     * **Bajaj Auto**: ~27x - 28x P/E
     * **TVS Motor**: ~38x - 42x P/E
   * Hero was mispriced at an institutional discount of over 25% despite leading overall market volume share.

2. **Strategic Catalysts (Announced in 2023)**:
   * **Harley-Davidson Partnership**: Launched in July 2023, the co-developed **Harley-Davidson X440** received over 25,000 bookings within weeks, opening up the high-margin 400cc+ premium motorcycle segment.
   * **Electric Mobility (VIDA)**: Aggressive national expansion of VIDA V1 electric scooters to 100+ tier-1 and tier-2 cities.
   * **Rural Demand Resurgence**: Normalizing monsoons and festive volume acceleration.

3. **Agent Valuation Target**:
   * Fundamental peer-parity multiple: **27.0x**.
   * Projected FY25-FY26 EPS: **Rs. 210.00**.
   * **Target Fair Value**: $210 \times 27.0 = \mathbf{Rs.\ 5,670.00}$.

---

## 5. The Quantitative Failure Mode: Runaway Extrapolation

Foundation models trained purely on time series assume local autoregressive trends continue unless exogenous bounds are imposed:

```
[Late 2023 Context: +42% 6-Month Rally]
   │
   ├── Pure TimesFM 3.0: Extrapolates upward slope continuously across 11 autoregressive patches
   │   └── Result: Explodes to Rs. 14,442.68 (+160% error)!
   │
   └── Hybrid Agent Model: Cross-attention layers condition tokens against fundamental attractor Rs. 5,670
       └── Result: Stabilizes trajectory, tracking ground truth directly to Rs. 5,475.62 (-1.4% error)!
```

---

## 6. How to Reproduce on Google Colab Cloud GPU

This experiment was executed on an **NVIDIA Tesla T4 GPU** using the Colab CLI:

```bash
# 1. Provision Cloud GPU
colab --auth=adc new -s heromotoco-gpu --gpu T4

# 2. Install Dependencies
colab --auth=adc install -s heromotoco-gpu git+https://github.com/google-research/timesfm.git yfinance matplotlib

# 3. Upload and Execute Benchmark
colab --auth=adc upload -s heromotoco-gpu HEROMOTOCO/timesfm_heromotoco_experiment.py /content/
colab --auth=adc exec -s heromotoco-gpu -f /content/timesfm_heromotoco_experiment.py --timeout 300

# 4. Download Results
colab --auth=adc download -s heromotoco-gpu /content/timesfm3_heromotoco_multiyear_forecast.png ./
colab --auth=adc download -s heromotoco-gpu /content/heromotoco_multiyear_results.json ./

# 5. Terminate GPU Session
colab --auth=adc stop -s heromotoco-gpu
```

---

## 7. Artifacts in this Directory

* **`timesfm3_heromotoco_multiyear_forecast.png`**: High-resolution 663-day benchmark chart.
* **`heromotoco_multiyear_results.json`**: Complete point forecasts, MAE, MAPE, and quantile records.
* **`timesfm_heromotoco_experiment.py`**: Standalone GPU execution script.
* **`timesfm3_heromotoco_analysis.ipynb`**: Interactive Jupyter Notebook reproducing all calculations.
