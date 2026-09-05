# TimesFM 3.0 Research, Benchmarking & Live Predictions

Comprehensive research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model across equities, macro indices, derivatives, live intraday forecasting, and **Hybrid LLM + TimesFM 3.0 Multi-Shot Systems**.

---

## 📚 Master Documentation Suite

| Guide | Target Audience / Objective | Core Content |
| :--- | :--- | :--- |
| 🌟 **[USER_GUIDE.md](guides%26docs/USER_GUIDE.md)** | **Traders, Investors & Portfolio Managers** | Non-technical manual, interpreting Bear/Base/Bull scenarios, Scenario Envelope Coverage, and capital risk management. |
| 🌟 **[DEVELOPER_GUIDE.md](guides%26docs/DEVELOPER_GUIDE.md)** | **Software Engineers & Quants** | Internal class hierarchy, PyTorch tensor contracts, adding new data feeds, Docker/Kubernetes sandboxing, and CI testing. |
| 🌟 **[LLM_GUIDE.md](guides%26docs/LLM_GUIDE.md)** | **AI Agents (Claude, ChatGPT, Gemini, Codex)** | Universal meta-prompt allowing any cloned AI assistant to understand and autonomously execute the system end-to-end. |
| 🌟 **[MODES_GUIDE.md](guides%26docs/MODES_GUIDE.md)** | **System Operators** | Detailed walkthrough of the 4 modes: `multi-agent`, `backtest`, `live`, and `intraday`. |
| 🌟 **[llm.md](guides%26docs/llm.md)** | **Autonomous LLMs & Colab Operations** | Complete operational manual, API configurations, Colab CLI instructions, and end-to-end test suite. |
| 🌟 **[MASTER_MULTI_AGENT_GUIDE](guides%26docs/MASTER_MULTI_AGENT_GUIDE.md)** | **Institutional Quants** | Complete Air-Gapped Triad (`MainIngestionAgent` ➔ `ProcessSandboxAgent` ➔ `OutputSynthesisAgent`). |
| 🌟 **[QUALITATIVE_GUIDE](guides%26docs/QUALITATIVE_DATA_AND_MACRO_GUIDE.md)** | **Macro & Fundamental Researchers** | Concalls, US Fed interest rate regimes, and India macro trends translated into foundation model math. |

---

## 🚀 Quickstart: Unified CLI Entry-Point (`v2/run_pipeline.py`)

Run any asset in **Tier-1 Institutional Quantitative Hedge Fund Grade** by default:

```bash
# 1. Institutional Mode (DEFAULT): Real-Time Live Close, VaR/CVaR, Half-Kelly Sizing & STT Frictions
python3 v2/run_pipeline.py --ticker MODISONLTD.NS --horizon 30

# 2. Air-Gapped Multi-Agent Mode (Strict Zero-Leakage Point-In-Time Historical Backtest)
python3 v2/run_pipeline.py --mode multi-agent --ticker INFY.NS --cutoff 2020-12-31 --horizon 60

# 3. Live Forward Projection Mode (Real-Time Future Horizon via Hybrid Pipeline)
python3 v2/run_pipeline.py --mode live --ticker RAYMONDREL.NS --horizon 30

# 4. High-Frequency Intraday & Options Volatility Mode
python3 v2/run_pipeline.py --mode intraday --ticker ^NSEI

# 5. Run Full Regression Verification Test Suite
python3 v2/test_agents.py
python3 v2/test_multi_agent_flow.py
```

