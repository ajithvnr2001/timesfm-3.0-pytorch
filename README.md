# TimesFM 3.0 Research, Benchmarking & Live Predictions

Comprehensive research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model across equities, macro indices, derivatives, and live intraday forecasting.

---

## Studies & Predictions

### 1. [Live Intraday NIFTY 50 Forecast (Today: Sep 3, 2026)](INTRADAY/) (`INTRADAY/`)
* **Session**: Thursday, September 3, 2026 (Weekly Options Expiry).
* **Horizon**: **All 7 hourly bars (09:15 AM to 03:30 PM IST)** + 15-minute sub-hourly trajectory.
* **Granular Input**: Multi-timeframe context (1-hour, 15-minute, and 5-minute bars) up to Sep 2 close (**23,914.45**).
* **Key Prediction**: Morning rangebound pinning near **23,900** followed by an afternoon short-covering lift to **23,918 – 23,940**.

### 2. [NIFTY Options & Volatility Study](OPTIONS/) (`OPTIONS/`)
* **Instruments**: Continuous 30-Day Constant Maturity **ATM Calls**, **ATM Puts**, **Straddles**, and **India VIX (`^INDIAVIX`)**.
* **Cutoff Date**: January 31, 2026.
* **Horizon**: **145 trading days** (February 2, 2026 – September 2, 2026).
* **Key Findings**:
  * **ATM Call Option MAPE**: **14.97%** (and **14.21%** in multivariate mode).
  * **80% CI Coverage**: **79.3%** for Calls, **74.5%** for Puts, **77.2%** for Straddles.

### 3. [NIFTY 50 Macro Index Study](NIFTY/) (`NIFTY/`)
* **Asset**: India's benchmark **NIFTY 50 Index (`^NSEI`)**.
* **Cutoff Date**: December 31, 2025 (Closing level: 26,129.60).
* **Horizon**: **164 trading days** (January 1, 2026 – September 2, 2026).
* **Key Findings**:
  * **Overall 8-Month MAPE**: **5.82%** (MAE: 1,388 index points).
  * **Q1 2026 MAPE**: **3.96%**.
  * **80% CI Coverage**: **83.5%** of trading sessions stayed within the predicted $[P_{10}, P_{90}]$ distribution cone.

### 4. [MODISONLTD Microcap Corporate Study](MODISONANALYSIS/) (`MODISONANALYSIS/`)
* **Asset**: Modison Limited (`MODISONLTD.NS` / BSE: `506261`).
* **Cutoff Date**: August 1, 2026 (Closing price: ₹268.40 on July 31, 2026).
* **Horizon**: 23 trading days (August 3, 2026 – September 2, 2026).
* **Key Findings**:
  * Pre-earnings MAPE was **7.27%** (< 5% in week 1).
  * On August 13, 2026, Modison released blowout Q1 FY27 results (Revenue +102%, PAT +605%), sparking a +94% rally to ₹520.65.

---

## Repository Structure

```
timesfm-3.0-pytorch/
├── README.md
├── .gitignore
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

---

## Citations & References
* **TimesFM 3.0**: Google Research ([`google/timesfm-3.0-pytorch`](https://huggingface.co/google/timesfm-3.0-pytorch))
* **TimesFM GitHub**: [google-research/timesfm](https://github.com/google-research/timesfm)
* **Exa MCP Server**: [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server)
