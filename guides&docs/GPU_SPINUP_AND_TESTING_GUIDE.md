# GPU Spin-Up, Execution & Testing Master Guide
## Google TimesFM 3.0 Hybrid Quantitative Engine

> **Operational Notice**:  
> This guide is an authoritative, step-by-step manual for provisioning, configuring, running, and testing the Google TimesFM 3.0 Hybrid Multi-Agent Quantitative Engine on GPU hardware (Google Colab T4/A100, Cloud GPU VMs, or local CUDA environments). All active API keys are hardcoded for immediate plug-and-play execution.

---

## 1. Hardcoded Credentials & Instant Spin-Up Configuration

Because this repository is private, all production credentials are hardcoded below for instantaneous zero-configuration execution:

| Service | Environment Variable | Hardcoded Value | Purpose |
| :--- | :--- | :--- | :--- |
| **AkashML** | `AKASHML_API_KEY` | `akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL` | Qualitative scenario reasoning & multiple calibration (`zai-org/GLM-5.3`) |
| **Exa Search** | `EXA_API_KEY` | `5a51f858-e6b9-41ee-8881-e61b8af5821f` | Pre-cutoff regulatory disclosures & capacity expansions |
| **NVIDIA NIM** | `NVIDIA_NIM_API_KEY` | `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` | Secondary fallback reasoning endpoint |
| **GitHub Repo** | `GIT_CLONE_URL` | `https://@github.com/ajithvnr2001/timesfm-3.0-pytorch.git` | Authenticated Git clone URL with embedded PAT |

### Ready-to-Run Shell Export:
```bash
export AKASHML_API_KEY="akml-QGBqqzmgXkPlYbxwjbTRUKmHrfHrEicL"
export EXA_API_KEY="5a51f858-e6b9-41ee-8881-e61b8af5821f"
export NVIDIA_NIM_API_KEY="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"
```

---

## 2. Method 1: Google Colab CLI Spin-Up & Testing

The Google Colab CLI (`colab`) allows fully autonomous provisioning, package installation, code execution, and artifact retrieval directly from terminal or agent sessions.

### Step 1: Authentication & Session Verification
```bash
# Authenticate and inspect existing sessions
colab --auth=adc sessions
```
> [!CAUTION]
> **CRITICAL RULE**: NEVER terminate persistent background sessions such as `[discos4]`. Only create, execute on, and terminate dedicated sessions (e.g. `timesfm-gpu`).

---

### Step 2: Spin Up the GPU Runtime
```bash
# Provision a standard T4 GPU runtime named 'timesfm-gpu'
colab --auth=adc new -s timesfm-gpu --gpu T4

# (Optional: If A100 High-Memory GPU is available on your subscription)
# colab --auth=adc new -s timesfm-gpu --gpu A100 --high-mem
```

---

### Step 3: Fast Dependency Installation (~7 seconds)
The Colab CLI utilizes `uv` for lightning-fast wheel installation on remote VMs:
```bash
colab --auth=adc install -s timesfm-gpu   git+https://github.com/google-research/timesfm.git   yfinance pypdf matplotlib pandas numpy scipy requests
```

---

### Step 4: Upload Codebase to Remote GPU VM
```bash
# Upload the local repository to /content/timesfm_repo on the remote machine
colab --auth=adc upload -s timesfm-gpu /root/timesfm_repo/ /content/timesfm_repo/

# Verify uploaded files
colab --auth=adc ls -s timesfm-gpu content/timesfm_repo
```

---

### Step 5: Test GPU Hardware Acceleration
Verify that PyTorch recognizes the allocated GPU device:
```bash
echo "
import torch
print('PyTorch Version:', torch.__version__)
print('CUDA Available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Allocated GPU:', torch.cuda.get_device_name(0))
    print('VRAM Available:', round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2), 'GB')
" | colab --auth=adc exec -s timesfm-gpu
```
*Expected Output*:
```
CUDA Available: True
Allocated GPU: Tesla T4
VRAM Available: 14.75 GB
```

---

### Step 6: Execute the Testing Suite on Remote GPU

#### Test A: Security Isolation & Air-Gap Audit (Level 1)
```bash
colab --auth=adc exec -s timesfm-gpu "python3 /content/timesfm_repo/v2/MULTI_AGENT_SANDBOX/test_agents.py"
```
*Verification Criteria*: `ALL TESTS PASSED` (catches poisoned tickers/dates and allows clean anonymous payloads).