### 🏛️ Institutional Engine by Default
Every forecast automatically generates an **Institutional Executive Scorecard**:
* **Live Real-Time Execution**: When `--cutoff` is omitted, the pipeline automatically ingests the latest real-time market session (e.g., Friday, September 4, 2026).
* **Cross-Asset Macro Regimes**: Benchmarked against `^NSEI` (NIFTY 50 trend) and `^INDIAVIX` volatility regimes (Normal, High Volatility, Extreme Panic).
* **Sector Beta & Relative Strength**: Auto-matched to NSE sector indices (`^CNXIT`, `^CNXAUTO`, `^CNXMETAL`, `^NSEBANK`, `^CNXFMCG`).
* **Value-at-Risk (VaR) & CVaR**: Parametric 95% 1-day VaR, 30-day Horizon VaR, Conditional VaR (Expected Shortfall tail risk), and Historical Peak-to-Trough Max Drawdown.
* **Indian Market Friction Deductions**: Deducts 0.25% roundtrip frictions (STT 0.1% buy + 0.1% sell, SEBI turnover, GST, exchange slippage) from expected returns.
* **Half-Kelly Position Sizing**: Computes mathematically optimal portfolio capital allocations ($f^*_{half}$) based on net win probability, payoff ratio, and volatility parity.
* **Asymmetric Risk/Reward Ratio (RRR)**: Compares net expected upside to objective invalidation stop-loss levels.
* **Institutional Executive Directives**: Outputs definitive decisions (`STRONG BUY`, `SELECTIVE ACCUMULATE`, `HOLD / MONITOR`, `TRIM / TAKE PROFIT`, `AVOID / HIGH RISK`).

---

## 📖 Architectural Guides

### 🌟 [The Comprehensive Architectural Guide: Integrating LLMs with TimesFM 3.0](HYBRID_GUIDE/) (`HYBRID_GUIDE/`)
* **Core Architecture**: How LLM Semantic Reasoning fuses with TimesFM 3.0 Quantitative Cross-Attention.
* **Interactive Notebook**: [`HYBRID_GUIDE/hybrid_agentic_pipeline.ipynb`](HYBRID_GUIDE/hybrid_agentic_pipeline.ipynb) (Interactive, step-by-step multi-asset execution).
* **Enterprise Script**: [`HYBRID_GUIDE/hybrid_agentic_pipeline.py`](HYBRID_GUIDE/hybrid_agentic_pipeline.py) (CLI with `--mode backtest|live`, `--check`, and batch GPU support).
* **Data Ingestion Pipeline**: Numerical market feeds (`yfinance`), BSE/NSE corporate PDF/XML parsing (`pypdf`), and macro intelligence via Exa Neural Search (`exa-py`).
* **The Zero-Leakage Protocol**: Eliminating lookahead bias in backtests (Point-In-Time timestamps, Corporate Action neutrality via Market Cap, and Entity Anonymization "Company X" protocol).
* **Prompt Library**: [`HYBRID_GUIDE/prompts/`](HYBRID_GUIDE/prompts/) (Extraction, Valuation, and Anonymization prompts).
* **Agent Harness (Non-API) Guide**: [`HYBRID_GUIDE/AGENT_HARNESS_INTEGRATION.md`](HYBRID_GUIDE/AGENT_HARNESS_INTEGRATION.md) (Use Antigravity, Claude Code, Codex, or OpenCode with zero external API keys).
* **Cloud GPU Guide (Colab CLI)**: [`HYBRID_GUIDE/COLAB_GPU_GUIDE.md`](HYBRID_GUIDE/COLAB_GPU_GUIDE.md) & [`run_colab_gpu.sh`](HYBRID_GUIDE/run_colab_gpu.sh) (On-demand T4/A100 cloud GPU execution and automated VM teardown).
---

## 🛡️ Four Architectural Flaws Eliminated in Production

Following rigorous audit against institutional production standards, four critical flaws were permanently resolved:

