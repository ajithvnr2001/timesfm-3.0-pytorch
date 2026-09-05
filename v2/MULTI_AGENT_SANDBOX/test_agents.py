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

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"PASS  {name}")
    print("ALL TESTS PASSED")
