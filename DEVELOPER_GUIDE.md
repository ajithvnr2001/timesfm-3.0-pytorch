# Developer Architecture & Engineering Guide
### Internal Mechanics, API Contracts, Extensibility & Testing

---

## 1. System Architecture Overview

The system is organized into decoupled, modular layers designed for high throughput, testability, and information-barrier enforcement:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                ARCHITECTURAL LAYERS                                    │
├───────────────────────┬────────────────────────────────────────────────────────────────┤
│ 1. Data Connectors    │ • yfinance (OHLCV Market Series, PIT Audited Statements)       │
│                       │ • pypdf (PDF Extraction for Annual Reports & Earnings)         │
│                       │ • exa-py (Neural Search for Point-in-Time Geopolitical News)   │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 2. Valuation & Risk   │ • scenario_builder.py (Statement-Audited Diluted EPS & Scenarios)│
│                       │ • covfree_forecaster.py (Volatility-Preserving Trajectory Math)│
│                       │ • institutional_engine.py (VaR, CVaR, Half-Kelly, STT Friction)│
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 3. Agent Plane        │ • MainIngestionAgent (Ingestion, Sanitization, PIT Blindfold)  │
│                       │ • ProcessSandboxAgent (Air-Gapped Foundation Model Execution)  │
│                       │ • OutputSynthesisAgent (Scorecard, Visualization, Directives)  │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 4. Protocol Plane     │ • A2AMessage (Standardized JSON serialization via a2aproject)  │
│                       │ • Ingress Security Gate (Regex Leakage Audit)                  │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 5. Foundation Engine  │ • Google TimesFM 3.0 (google/timesfm-3.0-pytorch) on CUDA      │
│                       │ • Vectorized `predict_batch` Multi-Scenario Inference          │
│                       │ • Dynamic Past/Future Covariate Cross-Attention                │
└───────────────────────┴────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Modules, Classes & API Contracts

### 1. `TimesFM3Forecaster` (`timesfm3/forecaster.py`)
Loads the pretrained PyTorch weights from Hugging Face (`google/timesfm-3.0-pytorch`).
* **Key Methods**:
  * `predict(context, horizon, ...)`: Single-series inference.
  * `predict_batch(contexts, horizons, ...)`: Vectorized batched tensor forward pass across all scenarios simultaneously.
* **Input Tensor Shapes**:
  * `context`: `np.ndarray` of shape `[Batch, Context_Len]` (e.g. `[1, 64]`).
  * `past_future_covariates`: `np.ndarray` of shape `[Batch, Channels, Context_Len + Horizon]` (e.g. `[1, 1, 128]`).
* **Output**: `ForecastResult` namedtuple containing `forecast` array `[Batch, Horizon]` and `quantiles` array `[Batch, Horizon, 9]`.

### 2. `scenario_builder` (`scenario_builder.py`)
Extracts audited balance sheet metrics and computes dynamic fundamental valuation scenarios:
```python
fund_res = build_scenarios(ticker="MODISONLTD.NS", current_price=469.95, as_of="2026-09-04")
# Returns:
# - eps: 22.35 (audited diluted EPS)
# - sector_pe: 22.0 (peer-group dynamic multiple)
# - scenarios: {'bear': 424.65, 'base': 480.53, 'bull': 536.40}
# - weighted_target: 480.53
# - thesis: "Modison trades at a ~5% discount to the sector..."
# - source: "llm_akashml_zai-org/GLM-5.3"
```

### 2b. `llm_reasoner` (`llm_reasoner.py`)
Integrates the AkashML semantic reasoning layer (`zai-org/GLM-5.3`) into scenario formulation:
```python
from llm_reasoner import reason_market_scenarios

res = reason_market_scenarios(
    ticker="MODISONLTD.NS",
    current_price=469.95,
    eps=22.35,
    sector_pe=22.0,
    eps_cagr=0.12,
    industry="Metals & Mining",
    recent_news="Debt-free balance sheet; expanding contact material market share."
)
# Returns calibrated Bear/Base/Bull forward multiples, probability weights, and qualitative thesis.
```

