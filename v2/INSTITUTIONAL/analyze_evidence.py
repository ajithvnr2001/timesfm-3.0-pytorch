"""
analyze_evidence.py
===================
Item 4: does giving the LLM real pre-cutoff evidence add predictive value, or does it just
let the model recognise the company?

Both modes are scored on *identical* TimesFM forecasts and identical realised forward returns —
only the LLM input differs:

  * `numbers_only`  : unit-free ratios and price behaviour, no free text
  * `with_evidence` : the same, plus Exa pre-cutoff snippets, anonymised

The decisive test is the third table: rank-IC of the with_evidence conviction score computed
separately on runs the adversarial probe judged clean versus runs it could identify. If the
signal lives only in the identified subset, it is contamination rather than skill.
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
    rx -= rx.mean(); ry -= ry.mean()
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return (float((rx * ry).sum() / d) if d > 0 else None), len(x)


def tier(probe):
    if not probe:
        return "no_probe"
    if not probe.get("leak"):
        return "clean"
    return "suspected" if probe.get("parse_fallback") else "confirmed"


def fmt(v, nd=3):
    return "n/a" if v is None else f"{v:+.{nd}f}"


def main(ledger_path, out_md):
    with open(ledger_path) as f:
        led = json.load(f)
    runs = [r for r in led["runs"].values() if "error" not in r and r.get("metrics")]
    lines = []

    def emit(s=""):
        print(s); lines.append(s)

    modes = ["numbers_only", "with_evidence"]
    have = {m: sum(1 for k in led["llm_cache"] if k.endswith(f"|{m}")) for m in modes}
    emit("# Evidence Mode Experiment — does anonymised pre-cutoff evidence add skill or leak identity?")
    emit()
    emit(f"LLM blocks: {have}. Forecasts are identical across modes ({len(runs)} runs), so any "
         f"difference comes purely from what the LLM was shown.")
    emit()

    # ---------------------------------------------------------------- leak rates
    emit("## 1. Adversarial identity probe by mode")
    emit()
    emit("| mode | clean | suspected | confirmed | any leak |")
    emit("| :--- | ---: | ---: | ---: | ---: |")
    leak_by_mode = {}
    for m in modes:
        t = defaultdict(int)
        for k, b in led["llm_cache"].items():
            if k.endswith(f"|{m}"):
                t[tier(b.get("identity_probe"))] += 1
        n = sum(t.values()) or 1
        leak_by_mode[m] = t
        emit(f"| `{m}` | {t['clean']} ({100*t['clean']/n:.0f}%) | {t['suspected']} "
             f"({100*t['suspected']/n:.0f}%) | {t['confirmed']} ({100*t['confirmed']/n:.0f}%) | "
             f"**{100*(t['suspected']+t['confirmed'])/n:.0f}%** |")
    emit()

    def llm_for(run, mode):
        return led["llm_cache"].get(f"{run['ticker']}|{run['cutoff']}|{mode}")

    # ------------------------------------------------------------------ rank-IC
    emit("## 2. Rank-IC of conviction vs realised forward return, same forecasts")
    emit()
    emit("| horizon | cutoff | n | IC numbers_only | IC with_evidence | delta |")
    emit("| :--- | :--- | ---: | ---: | ---: | ---: |")
    panel = defaultdict(dict)
    for H in sorted({r["horizon"] for r in runs}):
        for cut in sorted({r["cutoff"] for r in runs}):
            sub = [r for r in runs if r["horizon"] == H and r["cutoff"] == cut
                   and r.get("forward_return_pct") is not None]
            if len(sub) < 5:
                continue
            row = {}
            for m in modes:
                conv, fwd = [], []
                for r in sub:
                    b = llm_for(r, m)
                    if b and b.get("conviction_score") is not None:
                        conv.append(b["conviction_score"]); fwd.append(r["forward_return_pct"])
                ic, n = spearman(conv, fwd)
                row[m] = (ic, n)
            panel[(H, cut)] = row
            ic0, n0 = row["numbers_only"]; ic1, n1 = row["with_evidence"]
            delta = (ic1 - ic0) if (ic0 is not None and ic1 is not None) else None
            emit(f"| {H}d | {cut} | {max(n0, n1)} | {fmt(ic0)} | {fmt(ic1)} | {fmt(delta)} |")
    emit()
    from math import erfc, sqrt

    for m in modes:
        ics = [v[m][0] for v in panel.values() if v[m][0] is not None]
        if ics:
            k = len(ics)
            se = (np.std(ics, ddof=1) / sqrt(k)) if k > 1 else float("nan")
            t = (np.mean(ics) / se) if se and se == se and se > 0 else float("nan")
            p_approx = erfc(abs(t) / sqrt(2)) if t == t else float("nan")
            emit(f"* `{m}`: mean IC **{np.mean(ics):+.3f}**, median {np.median(ics):+.3f}, "
                 f"sd {np.std(ics, ddof=1):.3f} across k={k} panels, "
                 f"se {se:.3f}, t={t:.2f}, normal-approx p={p_approx:.3f}, "
                 f"positive in {sum(1 for i in ics if i > 0)}/{k} panels")
    emit()

    # ------------------------------------------------- decisive leak-vs-skill split
    emit("## 3. The decisive split: with_evidence IC on probe-clean vs probe-identified runs")
    emit()
    emit("| horizon | subset | n | rank-IC | top-quintile fwd | bottom-quintile fwd |")
    emit("| :--- | :--- | ---: | ---: | ---: | ---: |")
    summary_split = {}
    for H in sorted({r["horizon"] for r in runs}):
        for label, want_leak in (("probe-clean", False), ("probe-identified", True)):
            conv, fwd = [], []
            for r in runs:
                if r["horizon"] != H or r.get("forward_return_pct") is None:
                    continue
                b = llm_for(r, "with_evidence")
                if not b or b.get("conviction_score") is None:
                    continue
                leaked = bool(b.get("identity_probe", {}).get("leak"))
                if leaked == want_leak:
                    conv.append(b["conviction_score"]); fwd.append(r["forward_return_pct"])
            ic, n = spearman(conv, fwd)
            if n < 5:
                emit(f"| {H}d | {label} | {n} | insufficient | – | – |")
                continue
            order = np.argsort(conv); k = max(1, n // 5)
            top = float(np.mean([fwd[i] for i in order[-k:]]))
            bot = float(np.mean([fwd[i] for i in order[:k]]))
            summary_split[(H, label)] = (ic, n, top, bot)
            emit(f"| {H}d | {label} | {n} | {fmt(ic)} | {top:+.1f}% | {bot:+.1f}% |")
    emit()

    # ------------------------------------------------------- conviction agreement
    emit("## 4. How much did the evidence move the score?")
    emit()
    pairs = []
    for k, b in led["llm_cache"].items():
        if not k.endswith("|numbers_only"):
            continue
        base = k[: -len("numbers_only")]
        other = led["llm_cache"].get(base + "with_evidence")
        if other and b.get("conviction_score") is not None and other.get("conviction_score") is not None:
            pairs.append((b["conviction_score"], other["conviction_score"],
                          bool(other.get("identity_probe", {}).get("leak"))))
    if pairs:
        a = np.array([p[0] for p in pairs]); c = np.array([p[1] for p in pairs])
        rho, _ = spearman(a, c)
        emit(f"* {len(pairs)} paired scores. Mean conviction {a.mean():.1f} (numbers_only) vs "
             f"{c.mean():.1f} (with_evidence); mean absolute change **{np.abs(c-a).mean():.1f} points**; "
             f"rank correlation between modes {fmt(rho)}.")
        leaked = np.array([p[2] for p in pairs])
        if leaked.any() and (~leaked).any():
            emit(f"* Score change is {np.abs(c-a)[leaked].mean():.1f} points on probe-identified "
                 f"runs versus {np.abs(c-a)[~leaked].mean():.1f} on probe-clean runs.")
    emit()

    emit("## Interpretation")
    emit()
    emit("Read this cautiously: k=6 panels is a small sample, the panels overlap in time "
         "(adjacent 252-day windows share most of their return path), and this is a single "
         "pre-specified test rather than a survey. The result is suggestive, not established. "
         "The natural check is more, non-overlapping cutoffs.")
    emit()
    ics0 = [v["numbers_only"][0] for v in panel.values() if v["numbers_only"][0] is not None]
    ics1 = [v["with_evidence"][0] for v in panel.values() if v["with_evidence"][0] is not None]
    if ics0 and ics1:
        emit(f"Evidence mode moved mean rank-IC from **{np.mean(ics0):+.3f}** to "
             f"**{np.mean(ics1):+.3f}** while raising the probe leak rate from "
             f"{100*(leak_by_mode['numbers_only']['suspected']+leak_by_mode['numbers_only']['confirmed'])/max(1,sum(leak_by_mode['numbers_only'].values())):.0f}% "
             f"to {100*(leak_by_mode['with_evidence']['suspected']+leak_by_mode['with_evidence']['confirmed'])/max(1,sum(leak_by_mode['with_evidence'].values())):.0f}%.")
    emit()
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWROTE {out_md}")


if __name__ == "__main__":
    lp = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts/ledger.json")
    om = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "EVIDENCE_EXPERIMENT.md")
    main(lp, om)
