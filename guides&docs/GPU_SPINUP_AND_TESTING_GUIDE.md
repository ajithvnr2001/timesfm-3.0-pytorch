# GPU Spin-Up, Execution & Testing Master Guide
## Google TimesFM 3.0 Hybrid Multi-Agent Quantitative Engine

> **Operational Notice**:  
> This guide is the authoritative, step-by-step manual for provisioning, configuring, validating, running, and testing the Google TimesFM 3.0 Hybrid Multi-Agent Quantitative Engine on GPU hardware (Google Colab T4/A100 via OAuth2 CLI, Cloud GPU VMs, or local CUDA environments). All active API keys are provided for plug-and-play execution.

---

## 1. Hardcoded Credentials & Instant Spin-Up Configuration

Because this repository is private, all production credentials for the quantitative reasoner and data ingestion pipeline are configured below:

| Service | Environment Variable | Hardcoded Value | Purpose |
| :--- | :--- | :--- | :--- |
| **AkashML** | `AKASHML_API_KEY` | `akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL` | Qualitative scenario reasoning & forward multiple calibration (`zai-org/GLM-5.3`) |
| **Exa Search** | `EXA_API_KEY` | `5a51f858-e6b9-41ee-8881-e61b8af5821f` | Pre-cutoff regulatory disclosures, earnings transcripts & capacity expansions |
| **NVIDIA NIM** | `NVIDIA_NIM_API_KEY` | `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` | Secondary fallback reasoning endpoint (`moonshotai/kimi-k3` / `llama-3.2`) |

### Ready-to-Run Shell Export:
```bash
export AKASHML_API_KEY="akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL"
export EXA_API_KEY="5a51f858-e6b9-41ee-8881-e61b8af5821f"
export NVIDIA_NIM_API_KEY="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"
```

---

## 2. Method 1: Google Colab CLI Spin-Up & Testing (`--auth=oauth2`)

The Google Colab CLI (`colab`) allows automated provisioning, dependency installation, code execution, and artifact retrieval directly from your terminal.

### Authentication Modes: OAuth2 vs ADC
* **`--auth=oauth2` (Standard & Recommended)**: Uses Google OAuth2 token stored in `~/.config/colab-cli/token.json` (tied to your Google user account). This matches the authenticated interactive session.
* **`--auth=adc` (Cloud SDK Fallback)**: Uses Google Cloud Application Default Credentials (`gcloud auth application-default login`).

---

### Step 1: Inspect Existing Sessions
```bash
# Check active sessions using OAuth2
colab --auth=oauth2 sessions

# Check status of a specific session
colab --auth=oauth2 status -s discos4
```

> [!IMPORTANT]
> **Colab Free Tier Concurrency & Persistent Session Safety**:
> * **Single Session Limit**: On Colab Free Tier (`subTier: 0`), Google strictly enforces a limit of **1 active runtime** per Google account.
> * If a background session such as `[discos4]` is already running (e.g. running background jobs like `discovery-leecher`), attempting to provision a second runtime (`timesfm-gpu`) will return:
>   `ColabRequestError: 503 Service Unavailable: {"subTier":0,"outcome":2}`
>   (`outcome: 2` denotes that the account has reached its concurrent allocation limit or pool capacity).
> * **DO NOT TERMINATE `[discos4]`**: If `[discos4]` is running a user process, do not kill it. To run the GPU pipeline, either:
>   1. Pause the background task gracefully to free the slot, run the GPU benchmark, and restart it.
>   2. Upgrade to Colab Pro/Pro+ for multiple concurrent GPU/CPU runtimes.
>   3. Use a dedicated cloud GPU VM or interactive Colab web notebook (Method 2 & 3).

---

### Step 2: Spin Up the GPU Runtime
```bash
# Provision a standard T4 GPU runtime named 'timesfm-gpu' via OAuth2
colab --auth=oauth2 new -s timesfm-gpu --gpu T4

# (Optional: If A100 High-Memory GPU is available on Colab Pro+)
# colab --auth=oauth2 new -s timesfm-gpu --gpu A100 --high-mem
```

