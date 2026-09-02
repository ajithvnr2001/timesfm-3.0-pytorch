# TimesFM 3.0 Research & Benchmarking

Comprehensive research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model across equities, macro indices, and corporate event regimes.

---

## Studies & Experiments

### 1. [NIFTY 50 Macro Forecasting Study](NIFTY/) (`NIFTY/`)
* **Asset**: India's benchmark **NIFTY 50 Index (`^NSEI`)**.
* **Cutoff Date**: December 31, 2025 (Closing level: 26,129.60).
* **Horizon**: **164 trading days** (January 1, 2026 – September 2, 2026).
* **Key Findings**:
  * **Overall 8-Month MAPE**: **5.82%** (MAE: 1,388 index points).
  * **Q1 2026 MAPE**: **3.96%**.
  * **80% CI Coverage**: **83.5%** of trading sessions stayed within the model's predicted $[P_{10}, P_{90}]$ distribution envelope.
  * Demonstrates that foundation models excel at broad macroeconomic indices characterized by continuous liquidity and bounded volatility.

### 2. [MODISONLTD Microcap Study](MODISONANALYSIS/) (`MODISONANALYSIS/`)
* **Asset**: Modison Limited (`MODISONLTD.NS` / BSE: `506261`).
* **Cutoff Date**: August 1, 2026 (Closing price: ₹268.40 on July 31, 2026).
* **Horizon**: 23 trading days (August 3, 2026 – September 2, 2026).
* **Key Findings**:
  * Pre-earnings MAPE was **7.27%** (< 5% in week 1).
  * On August 13, 2026, Modison released blowout Q1 FY27 results (Revenue +102%, PAT +605%), sparking a +94% rally to ₹520.65.
  * Illustrates the empirical boundary between statistical autoregressive foundation modeling and exogenous fundamental corporate announcements.

---

## Repository Structure

```
timesfm-3.0-pytorch/
├── README.md
├── .gitignore
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
