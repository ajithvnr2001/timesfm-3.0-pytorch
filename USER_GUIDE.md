# The Executive User Guide: Google TimesFM 3.0 Quantitative System
### A Practical Manual for Traders, Portfolio Managers, and Financial Analysts

---

## 1. What is This System?

Standard AI trading models fail because they either:
1. **Hallucinate**: They predict extreme prices with no economic reality.
2. **Cheat**: They remember past stock prices from their training data (Data Leakage).

This repository contains the **Google TimesFM 3.0 Hybrid Quantitative Engine**. It combines:
* **Google Research's TimesFM 3.0**: A 200-million parameter deep learning time-series foundation model.
* **Qualitative Semantic Reasoning**: Ingestion of real-world audited financial statements, earnings conference calls, US Federal Reserve interest rate cycles, and Indian macroeconomic trends.
* **Air-Gapped Zero-Leakage Architecture**: An isolated 3-agent structure that physically prevents the forecasting AI from knowing the asset identity or cheating during historical backtests.

---

## 2. Understanding the 3 Forecast Scenarios

Instead of giving you a single speculative price, the system generates a **3-Branch Fundamental Scenario Tree**:

```
                                      ┌───► BULL SCENARIO (25% Probability)
                                      │     • High Growth, Margin Expansion, Multiple Re-Rating
                                      │
─── LAST HISTORICAL CLOSE ────────────┼───► BASE SCENARIO (50% Probability)
                                      │     • Median Historical Growth, Margin Defense
                                      │
                                      └───► BEAR SCENARIO (25% Probability)
                                            • Economic Headwinds, Margin Compression, Multiple De-Rating
```

### How to Interpret the Scenarios:
1. **The Base Case (50% Probability)**:  
   Represents the most likely fundamental path assuming current corporate guidance and historical median valuation multiples persist.
2. **The Bull Case (25% Probability)**:  
   Models positive operational catalysts (e.g. mega-deal contract wins, market share expansion, sector multiple re-rating).
3. **The Bear Case (25% Probability)**:  
   Models macroeconomic stress, raw material inflation, wage attrition, or valuation compression.
4. **The Scenario Envelope (The Light Blue Shaded Zone)**:  
   The boundary between the Bear and Bull projections. If a stock has **95%+ Scenario Envelope Coverage**, it means the real market price has stayed reliably bounded within our fundamental safety margins over multi-year cycles.

---

## 3. How to Use the System (No Coding Required)

### Method 1: Google Colab 1-Click Cloud GPU (Easiest)
You do not need an expensive GPU on your laptop. You can run this directly in the cloud:

1. Open **Google Colab** (Free or Pro).
2. Clone the repository:
   ```bash
   !git clone https://github.com/ajithvnr2001/timesfm-3.0-pytorch.git
   %cd timesfm-3.0-pytorch
   !pip install -r requirements.txt
   ```
3. Open any of the interactive notebooks:
   * **`INFOSYS_MONTHLY/timesfm3_infosys_monthly_analysis.ipynb`**: 5-Year Monthly Forecast.
   * **`HEROMOTOCO/timesfm3_heromotoco_analysis.ipynb`**: 2.7-Year Daily Forecast.
   * **`INTRADAY/timesfm3_intraday_analysis.ipynb`**: Live NIFTY 50 Intraday Forecast.
4. Click **Run All Cells** to view the forecast charts and probability envelopes.

---

### Method 2: Command-Line Interface (Unified CLI)

Run a forecast for any global or Indian stock in a single command:

#### 1. Air-Gapped Multi-Agent Mode (Strict Zero-Leakage)
Use this to backtest any stock in history with 100% mathematical certainty that the AI did not cheat:
```bash
python3 run_pipeline.py \
  --mode multi-agent \
  --ticker INFY.NS \
  --cutoff 2020-12-31 \
  --horizon 60
```

#### 2. Live Forecasting Mode (Real-Time Future Projection)
Use this to project prices into the future starting from today:
```bash
python3 run_pipeline.py \
  --mode live \
  --ticker RELIANCE.NS \
  --horizon 64
```

#### 3. Intraday Index & Options Mode
Use this on trading days to forecast hourly index trajectories:
```bash
python3 run_pipeline.py \
  --mode intraday \
  --ticker ^NSEI
```

---

## 4. How to Read Your Output Artifacts

Every run automatically produces three institutional-grade files in your output directory:
1. **High-Resolution PNG Chart (`*_forecast.png`)**:  
   Visualizes the historical context, the actual ground truth, the 3 scenarios, and the shaded scenario envelope.
2. **Executive Quant Report (`*_executive_report.md`)**:  
   A plain-English markdown summary detailing:
   * Starting price vs. Terminal forecast.
   * Percentage error of the Base, Bull, and Bear cases.
   * Multi-Year Mean Absolute Percentage Error (MAPE).
   * Scenario Envelope Coverage (% of days inside bounds).
3. **Raw Results Dataset (`*_results.json`)**:  
   Machine-readable numerical vectors containing every daily/monthly prediction scalar for downstream portfolio backtesting.

---

## 5. Risk Management & Practical Trading Rules

> [!WARNING]
> **Important Financial Disclaimer**:  
> No statistical or machine learning model can guarantee financial returns. Financial markets carry systemic risks, liquidity shocks, and black swan events.

### Recommended Risk Management Guidelines:
* **Position Sizing**: Never allocate capital based on the Bull scenario alone. Size your positions so that if the **Bear Scenario** hits, your portfolio does not incur unacceptable drawdowns.
* **Stop-Loss Anchoring**: Professional quantitative desks use the **lower boundary of the Scenario Envelope (Bear Case × 0.90)** as an objective invalidation level for long-term investments.
* **Envelope Invalidation**: If a stock breaks sustainably below the Bear envelope, it indicates that a fundamental structural impairment (e.g. accounting irregularity or regulatory ban) has occurred, requiring an immediate thesis reassessment.
