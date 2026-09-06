"""
Unit tests for the institutional engine that do NOT require a GPU or network.

Run:  python3 v3/tests/test_units.py

GPU/network-dependent behaviour (real TimesFM 3.0 inference, yfinance, Exa, LLM) is
verified separately on the Colab T4; those results are recorded in TIMESFM3_API.md,
ABLATION.md and VALIDATION.md.
"""

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from anonymizer import (GENERIC_NAME_TOKENS, anonymise_text, audit_packet,  # noqa: E402
                        build_name_variants, distinctive_tokens, identity_probe_verdict)
from calibration import (CalibrationResult, _standardised_errors, calibrate_pit,  # noqa: E402
                         rolling_origins, volatility_band_cap)
from pit_data import (build_past_covariates, build_past_future_covariates,  # noqa: E402
                      PAST_COVARIATE_NAMES, PAST_FUTURE_COVARIATE_NAMES, future_business_days)
from risk_sizing import compute_risk  # noqa: E402
from timesfm3_adapter import TimesFM3Adapter, TimesFMUnavailable  # noqa: E402

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"PASS  {name}")
    except Exception as exc:
        FAIL.append((name, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL  {name}: {type(exc).__name__}: {exc}")


# ------------------------------------------------------------------ calibration
def test_log_space_band_stays_positive():
    """Price-space widening produced negative floors; log space must not."""
    cal = CalibrationResult(k_low=6.0, k_high=6.0, status="fitted")
    median = np.array([5193.0, 5000.0])
    q10 = np.array([4200.0, 4000.0])
    q90 = np.array([6300.0, 6200.0])
    low, high = cal.apply(median, q10, q90)
    assert np.all(low > 0), f"lower band went non-positive: {low}"
    assert np.all(low < median) and np.all(high > median)
    # geometric symmetry when k_low == k_high
    assert abs((median[0] ** 2) - low[0] * high[0]) / median[0] ** 2 < 1e-6


def test_band_cap_prevents_absurd_upper_bound():
    """An uncapped multiplier on a very volatile name produced an 81779 upper bound on a
    215 rupee stock. The volatility-aware cap must bound it."""
    cal = CalibrationResult(k_low=6.0, k_high=6.0, status="fitted")
    median = np.array([215.0])
    q10, q90 = np.array([100.0]), np.array([500.0])   # very wide raw band
    cap = volatility_band_cap(ann_vol=0.90, horizon=252, slack=2.0)
    low, high = cal.apply(median, q10, q90, max_log_halfwidth=cap)
    assert low[0] > 0
    assert high[0] / median[0] < 15, f"upper bound still absurd: {high[0]:.0f}"
    uncapped_low, uncapped_high = cal.apply(median, q10, q90)
    assert uncapped_high[0] > high[0], "cap did not bind"
    assert volatility_band_cap(0.2, 60) < volatility_band_cap(0.2, 252)


def test_standardised_errors_are_log_ratios():
    med = np.array([100.0])
    q10, q90 = np.array([90.0]), np.array([110.0])
    e_at_median = _standardised_errors(np.array([100.0]), med, q10, q90)
    assert abs(e_at_median[0]) < 1e-12
    e_up = _standardised_errors(np.array([121.0]), med, q10, q90)
    e_dn = _standardised_errors(np.array([100.0 / 1.21]), med, q10, q90)
    assert e_up[0] > 0 > e_dn[0]
    assert abs(e_up[0] + e_dn[0]) < 1e-9, "log errors must be symmetric"


def test_calibrate_pit_reaches_target_coverage():
    """Synthetic model that is over-confident by 3x must be widened to ~80% coverage."""
    rng = np.random.default_rng(0)
    H = 30

    def predict_fn(origin, horizon):
        med = np.full(horizon, 100.0)
        # true dispersion 3x wider than the model's stated band
        true_sigma = 0.09
        actual = 100.0 * np.exp(rng.normal(0, true_sigma, horizon))
        return {"median": med, "q10": med * np.exp(-0.03), "q90": med * np.exp(0.03),
                "actual": actual}

    origins = pd.date_range("2020-01-01", periods=12, freq="30D")
    cal = calibrate_pit(predict_fn, origins, H, target_coverage=0.80)
    assert cal.status == "fitted", cal.status
    assert cal.n_calibration_points == 12 * H
    assert cal.k_low > 1.5 and cal.k_high > 1.5, (cal.k_low, cal.k_high)
    assert 70 <= cal.calibrated_coverage_pct <= 90, cal.calibrated_coverage_pct
    assert cal.raw_coverage_pct < 50, cal.raw_coverage_pct


def test_rolling_origins_are_all_pre_cutoff():
    dates = pd.bdate_range("2015-01-01", periods=2000)
    cutoff = dates[1500]
    origins = rolling_origins(dates, cutoff, horizon=60, n_origins=8)
    assert len(origins) == 8
    for o in origins:
        assert o <= cutoff
        pos = list(dates).index(o)
        assert dates[pos + 60] <= cutoff, "an origin's horizon leaked past the cutoff"


# ------------------------------------------------------------------ anonymiser
def test_name_variants_and_scrubbing():
    variants = build_name_variants(["Modison Limited", "Modison Metals"])
    assert "Modison" in variants
    text = "Modison Metals Limited reported FY24 growth; NIFTY rose in 2024 and 2026."
    out = anonymise_text(text, variants, cutoff_year=2024)
    assert "Modison" not in out
    assert "ASSET_ALPHA" in out
    assert "[BENCHMARK_INDEX]" in out
    assert "[T]" in out  # 2024 -> [T]


def test_future_year_is_flagged_not_masked():
    from anonymizer import AnonymisationReport

    rep = AnonymisationReport()
    anonymise_text("Order book strong in 2026 and FY27.", [], cutoff_year=2024, report=rep)
    assert rep.clean is False
    assert any("2026" in t for t in rep.future_tokens_found)


def test_audit_packet_catches_leak():
    packet = {"notes": "Cupid Limited makes condoms", "x": 1}
    rep = audit_packet(packet, build_name_variants(["Cupid Limited"]), 2024)
    assert rep.clean is False
    assert any("LEAK" in s for s in rep.scrubbed_terms)


def test_distinctive_tokens_excludes_generic_words():
    toks = distinctive_tokens(["Bharat Heavy Electricals", "Reliance Power"])
    assert "power" not in toks and "bharat" not in toks and "heavy" not in toks
    assert "electricals" not in toks  # in generic list
    assert "reliance" in toks
    for g in ("limited", "bank", "company", "technologies", "industrial"):
        assert g in GENERIC_NAME_TOKENS


def test_identity_probe_verdicts():
    leak = identity_probe_verdict({"company_guess": "Cupid Limited", "confidence": 0.9},
                                  ["Cupid Limited"])
    assert leak["leak"] is True and leak["matched_token"] == "cupid"
    generic = identity_probe_verdict({"company_guess": "some power company", "confidence": 0.9},
                                     ["Reliance Power"])
    assert generic["leak"] is False, "generic word must not count as identification"
    empty = identity_probe_verdict({"company_guess": "", "confidence": 0.1}, ["Cupid Limited"])
    assert empty["leak"] is False


# -------------------------------------------------------------------- pit data
def _synthetic_ohlcv(n=600):
    idx = pd.bdate_range("2020-01-01", periods=n)
    rng = np.random.default_rng(1)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, n)))
    return pd.DataFrame({"Close": close, "Volume": rng.integers(1e4, 1e6, n)}, index=idx)


