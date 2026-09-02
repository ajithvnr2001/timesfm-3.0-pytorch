# TimesFM 3.0 Research, Benchmarking & Live Predictions

Comprehensive research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model across equities, macro indices, derivatives, live intraday forecasting, and **Hybrid LLM + TimesFM 3.0 Multi-Shot Systems**.

---

## 📖 Architectural Guides

### 🌟 [The Comprehensive Architectural Guide: Integrating LLMs with TimesFM 3.0](HYBRID_GUIDE/) (`HYBRID_GUIDE/`)
* **Core Architecture**: How LLM Semantic Reasoning fuses with TimesFM 3.0 Quantitative Cross-Attention.
* **Interactive Notebook**: [`HYBRID_GUIDE/hybrid_agentic_pipeline.ipynb`](HYBRID_GUIDE/hybrid_agentic_pipeline.ipynb) (Interactive, step-by-step multi-asset execution).
* **Enterprise Script**: [`HYBRID_GUIDE/hybrid_agentic_pipeline.py`](HYBRID_GUIDE/hybrid_agentic_pipeline.py) (CLI with `--mode backtest|live`, `--check`, and batch GPU support).
* **Data Ingestion Pipeline**: Numerical market feeds (`yfinance`), BSE/NSE corporate PDF/XML parsing (`pypdf`), and macro intelligence via Exa Neural Search (`exa-py`).
* **The Zero-Leakage Protocol**: Eliminating lookahead bias in backtests (Point-In-Time timestamps, Corporate Action neutrality via Market Cap, and Entity Anonymization "Company X" protocol).
* **Prompt Library**: [`HYBRID_GUIDE/prompts/`](HYBRID_GUIDE/prompts/) (Extraction, Valuation, and Anonymization prompts).
* **1-Click Setup**: Install all dependencies via [`requirements.txt`](requirements.txt).

---

## Studies & Breakthrough Benchmarks

### 1. [Multi-Year Foundation Model Benchmark: CUPID LIMITED](CUPID/) (`CUPID/`)
* **Asset**: Cupid Limited (`CUPID.NS`).
* **Cutoff Date**: December 31, 2023 (Zero Lookahead).
* **Horizon**: **664 trading days (2.7 years)** across 2024, 2025, and 2026.
* **Key Findings**:
  * **TimesFM 3.0 Pure Baseline**: Suffered autoregressive mean decay across 11 rolling patches, collapsing from ₹11.20 to **₹3.59** (**-98.7% error**).
  * **Hybrid LLM + TimesFM 3.0**: Conditioned on Dec 2023 takeover filings and FMCG transformation, achieved a terminal target of **₹259.82** vs actual **₹280.70** (**92.6% terminal accuracy**, error only **-7.4%**).

### 2. [Breakthrough: Hybrid LLM + TimesFM 3.0 Multi-Shot Model](HYBRID_MODISON/) (`HYBRID_MODISON/`)
* **Asset**: Modison Limited (`MODISONLTD.NS`).
* **Strict Boundary**: Pre-August 1, 2026 data only (Zero Lookahead).
* **Intelligence Source**: Ingestion of Annual Report FY26 PDF & 43rd AGM Notice.
* **Key Results**:
  * **TimesFM 3.0 Baseline**: Flatlined at **₹275.22** (MAE: ₹91.12, MAPE: 22.34%, missed rally by **-47.1%**).
  * **Hybrid LLM + TimesFM 3.0**: Predicted the rally to **₹484.87** (MAE: **₹28.45**, MAPE: **7.68%**, error only **-6.8%** against actual ₹520.65!).

### 3. [Live Intraday NIFTY 50 Forecast (Today: Sep 3, 2026)](INTRADAY/) (`INTRADAY/`)
* **Session**: Thursday, September 3, 2026 (Weekly Options Expiry).
* **Horizon**: All 7 hourly bars (09:15 AM to 03:30 PM IST) + 15m sub-hourly trajectory.
* **Key Prediction**: Morning rangebound pinning near **23,900** followed by an afternoon short-covering lift to **23,918 – 23,940**.

### 4. [NIFTY Options & Volatility Study](OPTIONS/) (`OPTIONS/`)
* **Instruments**: Continuous 30-Day Constant Maturity **ATM Calls**, **ATM Puts**, **Straddles**, and **India VIX (`^INDIAVIX`)**.
* **Cutoff Date**: January 31, 2026.
* **Key Findings**: ATM Call Option MAPE of **14.97%** with **79.3%** 80% CI coverage.

### 5. [NIFTY 50 Macro Index Study](NIFTY/) (`NIFTY/`)
* **Asset**: India's benchmark **NIFTY 50 Index (`^NSEI`)**.
* **Cutoff Date**: December 31, 2025.
* **Key Findings**: 8-Month MAPE was **5.82%** (MAE: 1,388 index points) and **83.5%** CI coverage over 164 trading days.

### 6. [MODISONLTD Microcap Corporate Study](MODISONANALYSIS/) (`MODISONANALYSIS/`)
* **Asset**: Modison Limited (`MODISONLTD.NS` / BSE: `506261`).
* **Cutoff Date**: August 1, 2026.
* **Key Findings**: Baseline pure time-series zero-shot evaluation.

---

## Repository Structure

```
timesfm-3.0-pytorch/
├── README.md
├── .gitignore
├── HYBRID_GUIDE/                           # Comprehensive Architectural & Best Practices Guide
│   └── README.md                           # In-depth guide on LLM+TimesFM integration & leak-free backtesting
├── CUPID/                                  # Multi-Year Benchmark (2024 to Sep 2026, 664 Days)
│   ├── README.md                           # Comprehensive evaluation report
│   ├── timesfm3_cupid_analysis.ipynb       # Executed Jupyter Notebook
│   ├── timesfm_cupid_experiment.py         # Standalone GPU execution script
│   ├── timesfm3_cupid_multiyear_forecast.png # High-resolution benchmark chart
│   └── cupid_multiyear_results.json        # Raw multi-year predictions and metrics
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