### 3. `covfree_forecaster` (`covfree_forecaster.py`)
Replaces unphysical sigmoid heuristics with volatility-preserving forward diffusion:
```python
p_proj, lower_cone, upper_cone = forecast_covfree(
    last_price=469.95,
    target_price=491.70,
    annual_vol=0.25,
    horizon=30
)
```

### 4. `institutional_engine` (`institutional_engine.py`)
Provides Tier-1 hedge fund risk metrics, macro regimes, and position sizing:
```python
scorecard = build_institutional_scorecard(
    ticker="MODISONLTD.NS",
    last_price=469.95,
    fundamental_data=fund_data,
    forecast_results=forecast_tensors,
    horizon=30,
    portfolio_capital=1000000.0
)
# Returns:
# - VaR (95% 1-day & 30-day Horizon)
# - CVaR (Expected Shortfall tail risk)
# - Net Horizon Upside (with -0.25% STT & Indian market frictions deducted)
# - Half-Kelly Allocation & Recommended Share Quantity
# - Objective Invalidation Stop-Loss & Asymmetric R/R Ratio
# - Macro Regimes (^NSEI trend, ^INDIAVIX regime) & Sector Beta
```

### 5. `A2AMessage` (`MULTI_AGENT_SANDBOX/multi_agent_system.py`)
Encapsulates data passing between agents according to the `a2aproject/a2a` standard:
```python
@dataclass
class A2AMessage:
    message_id: str
    sender: str
    recipient: str
    protocol_version: str
    timestamp: str
    security_metadata: Dict[str, Any]
    payload: Dict[str, Any]
```

### 6. `ProcessSandboxAgent` (`MULTI_AGENT_SANDBOX/multi_agent_system.py`)
The air-gapped worker:
* Runs with zero network access.
* Implements `_verify_sandbox_security(message)` to reject any message carrying prohibited tokens (`INFY`, `2020`, etc.).
* Loops across Bear, Base, and Bull scenarios and aggregates the weighted forecast.

---

## 3. How to Extend the System

### Adding a New Data Connector (e.g. Bloomberg B-PIPE or AlphaVantage)
1. Subclass or extend the ingestion method in `MainIngestionAgent`:
   ```python
   def fetch_from_custom_provider(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
       # Implement client API call
       # Return normalized DataFrame with columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
       pass
   ```
2. Ensure timestamps are timezone-naive and sorted chronologically:
   ```python
   df.index = pd.to_datetime(df.index).tz_localize(None)
   df.sort_index(inplace=True)
   ```

### Adding a New Valuation Scenario (e.g. Turnaround Case)
In `synthesize_fundamental_valuation()`, add an entry to the scenario dictionary:
```python
scenarios["turnaround"] = {
    "probability": 0.15,
    "target_price": turnaround_price,
    "label": "Turnaround Case (Restructuring Success)",
    "color": "#ffaa00"
}
# Ensure probabilities sum to 1.0
```

---

## 4. Deploying with Docker & Kubernetes (`agent-sandbox`)

To deploy `ProcessSandboxAgent` in a hardened Kubernetes sandbox:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: timesfm3-process-sandbox
  labels:
    agent.sandbox.k8s.io/role: process-agent
spec:
  containers:
  - name: sandbox-worker
    image: ghcr.io/google-research/timesfm:v3.0-cuda
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: 16Gi
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
    # Sever all outbound internet access to enforce strict air-gap:
    networkPolicy:
      egress: []
```

---

## 5. Testing & Continuous Integration

Run the unit, integration, and institutional test suite:
```bash
# Test 1: Comprehensive 4-Component Unit & Security Regression Suite
python3 test_agents.py

# Test 2: Verify A2A Message Passing and Ingress Security Audit Gate
python3 MULTI_AGENT_SANDBOX/test_multi_agent_flow.py

# Test 3: Run Live Institutional Execution (Real-Time Market Session)
python3 run_pipeline.py --ticker MODISONLTD.NS --horizon 30

# Test 4: Run Historical Backtest in Strict Air-Gapped Mode
python3 run_pipeline.py --mode multi-agent --ticker INFY.NS --cutoff 2020-12-31 --horizon 60
```