def test_past_covariate_shape_and_finiteness():
    df = _synthetic_ohlcv()
    m = build_past_covariates(df)
    assert m.shape == (len(PAST_COVARIATE_NAMES), len(df)), m.shape
    assert np.all(np.isfinite(m))
    rsi_row = m[PAST_COVARIATE_NAMES.index("rsi_14")]
    assert rsi_row.min() >= 0.0 and rsi_row.max() <= 1.0
    dd = m[PAST_COVARIATE_NAMES.index("drawdown_from_252d_high")]
    assert dd.max() <= 1e-6, "drawdown must be <= 0"


def test_past_future_covariates_span_context_plus_horizon():
    df = _synthetic_ohlcv(300)
    H = 60
    fut = future_business_days(df.index[-1], H)
    m = build_past_future_covariates(df.index, fut)
    assert m.shape == (len(PAST_FUTURE_COVARIATE_NAMES), len(df) + H), m.shape
    assert np.all(np.isfinite(m))
    assert fut.min() > df.index[-1]


# ----------------------------------------------------------------- risk sizing
def test_stop_is_horizon_independent():
    """The old engine derived the stop from the terminal quantile, so a long horizon forced
    a -33% stop and 0% allocation. The stop must depend on stop_window, not horizon."""
    hist = _synthetic_ohlcv(700)["Close"].to_numpy()
    last = float(hist[-1])
    def band(H):
        med = np.full(H, last * 1.10)
        return med, med * 0.88, med * 1.30
    stops = []
    for H in (60, 252, 663):
        med, lo, hi = band(H)
        r = compute_risk(hist, last, med, lo, hi, horizon=H, stop_window=20)
        stops.append(r.stop_level)
    assert max(stops) - min(stops) < 0.02 * last, f"stop moved with horizon: {stops}"


