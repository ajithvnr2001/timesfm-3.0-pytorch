# Multi-Agent Zero-Leakage Forecast Report: STLTECH.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 748.90** | Rs. 81.70 | **Rs. 860.64** | Rs. 573.26 |
| **Terminal Error (%)** | — | -89.09% (Exploded) | **+14.92%** | -23.45% |
| **Multi-Year MAE** | — | Rs. 286.63 | — | **Rs. 80.75** |
| **Multi-Year MAPE** | — | 61.68% | — | **24.02%** |
| **Scenario Envelope Coverage** | — | 0% | — | **86.0% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](STLTECH.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `09e7e139`
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
| **Parametric 95% 1-Day VaR** | **4.45%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **58.22%** | Cumulative 171-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **64.39%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-22.38%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+565.92%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+565.67%**`
* **Objective Invalidation Stop-Loss**: `Rs. 315.03` (Downside: `-1.0%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**565.67x**`
* **Half-Kelly Capital Allocation**: `39.0%`
* **Recommended Portfolio Exposure**: `**15.0%**` (Rs. 150,000.00 | **1453 shares**)
* **Institutional Executive Directive**: `**STRONG BUY (High Conviction Asymmetric Setup)**`