| # | Flaw in Previous Implementations | Production Institutional Solution | Module |
| :- | :--- | :--- | :--- |
| **1** | **Static Hardcoded Valuation Ratios**: Hardcoded P/E multiples (e.g. 25x) disconnected from reality. | **Statement-Audited Fundamental Engine**: Extracts audited diluted EPS, sales, PAT, and dynamic peer-group sector multiples via official annual filings. | [`scenario_builder.py`](scenario_builder.py) |
| **2** | **Heuristic Sigmoid Anchoring**: Unphysical logistic curves arbitrarily forcing convergence. | **Volatility-Preserving Trajectory Diffusion**: Projects forward paths using annualized empirical historical volatility ($\sigma_{ann}$) and mean reversion. | [`covfree_forecaster.py`](covfree_forecaster.py) |
| **3** | **Single-Series Inference Loops**: Running model iteratively per scenario causing slow CPU execution. | **Vectorized Batch Processing**: Uses TimesFM 3.0 `predict_batch` to execute all scenarios in a single GPU forward pass on CUDA. | [`timesfm3/forecaster.py`](timesfm3/forecaster.py) |
| **4** | **Unquantified Downside & Friction Blindness**: Ignoring slippage, STT, and distribution fat tails. | **Institutional Risk Scorecard**: Full 95% Horizon VaR/CVaR, Half-Kelly sizing, -0.25% STT deductions, and macro regime filters. | [`institutional_engine.py`](institutional_engine.py) |
| **5** | **No Semantic Reasoning Bridge**: Pure numerical forecasters cannot interpret qualitative disclosures. | **AkashML LLM Reasoner**: Deploys `zai-org/GLM-5.3` (zero rate limits, deep chain-of-thought) to interpret guidance and synthesize mathematically verified scenario targets. | [`llm_reasoner.py`](llm_reasoner.py) |
| **6** | **Unverified Information Barriers**: Relying on manual developer inspection for data leakage. | **Automated Ingress Security Gate & Test Suite**: End-to-end A2A schema verification, token regex audits, and risk engine unit tests. | [`test_agents.py`](test_agents.py) |

---

## Studies & Breakthrough Benchmarks

### 1. [🌟 Live In-Depth Market Forecast: Monday, September 7, 2026](FORECAST_SEP7_2026/) (`FORECAST_SEP7_2026/`)
* **Focus**: Granular hour-by-hour NIFTY 50 forecast, weekly options cycle playbook (Sep 10 expiry), and multi-asset projections (Hindustan Zinc, Raymond Realty, Modison, Gold Futures).
* **Key Levels for Monday**:
  * **NIFTY 50**: Daily Pivot **23,922.83**, Support 1 **23,839.92**, Resistance 1 **23,980.62**, Resistance 2 **24,063.53**.
  * **Options Strategy**: Post-weekend theta decay playbook; 23,950/24,000 CE momentum triggers from PP (23,922); Sep 10 Strangle (24,150 CE / 23,750 PE).
  * **Stocks & Commodities**: Hindustan Zinc targeting ₹605–₹612, Raymond Realty targeting ₹538.11–₹548.91, Gold consolidating in $4,510–$4,540 corridor.

### 2. [🌟 Day-by-Day Forecast vs. Actual Market Outcome Audit (Sep 3 & Sep 4, 2026)](DAYWISE_ANALYSIS/) (`DAYWISE_ANALYSIS/`)
* **Focus**: Full ground-truth verification of all live predictions across Equities, Derivatives, and Commodities for September 3 and September 4, 2026 market sessions.
* **Key Findings**:
  * **Sep 4 NIFTY 50**: Resistance 1 predicted at **23,974.75**; Day High peaked at **23,975.75** (**1.00 pt / 0.004% error**)! Hour 5 predicted close of **23,948.60** vs actual close of **23,948.20** (**0.40 pt error**)!
  * **Sep 4 Hindustan Zinc**: Predicted Base **₹599.35** vs Actual Close **₹601.00** (**0.28% error**), Day High **₹603.00**!
  * **Sep 4 Raymond Realty**: Predicted R1 **₹542.17**, R2 **₹552.98**; Opened directly at R1 (**₹542.50**) and blasted past R2 to **₹559.00** (+5.2% intraday) on record 9.36L volume!
  * **Sep 4 Modison**: Predicted profit-taking pullback below ₹493; Day High capped at ₹494.65, closing at ₹469.95, vindicating 35% profit trim advice.
  * **Sep 3 Expiry**: Day Low hit **23,873.45** vs. predicted Support 2 of **23,872.32** (**1.13 pts / 0.004% error**). 24,000 Call and 23,800 Put both expired at ₹0.00 as predicted.

