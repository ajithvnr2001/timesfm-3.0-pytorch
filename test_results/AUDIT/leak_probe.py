#!/usr/bin/env python3
"""
leak_probe.py -- Point-In-Time (PIT) integrity probe for scenario_builder.py

Hypothesis under test:
  get_comprehensive_financial_data(tk, as_of, price) claims to be point-in-time,
  but sources EPS/growth from yfinance `.info` and `.quarterly_income_stmt`,
  neither of which accepts an as-of date. If so, the SAME fundamentals are
  returned for every cutoff -> forward-looking (post-cutoff) data leaks into
  every "zero-leakage" backtest.

Test: call the engine with three wildly different cutoffs. If the returned
EPS / growth / target are identical, the `as_of` argument is inert for
fundamentals and the backtest is contaminated.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MULTI_AGENT_SANDBOX"))

import yfinance as yf
from scenario_builder import get_comprehensive_financial_data, compute_institutional_target

TICKERS = ["TCS.NS", "STLTECH.NS", "MODISONLTD.NS"]
CUTOFFS = ["2023-12-31", "2024-12-31", "2025-12-31"]

def price_on(tk_obj, cutoff):
    h = tk_obj.history(period="max")
    h.index = h.index.tz_localize(None)
    s = h.loc[h.index <= cutoff]["Close"]
    return float(s.iloc[-1]) if len(s) else None

def main():
    report = {}
    for t in TICKERS:
        tk = yf.Ticker(t)
        live_px = price_on(tk, "2026-12-31")
        rows = []
        for c in CUTOFFS:
            px = price_on(tk, c)
            fd = get_comprehensive_financial_data(tk, as_of=c, current_price=px)
            tgt, eps, pe, src, regime = compute_institutional_target(t, px, fd)
            rows.append({
                "cutoff": c,
                "price_at_cutoff": round(px, 2),
                "trailing_eps": fd["trailing_eps"],
                "forward_eps": fd["forward_eps"],
                "run_rate_eps": fd["run_rate_eps"],
                "effective_eps": round(fd["effective_eps"], 2),
                "eps_source": fd["eps_source"],
                "earn_growth": fd["earn_growth"],
                "rev_growth": fd["rev_growth"],
                "target_pe": pe,
                "target_price": tgt,
                "regime": regime,
            })
        # Are fundamentals invariant to cutoff?
        keys = ["trailing_eps", "forward_eps", "run_rate_eps", "earn_growth", "rev_growth"]
        invariant = all(len({json.dumps(r[k]) for r in rows}) == 1 for k in keys)
        report[t] = {"latest_price_2026": round(live_px, 2), "rows": rows,
                     "fundamentals_invariant_to_cutoff": invariant}

        print("=" * 92)
        print(f"{t}   (latest close available in dataset: Rs.{live_px:,.2f})")
        print("=" * 92)
        print(f"{'cutoff':<12}{'px@cutoff':>11}{'trailEPS':>10}{'fwdEPS':>10}{'runRate':>10}"
              f"{'effEPS':>9}{'earnG':>8}{'PE':>7}{'target':>11}  {'regime'}")
        for r in rows:
            print(f"{r['cutoff']:<12}{r['price_at_cutoff']:>11,.2f}{str(r['trailing_eps']):>10}"
                  f"{str(round(r['forward_eps'],2) if r['forward_eps'] else None):>10}"
                  f"{str(round(r['run_rate_eps'],2) if r['run_rate_eps'] else None):>10}"
                  f"{r['effective_eps']:>9,.2f}{r['earn_growth']:>8}{r['target_pe']:>7}"
                  f"{r['target_price']:>11,.2f}  {r['regime']}")
        print(f"\n  >> fundamentals IDENTICAL across all 3 cutoffs? {invariant}")
        if invariant:
            print("  >> VERDICT: `as_of` does NOT filter fundamentals. Post-cutoff data leaks in.")
        t_2023 = rows[0]["target_price"]
        print(f"  >> target computed at the 2023-12-31 cutoff = Rs.{t_2023:,.2f} "
              f"vs true Sep-2026 price Rs.{live_px:,.2f} "
              f"(gap {(t_2023-live_px)/live_px*100:+.1f}%)")
        print()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leak_probe_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Saved -> {out}")

if __name__ == "__main__":
    main()
