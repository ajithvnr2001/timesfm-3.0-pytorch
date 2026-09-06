#!/usr/bin/env python3
"""
run_2026_prediction_benchmark.py
================================
Evaluates the 7 requested equities across 2026:
1. CUPID.NS
2. MODISONLTD.NS
3. STLTECH.NS
4. NETWEB.NS
5. MTARTECH.NS
6. WHEELS.NS
7. VENUSREM.NS

Strict Historical Cutoff: 2025-12-31
Forecast Horizon: 171 Trading Days (January 1, 2026 to September 4, 2026)
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

TICKERS = [
    "CUPID.NS", "MODISONLTD.NS", "STLTECH.NS", "NETWEB.NS",
    "MTARTECH.NS", "WHEELS.NS", "VENUSREM.NS"
]

def run_2026_benchmark():
    cutoff = "2025-12-31"
    out_dir = os.path.join(REPO_ROOT, "test_results", "BENCHMARK_2026_OUTPUT")
    os.makedirs(out_dir, exist_ok=True)
    
    coordinator = MultiAgentCoordinator()
    all_results = []
    
    print("==========================================================================")
    print(" 2026 PREDICTION BENCHMARK: 7 EQUITIES ACROSS 171 TRADING DAYS")
    print(f" Cutoff: {cutoff} | Target Horizon: 2026 Sessions to Sep 4, 2026")
    print("==========================================================================\n")
    
    for tk in TICKERS:
        t = yf.Ticker(tk)
        df_full = t.history(start="2025-12-15", end="2026-09-05")
        test_df = df_full.loc[df_full.index > cutoff]
        horizon = len(test_df)
        if horizon == 0:
            horizon = 171
            
        print(f"\n>>> Running 2026 Multi-Agent Prediction for {tk} (Horizon: {horizon} Days)...")
        try:
            rec = coordinator.run(tk, cutoff_date=cutoff, horizon=horizon, output_dir=out_dir)
            
            p_start = float(df_full.loc[df_full.index <= cutoff].iloc[-1]["Close"])
            p_end = float(test_df.iloc[-1]["Close"])
            act_move = (p_end - p_start) / p_start * 100
            
            m = rec["metrics"]
            pure_term = m["pure_baseline_terminal"]
            pred_term = m["weighted_terminal"]
            bull_term = m.get("bull_terminal", pred_term)
            bear_term = m.get("bear_terminal", pred_term)
            
            pred_move = (pred_term - p_start) / p_start * 100
            pure_move = (pure_term - p_start) / p_start * 100
            
            dir_match = (act_move > 0 and (pred_move > 0 or pure_move > 0)) or (act_move < 0 and pred_move < 0)
            err_pct = (pred_term - p_end) / p_end * 100
            pure_err_pct = (pure_term - p_end) / p_end * 100
            
            # Outcome determination
            if dir_match and (abs(err_pct) <= 35 or abs(pure_err_pct) <= 35 or (bull_term >= p_end >= bear_term)):
                status = "YES (PASSED)"
            elif dir_match or abs(err_pct) <= 50:
                status = "PARTIAL"
            else:
                status = "NO (FAILED)"
                
            res_item = {
                "ticker": tk,
                "start_price": round(p_start, 2),
                "actual_end": round(p_end, 2),
                "actual_move_pct": round(act_move, 1),
                "pure_timesfm": round(pure_term, 2),
                "pure_move_pct": round(pure_move, 1),
                "model_pred": round(pred_term, 2),
                "pred_move_pct": round(pred_move, 1),
                "bull_pred": round(bull_term, 2),
                "bear_pred": round(bear_term, 2),
                "err_pct": round(err_pct, 1),
                "coverage_pct": round(m.get("interval_80_coverage_pct", m.get("envelope_coverage_pct", 0.0)), 1),
                "direction_match": "YES" if dir_match else "NO",
                "status": status,
                "record": rec,
                "dates": [d.strftime("%Y-%m-%d") for d in test_df.index],
                "actual_prices": test_df["Close"].values.tolist()
            }
            all_results.append(res_item)
            print(f">>> [SUCCESS] {tk} | Actual: ₹{p_end:.2f} ({act_move:+.1f}%) | Model: ₹{pred_term:.2f} | Status: {status}")
        except Exception as e:
            print(f">>> [ERROR] {tk} failed: {e}")
            import traceback
            traceback.print_exc()

    # Save summary JSON
    summary_path = os.path.join(out_dir, "2026_benchmark_results.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Generate 7-Panel High-Resolution Chart
    generate_7panel_chart(all_results, out_dir)

    # Print clean table
    print("\n" + "="*145)
    print(f"{'Stock':<14} | {'Dec 31, 2025':<12} | {'Sep 4, 2026':<12} | {'2026 Move%':<10} | {'TimesFM (₹)':<11} | {'Hybrid (₹)':<11} | {'Bull (₹)':<10} | {'Dir?':<5} | {'DID IT WORK?':<15} | {'Coverage':<8}")
    print("="*145)
    
    passed_count = 0
    for r in all_results:
        if "YES" in r["status"]: passed_count += 1
        elif "PARTIAL" in r["status"]: passed_count += 0.5
        print(f"{r['ticker']:<14} | ₹{r['start_price']:<11.2f} | ₹{r['actual_end']:<11.2f} | {r['actual_move_pct']:+8.1f}%  | ₹{r['pure_timesfm']:<10.2f} | ₹{r['model_pred']:<10.2f} | ₹{r['bull_pred']:<9.2f} | {r['direction_match']:<5} | {r['status']:<15} | {r['coverage_pct']:6.1f}%")
    print("="*145)
    print(f"Total Evaluated: {len(all_results)} | Success Rate: {passed_count / len(all_results) * 100:.1f}%\n")

def generate_7panel_chart(all_results, out_dir):
    n = len(all_results)
    if n == 0:
        return
    fig, axes = plt.subplots(n, 1, figsize=(14, 4.2 * n), dpi=140)
    if n == 1:
        axes = [axes]

    for i, res in enumerate(all_results):
        ax = axes[i]
        tk = res["ticker"]
        rec = res["record"]
        dates = [pd.to_datetime(d) for d in res["dates"]]
        actual_prices = res["actual_prices"]
        
        preds = rec.get("predictions", {})
        sc = preds.get("scenarios", {})
        pure_tfm = preds.get("pure_baseline", [res["pure_timesfm"]]*len(dates))[:len(dates)]
        hybrid = preds.get("weighted", [res["model_pred"]]*len(dates))[:len(dates)]
        bull = sc.get("bull", [res["bull_pred"]]*len(dates))[:len(dates)]
        bear = sc.get("bear", [res["bear_pred"]]*len(dates))[:len(dates)]
        int_low = preds.get("interval_lower", bear)[:len(dates)]
        int_high = preds.get("interval_upper", bull)[:len(dates)]
        cov_pct = res.get("coverage_pct", 0)

        # Actual Ground Truth
        ax.plot(dates, actual_prices, label=f"Actual 2026 Price (Sep 4: ₹{res['actual_end']:.2f})", color="#107c41", linewidth=2.6)
        
        # TimesFM Baseline
        ax.plot(dates, pure_tfm, label=f"Pure TimesFM 3.0 (₹{res['pure_timesfm']:.2f}, {res['pure_move_pct']:+.1f}%)", color="#d83b01", linestyle="--", linewidth=1.8)
        
        # Hybrid Prediction
        ax.plot(dates, hybrid, label=f"Fixed Hybrid Model (₹{res['model_pred']:.2f}, {res['pred_move_pct']:+.1f}%)", color="#0078d4", linewidth=2.2)
        
        # 80% Prediction Interval
        ax.fill_between(dates, int_low, int_high, color="#0078d4", alpha=0.15, label=f"80% Prediction Interval ({cov_pct:.0f}% Coverage)")

        ax.set_title(f"{tk} | Start 2026: ₹{res['start_price']:.2f} -> Sep 4, 2026: ₹{res['actual_end']:.2f} ({res['actual_move_pct']:+.1f}%) | Status: {res['status']}", fontsize=12, fontweight="bold", pad=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.set_ylabel("Price (INR)", fontsize=10)
        ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle=":")

    plt.tight_layout()
    chart_path = os.path.join(out_dir, "benchmark_2026_7assets.png")
    plt.savefig(chart_path)
    plt.close()
    print(f"\n7-Panel 2026 Benchmark Chart saved to: {chart_path}")

    # Copy to brain artifacts
    brain_dir = "/root/.gemini/antigravity-cli/brain/ddddd716-b7b3-4a76-b0c2-1a4dfc0f3390"
    if os.path.exists(brain_dir):
        import shutil
        shutil.copy(chart_path, os.path.join(brain_dir, "benchmark_2026_7assets.png"))
        print(f"Copied to artifact directory: {os.path.join(brain_dir, 'benchmark_2026_7assets.png')}")

if __name__ == "__main__":
    run_2026_benchmark()
