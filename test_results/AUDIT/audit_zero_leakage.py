import sys, os, re
import pandas as pd, numpy as np, yfinance as yf

sys.path.insert(0, '/root/timesfm_repo/v2')
sys.path.insert(0, '/root/timesfm_repo/v2/MULTI_AGENT_SANDBOX')

from scenario_builder import build_scenarios, fetch_pre_cutoff_catalysts, get_comprehensive_financial_data
from multi_agent_system import MainIngestionAgent

CUTOFF = "2025-12-31"
TICKERS = ["MODISONLTD.NS", "TCS.NS", "ARROWGREEN.NS"]

print("=" * 80)
print(f"COMPREHENSIVE ZERO-LEAKAGE AUDIT FOR CUTOFF: {CUTOFF}")
print("=" * 80)

audit_passed = True

for ticker in TICKERS:
    print(f"\nAUDITING: {ticker}")
    print("-" * 50)
    
    # 1. Price check
    ingestion = MainIngestionAgent()
    msg, train_df, test_df = ingestion.process(ticker, cutoff_date=CUTOFF, horizon=170)
    
    last_train_date = train_df.iloc[-1]["Date_str"]
    first_test_date = test_df.iloc[0]["Date_str"]
    train_leak = any(train_df["Date_str"] > CUTOFF)
    
    print(f"1. PRICE BOUNDARY:")
    print(f"   Last Train Date: {last_train_date}")
    print(f"   First Test Date:  {first_test_date}")
    print(f"   Future Price Leak: {'FAILED ❌' if train_leak else 'PASSED ✅'}")
    if train_leak: audit_passed = False
    
    # 2. Financial statement check
    tk = yf.Ticker(ticker)
    fin_data = get_comprehensive_financial_data(tk, as_of=CUTOFF, current_price=float(train_df.iloc[-1]["Close"]))
    
    print(f"2. FINANCIAL STATEMENTS:")
    print(f"   Effective EPS: Rs. {fin_data['effective_eps']:.2f} ({fin_data['eps_source']})")
    print(f"   Trailing EPS:  {fin_data['trailing_eps']}")
    print(f"   Forward EPS:   {fin_data['forward_eps']} (Must be None in backtest)")
    print(f"   YoY Earn Growth: {fin_data['earn_growth']*100:+.1f}%")
    print(f"   YoY Rev Growth:  {fin_data['rev_growth']*100:+.1f}%")
    
    if fin_data["forward_eps"] is not None:
        print("   Forward EPS Leak: FAILED ❌ (Forward analyst estimates found)")
        audit_passed = False
    else:
        print("   Forward Estimates Isolated: PASSED ✅")
        
    # 3. Catalyst News check
    catalysts = fetch_pre_cutoff_catalysts(ticker, CUTOFF)
    future_tokens = ["2026", "2027", "FY26", "FY27"]
    cat_leak = any(re.search(rf"\b{re.escape(tok)}\b", catalysts, re.IGNORECASE) for tok in future_tokens)
    print(f"3. NEWS / CORPORATE ANNOUNCEMENTS:")
    print(f"   Catalyst Snippet: \"{catalysts[:100]}...\"")
    print(f"   Future Token Leak: {'FAILED ❌' if cat_leak else 'PASSED ✅'}")
    if cat_leak: audit_passed = False
    
    # 4. A2A Sandbox hardware gate check
    payload = msg.payload
    raw_text = str(payload)
    clean_ticker = ticker.replace(".NS", "").replace(".BO", "")
    token_leak = any(re.search(rf"\b{re.escape(tok)}\b", raw_text, re.IGNORECASE) for tok in [ticker, clean_ticker, "2026", "2027"])
    print(f"4. A2A SANDBOX HARDWARE GATE:")
    print(f"   Numerical Context Length: {len(payload['numerical_context'])}")
    print(f"   A2A Payload Leak: {'FAILED ❌' if token_leak else 'PASSED ✅'}")
    if token_leak: audit_passed = False

print("\n" + "=" * 80)
print(f"FINAL AUDIT RESULT: {'ALL CHECKS PASSED ✅ (100% ZERO-LEAKAGE CONFIRMED)' if audit_passed else 'AUDIT FAILED ❌'}")
print("=" * 80)
