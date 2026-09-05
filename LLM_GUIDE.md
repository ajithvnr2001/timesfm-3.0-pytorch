# Universal LLM System Guide
### Autonomous Operation Manual for Any AI Assistant (Claude, ChatGPT, Gemini, Codex, Antigravity)

> **Directive for Any AI Model Reading This Repository**:  
> You are acting as an Autonomous Quantitative Systems Engineer. This guide provides your master instructions to understand, run, debug, and extend this codebase.

---

## 1. Golden Rules of Operation

1. **Institutional Grade by Default**: All forecasts must default to Tier-1 institutional quantitative standards (`--mode institutional`), incorporating macro regimes, VaR/CVaR, Half-Kelly sizing, and Indian market friction deductions.
2. **Live Real-Time by Default**: When the user requests a forecast for today's market, do **NOT** pass an old historical `--cutoff`. Leave `--cutoff` empty or `None` so the system automatically ingests the latest real-time closing session.
3. **Strict Temporal Integrity for Backtests**: Never allow future information past a `--cutoff` date to enter the model context during backtests.
4. **Physical Blindfold**: In backtest or multi-agent modes, the forecasting foundation model must **never** receive the ticker, company name, or calendar dates.
5. **Statement-Audited Fundamentals**: Always use official audited diluted EPS and dynamic peer-group sector multiples via `scenario_builder.py`.
6. **Mandatory 3 Scenarios**: Always output Bear (25%), Base (50%), and Bull (25%) scenarios with explicit fundamental justifications.
7. **Evaluate with Scenario Envelope Coverage**: Terminal accuracy alone is not enough; report what percentage of historical days stayed inside the Bear-to-Bull envelope.

---

## 2. Directory Sitemap for AI Agents

```
timesfm-3.0-pytorch/
├── run_pipeline.py                         # Unified Entry-point CLI (Defaults to institutional mode)
├── institutional_engine.py                 # Macro regimes, VaR/CVaR, Half-Kelly, STT friction deduction
├── scenario_builder.py                     # Statement-audited diluted EPS & dynamic sector valuation
├── covfree_forecaster.py                   # Volatility-preserving trajectory diffusion math
├── test_agents.py                          # 4-Component unit & security regression test suite
├── requirements.txt                        # Master dependencies
├── USER_GUIDE.md                           # Plain-English manual for traders & analysts
├── DEVELOPER_GUIDE.md                      # Engineering architecture & extensibility guide
├── LLM_GUIDE.md                            # This universal AI operational manual
├── MODES_GUIDE.md                          # Guide to all 5 operating modes
├── MULTI_AGENT_SANDBOX/                    # 🌟 Air-Gapped Multi-Agent Triad
│   ├── MASTER_MULTI_AGENT_GUIDE.md         # Master architectural blueprint
│   ├── QUALITATIVE_DATA_AND_MACRO_GUIDE.md # Earnings, Fed policy & India macro integration
│   ├── LLM_AGENT_INSTRUCTIONS.md           # Standalone system prompt for sub-agents
│   ├── multi_agent_system.py               # Complete 3-Agent production code
│   └── test_multi_agent_flow.py            # 1-Click verification test script
├── INFOSYS_MONTHLY/                        # 5-Year Monthly Large-Cap Benchmark (60 Months)
├── HEROMOTOCO/                             # 2.7-Year Daily Large-Cap Benchmark (663 Days)
├── HYBRID_GUIDE/                           # Mathematical and semantic reasoning guide
├── INTRADAY/                               # Hourly index & options expiry forecasting
└── OPTIONS/                                # Volatility smile and strike forecasting
```

---

## 3. How to Execute Common User Tasks

### Task A: "Analyze / Predict [Stock] today (Live Real-Time Close)"
* **Mode**: `institutional` (DEFAULT)
* **Command**:
  ```bash
  python3 run_pipeline.py --ticker <TICKER> --horizon 30
  ```
  *Executes on live real-time market data, produces Half-Kelly sizing, VaR, friction deduction, and high-resolution forecast charts.*

### Task B: "Run an air-gapped historical backtest for [Stock] up to [Year]"
* **Mode**: `multi-agent`
* **Command**:
  ```bash
  python3 run_pipeline.py --mode multi-agent --ticker <TICKER> --cutoff <YYYY-MM-DD> --horizon <STEPS>
  ```

### Task C: "Predict today's Nifty index or weekly options expiry"
* **Mode**: `intraday`
* **Command**:
  ```bash
  python3 run_pipeline.py --mode intraday --ticker ^NSEI
  ```

### Task D: "Verify system integrity, security gates, and risk formulas"
* **Command**:
  ```bash
  python3 test_agents.py
  ```

---

## 4. Semantic Reasoning LLM Layer (NVIDIA NIM)

In addition to quantitative foundation models (TimesFM 3.0), the pipeline incorporates a deep-reasoning LLM layer (`llm_reasoner.py`) powered by **NVIDIA NIM**:

### Supported NIM Models:
- **Primary**: `moonshotai/kimi-k3` (Deep Chain-of-Thought Reasoning with `reasoning_effort="max"`)
- **High-Throughput Fallback**: `meta/llama-3.2-11b-vision-instruct` (Immediate latency, active when primary encounters 429/rate-limiting)
- **Deterministic Math Fallback**: Audited financial statement CAGR bands (`scenario_builder.py`)

### LLM Pipeline Role:
1. **Input**: Real-time audited Diluted EPS, Industry Benchmark P/E, Historical EPS CAGR, and Qualitative Catalysts / Earnings Disclosures.
2. **LLM Synthesis**: The LLM evaluates premium/discount drivers, competitive moats, and cyclicity to calibrate 12-month Forward P/E multiples and probability weights ($P_{bear}, P_{base}, P_{bull}$).
3. **Quantitative Guardrail**: The quantitative engine enforces strict mathematical integrity ($Target Price = EPS \times Target P/E$), preventing hallucinated arithmetic while preserving the qualitative reasoning.
4. **TimesFM 3.0 Vectorized Ingestion**: The resulting scenario trajectories and calibrated target endpoints are fed directly into TimesFM 3.0 on CUDA via single-pass `predict_batch`.

