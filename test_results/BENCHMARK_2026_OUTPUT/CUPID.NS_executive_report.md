# Multi-Agent Zero-Leakage Forecast Report: CUPID.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 283.15** | Rs. 289.09 | **Rs. 225.26** | Rs. 211.50 |
| **Terminal Error (%)** | — | +2.10% (Exploded) | **-20.44%** | -25.30% |
| **Multi-Year MAE** | — | Rs. 37.80 | — | **Rs. 38.22** |
| **Multi-Year MAPE** | — | 35.43% | — | **31.17%** |
| **Scenario Envelope Coverage** | — | 0% | — | **21.6% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](CUPID.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `3552b730`
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
| **Parametric 95% 1-Day VaR** | **5.01%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **65.52%** | Cumulative 171-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **47.11%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-7.98%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+94.56%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+94.31%**`
* **Objective Invalidation Stop-Loss**: `Rs. 157.14` (Downside: `-1.0%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**94.31x**`
* **Half-Kelly Capital Allocation**: `38.9%`
* **Recommended Portfolio Exposure**: `**15.0%**` (Rs. 150,000.00 | **1447 shares**)
* **Institutional Executive Directive**: `**STRONG BUY (High Conviction Asymmetric Setup)**`