def test_favourable_setup_gets_nonzero_allocation():
    hist = _synthetic_ohlcv(700)["Close"].to_numpy()
    last = float(hist[-1])
    H = 252
    med = np.linspace(last, last * 1.35, H)
    lo, hi = med * 0.92, med * 1.25
    r = compute_risk(hist, last, med, lo, hi, horizon=H, stop_window=20, p_win_empirical=0.578)
    assert r.recommended_alloc_pct > 0, (r.recommended_alloc_pct, r.risk_reward, r.stop_distance_pct)
    assert r.p_win_source == "walkforward_directional_hit_rate"
    assert r.directive in ("FAVOURABLE RISK/REWARD", "MILDLY FAVOURABLE")


def test_no_evidence_means_coinflip_pwin():
    hist = _synthetic_ohlcv(700)["Close"].to_numpy()
    last = float(hist[-1])
    med = np.full(120, last * 1.2)
    r = compute_risk(hist, last, med, med * 0.9, med * 1.3, horizon=120)
    assert r.p_win == 0.50 and "default_coinflip" in r.p_win_source


# --------------------------------------------------------------------- adapter
def test_adapter_refuses_to_predict_without_model():
    ad = TimesFM3Adapter(device="cpu")
    try:
        ad.predict(context=np.ones(100), horizon=10)
        raise AssertionError("adapter predicted without a loaded model")
    except TimesFMUnavailable:
        pass


def test_covariate_orientation_is_enforced():
    T = 512
    good = np.zeros((7, T), dtype=np.float32)
    bad = np.zeros((T, 7), dtype=np.float32)
    assert TimesFM3Adapter._check_cov(good, T, "past_covariates").shape == (7, T)
    for arr in (bad,):
        try:
            TimesFM3Adapter._check_cov(arr, T, "past_covariates")
            raise AssertionError("(T,k) covariates were accepted")
        except ValueError as exc:
            assert "transpose" in str(exc)
    try:
        TimesFM3Adapter._check_cov(np.full((3, T), np.nan, dtype=np.float32), T, "x")
        raise AssertionError("non-finite covariates accepted")
    except ValueError:
        pass


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            check(_name, _fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        for n, e in FAIL:
            print(f"  - {n}: {e}")
        sys.exit(1)
