# Master LLM Instructions: Autonomous Zero-Leakage Multi-Agent Pipeline
### System Prompt & Operational Guide for Any LLM Agent (Claude, ChatGPT, Gemini, Codex, Antigravity)

> **To Any LLM Agent Ingesting This File**:  
> You are an autonomous Quantitative AI Engineer. This document provides your complete operational instructions to execute, reproduce, and extend the **Air-Gapped Zero-Leakage TimesFM 3.0 Multi-Agent System**. Follow every protocol strictly.

---

## 1. System Role & Core Principles

You operate as the **Autonomous Multi-Agent Coordinator**. Your highest priority is **Zero Lookahead & Zero Identity Leakage**:
1. **Never allow the forecasting foundation model to see the stock ticker, company name, or calendar dates.**
2. **Always formulate a 3-branch scenario tree (Bear 25%, Base 50%, Bull 25%)** based on audited financial ratios and macroeconomic context known *prior* to the temporal cutoff.
3. **Always package communication between pipeline stages in standardized `A2AMessage` envelopes** (`a2aproject/a2a`).

---

## 2. Step-by-Step Autonomous Execution Workflow

When a user gives you an asset and a cutoff date (e.g. `INFY.NS` at `2020-12-31` or `HEROMOTOCO.NS` at `2023-12-31`), execute this 5-stage pipeline:

```mermaid
flowchart TD
    S1["Stage 1: Ingestion & Qualitative Macro Analysis<br/>(Earnings, Concalls, Fed Policy, India Macro)"] --> S2["Stage 2: Sanitization & Blind-Box Scenarios<br/>(Strip Ticker & Dates -> Generate Bear/Base/Bull)"]
    S2 --> S3["Stage 3: A2A Envelope Packaging<br/>(Numerical Tensors + Dynamic Covariates)"]
    S3 --> S4["Stage 4: Air-Gapped TimesFM 3.0 Execution<br/>(Inference inside Isolated Sandbox on GPU)"]
    S4 --> S5["Stage 5: Output Synthesis & Envelope Audit<br/>(Compute MAE, MAPE, and % Days Inside Bounds)"]
```

---

### Stage 1: Ingestion & Qualitative Macro Sourcing
Ingest historical prices strictly before `--cutoff YYYY-MM-DD`:

```python
import yfinance as yf
import pandas as pd

# Ingest historical data
df = yf.Ticker(ticker).history(period="max", interval=interval)
df.index = pd.to_datetime(df.index).tz_localize(None)
df["Date_str"] = df.index.strftime("%Y-%m-%d")

train_df = df[df["Date_str"] <= cutoff_date].copy()
test_df = df[df["Date_str"] > cutoff_date].copy()
```

#### Qualitative Macro Ingestion Checklist:
1. **Company Earnings**: Check TTM EPS, revenue growth, operating margin guidance, and major deal announcements.
2. **Global Geopolitics**: Check US Fed interest rate regime (rate cut vs rate hike cycle), global IT/commodity demand.
3. **India Situation**: Check domestic GDP growth, monsoon status (rural demand), RBI repo rate, currency (USD/INR).

---

### Stage 2: Sanitization & Scenario Formulation
Strip all identifiable tokens using this regex:

```python
import re

def sanitize_metadata(text: str, ticker: str, company_name: str, cutoff_year: int) -> str:
    # 1. Strip company names and tickers
    text = re.sub(rf"\b{re.escape(ticker)}\b", "[TARGET_ASSET_ALPHA]", text, flags=re.IGNORECASE)
    text = re.sub(rf"\b{re.escape(company_name)}\b", "[TARGET_COMPANY_ALPHA]", text, flags=re.IGNORECASE)
    # 2. Mask calendar years to relative tokens
    text = re.sub(rf"\b{cutoff_year}\b", "[YEAR_T]", text)
    text = re.sub(rf"\b{cutoff_year - 1}\b", "[YEAR_T-1]", text)
    return text
```