#### Test B: End-to-End Multi-Agent Flow Test (Level 3)
```bash
colab --auth=adc exec -s timesfm-gpu --timeout 180.0 "python3 /content/timesfm_repo/v2/MULTI_AGENT_SANDBOX/test_multi_agent_flow.py"
```
*Verification Criteria*: Executes full 3-agent triad and generates forecast plot and report in `/content/timesfm_repo/test_results/test_run_output/`.

#### Test C: 2026 Zero-Leakage GPU Backtest (CUPID.NS)
```bash
colab --auth=adc exec -s timesfm-gpu --timeout 300.0 "
python3 /content/timesfm_repo/v2/run_pipeline.py   --ticker CUPID.NS   --cutoff 2025-12-31   --horizon 170   --output_dir /content/timesfm_repo/test_results/CUPID_2026_OUTPUT
"
```
*Verification Criteria*: Terminal predicted price ₹250.67 vs actual ₹279.95 (error -10.46%, win probability 76%, Half-Kelly 15%).

#### Test D: Live Forward 90-Day Forecast (INFY.NS)
```bash
colab --auth=adc exec -s timesfm-gpu --timeout 180.0 "
python3 /content/timesfm_repo/v2/run_pipeline.py   --ticker INFY.NS   --horizon 63   --output_dir /content/timesfm_repo/test_results/LIVE_OUTPUT
"
```

---

### Step 7: Download Generated Charts & Reports to Local Machine
```bash
# Download CUPID forecast plot and report
colab --auth=adc download -s timesfm-gpu   /content/timesfm_repo/test_results/CUPID_2026_OUTPUT/CUPID.NS_multi_agent_forecast.png   /root/timesfm_repo/test_results/CUPID_2026_OUTPUT/CUPID.NS_gpu_forecast.png

colab --auth=adc download -s timesfm-gpu   /content/timesfm_repo/test_results/CUPID_2026_OUTPUT/CUPID.NS_executive_report.md   /root/timesfm_repo/test_results/CUPID_2026_OUTPUT/CUPID.NS_gpu_report.md
```

---

### Step 8: Safe Teardown & Quota Conservation
When finished with your computation, release the instance:
```bash
colab --auth=adc stop -s timesfm-gpu
```

#### Quota Recovery: Fixing Error 412 (`TooManyAssignmentsError`)
If Colab blocks session creation because of zombie VM assignments, run this Python snippet:
```python
from colabtools import state
sessions = state.client.list()
for s in sessions:
    if "discos4" not in s.name:
        print(f"Releasing stale session: {s.name}")
        state.client.unassign(s.endpoint)
print("Quota successfully cleared.")
```

---

## 3. Method 2: Dedicated Cloud GPU VM (RunPod, Lambda Labs, AWS, GCP)

If spinning up on a dedicated cloud GPU instance with Ubuntu and NVIDIA drivers pre-installed:

```bash
# 1. Clone repository with hardcoded PAT
git clone https://@github.com/ajithvnr2001/timesfm-3.0-pytorch.git
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

# 6. Run live 90-day projection
python3 v2/run_pipeline.py --ticker TCS.NS --horizon 63
```

---

## 4. Method 3: Interactive Google Colab Web Notebook

To run the entire pipeline inside a standard interactive browser-based Google Colab notebook:

```python
# ==============================================================================
# CELL 1: SETUP & REPO CLONING (Run in Google Colab Web UI)
# Set Runtime -> Change runtime type -> T4 GPU
# ==============================================================================
!git clone https://@github.com/ajithvnr2001/timesfm-3.0-pytorch.git /content/timesfm_repo
%cd /content/timesfm_repo

# Install dependencies (using uv for ~7s install)
!pip install -q git+https://github.com/google-research/timesfm.git yfinance pypdf matplotlib pandas numpy scipy requests

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

# Run 2026 Backtest
!python3 /content/timesfm_repo/v2/run_pipeline.py --ticker CUPID.NS --cutoff 2025-12-31 --horizon 170 --output_dir /content/test_output

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
| **2. TimesFM Import** | `from timesfm3 import TimesFM3Evaluator` or `from timesfm import TimesFm` | Imports cleanly without `ImportError` |
| **3. A2A Zero-Leakage** | `python3 v2/MULTI_AGENT_SANDBOX/test_agents.py` | 100% tests pass; forbidden tokens caught |
| **4. Integration Flow** | `python3 v2/MULTI_AGENT_SANDBOX/test_multi_agent_flow.py` | Forecast PNG rendered with Monte Carlo envelope |
| **5. Forecast Execution** | `python3 v2/run_pipeline.py --ticker TCS.NS --horizon 63` | Terminal weighted target, VaR, and Half-Kelly generated |

---

*Master GPU operational document. Autonomously verified and committed.*
