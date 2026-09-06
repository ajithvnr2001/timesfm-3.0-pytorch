"""
test_agents.py  --  FIX for Weakness #4
Real assertions: poisoned payloads MUST raise SecurityError,
clean payloads MUST pass, and the CPU fallback path MUST produce output.
Place next to multi_agent_system.py, then run:  python test_agents.py
"""
import os, sys, importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
mas_path = os.path.join(current_dir, "multi_agent_system.py")
if not os.path.exists(mas_path):
    mas_path = os.path.join(current_dir, "MULTI_AGENT_SANDBOX", "multi_agent_system.py")

if os.path.dirname(mas_path) not in sys.path:
    sys.path.insert(0, os.path.dirname(mas_path))

spec = importlib.util.spec_from_file_location("mas", mas_path)
mas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mas)

def mk(payload, prohibited):
    return mas.A2AMessage(sender="T", recipient="P", payload=payload,
                          security_metadata={"prohibited_tokens": prohibited})

def test_poisoned_ticker_rejected():
    a = mas.ProcessSandboxAgent(device="cpu")
    try:
        a._verify_sandbox_security(mk({"note":"HEROMOTOCO bullish"}, ["HEROMOTOCO"]))
        raise AssertionError("leak NOT caught")
    except mas.SecurityError:
        pass

def test_poisoned_year_rejected():
    a = mas.ProcessSandboxAgent(device="cpu")
    try:
        a._verify_sandbox_security(mk({"year":"2023"}, ["2023"]))
        raise AssertionError("year leak NOT caught")
    except mas.SecurityError:
        pass

def test_clean_payload_accepted():
    a = mas.ProcessSandboxAgent(device="cpu")
    a._verify_sandbox_security(mk({"asset_pseudonym":"ASSET_ALPHA"}, ["HEROMOTOCO","2023"]))

def test_fallback_forecast_runs_without_gpu():
    # Force the no-timesfm fallback branch by monkeypatching HAS_TIMESFM
    orig = mas.HAS_TIMESFM
    mas.HAS_TIMESFM = False
    a = mas.ProcessSandboxAgent(device="cpu")
    msg = mk({"asset_pseudonym":"ASSET_ALPHA","horizon":5,"last_known_scalar":100.0,
              "numerical_context":[98.0,99.0,100.0],
              "covariates":{"bear":[0]*8,"base":[0]*8,"bull":[0]*8},
              "scenarios":{"bear":{"probability":0.25,"target_price":90.0},
                           "base":{"probability":0.50,"target_price":105.0},
                           "bull":{"probability":0.25,"target_price":120.0}}},
             ["HEROMOTOCO","2023"])
    out = a.execute_forecast(msg)
    assert "weighted_expected" in out.payload["forecast_results"]
    assert len(out.payload["forecast_results"]["pure_baseline"]) == 5
    mas.HAS_TIMESFM = orig