### 3. [🌟 Raymond Realty (RAYMONDREL) Multidimensional Forecast Deep Dive](RAYMONDREL_ANALYSIS/) (`RAYMONDREL_ANALYSIS/`)
* **Focus**: Multidimensional analysis (TimesFM 3.0 + Exa Regulatory Data) following the post-demerger breakout.
* **Key Insights**: 100-acre Thane landbank (₹25,000 Cr GDV) + Mumbai JDAs (₹15,000 Cr GDV) = **₹40,000 Cr GDV portfolio**. Trading at only **0.88x NAV** vs peers at 2.6x to 3.5x NAV! Base Target **₹575.00**, Bull Target **₹635.00**.

### 4. [🌟 Zerodha Portfolio Deep Dive & Predictive Stock Audit (ZRJ225)](EXCEL_DATA/) (`EXCEL_DATA/`)
* **Focus**: Full quantitative health check and AI-driven decision matrix across all 28 direct equity holdings (₹4.02L) and 8 mutual funds (₹9.86L) totaling ₹13.88L.
* **Key Actions**: Strong Sell 5 penny traps (`VIKASECO`, `SARVESHWAR`, `TRIDENT`, etc.); Trim 35% on winners (`MODISONLTD`, `SILVERBEES`, `MANAPPURAM`); Hold compounders (`CDSL`, `GOLDBEES`, `NIFTYBEES`, `HINDZINC`, `TMCV`).

### 5. [Live 1-Month Daily Forecast: GOLD Continuous Futures](GOLD_LIVE/) (`GOLD_LIVE/`)
* **Asset**: Gold Continuous Futures (`GC=F`).
* **Start Date**: September 3, 2026 | **Horizon**: **22 Trading Days (Sep 3 to Oct 2, 2026)**.
* **Hardware**: Executed on active Google Colab **Tesla T4 GPU** (`infosys-gpu`).
* **Starting Price**: **$4,431.40 / oz**.
* **Key Findings**: Base Case projects steady accumulation toward **$4,473.90 / oz (+0.96%)**, with Bull boundary at **$4,547.21 / oz** driven by central bank buying and Fed rate easing.

### 2. [Live 1-Month Daily Forecast: HINDUSTAN ZINC](HINDZINC_LIVE/) (`HINDZINC_LIVE/`)
* **Asset**: Hindustan Zinc Limited (`HINDZINC.NS`).
* **Start Date**: September 3, 2026 | **Horizon**: **22 Trading Days (Sep 3 to Oct 2, 2026)**.
* **Hardware**: Executed on active Google Colab **Tesla T4 GPU** (`infosys-gpu`).
* **Starting Price**: **₹597.00**.
* **Key Findings**: Base Case projects steady accumulation to **₹608.39 (+1.91%)**, with Bull boundary at **₹636.37 (+6.59%)** supported by silver byproduct margins and high dividend yields.

### 3. [Live 1-Month Daily Forecast: MODISON LIMITED](MODISON_LIVE/) (`MODISON_LIVE/`)
* **Asset**: Modison Limited (`MODISONLTD.NS`).
* **Start Date**: September 3, 2026 | **Horizon**: **22 Trading Days (Sep 3 to Oct 2, 2026)**.
* **Hardware**: Executed on active Google Colab **Tesla T4 GPU** (`infosys-gpu`).
* **Starting Price**: **₹499.45**.
* **Key Findings**: Following an explosive volume surge to ₹499.45, the Base Case projects steady consolidation toward **₹517.12 (+3.54%)**, with Bull boundary extending to **₹568.34 (+13.79%)** on EV/renewable contact diversification.

