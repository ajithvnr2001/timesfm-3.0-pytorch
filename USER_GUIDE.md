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

Run a forecast for any global or Indian stock in a single command. **The system defaults to Tier-1 Institutional Quantitative Hedge Fund Grade**:

#### 1. Live Institutional Analysis (DEFAULT - Real-Time Market Close)
Simply supply the ticker. The engine automatically ingests the latest live market session (e.g. Friday, Sep 4, 2026), statement-audited diluted EPS, and computes complete institutional risk sizing:
```bash
python3 run_pipeline.py \
  --ticker MODISONLTD.NS \
  --horizon 30 \
  --portfolio_capital 1000000
```

#### 2. Air-Gapped Multi-Agent Mode (Strict Zero-Leakage Historical Backtest)
Use this to backtest any stock in history with 100% mathematical certainty that the AI did not cheat:
```bash
python3 run_pipeline.py \
  --mode multi-agent \
  --ticker INFY.NS \
  --cutoff 2020-12-31 \
  --horizon 60
```

#### 3. Live Forward Projection Mode (Real-Time Future Horizon)
Use this to project prices into the future starting from today:
```bash
python3 run_pipeline.py \
  --mode live \
  --ticker RELIANCE.NS \
  --horizon 64
```

#### 4. Intraday Index & Options Mode
Use this on trading days to forecast hourly index trajectories:
```bash
python3 run_pipeline.py \
  --mode intraday \
  --ticker ^NSEI
```

---

## 4. Understanding the Institutional Risk Scorecard

Every institutional run prints and saves an executive scorecard directly in your terminal and report:

```
=================================================================
 INSTITUTIONAL EXECUTIVE DIRECTIVE: MODISONLTD.NS
=================================================================
• Recommendation:         TRIM / TAKE PROFIT (Negative Expected Skew)
• Current Price:          Rs. 469.95
• Expected Target:        Rs. 486.16
• Invalidation Stop-Loss: Rs. 344.19 (Downside: -26.8%)
• Net Horizon Upside:     +5.69% (STT/Frictions -0.25% deducted)
• Asymmetric R/R Ratio:   0.21x
• 95% Horizon VaR:        33.34% | CVaR (Tail): 27.34%
• NIFTY Regime:           BULLISH_UPTREND (VIX: 13.5 - NORMAL_VOLATILITY)
• Sector Beta:            1.0 vs ^NSEI
• Half-Kelly Allocation:  0.0% of portfolio
• Sized Capital:          Rs. 0.00 (0 shares)
=================================================================
```

### Key Metrics Explained:
1. **Net Horizon Upside**: Gross upside minus **0.25% roundtrip Indian market frictions** (Securities Transaction Tax 0.1% buy + 0.1% sell, SEBI turnover fees, GST, and exchange slippage).
2. **Invalidation Stop-Loss**: Objective structural support level derived from fundamental scenario boundary (Bear Case target). A daily close below this invalidates the investment thesis.
3. **Asymmetric Risk/Reward Ratio (RRR)**: Compares net upside against maximum downside to invalidation. Institutional desks require $\ge 2.0\text{x}$ for fresh capital deployment.
4. **95% Horizon Value-at-Risk (VaR)**: Maximum cumulative percentage loss expected over the horizon with 95% statistical confidence.
5. **Conditional VaR (CVaR / Expected Shortfall)**: The average loss experienced in the worst 5% extreme tail-risk drawdowns.
6. **Half-Kelly Capital Allocation ($f^*_{half}$)**: Mathematically optimal capital allocation ($f^* = p - \frac{q}{b}$, scaled by 0.5 for risk protection). Prevents portfolio over-leveraging and catastrophic drawdown.

### Executive Directives:
* `STRONG BUY`: High conviction upside, favorable asymmetric RRR ($\ge 2.5\text{x}$), optimal Kelly size $> 10\%$.
* `SELECTIVE ACCUMULATE`: Positive expected value, moderate Kelly size (5% to 10%), favorable macro backdrop.
* `HOLD / MONITOR`: Balanced skew, existing positions held with trailing stops, zero fresh capital.
* `TRIM / TAKE PROFIT`: Asset reached or exceeded base fair value, risk/reward skewed negatively ($< 0.5\text{x}$), lock in gains.
* `AVOID / HIGH RISK`: Negative expected return or extreme tail-risk CVaR $> 35\%$.

---

## 5. How to Read Your Output Artifacts

Every run automatically produces three institutional-grade files in your output directory:
1. **High-Resolution PNG Chart (`*_multi_agent_forecast.png`)**:  
   Visualizes the historical context, actual ground truth (for backtests), the 3 scenarios, the weighted probabilistic path, and the shaded scenario envelope.
2. **Executive Quant Report (`*_executive_report.md`)**:  
   A plain-English markdown summary detailing the performance scorecard, security audit logs, macro regime classification, and capital allocation matrix.
3. **Raw Results Dataset (`*_multi_agent_results.json`)**:  
   Machine-readable numerical vectors containing every prediction scalar, quantiles, and risk metrics for downstream execution algorithms.

---

## 6. Risk Management & Practical Trading Rules

> [!WARNING]
> **Important Financial Disclaimer**:  
> No statistical or machine learning model can guarantee financial returns. Financial markets carry systemic risks, liquidity shocks, and black swan events.

### Recommended Rules for Institutional Execution:
* **Obey Half-Kelly Limits**: Never allocate more capital than the Half-Kelly recommendation. If Kelly recommends 0.0% (as in overextended rallies), do not chase the stock.
* **Respect Trailing Invalidation Levels**: Anchor stop-losses to the calculated invalidation level. If the stock breaks below, exit immediately.
* **Factor in Market Frictions**: In Indian equity cash and F&O markets, STT and turnover charges compound rapidly. Always trade against net friction-deducted targets.
