"""
run_ablation.py
===============
Regenerates the machine-readable configuration ablation that `ABLATION.md` reports.

Stage A: representation / context / covariate choices for TimesFM 3.0, scored against naive,
drift and seasonal-naive baselines. Stage B: H=60 calibration ablation (raw native band vs
PIT conformal) on the production configuration.

Writes artifacts/ablation_stageA.json and artifacts/ablation_h60.json so the numbers quoted
in the docs are reproducible instead of transcribed. Env: OUT_DIR.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calibration import calibrate_pit, rolling_origins, volatility_band_cap  # noqa: E402
from pit_data import build_pit_bundle, industry_of  # noqa: E402
from timesfm3_adapter import TimesFM3Adapter  # noqa: E402

TICKERS = ["INFY.NS", "TCS.NS", "MODISONLTD.NS", "CUPID.NS", "HEROMOTOCO.NS", "NETWEB.NS"]
CUTOFFS = ["2024-03-28", "2024-06-28", "2024-12-31", "2025-06-30"]
HORIZONS = [21, 60]
CFGS = ["uni_raw_4096", "multi_raw_4096", "uni_raw_ctx512", "uni_raw_ctx1024",
        "uni_raw_ctx2048", "uni_raw_noscale_2048", "uni_log_2048", "multi_log_2048",
        "uni_raw_cov_z_2048", "multi_raw_cov_z_2048"]


def zrows(m):
    mu = m.mean(axis=1, keepdims=True)
    sd = m.std(axis=1, keepdims=True)
    return ((m - mu) / np.where(sd < 1e-9, 1.0, sd)).astype(np.float32)


def run_cfg(ad, name, b, H):
    ctx, pcov, pfcov = b.context, b.past_covariates, b.past_future_covariates
    if name == "multi_raw_4096":
        r = ad.predict(context=ctx, horizon=H, target_names=b.target_names)
    elif name == "uni_raw_4096":
        r = ad.predict(context=ctx[0], horizon=H)
    elif name.startswith("uni_raw_ctx"):
        n = int(name.split("ctx")[1])
        r = ad.predict(context=ctx[0, -n:], horizon=H)
    elif name == "uni_raw_noscale_2048":
        r = ad.predict(context=ctx[0, -2048:], horizon=H, scale_targets=False)
    elif name == "uni_log_2048":
        lg = np.log(ctx[0, -2048:]).astype(np.float32)
        a = float(lg[-1])
        r = ad.predict(context=lg - a, horizon=H, scale_targets=False)
        return np.exp(r.point + a), np.exp(r.q10 + a), np.exp(r.q90 + a)
    elif name == "multi_log_2048":
        lg = np.log(ctx[:, -2048:]).astype(np.float32)
        a = lg[:, -1:].copy()
        r = ad.predict(context=lg - a, horizon=H, scale_targets=False, target_names=b.target_names)
        return (np.exp(r.point + a[0, 0]), np.exp(r.q10 + a[0, 0]), np.exp(r.q90 + a[0, 0]))
    elif name == "multi_raw_cov_z_2048":
        r = ad.predict(context=ctx[:, -2048:], horizon=H,
                       past_covariates=zrows(pcov[:, -2048:]),
                       past_future_covariates=zrows(pfcov[:, -(2048 + H):]),
                       target_names=b.target_names)
    elif name == "uni_raw_cov_z_2048":
        r = ad.predict(context=ctx[0, -2048:], horizon=H,
                       past_covariates=zrows(pcov[:, -2048:]),
                       past_future_covariates=zrows(pfcov[:, -(2048 + H):]))
    else:
        raise ValueError(name)
    return r.point, r.q10, r.q90


def stage_a(ad, industries):
    rows = []
    for tk in TICKERS:
        for cut in CUTOFFS:
            for H in HORIZONS:
                try:
                    b = build_pit_bundle(tk, cut, H, max_context=4096, industry=industries[tk])
                except Exception as exc:
                    print(f"  skip {tk} {cut} H{H}: {type(exc).__name__}")
                    continue
                if b.actuals is None or len(b.actuals) < H * 0.9:
                    continue
                act, last, hist = b.actuals, b.last_price, b.context[0]
                n = len(act)
                rec = {"ticker": tk, "cutoff": cut, "H": H,
                       "move_pct": round(100 * (act[-1] / last - 1), 2),
                       "naive_mape": round(float(np.mean(np.abs((act - last) / act)) * 100), 3)}
                look = min(60, len(hist) - 1)
                dpath = last + ((hist[-1] - hist[-look - 1]) / look) * np.arange(1, n + 1)
                rec["drift_mape"] = round(float(np.mean(np.abs((act - dpath) / act)) * 100), 3)
                seas = hist[-n:] * (last / hist[-n])
                rec["seasonal_mape"] = round(float(np.mean(np.abs((act - seas) / act)) * 100), 3)
                for cfg in CFGS:
                    try:
                        p, q10, q90 = run_cfg(ad, cfg, b, H)
                        rec[f"{cfg}__mape"] = round(float(np.mean(np.abs((act - p[:n]) / act)) * 100), 3)
                        rec[f"{cfg}__dir"] = int(np.sign(p[n - 1] - last) == np.sign(act[-1] - last))
                        rec[f"{cfg}__cov"] = round(float(np.mean((act >= q10[:n]) & (act <= q90[:n])) * 100), 1)
                    except Exception as exc:
                        rec[f"{cfg}__err"] = f"{type(exc).__name__}: {str(exc)[:70]}"
                rows.append(rec)
        print(f"  stage A done: {tk}")
    return rows


def stage_b(ad, industries):
    """H=60 calibration ablation on the production config, with the shipped log-space cap."""
    rows = []
    for tk in TICKERS[:4]:
        for cut in ["2024-06-28", "2024-12-31", "2025-06-30"]:
            try:
                b = build_pit_bundle(tk, cut, 60, max_context=4096, industry=industries[tk])
            except Exception:
                continue
            if b.actuals is None or len(b.actuals) < 54:
                continue
            r = ad.predict(context=b.context, horizon=60, target_names=b.target_names)
            act = b.actuals
            n = len(act)
            hist = b.context[0]
            rets = np.diff(hist) / hist[:-1]
            win = rets[-252:] if len(rets) >= 252 else rets
            ann_vol = float(np.std(win) * np.sqrt(252))
            cap = volatility_band_cap(ann_vol, 60)

            def predict_fn(origin, horizon):
                bb = build_pit_bundle(tk, str(origin.date()), horizon, max_context=4096,
                                      industry=industries[tk])
                if bb.actuals is None or len(bb.actuals) < horizon * 0.8:
                    return None
                rr = ad.predict(context=bb.context, horizon=horizon, target_names=bb.target_names)
                return {"median": rr.median, "q10": rr.q10, "q90": rr.q90, "actual": bb.actuals}

            cal = calibrate_pit(predict_fn, rolling_origins(b.dates, cut, 60, n_origins=8), 60)
            lo, hi = cal.apply(r.median, r.q10, r.q90, max_log_halfwidth=cap)
            rows.append({
                "ticker": tk, "cutoff": cut, "ann_vol": round(ann_vol, 3),
                "log_halfwidth_cap": round(cap, 3),
                "raw_cov_pct": round(float(np.mean((act >= r.q10[:n]) & (act <= r.q90[:n])) * 100), 1),
                "cal_cov_pct": round(float(np.mean((act >= lo[:n]) & (act <= hi[:n])) * 100), 1),
                "k_low": round(cal.k_low, 3), "k_high": round(cal.k_high, 3),
                "cal_status": cal.status, "n_cal_points": cal.n_calibration_points,
                "band_low_terminal": round(float(lo[n - 1]), 2),
                "band_high_terminal": round(float(hi[n - 1]), 2),
                "actual_terminal": round(float(act[-1]), 2),
                "negative_bound": bool(lo.min() <= 0),
            })
            print(f"  stage B {tk} {cut}: raw {rows[-1]['raw_cov_pct']}% -> cal {rows[-1]['cal_cov_pct']}%")
    return rows


def summarise(rows):
    df = pd.DataFrame(rows)
    out = {"n_cases": len(df), "by_horizon": {}}
    for H in sorted(df.H.unique()):
        sub = df[df.H == H]
        base = float(sub["naive_mape"].mean())
        block = {"n": int(len(sub)),
                 "naive_mape_mean": round(base, 3),
                 "naive_mape_median": round(float(sub["naive_mape"].median()), 3),
                 "drift_mape_mean": round(float(sub["drift_mape"].mean()), 3),
                 "seasonal_mape_mean": round(float(sub["seasonal_mape"].mean()), 3),
                 "configs": {}}
        for cfg in CFGS:
            c = f"{cfg}__mape"
            if c not in sub:
                continue
            block["configs"][cfg] = {
                "mape_mean": round(float(sub[c].mean()), 3),
                "mape_median": round(float(sub[c].median()), 3),
                "vs_naive_pp": round(float(sub[c].mean() - base), 3),
                "beats_naive": int((sub[c] < sub["naive_mape"]).sum()),
                "directional_acc_pct": round(100 * float(sub[f"{cfg}__dir"].mean()), 1),
                "coverage_pct": round(float(sub[f"{cfg}__cov"].mean()), 1),
            }
        out["by_horizon"][str(H)] = block
    pooled_base = float(df["naive_mape"].mean())
    out["pooled"] = {"n": int(len(df)), "naive_mape_mean": round(pooled_base, 3),
                     "naive_mape_median": round(float(df["naive_mape"].median()), 3),
                     "drift_mape_mean": round(float(df["drift_mape"].mean()), 3),
                     "seasonal_mape_mean": round(float(df["seasonal_mape"].mean()), 3),
                     "configs": {}}
    for cfg in CFGS:
        c = f"{cfg}__mape"
        if c not in df:
            continue
        out["pooled"]["configs"][cfg] = {
            "mape_mean": round(float(df[c].mean()), 3),
            "mape_median": round(float(df[c].median()), 3),
            "vs_naive_pp": round(float(df[c].mean() - pooled_base), 3),
            "beats_naive": int((df[c] < df["naive_mape"]).sum()),
            "directional_acc_pct": round(100 * float(df[f"{cfg}__dir"].mean()), 1),
            "coverage_pct": round(float(df[f"{cfg}__cov"].mean()), 1),
        }
    return out


def main():
    out_dir = os.environ.get("OUT_DIR", "/content/OUT/ABLATION")
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    ad = TimesFM3Adapter(device=os.environ.get("DEVICE", "cuda")).load()
    industries = {t: industry_of(t, True) for t in TICKERS}
    print(f"[ablation] model {ad.load_seconds}s | industries {industries}")

    a_rows = stage_a(ad, industries)
    a_summary = summarise(a_rows)
    with open(os.path.join(out_dir, "ablation_stageA.json"), "w") as f:
        json.dump({"cases": a_rows, "summary": a_summary,
                   "provenance": {"model_id": ad.model_id, "device": ad.device,
                                  "tickers": TICKERS, "cutoffs": CUTOFFS, "horizons": HORIZONS,
                                  "configs": CFGS}}, f, indent=2)
    print(f"[ablation] stage A: {a_summary['pooled']['n']} cases in {round(time.time()-t0)}s")
    for cfg, v in sorted(a_summary["pooled"]["configs"].items(), key=lambda kv: kv[1]["mape_mean"]):
        print(f"   {cfg:24s} mape={v['mape_mean']:6.2f} vs_naive={v['vs_naive_pp']:+6.2f} "
              f"beats={v['beats_naive']:2d} dir={v['directional_acc_pct']:5.1f}% cov={v['coverage_pct']:5.1f}%")
    print(f"   {'naive':24s} mape={a_summary['pooled']['naive_mape_mean']:6.2f}")

    b_rows = stage_b(ad, industries)
    b_summary = {"n": len(b_rows)}
    if b_rows:
        bdf = pd.DataFrame(b_rows)
        b_summary.update({
            "raw_cov_mean": round(float(bdf["raw_cov_pct"].mean()), 2),
            "cal_cov_mean": round(float(bdf["cal_cov_pct"].mean()), 2),
            "abs_miscal_raw_pp": round(float((bdf["raw_cov_pct"] - 80).abs().mean()), 2),
            "abs_miscal_cal_pp": round(float((bdf["cal_cov_pct"] - 80).abs().mean()), 2),
            "any_negative_bound": bool(bdf["negative_bound"].any()),
        })
    with open(os.path.join(out_dir, "ablation_h60.json"), "w") as f:
        json.dump({"cases": b_rows, "summary": b_summary}, f, indent=2)
    print(f"[ablation] stage B: {json.dumps(b_summary)}")
    print(f"[ablation] total {round(time.time()-t0)}s")


if __name__ == "__main__":
    main()