### 4. [5-Year Monthly Large-Cap Benchmark: INFOSYS](INFOSYS_MONTHLY/) (`INFOSYS_MONTHLY/`)
* **Asset**: Infosys Limited (`INFY.NS`).
* **Cutoff Date**: December 31, 2020 (Strict Zero Lookahead).
* **Horizon**: **60 monthly bars (5 full years, 2021 to 2025)**.
* **Hardware**: Executed on active Google Colab **Tesla T4 GPU** (`infosys-gpu`).
* **Key Findings**:
  * **Traditional Zero-Leakage (Pure TimesFM 3.0)**: Suffered severe multi-year autoregressive mean decay, drifting to **₹708.16** (**-55.2% error**, MAPE: **35.49%**).
  * **Latest Agent Zero-Leakage Triad**: Base Case scenario projected **₹1,504.84** vs actual **₹1,581.18** (**error only -4.8%**!). The Bear-to-Bull scenario envelope covered **96.7% of all 60 months (58/60 months)**, achieving a **73.1% error reduction**.

### 2. [Multi-Year Large-Cap Benchmark: HEROMOTOCO](HEROMOTOCO/) (`HEROMOTOCO/`)
* **Asset**: Hero MotoCorp Limited (`HEROMOTOCO.NS`).
* **Cutoff Date**: December 31, 2023 (Strict Zero Lookahead).
* **Horizon**: **663 trading days (2.7 years)** from January 2024 to September 2026.
* **Key Findings**:
  * **TimesFM 3.0 Pure Baseline**: Suffered severe runaway trend extrapolation, exploding to **₹14,442.68** (**+160.0% error**, MAPE: **92.87%**).
  * **Hybrid Agent Harness Model**: Conditioned on 2023 Harley-Davidson partnership, premiumization, and peer valuation re-rating, accurately tracked the cycle to **₹5,475.62** vs actual **₹5,555.00** (**error only -1.4%**, **88.4% error reduction**!).

### 2. [Multi-Year Foundation Model Benchmark: CUPID LIMITED](CUPID/) (`CUPID/`)
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

The repository is strictly partitioned into **4 dedicated root directories**:

