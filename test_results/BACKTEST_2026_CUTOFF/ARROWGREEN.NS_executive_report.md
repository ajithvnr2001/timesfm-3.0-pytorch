# Multi-Agent Zero-Leakage Forecast Report: ARROWGREEN.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 814.10** | Rs. 504.36 | **Rs. 504.36** | Rs. 504.36 |
| **Terminal Error (%)** | — | -38.05% (Exploded) | **-38.05%** | -38.05% |
| **Multi-Year MAE** | — | Rs. 105.30 | — | **Rs. 105.30** |
| **Multi-Year MAPE** | — | 18.59% | — | **18.59%** |
| **Scenario Envelope Coverage** | — | 0% | — | **31.8% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](ARROWGREEN.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `6c31575d`
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
| **Parametric 95% 1-Day VaR** | **4.82%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **62.90%** | Cumulative 170-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **46.35%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-23.10%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+261.39%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+261.14%**`
* **Objective Invalidation Stop-Loss**: `Rs. 372.44` (Downside: `-26.4%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**9.91x**`
* **Half-Kelly Capital Allocation**: `37.9%`
* **Recommended Portfolio Exposure**: `**15.0%**` (Rs. 150,000.00 | **296 shares**)
* **Institutional Executive Directive**: `**STRONG BUY (High Conviction Asymmetric Setup)**`
