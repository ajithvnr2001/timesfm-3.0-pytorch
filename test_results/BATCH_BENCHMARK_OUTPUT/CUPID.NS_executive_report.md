# Multi-Agent Zero-Leakage Forecast Report: CUPID.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 24.23** | Rs. 11.87 | **Rs. 13.86** | Rs. 11.37 |
| **Terminal Error (%)** | — | -51.03% (Exploded) | **-42.80%** | -53.07% |
| **Multi-Year MAE** | — | Rs. 8.41 | — | **Rs. 8.68** |
| **Multi-Year MAPE** | — | 39.74% | — | **40.97%** |
| **Scenario Envelope Coverage** | — | 0% | — | **5.0% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](CUPID.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `853ccbae`
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
| **Parametric 95% 1-Day VaR** | **7.06%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **54.72%** | Cumulative 60-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **28.94%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-7.38%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+1.37%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+1.12%**`
* **Objective Invalidation Stop-Loss**: `Rs. 7.33` (Downside: `-34.6%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**0.03x**`
* **Half-Kelly Capital Allocation**: `0.0%`
* **Recommended Portfolio Exposure**: `**0.0%**` (Rs. 0.00 | **0 shares**)
* **Institutional Executive Directive**: `**TRIM / TAKE PROFIT (Negative Expected Skew)**`
