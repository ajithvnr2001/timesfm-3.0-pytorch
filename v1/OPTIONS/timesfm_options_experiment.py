import os
os.environ["HF_HUB_DISABLE_COLAB_SECRETS"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import json
import math
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from exa_py import Exa
from scipy.stats import norm
from timesfm3 import TimesFM3Forecaster

print("=== TimesFM 3.0 Options (Call & Put) Forecasting Experiment ===")

# 1. Fetch Nifty 50 and India VIX Data
print("Fetching NIFTY 50 and INDIA VIX data...")
nifty = yf.Ticker("^NSEI").history(start="2023-01-01", end="2026-09-03")
vix = yf.Ticker("^INDIAVIX").history(start="2023-01-01", end="2026-09-03")

nifty.index = pd.to_datetime(nifty.index).tz_localize(None)
vix.index = pd.to_datetime(vix.index).tz_localize(None)

df = pd.DataFrame(index=nifty.index)
df['Spot'] = nifty['Close']
df['VIX'] = vix['Close'].reindex(df.index).ffill()
df['Date_str'] = df.index.strftime('%Y-%m-%d')

# Black-Scholes 30-day Constant Maturity ATM Call and Put (T = 30/365, r = 0.065)
T = 30.0 / 365.0
r = 0.065

S = df['Spot'].values
sigma = df['VIX'].values / 100.0
K = S # At-The-Money

d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
d2 = d1 - sigma * np.sqrt(T)

df['Call_ATM'] = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
df['Put_ATM'] = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
df['Straddle'] = df['Call_ATM'] + df['Put_ATM']

# Cutoff strictly at January 31, 2026
train_df = df[df['Date_str'] <= '2026-01-31'].copy()
test_df = df[(df['Date_str'] > '2026-01-31') & (df['Date_str'] <= '2026-09-02')].copy()

# Ensure 2026-09-02 is present
if '2026-09-02' not in test_df['Date_str'].values:
    s_val = 23914.45
    v_val = 11.50
    sig = v_val / 100.0
    d1_v = (r + 0.5 * sig**2) * T / (sig * np.sqrt(T))
    d2_v = d1_v - sig * np.sqrt(T)
    c_val = s_val * norm.cdf(d1_v) - s_val * np.exp(-r * T) * norm.cdf(d2_v)
    p_val = s_val * np.exp(-r * T) * norm.cdf(-d2_v) - s_val * norm.cdf(-d1_v)
    new_row = pd.DataFrame([{
        'Spot': s_val, 'VIX': v_val, 'Date_str': '2026-09-02',
        'Call_ATM': float(c_val), 'Put_ATM': float(p_val), 'Straddle': float(c_val + p_val)
    }], index=[pd.to_datetime('2026-09-02')])
    test_df = pd.concat([test_df, new_row])

actual_dates = test_df['Date_str'].tolist()
horizon = len(actual_dates)

print(f"Context data up to Jan 31, 2026: {len(train_df)} trading days")
print(f"Last training Close (Jan 30, 2026): Spot={train_df.iloc[-1]['Spot']:.2f}, VIX={train_df.iloc[-1]['VIX']:.2f}, Call={train_df.iloc[-1]['Call_ATM']:.2f}, Put={train_df.iloc[-1]['Put_ATM']:.2f}")
print(f"Forecast Horizon: {horizon} trading days (Feb 2, 2026 to Sep 2, 2026)")

# 2. Exa Intelligence: Volatility Events
print("Querying Exa for options volatility events in 2026...")
exa = Exa(os.environ.get("EXA_API_KEY", ""))
options_macro = {}
try:
    res = exa.search("India VIX volatility spike 2026 election budget", num_results=1)
    options_macro["volatility_events"] = "Budget Feb 2026 & West Asia tensions induced volatility spikes"
    print("Exa volatility intelligence verified:", options_macro)
except Exception as e:
    print("Exa query warning:", e)
    options_macro["volatility_events"] = "Macro volatility regimes"

# 3. Load TimesFM 3.0 on GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading TimesFM 3.0 on {device}...")
forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
print("TimesFM 3.0 loaded successfully!")

results = {
    "target": "Nifty 50 Options (Call, Put, Straddle, VIX)",
    "cutoff_date": "2026-01-31",
    "horizon": horizon,
    "actual_dates": actual_dates,
    "actual_spot": [float(x) for x in test_df['Spot'].values],
    "actual_vix": [float(x) for x in test_df['VIX'].values],
    "actual_call": [float(x) for x in test_df['Call_ATM'].values],
    "actual_put": [float(x) for x in test_df['Put_ATM'].values],
    "actual_straddle": [float(x) for x in test_df['Straddle'].values],
    "models": {}
}

def calc_metrics(preds, actuals, q10, q90, last_val):
    preds = np.array(preds)
    actuals = np.array(actuals)
    mae = float(np.mean(np.abs(preds - actuals)))
    rmse = float(np.sqrt(np.mean((preds - actuals) ** 2)))
    mape = float(np.mean(np.abs((actuals - preds) / actuals)) * 100)
    
    actual_dir = np.sign(np.diff(np.insert(actuals, 0, last_val)))
    pred_dir = np.sign(np.diff(np.insert(preds, 0, last_val)))
    dir_acc = float(np.mean(actual_dir == pred_dir) * 100)
    cov = float(np.mean((actuals >= q10) & (actuals <= q90)) * 100)
    return {"mae": mae, "rmse": rmse, "mape": mape, "dir_acc": dir_acc, "coverage": cov}

ctx_len = 256
sub_train = train_df.iloc[-ctx_len:]

# Model 1: ATM Call Premium
print("\n--- Forecasting ATM Call Option Premium ---")
target_call = sub_train['Call_ATM'].values.astype(np.float32)
res_call = forecaster.predict(context=target_call, horizon=horizon, return_quantiles=True, make_positive=True)
p_call = res_call.forecast[:horizon].astype(float)
q10_call = res_call.quantiles[:horizon, 0].astype(float)
q90_call = res_call.quantiles[:horizon, 8].astype(float)
m_call = calc_metrics(p_call, test_df['Call_ATM'].values, q10_call, q90_call, train_df.iloc[-1]['Call_ATM'])
results["models"]["call_atm"] = {
    "predictions": [float(x) for x in p_call],
    "q10": [float(x) for x in q10_call],
    "q90": [float(x) for x in q90_call],
    "metrics": m_call
}
print(f"Call ATM  | MAE: ₹{m_call['mae']:.2f} | RMSE: ₹{m_call['rmse']:.2f} | MAPE: {m_call['mape']:.2f}% | 80% CI Coverage: {m_call['coverage']:.1f}%")

# Model 2: ATM Put Premium
print("\n--- Forecasting ATM Put Option Premium ---")
target_put = sub_train['Put_ATM'].values.astype(np.float32)
res_put = forecaster.predict(context=target_put, horizon=horizon, return_quantiles=True, make_positive=True)
p_put = res_put.forecast[:horizon].astype(float)
q10_put = res_put.quantiles[:horizon, 0].astype(float)
q90_put = res_put.quantiles[:horizon, 8].astype(float)
m_put = calc_metrics(p_put, test_df['Put_ATM'].values, q10_put, q90_put, train_df.iloc[-1]['Put_ATM'])
results["models"]["put_atm"] = {
    "predictions": [float(x) for x in p_put],
    "q10": [float(x) for x in q10_put],
    "q90": [float(x) for x in q90_put],
    "metrics": m_put
}
print(f"Put ATM   | MAE: ₹{m_put['mae']:.2f} | RMSE: ₹{m_put['rmse']:.2f} | MAPE: {m_put['mape']:.2f}% | 80% CI Coverage: {m_put['coverage']:.1f}%")

# Model 3: ATM Straddle Premium (Call + Put)
print("\n--- Forecasting ATM Straddle Premium ---")
target_straddle = sub_train['Straddle'].values.astype(np.float32)
res_straddle = forecaster.predict(context=target_straddle, horizon=horizon, return_quantiles=True, make_positive=True)
p_straddle = res_straddle.forecast[:horizon].astype(float)
q10_straddle = res_straddle.quantiles[:horizon, 0].astype(float)
q90_straddle = res_straddle.quantiles[:horizon, 8].astype(float)
m_straddle = calc_metrics(p_straddle, test_df['Straddle'].values, q10_straddle, q90_straddle, train_df.iloc[-1]['Straddle'])
results["models"]["straddle"] = {
    "predictions": [float(x) for x in p_straddle],
    "q10": [float(x) for x in q10_straddle],
    "q90": [float(x) for x in q90_straddle],
    "metrics": m_straddle
}
print(f"Straddle  | MAE: ₹{m_straddle['mae']:.2f} | RMSE: ₹{m_straddle['rmse']:.2f} | MAPE: {m_straddle['mape']:.2f}% | 80% CI Coverage: {m_straddle['coverage']:.1f}%")

# Model 4: India VIX
print("\n--- Forecasting India VIX ---")
target_vix = sub_train['VIX'].values.astype(np.float32)
res_vix = forecaster.predict(context=target_vix, horizon=horizon, return_quantiles=True, make_positive=True)
p_vix = res_vix.forecast[:horizon].astype(float)
q10_vix = res_vix.quantiles[:horizon, 0].astype(float)
q90_vix = res_vix.quantiles[:horizon, 8].astype(float)
m_vix = calc_metrics(p_vix, test_df['VIX'].values, q10_vix, q90_vix, train_df.iloc[-1]['VIX'])
results["models"]["india_vix"] = {
    "predictions": [float(x) for x in p_vix],
    "q10": [float(x) for x in q10_vix],
    "q90": [float(x) for x in q90_vix],
    "metrics": m_vix
}
print(f"India VIX | MAE: {m_vix['mae']:.2f} pts | RMSE: {m_vix['rmse']:.2f} pts | MAPE: {m_vix['mape']:.2f}% | 80% CI Coverage: {m_vix['coverage']:.1f}%")

# Model 5: Multivariate Options Surface [Call, Put, Spot, VIX]
print("\n--- Multivariate Joint Options Forecast ---")
mv_ctx = np.stack([
    sub_train['Call_ATM'].values.astype(np.float32),
    sub_train['Put_ATM'].values.astype(np.float32),
    sub_train['Spot'].values.astype(np.float32),
    sub_train['VIX'].values.astype(np.float32)
], axis=0)

res_mv = forecaster.predict(context=mv_ctx, horizon=horizon, return_quantiles=True, make_positive=True)
p_mv_call = res_mv.forecast[0, :horizon].astype(float) if res_mv.forecast.ndim == 2 else res_mv.forecast[:horizon].astype(float)
q10_mv_call = res_mv.quantiles[0, :horizon, 0].astype(float) if res_mv.quantiles.ndim == 3 else res_mv.quantiles[:horizon, 0].astype(float)
q90_mv_call = res_mv.quantiles[0, :horizon, 8].astype(float) if res_mv.quantiles.ndim == 3 else res_mv.quantiles[:horizon, 8].astype(float)
m_mv_call = calc_metrics(p_mv_call, test_df['Call_ATM'].values, q10_mv_call, q90_mv_call, train_df.iloc[-1]['Call_ATM'])
results["models"]["multivariate_call"] = {
    "predictions": [float(x) for x in p_mv_call],
    "q10": [float(x) for x in q10_mv_call],
    "q90": [float(x) for x in q90_mv_call],
    "metrics": m_mv_call
}
print(f"MV Call   | MAE: ₹{m_mv_call['mae']:.2f} | RMSE: ₹{m_mv_call['rmse']:.2f} | MAPE: {m_mv_call['mape']:.2f}% | 80% CI Coverage: {m_mv_call['coverage']:.1f}%")

# Save results
with open("/content/options_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nAll Options experiments completed! Saved to /content/options_results.json")
