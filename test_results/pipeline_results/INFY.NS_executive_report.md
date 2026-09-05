# Multi-Agent Zero-Leakage Forecast Report: INFY.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Projection Horizon | Last Session Close | Pure Baseline Terminal | Bull Terminal (25% Prob) | Base Terminal (50% Prob) | Bear Terminal (25% Prob) | Probabilistic Weighted Fair Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **5 Trading Days** | **Rs. 1,130.00** | Rs. 1,125.55 | **Rs. 1,090.63** | Rs. 1,030.97 | Rs. 973.96 | **Rs. 1,045.72** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](INFY.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `1db1b103`
* **Air-Gapped Protocol**: `A2A/v1.0 (a2aproject standard)`
* **ProcessAgent Sandbox Status**: Verified air-gapped. Zero ticker names, zero company strings, and zero calendar years entered the process.
* **Leakage Detected**: **0 Tokens (100% Blind-Box Verified)**.

---

## 4. Institutional Risk, Macro Regime & Capital Sizing Matrix

### A. Cross-Asset Macro & Sector Alignment
* **NIFTY 50 Macro Regime**: `BULLISH_UPTREND` (Benchmark Close: Rs. 23,900.00)
* **India VIX Volatility Regime**: `NORMAL_VOLATILITY (Optimal Trading Environment)` (Level: 13.50 | Multiplier: 1.00x)
* **Sector Benchmark**: `^CNXIT` (Stock Beta to NIFTY: `1.0` | Beta to Sector: `1.0`)

### B. Value at Risk (VaR) & Tail Risk Profile
| Metric | Horizon Risk (% of Equity) | Interpretation |
| :--- | :--- | :--- |
| **Parametric 95% 1-Day VaR** | **3.45%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **7.71%** | Cumulative 5-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **9.12%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-14.89%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `-18.76%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**-19.01%**`
* **Objective Invalidation Stop-Loss**: `Rs. 803.25` (Downside: `-28.9%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**0.0x**`
* **Half-Kelly Capital Allocation**: `0.0%`
* **Recommended Portfolio Exposure**: `**0.0%**` (Rs. 0.00 | **0 shares**)
* **Institutional Executive Directive**: `**TRIM / TAKE PROFIT (Negative Expected Skew)**`
