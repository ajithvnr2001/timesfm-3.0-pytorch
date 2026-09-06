"""
engine.py
=========
Single entry point that composes the institutional pipeline for one (ticker, cutoff, horizon):

    PIT data  ->  TimesFM 3.0 (multivariate, native quantiles)
                  ->  PIT conformal calibration of the band
    PIT fundamentals + Exa evidence  ->  anonymise  ->  identity probe
                  ->  LLM conviction (multi-bagger axes, % re-rating)
    ->  risk & sizing  ->  result record

Design decisions, all justified by measured evidence recorded in ABLATION.md:
  * Point forecast config = multivariate raw context (stock, NIFTY, sector), 4096 steps,
    per-variate scaling, NO covariates. Covariates measurably hurt MAPE and coverage.
  * The reported 80% band is the conformally calibrated one; the raw model band is kept
    alongside it for transparency.
  * The LLM never sets the price path. It produces a conviction score used for ranking and
    a separate valuation-anchored scenario, so a hallucination cannot corrupt the forecast.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from calibration import calibrate_pit, rolling_origins, volatility_band_cap
from pit_data import build_pit_bundle, industry_of, pit_fundamentals
from risk_sizing import compute_risk
from timesfm3_adapter import TimesFM3Adapter

SECTOR_BUCKET = {
    "^CNXIT": "information_technology",
    "^CNXAUTO": "automotive",
    "^NSEBANK": "financials",
    "^CNXFMCG": "consumer",
    "^CNXMETAL": "industrials_materials",
    "^CNXENERGY": "energy_utilities",
    "^CNXPHARMA": "healthcare",
    "^CNXREALTY": "real_estate",
    "^NSEI": "diversified",
}


@dataclass
class RunConfig:
    horizon: int = 60
    max_context: int = 4096
    multivariate: bool = True
    use_covariates: bool = False  # measured to hurt; kept switchable for audit
    calibrate: bool = True
    n_calibration_origins: int = 8
    stop_window: int = 20
    use_llm: bool = True
    llm_samples: int = 3
    evidence_mode: str = "numbers_only"  # or "with_evidence" (identity can leak via business description)
    run_identity_probe: bool = True
    portfolio_capital: float = 1_000_000.0
    p_win_empirical: Optional[float] = None


def price_features(bundle) -> dict:
    """Unit-free price behaviour for the LLM packet (no absolute price, no dates)."""
    c = bundle.context[0]
    def chg(n):
        return None if len(c) <= n else round(float(c[-1] / c[-n - 1] - 1.0) * 100, 1)
    rets = np.diff(c) / c[:-1]
    vol = float(np.std(rets[-252:]) * np.sqrt(252) * 100) if len(rets) > 60 else None
    dd = float((c[-1] / np.max(c[-252:]) - 1.0) * 100) if len(c) >= 252 else None
    return {
        "return_1m_pct": chg(21),
        "return_3m_pct": chg(63),
        "return_12m_pct": chg(252),
        "return_36m_pct": chg(756),
        "annualised_vol_pct": None if vol is None else round(vol, 1),
        "drawdown_from_12m_high_pct": None if dd is None else round(dd, 1),
    }


def run_single(
    ticker: str,
    cutoff: Optional[str],
    cfg: RunConfig,
    adapter: TimesFM3Adapter,
    industry: Optional[str] = None,
    company_names: Optional[list] = None,
) -> dict:
    t_start = time.time()
    H = cfg.horizon
    ind = industry if industry is not None else industry_of(ticker, allow_live_metadata=True)
    bundle = build_pit_bundle(ticker, cutoff, H, max_context=cfg.max_context, industry=ind)

    ctx = bundle.context if cfg.multivariate else bundle.context[0]
    names = bundle.target_names if cfg.multivariate else ["stock"]
    kw = {}
    if cfg.use_covariates:
        kw["past_covariates"] = bundle.past_covariates
        kw["past_future_covariates"] = bundle.past_future_covariates
    fres = adapter.predict(context=ctx, horizon=H, target_names=names, ts_id="ASSET_ALPHA", **kw)

    hist_for_vol = bundle.context[0]
    _rets = np.diff(hist_for_vol) / hist_for_vol[:-1]
    _win = _rets[-252:] if len(_rets) >= 252 else _rets
    ann_vol_hist = float(np.std(_win) * np.sqrt(252)) if len(_win) > 2 else 0.30
    band_cap = volatility_band_cap(ann_vol_hist, H)

    raw_low, raw_high = fres.q10.copy(), fres.q90.copy()
    cal_info = {"status": "disabled", "k_low": 1.0, "k_high": 1.0}
    band_low, band_high = raw_low, raw_high
    if cfg.calibrate and cutoff is not None:
        origins = rolling_origins(bundle.dates, cutoff, H, n_origins=cfg.n_calibration_origins)

        def predict_fn(origin, horizon):
            bb = build_pit_bundle(ticker, str(origin.date()), horizon,
                                  max_context=cfg.max_context, industry=ind)
            if bb.actuals is None or len(bb.actuals) < horizon * 0.8:
                return None
            cc = bb.context if cfg.multivariate else bb.context[0]
            kk = {}
            if cfg.use_covariates:
                kk["past_covariates"] = bb.past_covariates
                kk["past_future_covariates"] = bb.past_future_covariates
            rr = adapter.predict(context=cc, horizon=horizon,
                                 target_names=bb.target_names if cfg.multivariate else ["stock"], **kk)
            return {"median": rr.median, "q10": rr.q10, "q90": rr.q90, "actual": bb.actuals}

        cal = calibrate_pit(predict_fn, origins, H)
        cal_info = asdict(cal)
        cal_info["ann_vol_hist"] = round(ann_vol_hist, 4)
        cal_info["log_halfwidth_cap"] = round(band_cap, 4)
        if cal.status == "fitted":
            band_low, band_high = cal.apply(fres.median, raw_low, raw_high,
                                            max_log_halfwidth=band_cap)
    elif cfg.calibrate and cutoff is None:
        # Live mode: calibrate on origins ending at the last available date
        origins = rolling_origins(bundle.dates, bundle.dates[-1], H,
                                  n_origins=cfg.n_calibration_origins)

        def predict_fn_live(origin, horizon):
            bb = build_pit_bundle(ticker, str(origin.date()), horizon,
                                  max_context=cfg.max_context, industry=ind)
            if bb.actuals is None or len(bb.actuals) < horizon * 0.8:
                return None
            cc = bb.context if cfg.multivariate else bb.context[0]
            rr = adapter.predict(context=cc, horizon=horizon,
                                 target_names=bb.target_names if cfg.multivariate else ["stock"])
            return {"median": rr.median, "q10": rr.q10, "q90": rr.q90, "actual": bb.actuals}

        cal = calibrate_pit(predict_fn_live, origins, H)
        cal_info = asdict(cal)
        cal_info["ann_vol_hist"] = round(ann_vol_hist, 4)
        cal_info["log_halfwidth_cap"] = round(band_cap, 4)
        if cal.status == "fitted":
            band_low, band_high = cal.apply(fres.median, raw_low, raw_high,
                                            max_log_halfwidth=band_cap)

    band_low = np.minimum(band_low, fres.median)
    band_high = np.maximum(band_high, fres.median)

    # ---------------------------------------------------------------- LLM layer
    llm_block = {"status": "disabled"}
    if cfg.use_llm:
        from llm_agents import (build_anonymised_packet, retrieve_pit_evidence,
                                run_identity_probe, score_conviction)

        names_for_scrub = list(company_names or []) + [ticker, ticker.split(".")[0]]
        evidence = (retrieve_pit_evidence(company_names or [ticker.split(".")[0]], cutoff)
                    if cfg.evidence_mode == "with_evidence"
                    else {"snippets": [], "status": "skipped_numbers_only_mode",
                          "provider": "none", "n_raw": 0, "n_kept": 0,
                          "dropped_future": 0, "dropped_boilerplate": 0})
        packet, anon_report = build_anonymised_packet(
            fundamentals=pit_fundamentals(ticker, cutoff),
            price_features=price_features(bundle),
            evidence=evidence,
            company_names=names_for_scrub,
            cutoff=cutoff,
            sector_bucket=SECTOR_BUCKET.get(bundle.sector_ticker, "diversified"),
            evidence_mode=cfg.evidence_mode,
        )
        probe = (run_identity_probe(packet, names_for_scrub)
                 if cfg.run_identity_probe else {"probe_ran": False, "leak": False})
        conv = score_conviction(packet, n_samples=cfg.llm_samples)
        llm_block = {
            "status": conv.status,
            "evidence": {k: v for k, v in evidence.items() if k != "snippets"},
            "anonymisation": anon_report,
            "identity_probe": probe,
            "conviction_score": conv.conviction_score,
            "axis_scores": conv.axis_scores,
            "expected_rerating_pct": conv.expected_rerating_pct,
            "thesis": conv.thesis,
            "risks": conv.risks,
            "n_samples": conv.n_samples,
            "disagreement": round(conv.disagreement, 2),
            "provider": conv.provider,
        }

    # -------------------------------------------------------------- risk layer
    risk = compute_risk(
        history=bundle.context[0], last_price=bundle.last_price,
        forecast_median=fres.median, band_low=band_low, band_high=band_high,
        horizon=H, stop_window=cfg.stop_window,
        p_win_empirical=cfg.p_win_empirical, portfolio_capital=cfg.portfolio_capital,
    )

    # ----------------------------------------------------------------- scoring
    act = bundle.actuals
    metrics = {}
    if act is not None and len(act) > 0:
        n = len(act)
        med = fres.median[:n]
        metrics = {
            "n_actuals": int(n),
            "actual_terminal": float(act[-1]),
            "actual_move_pct": round(float((act[-1] / bundle.last_price - 1) * 100), 2),
            "pred_terminal": float(med[-1]),
            "pred_move_pct": round(float((med[-1] / bundle.last_price - 1) * 100), 2),
            "mape": round(float(np.mean(np.abs((act - med) / act)) * 100), 3),
            "mae": round(float(np.mean(np.abs(act - med))), 3),
            "naive_mape": round(float(np.mean(np.abs((act - bundle.last_price) / act)) * 100), 3),
            "directional_correct": int(np.sign(med[-1] - bundle.last_price)
                                       == np.sign(act[-1] - bundle.last_price)),
            "raw_band_coverage_pct": round(float(np.mean((act >= raw_low[:n]) & (act <= raw_high[:n])) * 100), 1),
            "calibrated_band_coverage_pct": round(float(np.mean((act >= band_low[:n]) & (act <= band_high[:n])) * 100), 1),
            "pinball_q10_q90": round(float(
                np.mean(np.maximum(0.1 * (act - raw_low[:n]), 0.9 * (raw_low[:n] - act)))
                + np.mean(np.maximum(0.9 * (act - raw_high[:n]), 0.1 * (raw_high[:n] - act)))
            ), 3),
        }

    return {
        "ticker": ticker,
        "cutoff": bundle.cutoff,
        "horizon": H,
        "industry": ind,
        "last_price": bundle.last_price,
        "config": asdict(cfg),
        "pit_audit": bundle.audit,
        "forecast_provenance": fres.provenance,
        "calibration": cal_info,
        "forecast": {
            "median": [round(float(x), 4) for x in fres.median],
            "raw_q10": [round(float(x), 4) for x in raw_low],
            "raw_q90": [round(float(x), 4) for x in raw_high],
            "calibrated_low": [round(float(x), 4) for x in band_low],
            "calibrated_high": [round(float(x), 4) for x in band_high],
            "future_dates": [str(d.date()) for d in bundle.future_dates],
        },
        "actuals": None if act is None else [round(float(x), 4) for x in act],
        "actual_dates": None if bundle.actual_dates is None else [str(d.date()) for d in bundle.actual_dates],
        "metrics": metrics,
        "llm": llm_block,
        "risk": asdict(risk),
        "runtime_seconds": round(time.time() - t_start, 2),
        "valid_for_backtest": bool(
            cutoff is None or not llm_block.get("identity_probe", {}).get("leak", False)
        ),
    }