def test_render_report_with_all_none_macro():
    """Verifies that OutputSynthesisAgent renders cleanly without crash when macro/scorecard fields are None."""
    import pandas as pd
    out_agent = mas.OutputSynthesisAgent()
    
    # Message with all-None macro and partial scorecard
    msg = mas.A2AMessage(
        sender="Process_Sandbox_Agent",
        recipient="Output_Synthesis_Agent",
        message_type="PREDICTION_TENSOR_OUTPUT",
        payload={
            "asset_pseudonym": "ASSET_TEST",
            "horizon": 5,
            "last_scalar": 100.0,
            "forecast_results": {
                "pure_baseline": [100.0, 101.0, 102.0, 103.0, 104.0],
                "weighted_expected": [100.0, 101.5, 102.5, 103.5, 105.0],
                "bear": [98.0, 97.0, 96.0, 95.0, 94.0],
                "base": [100.0, 101.0, 102.0, 103.0, 104.0],
                "bull": [102.0, 104.0, 106.0, 108.0, 110.0],
                "neural_points": 5,
                "extrapolated_points": 0
            },
            "scenarios": {
                "bear": {"probability": 0.25, "target_price": 94.0},
                "base": {"probability": 0.50, "target_price": 104.0},
                "bull": {"probability": 0.25, "target_price": 110.0}
            },
            "fundamental_metadata": {}
        }
    )
    
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [95.0 + i for i in range(10)]}, index=dates)
    test_df = pd.DataFrame()
    
    # Monkeypatch scorecard builder to return an all-None macro scorecard
    orig_builder = mas.build_institutional_scorecard
    def mock_none_builder(**kwargs):
        return {
            "macro_environment": {
                "nifty_close": None,
                "nifty_trend": "UNAVAILABLE",
                "india_vix": None,
                "vix_regime": "UNAVAILABLE",
                "macro_multiplier": None
            },
            "sector_relative_strength": {
                "sector_index_ticker": "^NSEI",
                "beta_nifty": None,
                "corr_nifty": None,
                "beta_sector": None,
                "corr_sector": None
            },
            "institutional_risk_and_sizing": {
                "var_95_1day_pct": None,
                "var_95_horizon_pct": None,
                "cvar_95_horizon_pct": None,
                "historical_max_drawdown_pct": None,
                "gross_upside_pct": None,
                "friction_deduction_pct": None,
                "net_upside_pct": None,
                "stop_loss_invalidation_level": None,
                "downside_risk_pct": None,
                "net_risk_reward_ratio": None,
                "half_kelly_alloc_pct": None,
                "recommended_portfolio_alloc_pct": None,
                "recommended_capital_inr": None,
                "recommended_shares": None,
                "institutional_directive": "HOLD / UNAVAILABLE"
            }
        }
    mas.build_institutional_scorecard = mock_none_builder
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            res = out_agent.render(msg, "TEST.NS", train_df, test_df, output_dir=tmpdir)
            assert res is not None
            assert res["recommendation"]["action"] == "HOLD / UNAVAILABLE"
            # Verify report file exists and contains N/A without crashing
            report_file = os.path.join(tmpdir, "TEST.NS_executive_report.md")
            assert os.path.exists(report_file)
            with open(report_file) as f:
                content = f.read()
                assert "Benchmark Close: N/A" in content
                assert "Level: N/A" in content
    finally:
        mas.build_institutional_scorecard = orig_builder

def test_stochastic_bridge_reproducibility():
    try:
        from covfree_forecaster import forecast_covfree
    except ImportError:
        from v2.MULTI_AGENT_SANDBOX.covfree_forecaster import forecast_covfree
    import numpy as np
    p1, q10_1, q90_1 = forecast_covfree(100.0, 250.0, 0.30, 100)
    p2, q10_2, q90_2 = forecast_covfree(100.0, 250.0, 0.30, 100)
    assert np.allclose(p1, p2), "Stochastic bridge must be deterministic when seed=None"
    assert np.allclose(q10_1, q10_2), "Q10 must match"
    assert np.allclose(q90_1, q90_2), "Q90 must match"

def test_stochastic_bridge_unbiased_median():
    try:
        from covfree_forecaster import forecast_covfree
    except ImportError:
        from v2.MULTI_AGENT_SANDBOX.covfree_forecaster import forecast_covfree
    target = 250.0
    for vol in [0.10, 0.50, 0.90]:
        point, q10, q90 = forecast_covfree(
            last=100.0, target=target, annual_vol=vol, horizon=2000,
            half_life_days=60.0, n_sims=5000, seed=42
        )
        terminal_median = point[-1]
        bias_pct = abs(terminal_median - target) / target * 100.0
        assert bias_pct < 3.0, f"Vol {vol} terminal median {terminal_median:.2f} biased by {bias_pct:.2f}% (target {target})"

