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
    a._verify_sandbox_security(mk({
        "asset_pseudonym": "ASSET_ALPHA",
        "scenarios": {
            "bear": {"probability": 0.25, "target_price": 90.0},
            "base": {"probability": 0.50, "target_price": 105.0},
            "bull": {"probability": 0.25, "target_price": 120.0}
        }
    }, ["HEROMOTOCO","2023"]))

def test_missing_scenarios_rejected():
    a = mas.ProcessSandboxAgent(device="cpu")
    try:
        a._verify_sandbox_security(mk({"asset_pseudonym": "ASSET_NO_SCENARIOS"}, []))
        raise AssertionError("Payload without scenarios MUST raise SecurityError")
    except mas.SecurityError:
        pass

def test_fallback_forecast_runs_without_gpu():
    # Force the no-timesfm fallback branch by monkeypatching HAS_TIMESFM
    orig = mas.HAS_TIMESFM
    mas.HAS_TIMESFM = False
    a = mas.ProcessSandboxAgent(device="cpu")
    msg = mk({"asset_pseudonym":"ASSET_ALPHA","horizon":5,"last_known_scalar":100.0,
              "numerical_context":[98.0,99.0,100.0],
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
    import tempfile, pandas as pd, numpy as np
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [100.0]*10}, index=dates)
    test_df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Must execute cleanly and repair terminal order pointwise
        res = out_agent.render(msg, "INVERTED.NS", train_df, test_df, output_dir=tmpdir)
        assert res is not None
        assert res["metrics"]["bear_terminal"] <= res["metrics"]["bull_terminal"]
        # Pointwise repair across full scenario paths (Item 3)
        sc_res = res["predictions"]["scenarios"]
        assert np.all(np.array(sc_res["bear"]) <= np.array(sc_res["base"]))
        assert np.all(np.array(sc_res["base"]) <= np.array(sc_res["bull"]))
        # Intervals in predictions only, metrics has scalars only (Item 5)
        assert "interval_lower" in res["predictions"]
        assert "interval_upper" in res["predictions"]
        assert "interval_lower" not in res["metrics"]
        assert "interval_upper" not in res["metrics"]
        assert "interval_lower" not in res["calendar"]
        assert "interval_upper" not in res["calendar"]

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

def test_covariates_payload_rejected():
    """Verify that sending undeclared 'covariates' fails closed with SecurityError (Item 6)."""
    a = mas.ProcessSandboxAgent(device="cpu")
    msg = mk({
        "asset_pseudonym": "ASSET_COV", "horizon": 5, "last_known_scalar": 100.0,
        "numerical_context": [98.0, 99.0, 100.0],
        "covariates": {"bear": [0]*8},
        "scenarios": {"bear": {"probability": 0.25, "target_price": 90.0},
                     "base": {"probability": 0.50, "target_price": 100.0},
                     "bull": {"probability": 0.25, "target_price": 110.0}}
    }, [])
    try:
        a._verify_sandbox_security(msg)
        raise AssertionError("Sending 'covariates' key MUST raise SecurityError")
    except mas.SecurityError:
        pass

def test_antithetic_target_dispersion():
    """Verify that n_sims=5000 with antithetic variates reduces seed-to-seed noise to near-zero (Item 1)."""
    try:
        from covfree_forecaster import forecast_covfree
    except ImportError:
        from v2.MULTI_AGENT_SANDBOX.covfree_forecaster import forecast_covfree
    import numpy as np
    terminals = [forecast_covfree(100.0, 105.0, 0.35, 252, n_sims=5000, seed=s)[0][-1] for s in range(5)]
    std_dispersion = float(np.std(terminals))
    assert std_dispersion < 0.05, f"Monte Carlo dispersion across seeds should be < 0.05 with antithetic shocks, got {std_dispersion:.4f}"

def test_fused_scenario_interval_containment_and_centering():
    """Verify that fusing baseline paths B_k(t) with scenarios S_{s, k}(t) centers the interval on weighted_expected (Problem A)."""
    import numpy as np
    a = mas.ProcessSandboxAgent(device="cpu")
    h = 60
    msg = mk({
        "asset_pseudonym": "ASSET_FUSED",
        "horizon": h,
        "last_known_scalar": 100.0,
        "numerical_context": [100.0 + 0.1 * i for i in range(120)],
        "scenarios": {
            "bear": {"probability": 0.25, "target_price": 85.0},
            "base": {"probability": 0.50, "target_price": 105.0},
            "bull": {"probability": 0.25, "target_price": 130.0},
        }
    }, [])
    res = a.execute_forecast(msg)
    forecasts = res.payload["forecast_results"]
    q10 = np.array(forecasts["mixture_q10"])
    q90 = np.array(forecasts["mixture_q90"])
    w_exp = np.array(forecasts["weighted_expected"])

    # Pointwise containment assertion
    assert np.all(q10 <= w_exp), f"mixture_q10 must be <= weighted_expected pointwise, min diff: {np.min(w_exp - q10)}"
    assert np.all(w_exp <= q90), f"weighted_expected must be <= mixture_q90 pointwise, min diff: {np.min(q90 - w_exp)}"

    # Relative position within the band: (weighted - q10) / (q90 - q10) must be well-centered, not stuck at 96.7%
    rel_pos = (w_exp - q10) / (q90 - q10)
    assert 0.25 <= np.mean(rel_pos) <= 0.75, f"Expected centered rel_pos between 0.25 and 0.75, got mean {np.mean(rel_pos):.3f}"
    assert np.all(rel_pos >= 0.10) and np.all(rel_pos <= 0.90), f"rel_pos breached bounds: min {np.min(rel_pos):.3f}, max {np.max(rel_pos):.3f}"

