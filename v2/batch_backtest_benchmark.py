#!/usr/bin/env python3
"""
batch_backtest_benchmark.py
===========================
Executes full end-to-end multi-agent backtest across 5 diverse assets:
1. STLTECH.NS (Declining optical fiber / high debt)
2. MODISONLTD.NS (Consolidating industrial contacts)
3. NETWEB.NS (High-growth AI supercomputing / NVIDIA partner)
4. AETHER.NS (Specialty chemicals / Surat plant fire aftermath)
5. CUPID.NS (Promoter takeover / FMCG transformation)

Constraint: Strictly historical data up to 2023-12-31 (Cutoff).
Horizon: 60 Trading Days (Q1 2024).
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURR_DIR) if os.path.basename(CURR_DIR) == "v2" else CURR_DIR
sys.path.insert(0, CURR_DIR)
sys.path.insert(0, os.path.join(CURR_DIR, "MULTI_AGENT_SANDBOX"))
sys.path.insert(0, REPO_ROOT)

from multi_agent_system import MultiAgentCoordinator

def run_batch_benchmark():
    tickers = ["STLTECH.NS", "MODISONLTD.NS", "NETWEB.NS", "AETHER.NS", "CUPID.NS"]
    cutoff = "2023-12-31"
    horizon = 60
    out_dir = os.path.join(REPO_ROOT, "test_results", "BATCH_BENCHMARK_OUTPUT")
    os.makedirs(out_dir, exist_ok=True)

    coordinator = MultiAgentCoordinator()
    all_results = []

    print("==========================================================================")
    print(f" STARTING MULTI-ASSET INSTITUTIONAL BACKTEST BENCHMARK")
    print(f" Assets: {', '.join(tickers)}")
    print(f" Cutoff: {cutoff} | Horizon: {horizon} Trading Days")
    print("==========================================================================\n")

    for tk in tickers:
        print(f"\n>>> Running Benchmark on {tk}...")
        try:
            rec = coordinator.run(tk, cutoff_date=cutoff, horizon=horizon, output_dir=out_dir)
            all_results.append(rec)
            print(f">>> [SUCCESS] {tk} completed!")
        except Exception as e:
            print(f">>> [ERROR] {tk} failed: {e}")
            import traceback
            traceback.print_exc()

    # Save summary JSON
    summary_path = os.path.join(out_dir, "batch_benchmark_summary.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSummary saved to: {summary_path}")

    # Generate 5-Panel High-Resolution Benchmark Plot
    generate_multi_panel_chart(all_results, out_dir)

    # Print Terminal Comparison Table
    print_summary_table(all_results)

def generate_multi_panel_chart(all_results, out_dir):
    n = len(all_results)
    if n == 0:
        return
    fig, axes = plt.subplots(n, 1, figsize=(14, 4.5 * n), dpi=140, sharex=False)
    if n == 1:
        axes = [axes]

    for i, rec in enumerate(all_results):
        ax = axes[i]
        tk = rec["ticker"]
        metrics = rec["metrics"]
        cal = rec["calendar"]
        
        test_dates = [pd.to_datetime(d) for d in cal["actual_dates"]]
        actual_prices = cal["actual_closes"]
        pure_tfm = rec["predictions"]["pure_baseline"]
        weighted_hyb = rec["predictions"]["weighted"]
        bull_proj = rec["predictions"]["scenarios"]["bull"]
        bear_proj = rec["predictions"]["scenarios"]["bear"]
        int_low = rec["predictions"].get("interval_lower", cal.get("interval_lower", bear_proj))
        int_high = rec["predictions"].get("interval_upper", cal.get("interval_upper", bull_proj))
        cov_pct = metrics.get("interval_80_coverage_pct", metrics.get("envelope_coverage_pct", 0.0))

        # 1. Actual Market Ground Truth
        ax.plot(test_dates, actual_prices, label=f"Actual Ground Truth (Day 60: Rs. {metrics['actual_terminal']:.2f})", color="#107c41", linewidth=2.5)

        # 2. Pure TimesFM 3.0 Baseline
        ax.plot(test_dates, pure_tfm, label=f"Pure TimesFM 3.0 (Rs. {metrics['pure_baseline_terminal']:.2f}, Err: {metrics['pure_baseline_error_pct']:+.1f}%)", color="#d83b01", linestyle="--", linewidth=1.8)

        # 3. Weighted Hybrid (TimesFM + Catalyst LLM)
        ax.plot(test_dates, weighted_hyb, label=f"Weighted Hybrid (Rs. {metrics['weighted_terminal']:.2f}, Err: {metrics['weighted_error_pct']:+.1f}%)", color="#0078d4", linewidth=2.2)

        # 4. 80% Prediction Interval
        ax.fill_between(test_dates, int_low[:len(test_dates)], int_high[:len(test_dates)], color="#0078d4", alpha=0.15, label=f"80% Prediction Interval ({cov_pct:.0f}% Coverage)")

        start_p = actual_prices[0]
        end_p = actual_prices[-1]
        act_chg = (end_p - start_p) / start_p * 100

        ax.set_title(f"{tk} | Start: Rs. {start_p:.2f} -> Actual 60d: Rs. {end_p:.2f} ({act_chg:+.1f}%) | Hybrid Err: {metrics['weighted_error_pct']:+.1f}% | Coverage: {cov_pct:.0f}%", fontsize=12, fontweight="bold", pad=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.set_ylabel("Price (INR)", fontsize=10)
        ax.legend(loc="best", fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle=":")

    plt.tight_layout()
    chart_path = os.path.join(out_dir, "batch_benchmark_5assets.png")
    plt.savefig(chart_path)
    plt.close()
    print(f"5-Asset Benchmark Chart saved to: {chart_path}")

    # Copy to brain artifacts
    brain_dir = "/root/.gemini/antigravity-cli/brain/ddddd716-b7b3-4a76-b0c2-1a4dfc0f3390"
    if os.path.exists(brain_dir):
        import shutil
        shutil.copy(chart_path, os.path.join(brain_dir, "batch_benchmark_5assets.png"))

def print_summary_table(all_results):
    print("\n" + "="*125)
    print(f"{'Ticker':<14} | {'Start Rs':<9} | {'Actual Rs':<9} | {'Act Chg%':<8} | {'TimesFM Rs':<10} | {'TFM Err%':<9} | {'Hybrid Rs':<9} | {'Hyb Err%':<9} | {'Coverage%':<9} | {'Action':<15}")
    print("="*125)
    for r in all_results:
        tk = r["ticker"]
        m = r["metrics"]
        start_p = r["calendar"]["actual_closes"][0]
        end_p = m["actual_terminal"]
        act_chg = (end_p - start_p) / start_p * 100
        action = r["recommendation"]["action"]
        cov_pct = m.get("interval_80_coverage_pct", m.get("envelope_coverage_pct", 0.0))
        print(f"{tk:<14} | {start_p:9.2f} | {end_p:9.2f} | {act_chg:+7.1f}% | {m['pure_baseline_terminal']:10.2f} | {m['pure_baseline_error_pct']:+8.1f}% | {m['weighted_terminal']:9.2f} | {m['weighted_error_pct']:+8.1f}% | {cov_pct:8.0f}% | {action:<15}")
    print("="*125)

if __name__ == "__main__":
    run_batch_benchmark()