---

### Step 3: Fast Dependency Installation (~7 seconds)
Colab CLI uses `uv` for high-speed wheel installation on the remote VM:
```bash
colab --auth=oauth2 install -s timesfm-gpu \
  git+https://github.com/google-research/timesfm.git \
  yfinance pypdf matplotlib pandas numpy scipy requests exa_py
```

---

### Step 4: Upload Codebase to Remote GPU VM
```bash
# Package and upload repository
colab --auth=oauth2 upload -s timesfm-gpu /root/timesfm_repo/ /content/timesfm_repo/

# Verify uploaded files
colab --auth=oauth2 ls -s timesfm-gpu content/timesfm_repo
```

---

### Step 5: Test GPU Hardware Acceleration
Verify that PyTorch on the remote VM detects CUDA and the NVIDIA Tesla T4:
```bash
echo "
import torch
print('PyTorch Version:', torch.__version__)
print('CUDA Available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Allocated GPU:', torch.cuda.get_device_name(0))
    print('VRAM Available:', round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2), 'GB')
" | colab --auth=oauth2 exec -s timesfm-gpu
```

*Expected Terminal Output*:
```
PyTorch Version: 2.1.x+cu121 (or newer)
CUDA Available: True
Allocated GPU: Tesla T4
VRAM Available: 14.75 GB
```

---

### Step 6: Execute the Full Test Suite on Remote GPU

#### Test A: Security Isolation & Air-Gap Audit (Level 1)
```bash
colab --auth=oauth2 exec -s timesfm-gpu "python3 /content/timesfm_repo/v2/MULTI_AGENT_SANDBOX/test_agents.py"
```
*Verification Criteria*: `4/4 PASS`. Catches poisoned tickers, calendar leakage, and verifies blind-box payload transfer.

#### Test B: End-to-End Multi-Agent Flow Test (Level 2)
```bash
colab --auth=oauth2 exec -s timesfm-gpu --timeout 180.0 "cd /content/timesfm_repo/v2/MULTI_AGENT_SANDBOX && python3 test_multi_agent_flow.py"
```
*Verification Criteria*: Executes full 3-agent triad (`MainIngestionAgent` ➔ `ProcessSandboxAgent` ➔ `OutputSynthesisAgent`) with clean output.

#### Test C: 2026 Zero-Leakage GPU Backtest (CUPID.NS)
```bash
colab --auth=oauth2 exec -s timesfm-gpu --timeout 300.0 "
cd /content/timesfm_repo && python3 v2/run_2026_prediction_benchmark.py \
  --ticker CUPID.NS \
  --cutoff 2025-01-01 \
  --horizon 170 \
  --output_dir /content/gpu_output
"
```
*Verification Criteria*: Generates executive report, high-resolution chart, and institutional risk metrics in `/content/gpu_output`.

---

### Step 7: Download Generated Charts & Reports
```bash
# Download CUPID forecast plot and report
colab --auth=oauth2 download -s timesfm-gpu \
  /content/gpu_output/CUPID.NS_multi_agent_forecast.png \
  /root/timesfm_repo/test_results/CUPID_2026_BACKTEST/CUPID.NS_multi_agent_forecast.png

colab --auth=oauth2 download -s timesfm-gpu \
  /content/gpu_output/CUPID.NS_executive_report.md \
  /root/timesfm_repo/test_results/CUPID_2026_BACKTEST/CUPID.NS_executive_report.md

colab --auth=oauth2 download -s timesfm-gpu \
  /content/gpu_output/CUPID.NS_multi_agent_results.json \
  /root/timesfm_repo/test_results/CUPID_2026_BACKTEST/CUPID.NS_multi_agent_results.json
```

---

### Step 8: Safe Teardown & Quota Conservation
When finished with your test session, stop the VM:
```bash
colab --auth=oauth2 stop -s timesfm-gpu
```