def test_common_random_numbers_and_monotonicity():
    try:
        from covfree_forecaster import forecast_covfree
    except ImportError:
        from v2.MULTI_AGENT_SANDBOX.covfree_forecaster import forecast_covfree
    import numpy as np
    seed = 42
    h = 60
    half_life = float(np.clip(h / 2.0, 21.0, 252.0))
    bear, bear_q10, bear_q90 = forecast_covfree(100.0, 80.0, 0.35, h, half_life_days=half_life, seed=seed)
    base, base_q10, base_q90 = forecast_covfree(100.0, 110.0, 0.35, h, half_life_days=half_life, seed=seed)
    bull, bull_q10, bull_q90 = forecast_covfree(100.0, 150.0, 0.35, h, half_life_days=half_life, seed=seed)

    assert bear[-1] <= base[-1] <= bull[-1], f"Terminal ordering failed: {bear[-1]} <= {base[-1]} <= {bull[-1]}"
    assert np.all(bear <= base) and np.all(base <= bull), "Monotonicity violated across scenario paths with CRN"

def test_honest_neural_points_and_horizon_aware_drift():
    a = mas.ProcessSandboxAgent(device="cpu")
    msg = mas.A2AMessage(
        sender="T", recipient="P",
        payload={
            "asset_pseudonym": "ASSET_TEST",
            "horizon": 663,
            "last_known_scalar": 100.0,
            "numerical_context": [95.0 + 0.1 * i for i in range(100)],
            "scenarios": {
                "bear": {"probability": 0.25, "target_price": 80.0},
                "base": {"probability": 0.50, "target_price": 110.0},
                "bull": {"probability": 0.25, "target_price": 150.0},
            }
        },
        security_metadata={"prohibited_tokens": []}
    )
    res = a.execute_forecast(msg)
    forecasts = res.payload["forecast_results"]
    assert forecasts["neural_points"] == 0, f"Expected 0 neural points in fallback, got {forecasts['neural_points']}"
    assert forecasts["extrapolated_points"] == 0
    base_term = forecasts["pure_baseline"][-1]
    assert base_term <= 250.0, f"Exploded baseline detected: terminal {base_term:.2f} for last_val 100.0"

def test_prediction_interval_coverage_metric():
    out_agent = mas.OutputSynthesisAgent()
    h = 10
    msg = mas.A2AMessage(
        sender="Process_Sandbox_Agent", recipient="Output_Synthesis_Agent",
        message_type="PREDICTION_TENSOR_OUTPUT",
        payload={
            "asset_pseudonym": "ASSET_TEST",
            "horizon": h,
            "last_scalar": 100.0,
            "forecast_results": {
                "pure_baseline": [100.0] * h,
                "weighted_expected": [100.0] * h,
                "bear": [90.0] * h,
                "base": [100.0] * h,
                "bull": [110.0] * h,
                "bear_q10": [80.0] * h,
                "bull_q90": [120.0] * h,
                "neural_points": 0,
                "extrapolated_points": 0
            },
            "scenarios": {
                "bear": {"probability": 0.25, "target_price": 90.0},
                "base": {"probability": 0.50, "target_price": 100.0},
                "bull": {"probability": 0.25, "target_price": 110.0}
            },
            "fundamental_metadata": {}
        }
    )
    import tempfile, pandas as pd
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [100.0]*10}, index=dates)
    test_df = pd.DataFrame({"Close": [115.0]*h}, index=pd.date_range("2024-01-15", periods=h, freq="B"))
    with tempfile.TemporaryDirectory() as tmpdir:
        res = out_agent.render(msg, "TEST.NS", train_df, test_df, output_dir=tmpdir)
        metrics = res["metrics"]
        assert metrics["interval_80_coverage_pct"] == 100.0, f"Expected 100% interval coverage, got {metrics['interval_80_coverage_pct']}"


