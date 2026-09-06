# Notice: Legacy Benchmark Test Results

The benchmark artifacts and run outputs contained in the subdirectories of `test_results/` (e.g., `BACKTEST_2026_CUTOFF/`, `BATCH_BENCHMARK_OUTPUT/`, `BENCHMARK_2026_OUTPUT/`, `CUPID_2026_BACKTEST/`, `FUSED_GPU_2026/`) were generated during initial exploratory development prior to the **V2 Zero-Leakage Institutional Engine Audit**.

### Key Architectural Upgrades in V2 (`v2/MULTI_AGENT_SANDBOX/`)

1. **Strict Air-Gapped A2A Communication (`A2AMessage`)**:
   - Ticker identities, company names, and calendar timestamps are stripped before entering `ProcessSandboxAgent`.
   - Automated fail-closed whitelist validation on payload keys and numerical leaf checks eliminate forward leakage.

2. **Deterministic Stochastic Bridge Calibration**:
   - Terminal price paths across Monte Carlo / Ornstein-Uhlenbeck stochastic bridges are seeded deterministically using SHA-256 parameter hashes, ensuring 100% bit-exact reproducibility across runs.

3. **Dynamic Foundation Horizon Matching**:
   - `_init_forecaster` dynamically provisions `horizon_len = max(512, horizon)`, preventing neural horizon clipping and tracking exact neural vs. extrapolated boundary points.

4. **Synchronized Time-Series Beta Calculation**:
   - Beta calculations in `institutional_engine.py` now strictly align stock and benchmark series via `DateTimeIndex` inner joins, preventing index misalignments.

5. **Defensive Macro & Value at Risk (VaR) Rendering**:
   - Defensive `fmt_val` formatting protects all markdown and JSON outputs from `NoneType` rendering crashes during offline or missing benchmark data scenarios.

For current, fully-audited institutional runs, execute `v2/MULTI_AGENT_SANDBOX/multi_agent_system.py` or `v2/MULTI_AGENT_SANDBOX/test_multi_agent_flow.py`.
