# TimesFM 3.0 Research, Benchmarking & Live Predictions

Comprehensive research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model across equities, macro indices, derivatives, live intraday forecasting, and **Hybrid LLM + TimesFM 3.0 Multi-Shot Systems**.

---

## Studies & Breakthrough Benchmarks

### 1. [Breakthrough: Hybrid LLM + TimesFM 3.0 Multi-Shot Model](HYBRID_MODISON/) (`HYBRID_MODISON/`)
* **Asset**: Modison Limited (`MODISONLTD.NS`).
* **Strict Boundary**: Pre-August 1, 2026 data only (Zero Lookahead).
* **Intelligence Source**: Ingestion of Annual Report FY26 PDF & 43rd AGM Notice.
* **Key Results**:
  * **TimesFM 3.0 Baseline**: Flatlined at **Rs. 275.22** (MAE: Rs. 91.12, MAPE: 22.34%, missed rally by **-47.1%**).
  * **Hybrid LLM + TimesFM 3.0**: Predicted the rally to **Rs. 484.87** (MAE: **Rs. 28.45**, MAPE: **7.68%**, error only **-6.8%** against actual Rs. 520.65!).

### 2. [Live Intraday NIFTY 50 Forecast (Today: Sep 3, 2026)](INTRADAY/) (`INTRADAY/`)
* **Session**: Thursday, September 3, 2026 (Weekly Options Expiry).
* **Horizon**: All 7 hourly bars (09:15 AM to 03:30 PM IST) + 15m sub-hourly trajectory.
* **Key Prediction**: Morning rangebound pinning near **23,900** followed by an afternoon short-covering lift to **23,918 – 23,940**.

### 3. [NIFTY Options & Volatility Study](OPTIONS/) (`OPTIONS/`)
* **Instruments**: Continuous 30-Day Constant Maturity **ATM Calls**, **ATM Puts**, **Straddles**, and **India VIX (`^INDIAVIX`)**.
* **Cutoff Date**: January 31, 2026.
* **Key Findings**: ATM Call Option MAPE of **14.97%** with **79.3%** 80% CI coverage.

### 4. [NIFTY 50 Macro Index Study](NIFTY/) (`NIFTY/`)
* **Asset**: India's benchmark **NIFTY 50 Index (`^NSEI`)**.
* **Cutoff Date**: December 31, 2025.
* **Key Findings**: 8-Month MAPE was **5.82%** (MAE: 1,388 index points) and **83.5%** CI coverage over 164 trading days.

### 5. [MODISONLTD Microcap Corporate Study](MODISONANALYSIS/) (`MODISONANALYSIS/`)
* **Asset**: Modison Limited (`MODISONLTD.NS` / BSE: `506261`).
* **Cutoff Date**: August 1, 2026.
* **Key Findings**: Baseline pure time-series zero-shot evaluation.

---

## Repository Structure

```
timesfm-3.0-pytorch/
├── README.md
├── .gitignore
├── HYBRID_MODISON/                         # Breakthrough: Hybrid LLM + TimesFM 3.0 Model
│   ├── README.md                           # Comprehensive evaluation report
│   ├── timesfm3_hybrid_analysis.ipynb      # Executed Jupyter Notebook
│   ├── timesfm_hybrid_experiment.py        # Standalone GPU execution script
│   ├── timesfm3_hybrid_forecast_vs_actual.png # Benchmark comparison chart
│   └── hybrid_modison_results.json         # Raw predictions, quantiles, and metrics
├── INTRADAY/                               # Live Intraday Hourly Forecast for Today (Sep 3)
│   ├── README.md                           # Hourly trajectory & trading plan
│   ├── timesfm3_intraday_analysis.ipynb    # Executed Jupyter Notebook
│   ├── timesfm_intraday_experiment.py      # Standalone GPU execution script
│   ├── timesfm3_nifty_intraday_sep3_forecast.png # High-resolution intraday forecast chart
│   └── nifty_intraday_results.json         # Raw hourly & 15m predictions and quantiles
├── OPTIONS/                                # NIFTY Options & Volatility Benchmark
│   ├── README.md                           # Detailed evaluation report
│   ├── timesfm3_options_analysis.ipynb     # Interactive, executed Jupyter Notebook
│   ├── timesfm_options_experiment.py       # Standalone GPU execution script
│   ├── timesfm3_options_forecast_vs_actual.png # 4-panel high-resolution benchmark chart
│   └── options_results.json                # Complete point forecasts, quantiles, and metrics
├── NIFTY/                                  # NIFTY 50 8-Month Macro Benchmark
│   ├── README.md                           # Detailed evaluation report
│   ├── timesfm3_nifty_analysis.ipynb       # Interactive, executed Jupyter Notebook
│   ├── timesfm_nifty_experiment.py         # Standalone GPU execution script
│   ├── timesfm3_nifty_forecast_vs_actual.png # High-resolution benchmark chart
│   └── nifty_results.json                  # Complete point forecasts, quantiles, and metrics
└── MODISONANALYSIS/                        # MODISONLTD Corporate Event Benchmark
    ├── README.md                           # Comprehensive evaluation report
    ├── timesfm3_modison_analysis.ipynb     # Interactive, executed Jupyter Notebook
    ├── timesfm_modison_experiment.py       # Standalone GPU execution script
    ├── timesfm3_exa_experiment.py          # Script with Exa event covariates
    ├── timesfm3_forecast_vs_actual.png     # High-resolution benchmark chart
    ├── timesfm_results.json                # JSON dataset of forecasts and metrics
    └── filings/                            # Official BSE PDF filings
```