def test_mixture_prediction_interval():
    try:
        from covfree_forecaster import mixture_prediction_interval
    except ImportError:
        from v2.MULTI_AGENT_SANDBOX.covfree_forecaster import mixture_prediction_interval
    import numpy as np
    
    # 3 scenarios with 1000 simulated paths each across horizon=10
    np.random.seed(42)
    paths_bear = np.random.normal(80, 5, (1000, 10))
    paths_base = np.random.normal(100, 5, (1000, 10))
    paths_bull = np.random.normal(120, 5, (1000, 10))
    
    paths_dict = {"bear": paths_bear, "base": paths_base, "bull": paths_bull}
    probs = {"bear": 0.25, "base": 0.50, "bull": 0.25}
    
    mix_q10, mix_q90 = mixture_prediction_interval(paths_dict, probs, 0.10, 0.90)
    assert len(mix_q10) == 10 and len(mix_q90) == 10
    assert np.all(mix_q10 < mix_q90)
    
    # Check that mixture width is strictly narrower than the union min(q10_bear) to max(q90_bull)
    union_low = np.percentile(paths_bear, 10, axis=0)
    union_high = np.percentile(paths_bull, 90, axis=0)
    assert np.all(mix_q10 >= union_low)
    assert np.all(mix_q90 <= union_high)
    assert np.mean(mix_q90 - mix_q10) < np.mean(union_high - union_low)

def test_non_asserting_terminal_ordering_and_monotonic_repair():
    """Verify that inverted scenario terminal ordering triggers monotonic repair without crashing."""
    out_agent = mas.OutputSynthesisAgent()
    h = 5
    # Deliberately invert terminal ordering: Bear (120) > Base (100) > Bull (80)
    msg = mas.A2AMessage(
        sender="Process_Sandbox_Agent", recipient="Output_Synthesis_Agent",
        message_type="PREDICTION_TENSOR_OUTPUT",
        payload={
            "asset_pseudonym": "ASSET_INVERTED",
            "horizon": h,
            "last_scalar": 100.0,
            "forecast_results": {
                "pure_baseline": [100.0] * h,
                "weighted_expected": [100.0] * h,
                "bear": [120.0] * h,
                "base": [100.0] * h,
                "bull": [80.0] * h,
                "mixture_q10": [75.0] * h,
                "mixture_q90": [125.0] * h,
                "neural_points": 0,
                "extrapolated_points": 0
            },
            "scenarios": {
                "bear": {"probability": 0.25, "target_price": 120.0},
                "base": {"probability": 0.50, "target_price": 100.0},
                "bull": {"probability": 0.25, "target_price": 80.0}
            },
            "fundamental_metadata": {}
        }
    )
    import tempfile, pandas as pd
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [100.0]*10}, index=dates)
    test_df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Must execute cleanly and repair terminal order
        res = out_agent.render(msg, "INVERTED.NS", train_df, test_df, output_dir=tmpdir)
        assert res is not None
        assert res["metrics"]["bear_terminal"] <= res["metrics"]["bull_terminal"]
        assert "interval_lower" in res["predictions"]
        assert "interval_upper" in res["predictions"]
        assert "interval_lower" in res["calendar"]

def test_quantiles_unavailable_handling():
    """Verify that tensor layout exceptions set quantiles_unavailable=True and preserve pure baseline."""
    a = mas.ProcessSandboxAgent(device="cpu")
    # Mock a forecaster whose predict_batch returns quantiles with unexpected 1D shape
    class MalformedQuantileForecaster:
        def predict_batch(self, series, horizon, return_quantiles=True, use_symmetric_averaging=False):
            class Out:
                forecast = [105.0] * horizon
                quantiles = [1.0, 2.0]  # Shape (2,), fails assert q.ndim == 2 and q.shape[1] >= 9
            return [Out()]
    
    a.forecaster = MalformedQuantileForecaster()
    msg = mk({"asset_pseudonym": "ASSET_QFAIL", "horizon": 5, "last_known_scalar": 100.0,
              "numerical_context": [98.0, 99.0, 100.0],
              "scenarios": {"bear": {"probability": 0.25, "target_price": 90.0},
                           "base": {"probability": 0.50, "target_price": 100.0},
                           "bull": {"probability": 0.25, "target_price": 110.0}}},
             [])
    res = a.execute_forecast(msg)
    forecasts = res.payload["forecast_results"]
    assert forecasts.get("quantiles_unavailable") is True
    assert "pure_baseline" in forecasts
    assert len(forecasts["pure_baseline"]) == 5


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"PASS  {name}")
    print("ALL TESTS PASSED")

