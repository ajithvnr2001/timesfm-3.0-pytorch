#!/usr/bin/env python3
"""
run_1year_benchmark.py
======================
Executes 1-Year Multi-Agent Benchmark (246 Trading Days) across 15 Indian Equities.
Cutoff Date: 2023-12-31
Evaluation Period: 2024-01-01 to 2024-12-31 (Full 2024 Calendar Year)
"""

import os
import sys
import json
import concurrent.futures
import pandas as pd
import numpy as np
import yfinance as yf

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURR_DIR) if os.path.basename(CURR_DIR) == "v2" else CURR_DIR
sys.path.insert(0, CURR_DIR)
sys.path.insert(0, os.path.join(CURR_DIR, "MULTI_AGENT_SANDBOX"))
sys.path.insert(0, REPO_ROOT)

from multi_agent_system import MultiAgentCoordinator

TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "BHARTIARTL.NS",
    "ITC.NS", "HAL.NS", "BHEL.NS", "STLTECH.NS", "MODISONLTD.NS",
    "AETHER.NS", "CUPID.NS", "HEROMOTOCO.NS", "NETWEB.NS", "SBIN.NS"
]

def evaluate_ticker(tk):
    cutoff = "2023-12-31"
    horizon = 246
    out_dir = os.path.join(REPO_ROOT, "test_results", "BENCHMARK_1YEAR_OUTPUT")
    os.makedirs(out_dir, exist_ok=True)
    
    coordinator = MultiAgentCoordinator()
    print(f"[{tk}] Starting 1-year evaluation (246 days)...")
    try:
        rec = coordinator.run(tk, cutoff_date=cutoff, horizon=horizon, output_dir=out_dir)
        m = rec["metrics"]
        cal = rec.get("calendar", {})
        
        # Get exact actual prices from history
        t = yf.Ticker(tk)
        hist = t.history(start="2024-01-01", end="2025-01-01")
        p_start = float(hist.iloc[0]["Close"])
        p_end = float(hist.iloc[-1]["Close"])
        act_move = (p_end - p_start) / p_start * 100
        
        pred_term = m["weighted_terminal"]
        bull_term = m.get("bull_terminal", pred_term)
        pure_term = m["pure_baseline_terminal"]
        pred_move = (pred_term - p_start) / p_start * 100
        
        # Direction match
        dir_match = (act_move > 0 and pred_move > 0) or (act_move < 0 and pred_move < 0) or (abs(act_move) < 8 and abs(pred_move) < 8)
        
        # Error vs actual
        err_pct = (pred_term - p_end) / p_end * 100
        bull_err_pct = (bull_term - p_end) / p_end * 100
        
        # Did it work?
        if abs(err_pct) <= 20 or (bull_term >= p_end >= pred_term) or (dir_match and abs(err_pct) <= 30):
            status = "YES (PASSED)"
        elif dir_match or abs(bull_err_pct) <= 25:
            status = "PARTIAL"
        else:
            status = "NO (FAILED)"
            
        return {
            "ticker": tk,
            "start_price": round(p_start, 2),
            "actual_end": round(p_end, 2),
            "actual_move_pct": round(act_move, 1),
            "model_pred": round(pred_term, 2),
            "bull_pred": round(bull_term, 2),
            "pure_timesfm": round(pure_term, 2),
            "pred_move_pct": round(pred_move, 1),
            "err_pct": round(err_pct, 1),
            "coverage_pct": round(m["envelope_coverage_pct"], 1),
            "direction_match": "YES" if dir_match else "NO",
            "status": status,
            "action": rec.get("recommendation", {}).get("action", "N/A"),
            "thesis": rec.get("institutional_scorecard", {}).get("thesis", "")
        }
    except Exception as e:
        print(f"[{tk}] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("==========================================================================")
    print(f" 1-YEAR (246 TRADING DAYS) MULTI-AGENT INSTITUTIONAL BENCHMARK")
    print(f" Tickers ({len(TICKERS)}): {', '.join(TICKERS)}")
    print(f" Evaluation Window: 2024-01-01 to 2024-12-31 | Cutoff: 2023-12-31")
    print("==========================================================================\n")

    results = []
    # Run sequentially or max 2 workers to avoid rate limits
    for tk in TICKERS:
        res = evaluate_ticker(tk)
        if res:
            results.append(res)
            print(f">>> Completed {tk}: Actual={res['actual_end']} | Model={res['model_pred']} | Status={res['status']}")

    out_file = os.path.join(REPO_ROOT, "BENCHMARK_1YEAR_OUTPUT", "1year_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*135)
    print(f"{'Stock':<14} | {'Start (₹)':<9} | {'Actual 1-Yr (₹)':<15} | {'Actual %':<8} | {'Model Pred (₹)':<14} | {'Bull Target':<11} | {'Dir?':<5} | {'DID IT WORK?':<15} | {'Coverage':<8}")
    print("="*135)
    
    passed_count = 0
    for r in results:
        if "YES" in r["status"]: passed_count += 1
        elif "PARTIAL" in r["status"]: passed_count += 0.5
        print(f"{r['ticker']:<14} | {r['start_price']:9.2f} | {r['actual_end']:15.2f} | {r['actual_move_pct']:+7.1f}% | {r['model_pred']:14.2f} | {r['bull_pred']:11.2f} | {r['direction_match']:<5} | {r['status']:<15} | {r['coverage_pct']:6.1f}%")
    print("="*135)
    print(f"Total Evaluated: {len(results)} | Success Rate: {passed_count / len(results) * 100:.1f}%\n")

if __name__ == "__main__":
    main()
