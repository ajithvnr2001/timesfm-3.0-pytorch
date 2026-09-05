# Multi-Agent Zero-Leakage Forecast Report: RAYMONDREL.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 529.15** | Rs. 518.07 | **Rs. 544.37** | Rs. 530.84 |
| **Terminal Error (%)** | — | -2.09% (Exploded) | **+2.88%** | +0.32% |
| **Multi-Year MAE** | — | Rs. 14.39 | — | **Rs. 8.59** |
| **Multi-Year MAPE** | — | 2.74% | — | **1.64%** |
| **Scenario Envelope Coverage** | — | 0% | — | **100.0% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](RAYMONDREL.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `75b5591d`
* **Air-Gapped Protocol**: `A2A/v1.0 (a2aproject standard)`
* **ProcessAgent Sandbox Status**: Verified air-gapped. Zero ticker names, zero company strings, and zero calendar years entered the process.
* **Leakage Detected**: **0 Tokens (100% Blind-Box Verified)**.

---

## 4. Institutional Risk, Macro Regime & Capital Sizing Matrix

### A. Cross-Asset Macro & Sector Alignment
* **NIFTY 50 Macro Regime**: `BULLISH_UPTREND` (Benchmark Close: Rs. 23,900.00)
* **India VIX Volatility Regime**: `NORMAL_VOLATILITY (Optimal Trading Environment)` (Level: 13.50 | Multiplier: 1.00x)
* **Sector Benchmark**: `^NSEI` (Stock Beta to NIFTY: `1.0` | Beta to Sector: `1.0`)

### B. Value at Risk (VaR) & Tail Risk Profile
| Metric | Horizon Risk (% of Equity) | Interpretation |
| :--- | :--- | :--- |
| **Parametric 95% 1-Day VaR** | **5.10%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **23.93%** | Cumulative 22-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **30.43%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-28.50%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+50.68%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+50.43%**`
* **Objective Invalidation Stop-Loss**: `Rs. 526.33` (Downside: `-1.0%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**50.43x**`
* **Half-Kelly Capital Allocation**: `38.8%`
* **Recommended Portfolio Exposure**: `**15.0%**` (Rs. 150,000.00 | **290 shares**)
* **Institutional Executive Directive**: `**STRONG BUY (High Conviction Asymmetric Setup)**`
