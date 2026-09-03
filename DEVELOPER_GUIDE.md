# Developer Architecture & Engineering Guide
### Internal Mechanics, API Contracts, Extensibility & Testing

---

## 1. System Architecture Overview

The system is organized into decoupled, modular layers designed for high throughput, testability, and information-barrier enforcement:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                ARCHITECTURAL LAYERS                                    │
├───────────────────────┬────────────────────────────────────────────────────────────────┤
│ 1. Data Connectors    │ • yfinance (OHLCV Market Series)                               │
│                       │ • pypdf (PDF Extraction for Annual Reports & Earnings)         │
│                       │ • exa-py (Neural Search for Point-in-Time Geopolitical News)   │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 2. Agent Plane        │ • MainIngestionAgent (Ingestion, Sanitization, S-Curves)       │
│                       │ • ProcessSandboxAgent (Air-Gapped Foundation Model Execution)  │
│                       │ • OutputSynthesisAgent (Metrics, Visualization, Reporting)     │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 3. Protocol Plane     │ • A2AMessage (Standardized JSON serialization via a2aproject)  │
│                       │ • Ingress Security Gate (Regex Leakage Audit)                  │
├───────────────────────┼────────────────────────────────────────────────────────────────┤
│ 4. Foundation Engine  │ • Google TimesFM 3.0 (google/timesfm-3.0-pytorch) on CUDA      │
│                       │ • Dynamic Past/Future Covariate Cross-Attention                │
└───────────────────────┴────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Python Classes & Responsibilities

### 1. `TimesFM3Forecaster` (`timesfm3/forecaster.py`)
Loads the pretrained PyTorch weights from Hugging Face (`google/timesfm-3.0-pytorch`).
* **Key Method**: `predict(context, horizon, past_only_covariates, past_future_covariates, ...)`
* **Input Tensor Shapes**:
  * `context`: `np.ndarray` of shape `[Batch, Context_Len]` (e.g. `[1, 64]`).
  * `past_future_covariates`: `np.ndarray` of shape `[Batch, Channels, Context_Len + Horizon]` (e.g. `[1, 1, 128]`).
* **Output**: `ForecastResult` namedtuple containing:
  * `forecast`: Array of shape `[Batch, Horizon]` representing the mean expected trajectory.
  * `quantiles`: Array of shape `[Batch, Horizon, 9]` containing quantiles from $10\%$ to $90\%$.

### 2. `A2AMessage` (`MULTI_AGENT_SANDBOX/multi_agent_system.py`)
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

### 3. `ProcessSandboxAgent` (`MULTI_AGENT_SANDBOX/multi_agent_system.py`)
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

Run the unit and integration test suite:
```bash
# Test 1: Verify A2A Message Passing and Security Audit Gate
python3 MULTI_AGENT_SANDBOX/test_multi_agent_flow.py

# Test 2: Run End-to-End Pipeline in Sandbox Mode
python3 run_pipeline.py --mode multi-agent --ticker INFY.NS --cutoff 2020-12-31 --horizon 60
```
