# Multi-Agent Zero-Leakage Forecast Report: TCS.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 2320.10** | Rs. 4118.81 | **Rs. 4118.81** | Rs. 4118.81 |
| **Terminal Error (%)** | — | +77.53% (Exploded) | **+77.53%** | +77.53% |
| **Multi-Year MAE** | — | Rs. 1192.81 | — | **Rs. 1192.81** |
| **Multi-Year MAPE** | — | 51.71% | — | **51.71%** |
| **Scenario Envelope Coverage** | — | 0% | — | **13.5% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](TCS.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `71619d09`
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
| **Parametric 95% 1-Day VaR** | **1.68%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **21.95%** | Cumulative 170-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **17.38%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-3.57%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `-27.10%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**-27.35%**`
* **Objective Invalidation Stop-Loss**: `Rs. 1925.70` (Downside: `-37.7%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**0.0x**`
* **Half-Kelly Capital Allocation**: `0.0%`
* **Recommended Portfolio Exposure**: `**0.0%**` (Rs. 0.00 | **0 shares**)
* **Institutional Executive Directive**: `**TRIM / TAKE PROFIT (Negative Expected Skew)**`
