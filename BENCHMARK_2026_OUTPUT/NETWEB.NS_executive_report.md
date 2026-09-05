# Multi-Agent Zero-Leakage Forecast Report: NETWEB.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 5193.00** | Rs. 2208.37 | **Rs. 5864.64** | Rs. 4583.93 |
| **Terminal Error (%)** | — | -57.47% (Exploded) | **+12.93%** | -11.73% |
| **Multi-Year MAE** | — | Rs. 1374.79 | — | **Rs. 316.24** |
| **Multi-Year MAPE** | — | 31.16% | — | **7.48%** |
| **Scenario Envelope Coverage** | — | 0% | — | **100.0% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](NETWEB.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `6a75d9aa`
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
| **Parametric 95% 1-Day VaR** | **5.90%** | 95% confidence max expected single-day loss |
| **Parametric 95% Horizon VaR** | **77.21%** | Cumulative 171-day volatility exposure |
| **Conditional VaR (CVaR / Expected Shortfall)** | **100.71%** | Average loss in worst 5% tail-risk scenarios |
| **Historical Max Drawdown** | **-30.32%** | Deepest peak-to-trough historical correction |

### C. Capital Allocation & Execution Matrix (Indian Market Frictions Deducted)
* **Gross Potential Upside**: `+62.87%`
* **Indian Frictions Deducted (STT + SEBI + GST + Slippage)**: `-0.25%`
* **Net Horizon Upside**: `**+62.62%**`
* **Objective Invalidation Stop-Loss**: `Rs. 3107.95` (Downside: `-1.0%`)
* **Asymmetric Risk/Reward Ratio (RRR)**: `**62.62x**`
* **Half-Kelly Capital Allocation**: `38.8%`
* **Recommended Portfolio Exposure**: `**15.0%**` (Rs. 150,000.00 | **48 shares**)
* **Institutional Executive Directive**: `**STRONG BUY (High Conviction Asymmetric Setup)**`
