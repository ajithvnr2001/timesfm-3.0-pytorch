"""
analyze_validation.py
=====================
Turns the walk-forward ledger into an honest scorecard. Runs on CPU from the local ledger.

Reports:
  1. Forecast skill vs naive / drift / seasonal baselines, per horizon, with beats-naive rates.
  2. Interval calibration: raw TimesFM 3.0 band vs PIT-conformal calibrated band.
  3. Screener quality: Spearman rank-IC between the anonymised LLM conviction score and the
     realised forward return, plus top-vs-bottom quintile spreads and multi-bagger hit rate.
  4. Leak accounting in two tiers, and the same screener numbers recomputed with leaking
     runs removed, so the reader can see how much the conclusion depends on them.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import numpy as np


def spearman(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 4:
        return None, len(x)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return (float((rx * ry).sum() / denom) if denom > 0 else None), len(x)


def _skill_groups(runs):
    """(horizon, label, subset) groups: all quarterly cutoffs for 60d, plus both the
    non-overlapping and full sets for 252d."""
    out = []
    for H in sorted({r["horizon"] for r in runs}):
        sub = [r for r in runs if r["horizon"] == H]
        if H >= 252:
            no = [r for r in sub if r["cutoff"] in NON_OVERLAPPING_252D]
            if no:
                out.append((H, f"{H}d non-overlapping", no))
            out.append((H, f"{H}d all cutoffs (overlapping)", sub))
        else:
            out.append((H, f"{H}d", sub))
    return out


def leak_tier(probe: dict) -> str:
    if not probe:
        return "no_probe"
    if not probe.get("leak"):
        return "clean"
    return "suspected" if probe.get("parse_fallback") else "confirmed"


def fmt(v, nd=2, dash="  n/a"):
    return dash if v is None else f"{v:.{nd}f}"


NON_OVERLAPPING_252D = ["2022-12-30", "2023-12-29", "2024-12-31"]


def main(ledger_path: str, out_md: str):
    with open(ledger_path) as f:
        ledger = json.load(f)
    runs = [r for r in ledger["runs"].values() if "error" not in r and r.get("metrics")]
    errs = [r for r in ledger["runs"].values() if "error" in r]
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("# Walk-Forward Validation — TimesFM 3.0 + Anonymised LLM Screener")
    emit()
    emit(f"Runs completed: **{len(runs)}**  |  errored: {len(errs)}  |  "
         f"cutoffs: {sorted({r['cutoff'] for r in runs})}  |  "
         f"horizons: {sorted({r['horizon'] for r in runs})}  |  "
         f"names: {len({r['ticker'] for r in runs})}")
    prov = next((r.get("provenance") for r in runs if r.get("provenance")), {})
    emit(f"Model: `{prov.get('model_id')}` on `{prov.get('device')}`, context "
         f"{prov.get('context_length')}, targets {prov.get('target_names')}, "
         f"neural points = full horizon (no extrapolation).")
    emit()

    # ---------------------------------------------------------------- 1. skill
    emit("## 0. Panel design")
    emit()
    emit("60 trading days is roughly one quarter, so quarterly cutoffs give near-independent "
         "60d panels and all of them are used. 252-day windows from adjacent quarterly cutoffs "
         "share ~80% of their return path, so for the 252d horizon the **headline** uses only "
         f"the annually spaced, non-overlapping subset `{NON_OVERLAPPING_252D}`; the full "
         "overlapping set is reported alongside and flagged, because its panels are correlated "
         "and its effective sample size is smaller than n suggests.")
    emit()

    emit("## 1. Point-forecast skill vs baselines")
    emit()
    emit("| horizon | n | TimesFM MAPE (mean / median) | naive | drift | seasonal | "
         "beats naive | directional acc |")
    emit("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for H, label, sub in _skill_groups(runs):
        m = np.array([r["metrics"]["mape"] for r in sub], dtype=float)
        nv = np.array([r["metrics"]["naive_mape"] for r in sub], dtype=float)
        dr = np.array([r.get("baselines", {}).get("drift_mape", np.nan) for r in sub], dtype=float)
        se = np.array([r.get("baselines", {}).get("seasonal_mape", np.nan) for r in sub], dtype=float)
        d = np.array([r["metrics"]["directional_correct"] for r in sub], dtype=float)
        emit(f"| {label} | {len(sub)} | **{m.mean():.2f} / {np.median(m):.2f}** | "
             f"{nv.mean():.2f} / {np.median(nv):.2f} | {np.nanmean(dr):.2f} | "
             f"{np.nanmean(se):.2f} | {100*np.mean(m < nv):.0f}% | {100*d.mean():.0f}% |")
    emit()
    allm = np.array([r["metrics"]["mape"] for r in runs])
    alln = np.array([r["metrics"]["naive_mape"] for r in runs])
    dirs = np.array([r["metrics"]["directional_correct"] for r in runs], dtype=float)
    n = len(dirs)
    hit = float(dirs.mean())
    z = (hit - 0.5) / np.sqrt(0.25 / n) if n else 0.0
    # two-sided normal approximation p-value
    from math import erfc, sqrt

    pval = erfc(abs(z) / sqrt(2))
    emit(f"Pooled: TimesFM mean MAPE {allm.mean():.2f}% vs naive {alln.mean():.2f}% "
         f"(**{allm.mean()-alln.mean():+.2f}pp**), beats naive on {100*np.mean(allm<alln):.0f}% of runs.")
    emit()
    verdict = ("statistically significant at the 5% level" if pval < 0.05
               else "NOT statistically significant" if pval >= 0.05 else "")
    emit(f"Directional accuracy **{100*hit:.1f}%** on n={n} runs "
         f"(z={z:.2f}, two-sided p={pval:.3f} against a 50% coin flip) - {verdict}.")
    emit()
    if pval >= 0.05:
        emit("> An earlier, smaller version of this study (n=192, three cutoffs) measured 57.8% "
             "with p=0.030 and the docs described it as the model's one real edge. Expanding to "
             f"{n} runs across eight cutoffs pulled it back to {100*hit:.1f}% with p={pval:.3f}. "
             "The original figure was a small-sample artefact. The honest conclusion is that "
             "**no component of the point forecast has demonstrated skill** on this data; only "
             "the calibrated interval survives scrutiny.")
        emit()
    emit()
    emit(f"Against the *trend-following* baselines the model is far ahead at long horizons: "
         f"252d mean MAPE {np.mean([r['metrics']['mape'] for r in runs if r['horizon']==252]):.1f}% "
         f"vs drift {np.nanmean([r.get('baselines',{}).get('drift_mape',np.nan) for r in runs if r['horizon']==252]):.1f}% "
         f"and seasonal {np.nanmean([r.get('baselines',{}).get('seasonal_mape',np.nan) for r in runs if r['horizon']==252]):.1f}%. "
         f"It is the flat random walk specifically that it cannot beat.")
    emit()
    with open("/tmp/_hitrate.txt", "w") as f:
        f.write(str(hit))

    # ---------------------------------------------------------- 2. calibration
    emit("## 2. Interval calibration (nominal 80%)")
    emit()
    emit("| horizon | n | raw q10-q90 coverage | PIT-conformal coverage | "
         "median k_low | median k_high | calibration status |")
    emit("| :--- | ---: | ---: | ---: | ---: | ---: | :--- |")
    for H in sorted({r["horizon"] for r in runs}):
        sub = [r for r in runs if r["horizon"] == H]
        raw = np.array([r["metrics"]["raw_band_coverage_pct"] for r in sub], dtype=float)
        cal = np.array([r["metrics"]["calibrated_band_coverage_pct"] for r in sub], dtype=float)
        kl = np.array([r["calibration"].get("k_low", np.nan) for r in sub], dtype=float)
        kh = np.array([r["calibration"].get("k_high", np.nan) for r in sub], dtype=float)
        fitted = sum(1 for r in sub if r["calibration"].get("status") == "fitted")
        emit(f"| {H}d | {len(sub)} | {raw.mean():.1f}% | **{cal.mean():.1f}%** | "
             f"{np.nanmedian(kl):.2f} | {np.nanmedian(kh):.2f} | {fitted}/{len(sub)} fitted |")
    emit()
    raw_all = np.array([r["metrics"]["raw_band_coverage_pct"] for r in runs])
    cal_all = np.array([r["metrics"]["calibrated_band_coverage_pct"] for r in runs])
    emit(f"Pooled coverage: raw **{raw_all.mean():.1f}%** -> calibrated **{cal_all.mean():.1f}%** "
         f"against an 80% nominal band. Absolute miscalibration "
         f"|coverage-80| improves from {np.abs(raw_all-80).mean():.1f}pp to "
         f"{np.abs(cal_all-80).mean():.1f}pp.")
    emit()

    # ------------------------------------------------------------- 3. screener
    emit("## 3. Multi-bagger screener: does the anonymised LLM conviction rank anything?")
    emit()
    emit("| horizon | cutoff | n | rank-IC (conviction vs forward return) | "
         "top-quintile mean fwd | bottom-quintile mean fwd | spread |")
    emit("| :--- | :--- | ---: | ---: | ---: | ---: | ---: |")
    ic_rows = []
    for H in sorted({r["horizon"] for r in runs}):
        for cut in sorted({r["cutoff"] for r in runs}):
            sub = [r for r in runs if r["horizon"] == H and r["cutoff"] == cut
                   and r["llm"].get("conviction_score") is not None
                   and r.get("forward_return_pct") is not None]
            if len(sub) < 5:
                continue
            conv = [r["llm"]["conviction_score"] for r in sub]
            fwd = [r["forward_return_pct"] for r in sub]
            ic, n = spearman(conv, fwd)
            order = np.argsort(conv)
            k = max(1, len(sub) // 5)
            top = np.mean([fwd[i] for i in order[-k:]])
            bot = np.mean([fwd[i] for i in order[:k]])
            ic_rows.append((H, cut, n, ic, top, bot))
            emit(f"| {H}d | {cut} | {n} | {fmt(ic,3)} | {top:+.1f}% | {bot:+.1f}% | "
                 f"{top-bot:+.1f}pp |")
    emit()
    if ic_rows:
        ics = [r[3] for r in ic_rows if r[3] is not None]
        emit(f"Mean rank-IC across {len(ics)} (horizon, cutoff) panels: **{np.mean(ics):+.3f}** "
             f"(median {np.median(ics):+.3f}, sd {np.std(ics):.3f}). "
             f"Panels with positive IC: {sum(1 for i in ics if i>0)}/{len(ics)}.")
    emit()

    # --------------------------------------------------------- 4. leak audit
    emit("## 4. Leakage audit (adversarial identity probe)")
    emit()
    tiers = defaultdict(int)
    for key, block in ledger["llm_cache"].items():
        tiers[leak_tier(block.get("identity_probe"))] += 1
    total = sum(tiers.values())
    emit(f"LLM blocks: {total}. Probe verdicts -> "
         + ", ".join(f"**{k}**: {v} ({100*v/max(1,total):.0f}%)" for k, v in sorted(tiers.items())))
    emit()
    emit("* `confirmed` = the probe returned a parsed guess containing a distinctive token of "
         "the real company name. Those runs are marked `valid_for_backtest=false`.")
    emit("* `suspected` = no parsable JSON, but a distinctive token appeared in the model's "
         "reasoning prose. Conservative, may include false positives.")
    emit("* `clean` = the probe could not name the company.")
    emit()

    clean_runs = [r for r in runs
                  if leak_tier(r["llm"].get("identity_probe")) == "clean"]
    emit(f"Screener recomputed on probe-clean runs only (n={len(clean_runs)}):")
    emit()
    emit("| horizon | n | rank-IC | top-quintile fwd | bottom-quintile fwd |")
    emit("| :--- | ---: | ---: | ---: | ---: |")
    for H in sorted({r["horizon"] for r in clean_runs}):
        sub = [r for r in clean_runs if r["horizon"] == H
               and r["llm"].get("conviction_score") is not None
               and r.get("forward_return_pct") is not None]
        if len(sub) < 5:
            continue
        conv = [r["llm"]["conviction_score"] for r in sub]
        fwd = [r["forward_return_pct"] for r in sub]
        ic, n = spearman(conv, fwd)
        order = np.argsort(conv)
        k = max(1, len(sub) // 5)
        emit(f"| {H}d | {n} | {fmt(ic,3)} | "
             f"{np.mean([fwd[i] for i in order[-k:]]):+.1f}% | "
             f"{np.mean([fwd[i] for i in order[:k]]):+.1f}% |")
    emit()

    # ------------------------------------------------------- 5. multibaggers
    emit("## 5. Did it find the big winners?")
    emit()
    big = sorted([r for r in runs if r["horizon"] == max({x["horizon"] for x in runs})
                  and r.get("forward_return_pct") is not None],
                 key=lambda r: -r["forward_return_pct"])[:10]
    emit("| ticker | cutoff | realised fwd return | conviction | probe | "
         "TimesFM predicted move | directive |")
    emit("| :--- | :--- | ---: | ---: | :--- | ---: | :--- |")
    for r in big:
        emit(f"| {r['ticker']} | {r['cutoff']} | **{r['forward_return_pct']:+.1f}%** | "
             f"{fmt(r['llm'].get('conviction_score'),0)} | "
             f"{leak_tier(r['llm'].get('identity_probe'))} | "
             f"{fmt(r['metrics'].get('pred_move_pct'),1)}% | {r['risk']['directive']} |")
    emit()

    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWROTE {out_md}")


if __name__ == "__main__":
    lp = sys.argv[1] if len(sys.argv) > 1 else \
        "/root/timesfm-3.0-pytorch/v2/INSTITUTIONAL/artifacts/ledger.json"
    om = sys.argv[2] if len(sys.argv) > 2 else \
        "/root/timesfm-3.0-pytorch/v2/INSTITUTIONAL/VALIDATION.md"
    main(lp, om)
