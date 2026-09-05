# Multi-Agent Zero-Leakage Forecast Report: HEROMOTOCO.NS
### Architecture: MainAgent (Ingestion) ➔ ProcessAgent (Sandbox TimesFM) ➔ OutputAgent (Reporting)

---

## 1. Multi-Agent Triad Performance Scorecard

| Metric | Actual Ground Truth | ProcessAgent Pure Baseline | ProcessAgent Bull Scenario | Probabilistic Weighted Path |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal Price** | **Rs. 5555.00** | Rs. 6208.52 | **Rs. 3488.48** | Rs. 3023.34 |
| **Terminal Error (%)** | — | +11.76% (Exploded) | **-37.20%** | -45.57% |
| **Multi-Year MAE** | — | Rs. 636.43 | — | **Rs. 1328.12** |
| **Multi-Year MAPE** | — | 14.36% | — | **26.36%** |
| **Scenario Envelope Coverage** | — | 0% | — | **18.3% of all trading days** |

---

## 2. High-Resolution Forecast Chart

![Multi Agent Forecast](HEROMOTOCO.NS_multi_agent_forecast.png)

---

## 3. Sandboxing & Security Audit Log

* **Ingress Message ID**: `9ebfd44e`
* **Air-Gapped Protocol**: `A2A/v1.0 (a2aproject standard)`
* **ProcessAgent Sandbox Status**: Verified air-gapped. Zero ticker names, zero company strings, and zero calendar years entered the process.
* **Leakage Detected**: **0 Tokens (100% Blind-Box Verified)**.
