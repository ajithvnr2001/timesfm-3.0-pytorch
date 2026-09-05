# Multi-Agent Zero-Leakage Forecast Report: NETWEB.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 1603.29** | Rs. 1254.20 | **Rs. 689.73** | Rs. 637.76 |
| **Terminal Error (%)** | — | -21.77% (Exploded) | **-56.98%** | -60.22% |
| **Multi-Year MAE** | — | Rs. 245.81 | — | **Rs. 555.62** |
| **Multi-Year MAPE** | — | 16.02% | — | **36.35%** |
| **Scenario Envelope Coverage** | — | 0% | — | **10.0% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](NETWEB.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `e629c2bd`
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
| **Parametric 95% 1-Day VaR** | **5.56%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **43.04%** | Cumulative 60-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **43.75%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-16.68%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `-75.27%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**-75.52%**`
* **Objective Invalidation Stop-Loss**: `Rs. 207.20` (Downside: `-82.5%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**0.0x**`
* **Half-Kelly Capital Allocation**: `0.0%`
* **Recommended Portfolio Exposure**: `**0.0%**` (Rs. 0.00 | **0 shares**)
* **Institutional Executive Directive**: `**TRIM / TAKE PROFIT (Negative Expected Skew)**`
