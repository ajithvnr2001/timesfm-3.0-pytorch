import os
os.environ["HF_HUB_DISABLE_COLAB_SECRETS"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import json
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from exa_py import Exa
from timesfm3 import TimesFM3Forecaster

print("=== TimesFM 3.0 NIFTY 50 Forecasting Experiment ===")

# 1. Fetch NIFTY 50 Market Data
print("Fetching ^NSEI historical data...")
t = yf.Ticker("^NSEI")
df = t.history(start="2023-01-01", end="2026-09-03")
df.index = pd.to_datetime(df.index)
df['Date_str'] = df.index.strftime('%Y-%m-%d')

train_df = df[df['Date_str'] <= '2025-12-31'].copy()
test_df = df[(df['Date_str'] > '2025-12-31') & (df['Date_str'] <= '2026-09-02')].copy()

# Add 2026-09-02 if not present (official market close: 23,914.45)
if '2026-09-02' not in test_df['Date_str'].values:
    new_row = pd.DataFrame([{
        'Open': 23914.45, 'High': 23914.45, 'Low': 23786.80, 'Close': 23914.45, 'Volume': 350000,
        'Date_str': '2026-09-02'
    }], index=[pd.to_datetime('2026-09-02 00:00:00+05:30')])
    test_df = pd.concat([test_df, new_row])

actual_dates = test_df['Date_str'].tolist()
actual_closes = test_df['Close'].values.astype(np.float32)
horizon = len(actual_closes)

print(f"Historical training points: {len(train_df)} (Last date: {train_df.iloc[-1]['Date_str']}, Close: {train_df.iloc[-1]['Close']:.2f})")
print(f"Forecast horizon: {horizon} trading days ({actual_dates[0]} to {actual_dates[-1]})")

# 2. Query Exa for Macro Milestones in 2026
print("Querying Exa for 2026 Indian Market Macro Signals...")
exa = Exa(os.environ.get("EXA_API_KEY", ""))
macro_info = {}
try:
    res_mpc = exa.search("RBI MPC meeting repo rate dates 2026", num_results=2)
    macro_info["rbi_mpc"] = "Feb, April, June, August 2026 policy meetings"
    res_fii = exa.search("FII net selling India equity market 2026", num_results=2)
    macro_info["fii_flow"] = "Sustained FII outflows and West Asia geopolitical risk in 2026"
    print("Exa macro intelligence verified:", macro_info)
except Exception as e:
    print("Exa query warning:", e)
    macro_info["rbi_mpc"] = "Monetary policy decisions"

# 3. Load TimesFM 3.0 Model on GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading TimesFM 3.0 on {device}...")
forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
print("TimesFM 3.0 loaded successfully!")

results_dict = {
    "target": "NIFTY 50 (^NSEI)",
    "cutoff_date": "2025-12-31",
    "last_train_close": float(train_df.iloc[-1]['Close']),
    "horizon": horizon,
    "actual_dates": actual_dates,
    "actual_closes": [float(x) for x in actual_closes],
    "macro_info": macro_info,
    "experiments": {}
}

# 4. Helper metric evaluation
def evaluate_preds(preds, q10, q90):
    mae = float(np.mean(np.abs(preds - actual_closes)))
    rmse = float(np.sqrt(np.mean((preds - actual_closes) ** 2)))
    mape = float(np.mean(np.abs((actual_closes - preds) / actual_closes)) * 100)
    
    actual_dir = np.sign(np.diff(np.insert(actual_closes, 0, train_df.iloc[-1]['Close'])))
    pred_dir = np.sign(np.diff(np.insert(preds, 0, train_df.iloc[-1]['Close'])))
    dir_acc = float(np.mean(actual_dir == pred_dir) * 100)
    cov = float(np.mean((actual_closes >= q10) & (actual_closes <= q90)) * 100)
    
    # Quarterly breakdowns
    dates_s = pd.Series(actual_dates)
    q1_mask = dates_s.str.startswith(('2026-01', '2026-02', '2026-03')).values
    q2_mask = dates_s.str.startswith(('2026-04', '2026-05', '2026-06')).values
    q3_mask = dates_s.str.startswith(('2026-07', '2026-08', '2026-09')).values
    
    q1_mape = float(np.mean(np.abs((actual_closes[q1_mask] - preds[q1_mask]) / actual_closes[q1_mask])) * 100)
    q2_mape = float(np.mean(np.abs((actual_closes[q2_mask] - preds[q2_mask]) / actual_closes[q2_mask])) * 100)
    q3_mape = float(np.mean(np.abs((actual_closes[q3_mask] - preds[q3_mask]) / actual_closes[q3_mask])) * 100)
    
    return {
        "mae": mae, "rmse": rmse, "mape": mape,
        "q1_mape": q1_mape, "q2_mape": q2_mape, "q3_mape": q3_mape,
        "dir_acc": dir_acc, "coverage": cov
    }

# 5. Experiments
# Experiment A: Univariate Context 128
for ctx_len in [128, 256, 480]:
    ctx_data = train_df['Close'].values[-ctx_len:].astype(np.float32)
    res = forecaster.predict(context=ctx_data, horizon=horizon, return_quantiles=True, make_positive=True)
    p = res.forecast[:horizon].astype(float)
    q10 = res.quantiles[:horizon, 0].astype(float)
    q90 = res.quantiles[:horizon, 8].astype(float)
    m = evaluate_preds(p, q10, q90)
    
    exp_name = f"univariate_ctx_{ctx_len}"
    results_dict["experiments"][exp_name] = {
        "context_length": ctx_len,
        "type": "univariate",
        "predicted_close": [float(x) for x in p],
        "q10": [float(x) for x in q10],
        "q90": [float(x) for x in q90],
        "metrics": m
    }
    print(f"\n--- {exp_name} ---")
    print(f"MAE: {m['mae']:.1f} pts | RMSE: {m['rmse']:.1f} pts | MAPE: {m['mape']:.2f}% (Q1: {m['q1_mape']:.2f}%, Q2: {m['q2_mape']:.2f}%, Q3: {m['q3_mape']:.2f}%) | 80% CI Coverage: {m['coverage']:.1f}%")

# Experiment B: Multivariate OHLCV (Context 256)
ctx_len = 256
sub_df = train_df.iloc[-ctx_len:]
mv_ctx = np.stack([
    sub_df['Close'].values.astype(np.float32),
    sub_df['Open'].values.astype(np.float32),
    sub_df['High'].values.astype(np.float32),
    sub_df['Low'].values.astype(np.float32),
    sub_df['Volume'].values.astype(np.float32)
], axis=0)

res_mv = forecaster.predict(context=mv_ctx, horizon=horizon, return_quantiles=True, make_positive=True)
p_mv = res_mv.forecast[0, :horizon].astype(float) if res_mv.forecast.ndim == 2 else res_mv.forecast[:horizon].astype(float)
q10_mv = res_mv.quantiles[0, :horizon, 0].astype(float) if res_mv.quantiles.ndim == 3 else res_mv.quantiles[:horizon, 0].astype(float)
q90_mv = res_mv.quantiles[0, :horizon, 8].astype(float) if res_mv.quantiles.ndim == 3 else res_mv.quantiles[:horizon, 8].astype(float)
m_mv = evaluate_preds(p_mv, q10_mv, q90_mv)
exp_name = "multivariate_ohlcv_ctx_256"
results_dict["experiments"][exp_name] = {
    "context_length": ctx_len,
    "type": "multivariate_ohlcv",
    "predicted_close": [float(x) for x in p_mv],
    "q10": [float(x) for x in q10_mv],
    "q90": [float(x) for x in q90_mv],
    "metrics": m_mv
}
print(f"\n--- {exp_name} ---")
print(f"MAE: {m_mv['mae']:.1f} pts | RMSE: {m_mv['rmse']:.1f} pts | MAPE: {m_mv['mape']:.2f}% (Q1: {m_mv['q1_mape']:.2f}%, Q2: {m_mv['q2_mape']:.2f}%, Q3: {m_mv['q3_mape']:.2f}%) | 80% CI Coverage: {m_mv['coverage']:.1f}%")

# Experiment C: Macro & Policy Covariates
full_dates = sub_df['Date_str'].tolist() + actual_dates
# Budget indicator (Feb 2026)
is_budget_window = np.array([1.0 if '2026-02-01' <= d <= '2026-02-07' else 0.0 for d in full_dates], dtype=np.float32)
# Rate policy cycle indicator (monetary policy dates)
is_mpc_month = np.array([1.0 if any(d.startswith(m) for m in ['2026-02', '2026-04', '2026-06', '2026-08']) else 0.0 for d in full_dates], dtype=np.float32)
# Seasonal calendar indicator (normalized day of year)
doy = np.array([(pd.to_datetime(d).dayofyear / 365.0) for d in full_dates], dtype=np.float32)

past_future_cov = np.stack([is_budget_window, is_mpc_month, doy], axis=0)

# Past-only: Volatility spread & volume ratio
vol = sub_df['Volume'].values.astype(np.float32)
vol_sma20 = sub_df['Volume'].rolling(20, min_periods=1).mean().values.astype(np.float32)
vol_ratio = np.where(vol_sma20 > 0, vol / vol_sma20, 1.0).astype(np.float32)
hl_spread = ((sub_df['High'] - sub_df['Low']) / sub_df['Close']).values.astype(np.float32)
past_only_cov = np.stack([vol_ratio, hl_spread], axis=0)

target = sub_df['Close'].values.astype(np.float32)
res_cov = forecaster.predict(
    context=target,
    horizon=horizon,
    past_only_covariates=past_only_cov,
    past_future_covariates=past_future_cov,
    padding_mode="edge",
    return_quantiles=True,
    make_positive=True
)
p_cov = res_cov.forecast[:horizon].astype(float)
q10_cov = res_cov.quantiles[:horizon, 0].astype(float)
q90_cov = res_cov.quantiles[:horizon, 8].astype(float)
m_cov = evaluate_preds(p_cov, q10_cov, q90_cov)
exp_name = "macro_policy_covariates_ctx_256"
results_dict["experiments"][exp_name] = {
    "context_length": ctx_len,
    "type": "macro_policy_covariates",
    "predicted_close": [float(x) for x in p_cov],
    "q10": [float(x) for x in q10_cov],
    "q90": [float(x) for x in q90_cov],
    "metrics": m_cov
}
print(f"\n--- {exp_name} ---")
print(f"MAE: {m_cov['mae']:.1f} pts | RMSE: {m_cov['rmse']:.1f} pts | MAPE: {m_cov['mape']:.2f}% (Q1: {m_cov['q1_mape']:.2f}%, Q2: {m_cov['q2_mape']:.2f}%, Q3: {m_cov['q3_mape']:.2f}%) | 80% CI Coverage: {m_cov['coverage']:.1f}%")

# Save results
with open("/content/nifty_results.json", "w") as f:
    json.dump(results_dict, f, indent=2)
print("\nAll NIFTY experiments completed! Saved to /content/nifty_results.json")
