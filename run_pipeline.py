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
        default="institutional",
        choices=["institutional", "multi-agent", "screen", "backtest", "live", "intraday"],
        help="Execution mode (default: institutional - Tier-1 Quantitative Hedge Fund Grade)"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="INFY.NS",
        help="Stock ticker symbol (e.g. INFY.NS, HEROMOTOCO.NS, MODISONLTD.NS, ^NSEI)"
    )
    parser.add_argument(
        "--cutoff",
        type=str,
        default="2024-01-01",
        help="Strict point-in-time cutoff date YYYY-MM-DD (for backtest and multi-agent modes)"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=30,
        help="Forecast horizon in bars (default: 30)"
    )
    parser.add_argument(
        "--portfolio_capital",
        type=float,
        default=1000000.0,
        help="Portfolio capital in INR for Half-Kelly and risk-budget position sizing (default: 10,00,000)"
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
    print(" GOOGLE TIMESFM 3.0 INSTITUTIONAL-GRADE QUANTITATIVE PIPELINE")
    print(f" Mode: {args.mode.upper()} | Target: {args.ticker} | Horizon: {args.horizon} Days")
    print(f" Portfolio Capital: Rs. {args.portfolio_capital:,.2f} | Standard: Tier-1 Hedge Fund")
    print("=================================================================\n")

    if args.mode in ["institutional", "multi-agent"]:
        sys.path.insert(0, os.path.join(repo_root, "MULTI_AGENT_SANDBOX"))
        sys.path.insert(0, repo_root)
        from multi_agent_system import MultiAgentCoordinator
        print("[Dispatcher] Launching Zero-Leakage Multi-Agent Triad (Institutional Engine)...")
        coordinator = MultiAgentCoordinator()
        record = coordinator.run(
            ticker=args.ticker,
            cutoff_date=args.cutoff,
            horizon=args.horizon,
            output_dir=args.output_dir
        )

        scorecard = record.get("institutional_scorecard")
        if scorecard:
            risk = scorecard["institutional_risk_and_sizing"]
            macro = scorecard["macro_environment"]
            sec = scorecard["sector_relative_strength"]

            print("\n" + "="*65)
            print(f" INSTITUTIONAL EXECUTIVE DIRECTIVE: {args.ticker}")
            print("="*65)
            print(f"• Recommendation:         {risk['institutional_directive']}")
            print(f"• Current Price:          Rs. {scorecard['last_close']:,.2f}")
            print(f"• Expected Target:        Rs. {scorecard['timesfm_probabilistic_forecast']['terminal_expected']:,.2f}")
            print(f"• Invalidation Stop-Loss: Rs. {risk['stop_loss_invalidation_level']:,.2f} (Downside: -{risk['downside_risk_pct']:.1f}%)")
            print(f"• Net Horizon Upside:     {risk['net_upside_pct']:+.2f}% (STT/Frictions -0.25% deducted)")
            print(f"• Asymmetric R/R Ratio:   {risk['net_risk_reward_ratio']}x")
            print(f"• 95% Horizon VaR:        {risk['var_95_horizon_pct']:.2f}% | CVaR (Tail): {risk['cvar_95_horizon_pct']:.2f}%")
            print(f"• NIFTY Regime:           {macro['nifty_trend']} (VIX: {macro['india_vix']:.1f} - {macro['vix_regime']})")
            print(f"• Sector Beta:            {sec['beta_sector']} vs {sec['sector_index_ticker']}")
            print(f"• Half-Kelly Allocation:  {risk['half_kelly_alloc_pct']}% of portfolio")
            print(f"• Sized Capital:          Rs. {risk['recommended_capital_inr']:,.2f} ({risk['recommended_shares']} shares)")
            print("="*65 + "\n")

    elif args.mode in ["backtest", "live"]:
        script_path = os.path.join(repo_root, "HYBRID_GUIDE", "hybrid_agentic_pipeline.py")
        cmd = [
            sys.executable,
            script_path,
            "--mode", args.mode,
            "--tickers", args.ticker,
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


