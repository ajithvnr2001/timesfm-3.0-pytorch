# Execution Modes Guide: Google TimesFM 3.0 System
### How to Select and Run the Right Mode for Your Workflow

The system supports four specialized execution modes tailored for different quantitative objectives:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 4 OPERATING MODES                                  │
├───────────────────────┬───────────────────────────┬────────────────────────────────────┤
│ Mode Flag             │ Primary Purpose           │ Key Characteristics                │
├───────────────────────┼───────────────────────────┼────────────────────────────────────┤
│ 1. `multi-agent`      │ Air-Gapped Zero-Leakage   │ 3-Agent Triad, A2A wire protocol,  │
│                       │ Historical Backtesting    │ 100% physically blind to ticker    │
├───────────────────────┼───────────────────────────┼────────────────────────────────────┤
│ 2. `backtest`         │ Rapid Single-Agent        │ Regex entity masking, 3-scenario   │
│                       │ Historical Validation     │ tree, single-process execution     │
├───────────────────────┼───────────────────────────┼────────────────────────────────────┤
│ 3. `live`             │ Real-Time Forward         │ Unmasked latest fundamentals,      │
│                       │ Investment Projection     │ Exa news, active catalyst pricing  │
├───────────────────────┼───────────────────────────┼────────────────────────────────────┤
│ 4. `intraday`         │ Sub-Daily High Frequency  │ Hourly bars, options volatility,   │
│                       │ Index & Options Trading   │ same-day expiry strike projections │
└───────────────────────┴───────────────────────────┴────────────────────────────────────┘
```

---

## Mode 1: `multi-agent` (The Institutional Gold Standard)

* **When to Use**: When conducting official, verifiable backtests where you need mathematical certainty that the forecasting model did not look ahead or memorize prices from pre-training.
* **Architecture**:
  * Agent 1 (`MainIngestionAgent`): Slices data strictly at `--cutoff YYYY-MM-DD`. Strips all names, tickers, and dates.
  * Agent 2 (`ProcessSandboxAgent`): Isolated sandbox. Runs Google TimesFM 3.0 with zero network access and zero ticker awareness.
  * Agent 3 (`OutputSynthesisAgent`): Computes terminal error, MAPE, and % days inside the scenario envelope.
* **CLI Command**:
  ```bash
  python3 run_pipeline.py \
    --mode multi-agent \
    --ticker INFY.NS \
    --cutoff 2020-12-31 \
    --horizon 60 \
    --output_dir ./output_infosys
  ```

---

## Mode 2: `backtest` (Rapid Single-Agent Historical Validation)

* **When to Use**: When rapidly testing multiple stocks or parameter sweeps in a single Python process without spawning multiple agents.
* **Architecture**:
  * Ingests historical data up to `--cutoff`.
  * Masks entity names and calendar years via `anonymize_text_for_backtest()`.
  * Computes Bear, Base, and Bull scenario curves.
* **CLI Command**:
  ```bash
  python3 run_pipeline.py \
    --mode backtest \
    --ticker HEROMOTOCO.NS \
    --cutoff 2023-12-31 \
    --horizon 663
  ```

---

## Mode 3: `live` (Real-Time Future Projection)

* **When to Use**: When projecting into the future from today's current market session.
* **Architecture**:
  * Ingests latest live prices, latest quarterly filings, and latest broker price targets.
  * Uses unmasked company names so the LLM has full semantic context on recent management changes, capex plans, and product launches.
* **CLI Command**:
  ```bash
  python3 run_pipeline.py \
    --mode live \
    --ticker RELIANCE.NS \
    --horizon 64
  ```

---

## Mode 4: `intraday` (High-Frequency & Options Expiry)

* **When to Use**: During active market sessions (e.g. 09:15 AM to 03:30 PM IST) for day trading and options expiry positioning.
* **Architecture**:
  * Ingests 15-minute and 1-hour OHLCV bars.
  * Projects intraday mean reversion channels and implied volatility boundaries.
* **CLI Command**:
  ```bash
  python3 run_pipeline.py \
    --mode intraday \
    --ticker ^NSEI
  ```