#### Generate 3 Discrete Scenarios:
1. **Bear Case (25% Probability)**: Conservative downside valuation (multiple de-rating to 5-year trough).
2. **Base Case (50% Probability)**: Continuation of historical median growth and sector multiples.
3. **Bull Case (25% Probability)**: Growth acceleration, market share gains, and peer multiple parity.

---

### Stage 3: A2A Wire Envelope Dispatch
Serialize the anonymized tensors into a JSON envelope:

```python
a2a_payload = {
    "message_id": f"a2a-{uuid.uuid4().hex[:8]}",
    "sender": "Main_Ingestion_Agent",
    "recipient": "Process_Sandbox_Agent",
    "security_metadata": {
        "isolation_level": "AIR_GAPPED_NUMERICAL",
        "entity_masking": "ACTIVE",
        "contains_real_ticker": False,
        "contains_calendar_dates": False,
        "prohibited_tokens": [ticker, company_name, str(cutoff_year)]
    },
    "payload": {
        "asset_pseudonym": "ASSET_ALPHA",
        "context_length": len(context_array),
        "horizon": horizon_steps,
        "last_known_scalar": float(context_array[-1]),
        "numerical_context": context_array.tolist(),
        "scenarios": {
            "bear": {"probability": 0.25, "target_price": bear_target},
            "base": {"probability": 0.50, "target_price": base_target},
            "bull": {"probability": 0.25, "target_price": bull_target}
        },
        "covariates": {
            "bear": bear_s_curve.tolist(),
            "base": base_s_curve.tolist(),
            "bull": bull_s_curve.tolist()
        }
    }
}
```

---

### Stage 4: Sandboxed TimesFM 3.0 Execution

1. **Verify Security Gate**:
   ```python
   payload_str = json.dumps(a2a_payload["payload"])
   for token in a2a_payload["security_metadata"]["prohibited_tokens"]:
       if re.search(rf"\b{re.escape(token)}\b", payload_str, re.IGNORECASE):
           raise SecurityError(f"CRITICAL LEAKAGE: Prohibited token '{token}' found!")
   ```

2. **Run PyTorch Inference on GPU**:
   ```python
   from timesfm3 import TimesFM3Forecaster

   forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cuda")

   # For each scenario, run TimesFM with future covariates:
   result = forecaster.predict(
       context=ctx_tensor,
       horizon=horizon_steps,
       past_future_covariates=cov_tensor,
       padding_mode="edge",
       return_quantiles=False
   )
   ```

---

### Stage 5: Output Synthesis & Evaluation

1. **Calculate Accuracy**:
   * Multi-Year Mean Absolute Percentage Error (MAPE):
     $$\text{MAPE} = \frac{1}{H} \sum_{t=1}^{H} \left| \frac{P_{\text{actual}}(t) - \hat{y}(t)}{P_{\text{actual}}(t)} \right| \times 100\%$$
2. **Calculate Scenario Envelope Coverage**:
   * The percentage of actual trading days/months that fell inside the Bear-to-Bull boundaries:
     $$\text{Coverage} = \frac{\sum_{t=1}^{H} \mathbb{I}\Big( P_{\text{actual}}(t) \in [\hat{y}_{\text{bear}}(t) \times 0.90, \hat{y}_{\text{bull}}(t) \times 1.10] \Big)}{H} \times 100\%$$

---

## 3. Terminal Command Reference

If executing this in bash or inside a remote shell:

```bash
# 1. Run Verification Test
python3 MULTI_AGENT_SANDBOX/test_multi_agent_flow.py

# 2. Run Custom Ticker Analysis
python3 MULTI_AGENT_SANDBOX/multi_agent_system.py \
  --ticker INFY.NS \
  --cutoff 2020-12-31 \
  --horizon 60 \
  --output_dir ./results

# 3. Cloud GPU Execution via Google Colab CLI
colab --auth=adc exec -s infosys-gpu -f MULTI_AGENT_SANDBOX/test_multi_agent_flow.py --timeout 300
```
