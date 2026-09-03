#!/usr/bin/env python3
"""
run_pipeline.py
===============
Unified Master CLI Entry-Point for the Google TimesFM 3.0 Quantitative System.
Dispatches to:
  • mode 'multi-agent': Air-Gapped 3-Agent Triad (Strict Zero-Leakage)
  • mode 'backtest': Single-Agent Strict Zero-Leakage Validation
  • mode 'live': Real-Time Future Projection with Unmasked Fundamentals
  • mode 'intraday': Hourly Index & Options Volatility Trajectory

Usage:
  python3 run_pipeline.py --mode multi-agent --ticker INFY.NS --cutoff 2020-12-31 --horizon 60
  python3 run_pipeline.py --mode backtest --ticker HEROMOTOCO.NS --cutoff 2023-12-31 --horizon 663
  python3 run_pipeline.py --mode live --ticker RELIANCE.NS --horizon 64
  python3 run_pipeline.py --mode intraday --ticker ^NSEI
"""

import argparse
import os
import sys
import subprocess

def main():
    parser = argparse.ArgumentParser(
        description="Google TimesFM 3.0 Unified Quantitative Execution Pipeline"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="multi-agent",
        choices=["multi-agent", "backtest", "live", "intraday"],
        help="Execution mode (default: multi-agent)"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="INFY.NS",
        help="Stock ticker symbol (e.g. INFY.NS, HEROMOTOCO.NS, ^NSEI)"
    )
    parser.add_argument(
        "--cutoff",
        type=str,
        default="2020-12-31",
        help="Strict point-in-time cutoff date YYYY-MM-DD (for backtest and multi-agent modes)"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=60,
        help="Forecast horizon in bars (default: 60)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./pipeline_results",
        help="Output directory for charts, JSONs, and executive reports"
    )

    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.output_dir, exist_ok=True)

    print("=================================================================")
    print(" GOOGLE TIMESFM 3.0 UNIFIED QUANTITATIVE PIPELINE")
    print(f" Mode: {args.mode.upper()} | Ticker: {args.ticker}")
    print("=================================================================")

    if args.mode == "multi-agent":
        sys.path.insert(0, os.path.join(repo_root, "MULTI_AGENT_SANDBOX"))
        from multi_agent_system import MultiAgentCoordinator
        print("[Dispatcher] Launching Air-Gapped Multi-Agent Triad...")
        coordinator = MultiAgentCoordinator()
        record = coordinator.run(
            ticker=args.ticker,
            cutoff_date=args.cutoff,
            horizon=args.horizon,
            output_dir=args.output_dir
        )
        print("\n[Dispatcher] Multi-Agent Pipeline Completed Successfully!")

    elif args.mode in ["backtest", "live"]:
        script_path = os.path.join(repo_root, "HYBRID_GUIDE", "hybrid_agentic_pipeline.py")
        cmd = [
            sys.executable,
            script_path,
            "--mode", args.mode,
            "--ticker", args.ticker,
            "--horizon", str(args.horizon),
            "--output_dir", args.output_dir
        ]
        if args.mode == "backtest":
            cmd.extend(["--cutoff", args.cutoff])
        print(f"[Dispatcher] Running {args.mode.upper()} mode via {script_path}...")
        subprocess.run(cmd, check=True)

    elif args.mode == "intraday":
        script_path = os.path.join(repo_root, "INTRADAY", "timesfm_intraday_experiment.py")
        print(f"[Dispatcher] Running INTRADAY mode via {script_path}...")
        subprocess.run([sys.executable, script_path], check=True)

if __name__ == "__main__":
    main()

