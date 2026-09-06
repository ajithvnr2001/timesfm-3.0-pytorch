"""
run_forward.py
==============
Live forward prediction (no cutoff) for a shortlist, using exactly the configuration that
was walk-forward validated, and the empirically measured directional hit-rate as the Kelly
win probability instead of a circular self-derived number.

Outputs per ticker: calibrated 80% band, horizon-matched stop, sizing, anonymised LLM
conviction with its identity-probe verdict, plus a portfolio-level summary table.

Env: HORIZONS (comma list), TICKERS (comma list), P_WIN, OUT_DIR, EVIDENCE_MODE
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import RunConfig, run_single  # noqa: E402
from pit_data import industry_of  # noqa: E402
from run_validation import COMPANY_NAMES  # noqa: E402
from timesfm3_adapter import TimesFM3Adapter  # noqa: E402

DEFAULT_TICKERS = ["MODISONLTD.NS", "CUPID.NS", "INFY.NS", "TCS.NS", "NETWEB.NS",
                   "HEROMOTOCO.NS", "ARROWGREEN.NS", "CGPOWER.NS", "HAL.NS", "POLYCAB.NS"]


def main():
    horizons = [int(h) for h in os.environ.get("HORIZONS", "60,252").split(",")]
    tickers = [t.strip() for t in os.environ.get("TICKERS", ",".join(DEFAULT_TICKERS)).split(",") if t.strip()]
    # Directional accuracy was 53.2% (p=0.150) over 494 walk-forward runs - not
    # statistically distinguishable from a coin flip - so the default is 0.50. Supplying a
    # higher P_WIN asserts an edge the validation does not support.
    p_win = float(os.environ.get("P_WIN", "0.5"))
    out_dir = os.environ.get("OUT_DIR", "/content/OUT/FORWARD")
    evidence_mode = os.environ.get("EVIDENCE_MODE", "numbers_only")
    os.makedirs(out_dir, exist_ok=True)

    adapter = TimesFM3Adapter(device=os.environ.get("DEVICE", "cuda")).load()
    print(f"[forward] model loaded {adapter.load_seconds}s | p_win={p_win} | horizons={horizons}")

    results = []
    for tk in tickers:
        ind = industry_of(tk, allow_live_metadata=True)
        for H in horizons:
            t0 = time.time()
            try:
                cfg = RunConfig(horizon=H, llm_samples=2, n_calibration_origins=8,
                                evidence_mode=evidence_mode, p_win_empirical=p_win,
                                use_llm=(H == horizons[0]), run_identity_probe=(H == horizons[0]))
                rec = run_single(tk, None, cfg, adapter, industry=ind,
                                 company_names=COMPANY_NAMES.get(tk, [tk.split(".")[0]]))
                if H != horizons[0] and results:
                    prev = next((r for r in results if r["ticker"] == tk and r["llm"].get("status") == "ok"), None)
                    if prev:
                        rec["llm"] = prev["llm"]
                fc = rec["forecast"]
                row = {
                    "ticker": tk, "industry": ind, "horizon": H,
                    "last_price": rec["last_price"],
                    "as_of": rec["pit_audit"]["context_last_date"],
                    "median_terminal": fc["median"][-1],
                    "band_low_terminal": fc["calibrated_low"][-1],
                    "band_high_terminal": fc["calibrated_high"][-1],
                    "expected_move_pct": rec["risk"]["expected_move_pct"],
                    "stop_level": rec["risk"]["stop_level"],
                    "stop_distance_pct": rec["risk"]["stop_distance_pct"],
                    "risk_reward": rec["risk"]["risk_reward"],
                    "alloc_pct": rec["risk"]["recommended_alloc_pct"],
                    "shares": rec["risk"]["recommended_shares"],
                    "directive": rec["risk"]["directive"],
                    "ann_vol_pct": rec["risk"]["ann_vol_pct"],
                    "conviction": rec["llm"].get("conviction_score"),
                    "axis_scores": rec["llm"].get("axis_scores"),
                    "rerating_pct": rec["llm"].get("expected_rerating_pct"),
                    "thesis": rec["llm"].get("thesis"),
                    "identity_probe_leak": rec["llm"].get("identity_probe", {}).get("leak"),
                    "calibration_status": rec["calibration"].get("status"),
                    "calibration_k": [rec["calibration"].get("k_low"), rec["calibration"].get("k_high")],
                    "provenance": rec["forecast_provenance"],
                    "llm": rec["llm"],
                    "forecast": fc,
                    "seconds": round(time.time() - t0, 1),
                }
                results.append(row)
                print(f"  {tk} H{H}: last={row['last_price']:.1f} -> med={row['median_terminal']:.1f} "
                      f"({row['expected_move_pct']:+.1f}%) band=[{row['band_low_terminal']:.0f},"
                      f"{row['band_high_terminal']:.0f}] conv={row['conviction']} "
                      f"stop={row['stop_level']:.1f} alloc={row['alloc_pct']}% {row['directive']}")
            except Exception as exc:
                print(f"  ERROR {tk} H{H}: {type(exc).__name__}: {str(exc)[:160]}")

    with open(os.path.join(out_dir, "forward_predictions.json"), "w") as f:
        json.dump(results, f, indent=2)

    # ------------------------------------------------------------------ report
    lines = ["# Forward Predictions (live, no cutoff)", ""]
    if results:
        lines.append(f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} | "
                     f"model `{results[0]['provenance']['model_id']}` on "
                     f"`{results[0]['provenance']['device']}` | "
                     f"Kelly win probability = {p_win:.2f} (walk-forward directional hit-rate)")
        lines.append("")
        lines.append("> These are probabilistic projections, not advice. The walk-forward study "
                     "found this model has **no edge over a random walk on price level** and only "
                     "a modest directional edge, so the calibrated band matters more than the "
                     "median path.")
        lines.append("")
        for H in horizons:
            sub = [r for r in results if r["horizon"] == H]
            if not sub:
                continue
            lines.append(f"## Horizon {H} trading days")
            lines.append("")
            lines.append("| ticker | spot | median | 80% band | exp. move | stop | R:R | "
                         "conviction | alloc | directive |")
            lines.append("| :--- | ---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- |")
            for r in sorted(sub, key=lambda x: -(x["conviction"] or 0)):
                lines.append(
                    f"| {r['ticker']} | {r['last_price']:.1f} | {r['median_terminal']:.1f} | "
                    f"{r['band_low_terminal']:.0f} – {r['band_high_terminal']:.0f} | "
                    f"{r['expected_move_pct']:+.1f}% | {r['stop_level']:.1f} "
                    f"(-{r['stop_distance_pct']:.1f}%) | {r['risk_reward']:.2f} | "
                    f"{r['conviction'] if r['conviction'] is not None else 'n/a'} | "
                    f"{r['alloc_pct']:.1f}% | {r['directive']} |")
            lines.append("")
        lines.append("## Anonymised LLM theses")
        lines.append("")
        seen = set()
        for r in results:
            if r["ticker"] in seen or not r.get("thesis"):
                continue
            seen.add(r["ticker"])
            lines.append(f"* **{r['ticker']}** (conviction {r['conviction']}, "
                         f"probe leak: {r['identity_probe_leak']}): {r['thesis']}")
        lines.append("")
    with open(os.path.join(out_dir, "FORWARD_REPORT.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n[forward] wrote {out_dir}/forward_predictions.json and FORWARD_REPORT.md")


if __name__ == "__main__":
    main()