def test_diffusion_floor_log_width():
    """Verify that the diffusion floor prevents interval saturation over long horizons (Problem B)."""
    import numpy as np
    a = mas.ProcessSandboxAgent(device="cpu")
    h = 252
    msg = mk({
        "asset_pseudonym": "ASSET_DIFF",
        "horizon": h,
        "last_known_scalar": 100.0,
        "numerical_context": [100.0 * (1.0 + 0.01 * np.sin(i / 10.0)) for i in range(120)],
        "scenarios": {
            "bear": {"probability": 0.25, "target_price": 90.0},
            "base": {"probability": 0.50, "target_price": 100.0},
            "bull": {"probability": 0.25, "target_price": 110.0},
        }
    }, [])
    res = a.execute_forecast(msg)
    forecasts = res.payload["forecast_results"]
    q10 = np.array(forecasts["mixture_q10"])
    q90 = np.array(forecasts["mixture_q90"])
    w_exp = np.array(forecasts["weighted_expected"])
    ann_vol = forecasts.get("annualized_vol", 0.25)

    # Diffusion floor: log(q90 / w_exp) >= 1.28155 * ann_vol * sqrt((t+1)/252)
    t_grid = np.arange(1, h + 1, dtype=float) / 252.0
    expected_log_half_width = 1.28155 * ann_vol * np.sqrt(t_grid)
    actual_log_upper = np.log(q90 / w_exp)
    actual_log_lower = np.log(w_exp / q10)

    # Allow tiny float rounding tolerance of 1e-6
    assert np.all(actual_log_upper >= expected_log_half_width - 1e-6), "Upper band violated diffusion floor"
    assert np.all(actual_log_lower >= expected_log_half_width - 1e-6), "Lower band violated diffusion floor"

def test_drift_clip_binding_and_scaling():
    """Verify that fallback drift clipping sets drift_clip_binding=True and scales w_tfm down (Problem C)."""
    a = mas.ProcessSandboxAgent(device="cpu")
    # Highly steep historical context that exceeds the volatility-aware drift boundary over 663 days
    ctx_steep = [100.0 * (1.005 ** i) for i in range(100)]
    msg = mk({
        "asset_pseudonym": "ASSET_CLIP",
        "horizon": 663,
        "last_known_scalar": ctx_steep[-1],
        "numerical_context": ctx_steep,
        "scenarios": {
            "bear": {"probability": 0.25, "target_price": ctx_steep[-1] * 0.90},
            "base": {"probability": 0.50, "target_price": ctx_steep[-1] * 1.05},
            "bull": {"probability": 0.25, "target_price": ctx_steep[-1] * 1.20},
        }
    }, [])
    res = a.execute_forecast(msg)
    forecasts = res.payload["forecast_results"]
    assert forecasts.get("drift_clip_binding") is True, "Expected drift_clip_binding=True for steep multi-year trend"

    # Verify OutputSynthesisAgent captures drift_clip_binding in JSON and metrics
    import tempfile, pandas as pd
    out_agent = mas.OutputSynthesisAgent()
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [ctx_steep[-1]] * 10}, index=dates)
    with tempfile.TemporaryDirectory() as tmpdir:
        json_out = out_agent.render(res, "CLIP.NS", train_df, pd.DataFrame(), output_dir=tmpdir)
        assert json_out.get("drift_clip_binding") is True
        assert json_out["metrics"].get("drift_clip_binding") is True

        # Check that report includes the warning note
        report_file = json_out["report_saved"]
        with open(report_file, "r") as f:
            report_text = f.read()
        assert "Baseline Drift Clip Active" in report_text

def test_empirical_momentum_extension_note_in_report():
    """Verify that when weighted_expected > bull_terminal, report explains momentum blending (Problem D)."""
    import tempfile, pandas as pd
    out_agent = mas.OutputSynthesisAgent()
    h = 10
    msg = mas.A2AMessage(
        sender="Process_Sandbox_Agent", recipient="Output_Synthesis_Agent",
        message_type="PREDICTION_TENSOR_OUTPUT",
        payload={
            "asset_pseudonym": "ASSET_MOM",
            "horizon": h,
            "last_scalar": 100.0,
            "forecast_results": {
                "pure_baseline": [150.0] * h,
                "weighted_expected": [135.0] * h,  # Above bull terminal of 120.0
                "bear": [80.0] * h,
                "base": [100.0] * h,
                "bull": [120.0] * h,
                "mixture_q10": [75.0] * h,
                "mixture_q90": [140.0] * h,
                "neural_points": 0,
                "extrapolated_points": 0
            },
            "scenarios": {
                "bear": {"probability": 0.25, "target_price": 80.0},
                "base": {"probability": 0.50, "target_price": 100.0},
                "bull": {"probability": 0.25, "target_price": 120.0}
            },
            "fundamental_metadata": {}
        }
    )
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    train_df = pd.DataFrame({"Close": [100.0] * 10}, index=dates)
    with tempfile.TemporaryDirectory() as tmpdir:
        json_out = out_agent.render(msg, "MOM.NS", train_df, pd.DataFrame(), output_dir=tmpdir)
        with open(json_out["report_saved"], "r") as f:
            report_text = f.read()
        assert "Empirical Momentum Extension" in report_text


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"PASS  {name}")
    print("ALL TESTS PASSED")

