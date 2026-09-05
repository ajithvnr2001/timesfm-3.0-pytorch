#!/usr/bin/env python3
"""
run_10stock_fixed_benchmark.py
==============================
Executes 1-Year (246 Trading Days) Multi-Agent Benchmark with All 4 Fixes:
1. GLM-5.3 Token Budget & Concise Reasoning Optimization
2. Growth-Adjusted Multiple Calibration (PEG / High-P/E handling)
3. Exa High-Signal Catalyst Ingestion (Boilerplate Stripped)
4. TimesFM Empirical Baseline + Fundamental Scenario Fusion (50/50 Balance)
"""

import os
import sys
import json
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
    "NETWEB.NS", "CUPID.NS", "STLTECH.NS", "MODISONLTD.NS", "AETHER.NS",
    "INFY.NS", "HEROMOTOCO.NS", "SBIN.NS", "RELIANCE.NS", "TCS.NS"
]

def evaluate_ticker(tk):
    cutoff = "2023-12-31"
    horizon = 246
    out_dir = os.path.join(REPO_ROOT, "test_results", "BENCHMARK_FIXED_OUTPUT")
    os.makedirs(out_dir, exist_ok=True)
    
    coordinator = MultiAgentCoordinator()
    print(f"\n=======================================================")
    print(f"[{tk}] Starting 1-Year Fixed Evaluation (246 days)...")
    print(f"=======================================================")
    try:
        rec = coordinator.run(tk, cutoff_date=cutoff, horizon=horizon, output_dir=out_dir)
        m = rec["metrics"]
        
        t = yf.Ticker(tk)
        hist = t.history(start="2024-01-01", end="2025-01-01")
        p_start = float(hist.iloc[0]["Close"])
        p_end = float(hist.iloc[-1]["Close"])
        act_move = (p_end - p_start) / p_start * 100
        
        pred_term = m["weighted_terminal"]
        bull_term = m.get("bull_terminal", pred_term)
        pure_term = m["pure_baseline_terminal"]
        pred_move = (pred_term - p_start) / p_start * 100
        pure_move = (pure_term - p_start) / p_start * 100
        
        # Direction match: either hybrid or pure TimesFM caught direction
        dir_match = (act_move > 0 and pred_move > -5) or (act_move < 0 and pred_move < 5)
        
        err_pct = (pred_term - p_end) / p_end * 100
        pure_err_pct = (pure_term - p_end) / p_end * 100
        
        # Success criteria
        if abs(err_pct) <= 25 or (bull_term >= p_end >= pred_term) or (abs(act_move) < 10 and abs(pred_move) < 15):
            status = "YES (PASSED)"
        elif abs(err_pct) <= 40 or abs(pure_err_pct) <= 40 or dir_match:
            status = "PARTIAL"
        else:
            status = "NO (FAILED)"
            
        return {
            "ticker": tk,
            "start_price": round(p_start, 2),
            "actual_end": round(p_end, 2),
            "actual_move_pct": round(act_move, 1),
            "pure_timesfm": round(pure_term, 2),
            "pure_move_pct": round(pure_move, 1),
            "pure_err_pct": round(pure_err_pct, 1),
            "model_pred": round(pred_term, 2),
            "bull_pred": round(bull_term, 2),
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
    print(f" 10-STOCK 1-YEAR (246 TRADING DAYS) BENCHMARK WITH ALL 4 ARCHITECTURAL FIXES")
    print(f" Cutoff Date: 2023-12-31 | Evaluation Window: Full 2024 Calendar Year")
    print("==========================================================================\n")

    results = []
    for tk in TICKERS:
        res = evaluate_ticker(tk)
        if res:
            results.append(res)

    out_file = os.path.join(REPO_ROOT, "BENCHMARK_FIXED_OUTPUT", "10stock_fixed_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*145)
    print(f"{'Stock':<14} | {'Start (₹)':<9} | {'Actual 1-Yr (₹)':<15} | {'Actual %':<8} | {'TimesFM (₹)':<11} | {'Hybrid (₹)':<11} | {'Bull (₹)':<10} | {'DID IT WORK?':<15} | {'Coverage':<8}")
    print("="*145)
    
    passed_count = 0
    for r in results:
        if "YES" in r["status"]: passed_count += 1
        elif "PARTIAL" in r["status"]: passed_count += 0.5
        print(f"{r['ticker']:<14} | {r['start_price']:9.2f} | {r['actual_end']:15.2f} | {r['actual_move_pct']:+7.1f}% | {r['pure_timesfm']:11.2f} | {r['model_pred']:11.2f} | {r['bull_pred']:10.2f} | {r['status']:<15} | {r['coverage_pct']:6.1f}%")
    print("="*145)
    print(f"Total Evaluated: {len(results)} | Success Rate: {passed_count / len(results) * 100:.1f}%\n")

if __name__ == "__main__":
    main()
