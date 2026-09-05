#!/usr/bin/env python3
"""
bull_bear_test.py -- runs the REAL MultiAgentCoordinator on Indian equities
in two regimes to separate genuine skill from look-ahead bias.

REGIME A ("as documented"): cutoff 2025-12-31 -> Sep 2026.
    The leaked yfinance `.info` fundamentals describe Sep-2026 reality,
    i.e. exactly the period being "predicted".

REGIME B ("controlled"):    cutoff 2023-12-31 -> Dec 2024.
    Identical code, identical leak -- but now the leaked Sep-2026
    fundamentals describe a period 21 months AFTER the forecast window.
    If the engine has real skill, error stays similar. If the accuracy in
    Regime A came from the leak, error explodes here.

Bull cases : STLTECH.NS, MODISONLTD.NS
Bear cases : TCS.NS, plus a 2024 bear window for STLTECH
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")

REPO = "/root/timesfm_repo"
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "MULTI_AGENT_SANDBOX"))

import pandas as pd
import yfinance as yf
from multi_agent_system import MultiAgentCoordinator

OUT = os.path.join(REPO, "AUDIT", "BULL_BEAR_OUTPUT")
os.makedirs(OUT, exist_ok=True)

CASES = [
    # label,          ticker,           cutoff,        window_end,   expected_bias
    ("A-BEAR  doc window",  "TCS.NS",        "2025-12-31", "2026-09-05", "bear"),
    ("A-BULL  doc window",  "STLTECH.NS",    "2025-12-31", "2026-09-05", "bull"),
    ("A-BULL  doc window",  "MODISONLTD.NS", "2025-12-31", "2026-09-05", "bull"),
    ("B-BULL  controlled",  "MODISONLTD.NS", "2023-12-31", "2024-12-31", "bull"),
    ("B-BEAR  controlled",  "STLTECH.NS",    "2023-12-31", "2024-12-31", "bear"),
    ("B-BULL  controlled",  "TCS.NS",        "2023-12-31", "2024-12-31", "bull"),
]

def main():
    coord = MultiAgentCoordinator()
    rows = []
    for label, tk, cutoff, wend, bias in CASES:
        h = yf.Ticker(tk).history(period="max")
        h.index = pd.to_datetime(h.index).tz_localize(None)
        train = h.loc[h.index <= cutoff]["Close"]
        test = h.loc[(h.index > cutoff) & (h.index <= wend)]["Close"]
        if len(train) == 0 or len(test) == 0:
            print(f"!! skip {tk} {cutoff}: no data")
            continue
        horizon = len(test)
        p0, p1 = float(train.iloc[-1]), float(test.iloc[-1])

        sub = os.path.join(OUT, f"{tk.replace('.','_')}_{cutoff}")
        os.makedirs(sub, exist_ok=True)
        try:
            rec = coord.run(tk, cutoff_date=cutoff, horizon=horizon, output_dir=sub)
        except Exception as e:
            print(f"!! {tk} {cutoff} failed: {e}")
            continue

        m = rec["metrics"]
        pred = float(m["weighted_terminal"])
        pure = float(m["pure_baseline_terminal"])
        act_move = (p1 - p0) / p0 * 100
        pred_move = (pred - p0) / p0 * 100
        pure_move = (pure - p0) / p0 * 100
        err = (pred - p1) / p1 * 100
        pure_err = (pure - p1) / p1 * 100
        # honest directional test: sign of the model's own point forecast only
        dir_ok = (act_move > 0) == (pred_move > 0)

        rows.append(dict(label=label, ticker=tk, cutoff=cutoff, horizon=horizon,
                         start=round(p0, 2), actual=round(p1, 2),
                         act_move=round(act_move, 1), pred=round(pred, 2),
                         pred_move=round(pred_move, 1), err=round(err, 1),
                         pure=round(pure, 2), pure_move=round(pure_move, 1),
                         pure_err=round(pure_err, 1), dir_ok=dir_ok,
                         regime=rec.get("regime", m.get("regime", "?"))))
        print(f"\n### {label} {tk} {cutoff} -> {wend}: actual {act_move:+.1f}% | "
              f"model {pred_move:+.1f}% | error {err:+.1f}%\n")

    with open(os.path.join(OUT, "bull_bear_results.json"), "w") as f:
        json.dump(rows, f, indent=2, default=str)

    print("\n" + "=" * 122)
    print("BULL / BEAR TEST -- SAME CODE, TWO FORECAST WINDOWS")
    print("=" * 122)
    print(f"{'case':<20}{'ticker':<15}{'cutoff':<12}{'H':>4}{'start':>10}{'actual':>10}"
          f"{'act%':>8}{'model':>10}{'pred%':>9}{'err%':>8}{'dir':>5}")
    print("-" * 122)
    for r in rows:
        print(f"{r['label']:<20}{r['ticker']:<15}{r['cutoff']:<12}{r['horizon']:>4}"
              f"{r['start']:>10,.2f}{r['actual']:>10,.2f}{r['act_move']:>+8.1f}"
              f"{r['pred']:>10,.2f}{r['pred_move']:>+9.1f}{r['err']:>+8.1f}"
              f"{'OK' if r['dir_ok'] else 'MISS':>5}")
    print("=" * 122)
    for tag in ("A-", "B-"):
        g = [r for r in rows if r["label"].startswith(tag)]
        if g:
            mape = sum(abs(r["err"]) for r in g) / len(g)
            hit = sum(r["dir_ok"] for r in g)
            print(f"Regime {tag[0]}: mean |error| = {mape:6.1f}%   direction {hit}/{len(g)}")

if __name__ == "__main__":
    main()