```
timesfm-3.0-pytorch/
├── README.md                               # Central Repository Dashboard
├── requirements.txt                        # Master dependencies
├── .gitignore
├── .akashml_key                            # AkashML API key configuration
├── .nvidia_key                             # NVIDIA NIM API key configuration
│
├── v1/                                     # 📦 Legacy Standalone Experiments & Exploratory Work
│   ├── CUPID/                              # Multi-Year Cupid benchmark
│   ├── DAYWISE_ANALYSIS/                   # Live Day-by-Day Forecast vs Ground Truth Audits
│   ├── EXCEL_DATA/                         # Zerodha Portfolio Deep Dive (ZRJ225)
│   ├── FORECAST_SEP4_2026/                 # Live Market Forecast (Sep 4, 2026)
│   ├── FORECAST_SEP7_2026/                 # Live Market Forecast (Sep 7, 2026)
│   ├── GOLD_LIVE/                          # Live Gold Futures (GC=F) 1-month forecast
│   ├── HEROMOTOCO/                         # Multi-Year Large-Cap Hero MotoCorp benchmark
│   ├── HINDZINC_LIVE/                      # Live Hindustan Zinc 1-month forecast
│   ├── HYBRID_GUIDE/                       # Early hybrid prototype and single-asset pipeline
│   ├── HYBRID_MODISON/                     # LLM + TimesFM 3.0 prototype experiment
│   ├── INFOSYS_MONTHLY/                    # 5-Year Monthly benchmark (2021-2025)
│   ├── INTRADAY/                           # Hourly Index & Options Volatility scripts
│   ├── MODISONANALYSIS/                    # MODISONLTD corporate event benchmark & filings
│   ├── MODISON_LIVE/                       # Live Modison Ltd 1-month forecast
│   ├── NIFTY/                              # NIFTY 50 8-month macro benchmark
│   ├── OPTIONS/                            # NIFTY options and volatility experiments
│   ├── RAYMONDREL_ANALYSIS/                # Raymond Realty 22-day forecast & GDV
│   └── daywise_sep4_audit_and_monday_prediction.py
│
├── v2/                                     # 🚀 Production Multi-Agent Air-Gapped Quantitative System
│   ├── run_pipeline.py                     # 🌟 Master CLI Dispatcher (Institutional, Multi-Agent, Backtest, Live, Intraday)
│   ├── run_2026_prediction_benchmark.py    # 2026 forward prediction benchmark runner (7+ assets)
│   ├── run_10stock_fixed_benchmark.py      # Fixed 10-stock backtest benchmark
│   ├── run_1year_benchmark.py              # 1-year historical benchmark runner
│   ├── batch_backtest_benchmark.py         # Batch multi-asset backtesting runner
│   │
│   └── MULTI_AGENT_SANDBOX/                # 🌟 Core Air-Gapped Multi-Agent Triad Engine
│       ├── multi_agent_system.py           # Complete 3-Agent Triad (MainIngestion -> ProcessSandbox -> OutputSynthesis)
│       ├── scenario_builder.py             # Point-in-time financial statement parsing & two-sided valuation engine
│       ├── llm_reasoner.py                 # Multi-provider LLM reasoner (AkashML DeepSeek/GLM, OpenCode, NVIDIA NIM)
│       ├── covfree_forecaster.py           # Statistical Monte Carlo quantile forecaster & covariate generator
│       ├── institutional_engine.py         # Half-Kelly sizing, 95% VaR/CVaR, STT frictions, Sector Beta, Macro regimes
│       ├── sample_a2a_payload.json         # Wire specification for zero-leakage A2A messages
│       ├── test_agents.py                  # Regression & poison-token rejection unit tests
│       ├── test_multi_agent_flow.py        # End-to-end integration test runner
│       └── hybrid_method_comparison.csv    # Comparative methodology benchmarks
│
├── guides&docs/                            # 📚 Complete System Documentation & Architectural Manuals
│   ├── USER_GUIDE.md                       # Non-technical manual for traders, investors, and PMs
│   ├── DEVELOPER_GUIDE.md                  # Software engineering manual, class hierarchy, tensor contracts
│   ├── LLM_GUIDE.md                        # Universal meta-prompt for AI agents
│   ├── MODES_GUIDE.md                      # Detailed walkthrough of execution modes
│   ├── MASTER_MULTI_AGENT_GUIDE.md         # Definitive end-to-end multi-agent architecture guide
│   ├── QUALITATIVE_DATA_AND_MACRO_GUIDE.md # Macro, Concalls, and Federal Reserve data integration
│   ├── LLM_AGENT_INSTRUCTIONS.md           # Master autonomous instructions for AI agents
│   └── llm.md                              # End-to-end LLM onboarding, Colab CLI guide, testing procedures
│
└── test_results/                           # 📊 Benchmark Results, Scorecards, Charts & Executive Reports
    ├── AUDIT/                              # Security and token-leakage audit probes
    ├── BATCH_BENCHMARK_OUTPUT/             # Multi-asset batch backtest outputs
    ├── BENCHMARK_1YEAR_OUTPUT/             # 1-Year historical backtest benchmark outputs
    ├── BENCHMARK_2026_OUTPUT/              # Forward 2026 multi-asset prediction outputs
    ├── BENCHMARK_FIXED_OUTPUT/             # 10-Stock fixed backtest benchmark outputs
    ├── GPU_E2E_OUTPUT/                     # Colab GPU execution results
    ├── TCS_2026_OUTPUT/                    # TCS 2026 deep-dive predictions and scorecards
    ├── pipeline_results/                   # Default output directory for run_pipeline.py
    └── test_run_output/                    # Output from test_multi_agent_flow.py
```