#### Quota Recovery & Session Synchronization:
If you ever encounter zombie assignments or local session desynchronization:
```python
from colab_cli.common import state
state.auth_provider = 'oauth2'
sessions, assignments = state.sync_sessions()
print("Active Assignments:", assignments)
# To safely inspect without dropping discos4:
for a in assignments:
    print(f"Endpoint: {a.endpoint} | Variant: {a.variant.name} | Accel: {a.accelerator.value}")
```

---

## 3. Method 2: Dedicated Cloud GPU VM (RunPod, Lambda Labs, AWS, GCP)

If executing on a dedicated cloud GPU instance with Ubuntu and NVIDIA drivers:

```bash
# 1. Clone repository
git clone https://github.com/ajithvnr2001/timesfm-3.0-pytorch.git
cd timesfm-3.0-pytorch

# 2. Export active API keys
export AKASHML_API_KEY="akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL"
export EXA_API_KEY="5a51f858-e6b9-41ee-8881-e61b8af5821f"
export NVIDIA_NIM_API_KEY="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"

# 3. Install dependencies
pip install torch torchvision tqdm yfinance pandas numpy scipy matplotlib seaborn pypdf exa-py requests
pip install git+https://github.com/google-research/timesfm.git

# 4. Verify GPU
nvidia-smi

# 5. Run end-to-end integration test
python3 v2/MULTI_AGENT_SANDBOX/test_multi_agent_flow.py

# 6. Run live multi-agent benchmark
python3 v2/run_2026_prediction_benchmark.py --ticker CUPID.NS --cutoff 2025-01-01 --horizon 170
```

---

## 4. Method 3: Interactive Google Colab Web Notebook

To run the entire pipeline inside an interactive browser-based Google Colab notebook:

```python
# ==============================================================================
# CELL 1: SETUP & REPO CLONING (Run in Google Colab Web UI)
# Set Runtime -> Change runtime type -> T4 GPU
# ==============================================================================
!git clone https://github.com/ajithvnr2001/timesfm-3.0-pytorch.git /content/timesfm_repo
%cd /content/timesfm_repo

# Install dependencies
!pip install -q git+https://github.com/google-research/timesfm.git yfinance pypdf matplotlib pandas numpy scipy requests exa_py

# Set hardcoded environment keys
import os
os.environ["AKASHML_API_KEY"] = "akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL"
os.environ["EXA_API_KEY"] = "5a51f858-e6b9-41ee-8881-e61b8af5821f"
os.environ["NVIDIA_NIM_API_KEY"] = "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"

# Verify GPU
import torch
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device Name:", torch.cuda.get_device_name(0))

# Run 2026 Backtest Benchmark
!python3 /content/timesfm_repo/v2/run_2026_prediction_benchmark.py --ticker CUPID.NS --cutoff 2025-01-01 --horizon 170 --output_dir /content/test_output

# Display generated forecast plot inline
from IPython.display import Image, display
display(Image('/content/test_output/CUPID.NS_multi_agent_forecast.png'))
```

---

## 5. Testing & Verification Checklist

When spinning up a new GPU environment, verify these 5 checkpoints:

| Checkpoint | Command | Acceptance Standard |
| :--- | :--- | :--- |
| **1. GPU Device** | `torch.cuda.is_available()` | Returns `True` with device name (Tesla T4, A100, etc.) |
| **2. TimesFM Import** | `from timesfm import TimesFm` | Imports cleanly without `ImportError` |
| **3. A2A Zero-Leakage** | `python3 v2/MULTI_AGENT_SANDBOX/test_agents.py` | 4/4 tests pass; forbidden tokens caught |
| **4. Integration Flow** | `python3 v2/MULTI_AGENT_SANDBOX/test_multi_agent_flow.py` | Full multi-agent pipeline completes without errors |
| **5. Forecast Execution** | `python3 v2/run_2026_prediction_benchmark.py` | Terminal price, error %, VaR, and Half-Kelly generated |

---
*Master GPU operational document. Fully synchronized with V2 Multi-Agent Architecture.*
