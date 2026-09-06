"""
run_validation.py
=================
Walk-forward validation harness with a resumable ledger.

For every (ticker, cutoff) in a point-in-time universe it records:
  * TimesFM 3.0 forecast metrics at each horizon vs naive / drift / seasonal baselines
  * raw vs PIT-conformal-calibrated interval coverage
  * the anonymised LLM conviction score and the adversarial identity-probe verdict
  * the realised forward return, so the screener can be scored by rank-IC and hit-rate

The LLM block is cached per (ticker, cutoff, evidence_mode) because it does not depend on
the forecast horizon - that roughly halves the API cost.

Designed to be run repeatedly: each invocation works until `TIME_BUDGET_S` is exhausted,
writes the ledger, and exits. Re-running resumes exactly where it stopped, which matters
because Colab kernels and exec calls both have time limits.

Env:
  TIME_BUDGET_S   seconds of work before a clean exit (default 1500)
  EVIDENCE_MODE   numbers_only | with_evidence   (default numbers_only)
  LEDGER          path to the ledger json
  OUT_DIR         where universe files and the summary land
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import RunConfig, price_features, run_single  # noqa: E402
from pit_data import build_pit_bundle, industry_of, pit_fundamentals  # noqa: E402
from timesfm3_adapter import TimesFM3Adapter  # noqa: E402
from universe import forward_return_pct, save_universe, screen_universe  # noqa: E402

CUTOFFS = ["2023-12-29", "2024-06-28", "2024-12-31"]
HORIZONS = [60, 252]

COMPANY_NAMES = {
    "MODISONLTD.NS": ["Modison Limited", "Modison Metals"],
    "CUPID.NS": ["Cupid Limited"],
    "INFY.NS": ["Infosys Limited", "Infosys"],
    "TCS.NS": ["Tata Consultancy Services"],
    "NETWEB.NS": ["Netweb Technologies India"],
    "HEROMOTOCO.NS": ["Hero MotoCorp"],
    "RELIANCE.NS": ["Reliance Industries"],
    "HDFCBANK.NS": ["HDFC Bank"],
    "ICICIBANK.NS": ["ICICI Bank"],
    "SBIN.NS": ["State Bank of India"],
    "ITC.NS": ["ITC Limited"],
    "BHARTIARTL.NS": ["Bharti Airtel"],
    "MARUTI.NS": ["Maruti Suzuki India"],
    "SUNPHARMA.NS": ["Sun Pharmaceutical Industries"],
    "TITAN.NS": ["Titan Company"],
    "HAL.NS": ["Hindustan Aeronautics"],
    "BEL.NS": ["Bharat Electronics"],
    "BHEL.NS": ["Bharat Heavy Electricals"],
    "TATAPOWER.NS": ["Tata Power Company"],
    "PERSISTENT.NS": ["Persistent Systems"],
    "COFORGE.NS": ["Coforge Limited"],
    "POLYCAB.NS": ["Polycab India"],
    "APLAPOLLO.NS": ["APL Apollo Tubes"],
    "CGPOWER.NS": ["CG Power and Industrial Solutions"],
    "SUZLON.NS": ["Suzlon Energy"],
    "STLTECH.NS": ["Sterlite Technologies"],
    "AETHER.NS": ["Aether Industries"],
    "MTARTECH.NS": ["MTAR Technologies"],
    "VENUSREM.NS": ["Venus Remedies"],
    "WHEELS.NS": ["Wheels India"],
    "RAYMONDREL.NS": ["Raymond Realty"],
    "ARROWGREEN.NS": ["Arrow Greentech"],
    "KPITTECH.NS": ["KPIT Technologies"],
    "IDEA.NS": ["Vodafone Idea"],
    "YESBANK.NS": ["Yes Bank"],
    "RPOWER.NS": ["Reliance Power"],
    "JPPOWER.NS": ["Jaiprakash Power Ventures"],
    "SOUTHBANK.NS": ["South Indian Bank"],
}


def load_ledger(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"runs": {}, "llm_cache": {}, "universes": {}, "industries": {}}


def save_ledger(ledger, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ledger, f)
    os.replace(tmp, path)


def baselines(bundle) -> dict:
    act = bundle.actuals
    last = bundle.last_price
    hist = bundle.context[0]
    n = len(act)
    out = {"naive_mape": float(np.mean(np.abs((act - last) / act)) * 100)}
    look = min(60, len(hist) - 1)
    drift = (hist[-1] - hist[-look - 1]) / look
    dpath = last + drift * np.arange(1, n + 1)
    out["drift_mape"] = float(np.mean(np.abs((act - dpath) / act)) * 100)
    seas = hist[-n:] * (last / hist[-n])
    out["seasonal_mape"] = float(np.mean(np.abs((act - seas) / act)) * 100)
    out["naive_directional"] = 0  # a flat forecast has no direction
    return out


def main():
    budget = float(os.environ.get("TIME_BUDGET_S", "1500"))
    evidence_mode = os.environ.get("EVIDENCE_MODE", "numbers_only")
    ledger_path = os.environ.get("LEDGER", "/content/OUT/ledger.json")
    out_dir = os.environ.get("OUT_DIR", "/content/OUT/VALIDATION")
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    ledger = load_ledger(ledger_path)
    adapter = TimesFM3Adapter(device="cuda").load()
    print(f"[harness] model loaded in {adapter.load_seconds}s | evidence_mode={evidence_mode}")

    # ---- universes (point-in-time, cached in the ledger)
    for cut in CUTOFFS:
        if cut not in ledger["universes"]:
            u = screen_universe(cut)
            ledger["universes"][cut] = u
            save_universe(u, out_dir)
            save_ledger(ledger, ledger_path)

    todo = []
    for cut in CUTOFFS:
        for m in ledger["universes"][cut]["members"]:
            for H in HORIZONS:
                key = f"{m['ticker']}|{cut}|{H}|{evidence_mode}"
                if key not in ledger["runs"]:
                    todo.append((m["ticker"], cut, H, key))
    print(f"[harness] {len(todo)} runs remaining of "
          f"{sum(len(ledger['universes'][c]['members']) for c in CUTOFFS) * len(HORIZONS)}")

    done_now = 0
    for ticker, cut, H, key in todo:
        if time.time() - t0 > budget:
            print(f"[harness] time budget reached; {len(todo) - done_now} runs still pending")
            break
        try:
            if ticker not in ledger["industries"]:
                ledger["industries"][ticker] = industry_of(ticker, allow_live_metadata=True)
            ind = ledger["industries"][ticker]

            llm_key = f"{ticker}|{cut}|{evidence_mode}"
            cached_llm = ledger["llm_cache"].get(llm_key)

            cfg = RunConfig(
                horizon=H, llm_samples=2, n_calibration_origins=6,
                evidence_mode=evidence_mode,
                use_llm=cached_llm is None,
                run_identity_probe=cached_llm is None,
            )
            rec = run_single(ticker, cut, cfg, adapter, industry=ind,
                             company_names=COMPANY_NAMES.get(ticker, [ticker.split(".")[0]]))
            if cached_llm is None:
                ledger["llm_cache"][llm_key] = rec["llm"]
            else:
                rec["llm"] = cached_llm
                rec["valid_for_backtest"] = not cached_llm.get("identity_probe", {}).get("leak", False)

            bundle_actuals = rec.get("actuals")
            row = {
                "ticker": ticker, "cutoff": cut, "horizon": H,
                "industry": ind, "last_price": rec["last_price"],
                "metrics": rec["metrics"],
                "calibration": {k: rec["calibration"].get(k) for k in
                                ("status", "k_low", "k_high", "n_origins_used",
                                 "n_calibration_points", "raw_coverage_pct")},
                "risk": {k: rec["risk"][k] for k in
                         ("stop_level", "stop_distance_pct", "expected_move_pct",
                          "net_expected_move_pct", "risk_reward", "ann_vol_pct",
                          "recommended_alloc_pct", "directive")},
                "llm": {k: rec["llm"].get(k) for k in
                        ("status", "conviction_score", "axis_scores",
                         "expected_rerating_pct", "disagreement", "identity_probe")},
                "valid_for_backtest": rec["valid_for_backtest"],
                "forward_return_pct": forward_return_pct(ticker, cut, H),
                "provenance": rec["forecast_provenance"],
                "n_actuals": 0 if bundle_actuals is None else len(bundle_actuals),
            }
            # baselines need the bundle again (cheap, prices are cached)
            b = build_pit_bundle(ticker, cut, H, max_context=cfg.max_context, industry=ind)
            if b.actuals is not None and len(b.actuals) > 0:
                row["baselines"] = baselines(b)
            ledger["runs"][key] = row
            done_now += 1
            m = row["metrics"]
            print(f"  [{done_now}/{len(todo)}] {ticker} {cut} H{H}: "
                  f"mape={m.get('mape')} naive={m.get('naive_mape')} "
                  f"dir={m.get('directional_correct')} "
                  f"cov_raw={m.get('raw_band_coverage_pct')} cov_cal={m.get('calibrated_band_coverage_pct')} "
                  f"conv={row['llm'].get('conviction_score')} fwd={row['forward_return_pct']}")
            if done_now % 5 == 0:
                save_ledger(ledger, ledger_path)
        except Exception as exc:
            ledger["runs"][key] = {"ticker": ticker, "cutoff": cut, "horizon": H,
                                   "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
            print(f"  ERROR {ticker} {cut} H{H}: {type(exc).__name__}: {str(exc)[:160]}")
        finally:
            save_ledger(ledger, ledger_path)

    save_ledger(ledger, ledger_path)
    remaining = sum(1 for _t, _c, _h, k in todo if k not in ledger["runs"])
    print(f"[harness] done_now={done_now} remaining={remaining} "
          f"elapsed={round(time.time()-t0,1)}s")
    print("REMAINING:" + str(remaining))


if __name__ == "__main__":
    main()
