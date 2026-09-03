# Universal LLM System Guide
### Autonomous Operation Manual for Any AI Assistant (Claude, ChatGPT, Gemini, Codex, Antigravity)

> **Directive for Any AI Model Reading This Repository**:  
> You are acting as an Autonomous Quantitative Systems Engineer. This guide provides your master instructions to understand, run, debug, and extend this codebase.

---

## 1. Golden Rules of Operation

1. **Strict Temporal Integrity**: Never allow future information past a `--cutoff` date to enter the model context.
2. **Physical Blindfold**: In backtest or multi-agent modes, the forecasting foundation model must **never** receive the ticker, company name, or calendar dates.
3. **Mandatory 3 Scenarios**: Always output Bear (25%), Base (50%), and Bull (25%) scenarios with explicit fundamental justifications.
4. **Evaluate with Scenario Envelope Coverage**: Terminal accuracy alone is not enough; report what percentage of historical days stayed inside the Bear-to-Bull envelope.

---

## 2. Directory Sitemap for AI Agents

```
timesfm-3.0-pytorch/
├── run_pipeline.py                         # Unified Entry-point CLI (Dispatches to all modes)
├── requirements.txt                        # Master dependencies
├── USER_GUIDE.md                           # Plain-English manual for traders & analysts
├── DEVELOPER_GUIDE.md                      # Engineering architecture & extensibility guide
├── LLM_GUIDE.md                            # This universal AI operational manual
├── MODES_GUIDE.md                          # Guide to multi-agent, backtest, live, and intraday modes
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

### Task A: "Run a backtest for [Stock] up to [Year]"
* **Mode**: `multi-agent`
* **Command**:
  ```bash
  python3 run_pipeline.py --mode multi-agent --ticker <TICKER> --cutoff <YYYY-MM-DD> --horizon <STEPS>
  ```

### Task B: "Forecast where [Stock] will go over the next 60 days"
* **Mode**: `live`
* **Command**:
  ```bash
  python3 run_pipeline.py --mode live --ticker <TICKER> --horizon 60
  ```

### Task C: "Predict today's Nifty index or expiry"
* **Mode**: `intraday`
* **Command**:
  ```bash
  python3 run_pipeline.py --mode intraday --ticker ^NSEI
  ```

### Task D: "Verify that the multi-agent system is working and leak-free"
* **Command**:
  ```bash
  python3 MULTI_AGENT_SANDBOX/test_multi_agent_flow.py
  ```
