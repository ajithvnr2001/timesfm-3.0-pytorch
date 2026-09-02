import os
os.environ["HF_HUB_DISABLE_COLAB_SECRETS"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import json
import numpy as np
import pandas as pd
import torch
import yfinance as yf
from timesfm3 import TimesFM3Forecaster

print("=== TimesFM 3.0 MODISONLTD Stock Forecasting Experiment ===")

# 1. Fetch data
print("Fetching MODISONLTD.NS data...")
ticker = yf.Ticker("MODISONLTD.NS")
df = ticker.history(period="max")
df.index = pd.to_datetime(df.index)
df['Date_str'] = df.index.strftime('%Y-%m-%d')

# Filter train (strictly before Aug 1, 2026) and test (Aug 1 to Sep 2, 2026)
train_df = df[df['Date_str'] < '2026-08-01'].copy()
test_df = df[(df['Date_str'] >= '2026-08-01') & (df['Date_str'] <= '2026-09-02')].copy()

# Note: for 2026-09-02, if Close is NaN in yfinance, fill with official market close 520.65
if np.isnan(test_df.iloc[-1]['Close']):
    test_df.loc[test_df.index[-1], 'Close'] = 520.65
    test_df.loc[test_df.index[-1], 'Open'] = 509.00
    test_df.loc[test_df.index[-1], 'High'] = 546.00
    test_df.loc[test_df.index[-1], 'Low'] = 509.00

actual_dates = test_df['Date_str'].tolist()
actual_closes = test_df['Close'].values.astype(np.float32)
horizon = len(actual_closes)

print(f"Historical training data points available: {len(train_df)} (Last date: {train_df.iloc[-1]['Date_str']}, Close: {train_df.iloc[-1]['Close']:.2f})")
print(f"Forecast horizon: {horizon} trading days ({actual_dates[0]} to {actual_dates[-1]})")

# 2. Load TimesFM 3.0 Model
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading TimesFM 3.0 from Hugging Face on {device}...")
forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
print("TimesFM 3.0 loaded successfully!")

results_dict = {
    "horizon": horizon,
    "actual_dates": actual_dates,
    "actual_closes": [float(x) for x in actual_closes],
    "last_train_date": train_df.iloc[-1]['Date_str'],
    "last_train_close": float(train_df.iloc[-1]['Close']),
    "experiments": {}
}

# Context lengths to test: 64, 128, 256, 512
contexts = [64, 128, 256, 512]

for ctx_len in contexts:
    ctx_data = train_df['Close'].values[-ctx_len:].astype(np.float32)
    
    # Univariate forecast
    res = forecaster.predict(
        context=ctx_data,
        horizon=horizon,
        return_quantiles=True,
        make_positive=True
    )
    
    pred_median = res.forecast[:horizon].astype(float)
    quantiles = res.quantiles[:horizon, :].astype(float) # shape (horizon, 9)
    
    # Metrics
    mae = float(np.mean(np.abs(pred_median - actual_closes)))
    rmse = float(np.sqrt(np.mean((pred_median - actual_closes) ** 2)))
    mape = float(np.mean(np.abs((actual_closes - pred_median) / actual_closes)) * 100)
    
    # Directional accuracy
    actual_dir = np.sign(np.diff(np.insert(actual_closes, 0, train_df.iloc[-1]['Close'])))
    pred_dir = np.sign(np.diff(np.insert(pred_median, 0, train_df.iloc[-1]['Close'])))
    dir_acc = float(np.mean(actual_dir == pred_dir) * 100)
    
    # Quantile coverage (10% to 90%)
    q10 = quantiles[:, 0]
    q90 = quantiles[:, 8]
    coverage = float(np.mean((actual_closes >= q10) & (actual_closes <= q90)) * 100)
    
    exp_name = f"univariate_ctx_{ctx_len}"
    results_dict["experiments"][exp_name] = {
        "context_length": ctx_len,
        "type": "univariate",
        "predicted_close": [float(x) for x in pred_median],
        "q10": [float(x) for x in q10],
        "q50": [float(x) for x in pred_median],
        "q90": [float(x) for x in q90],
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "directional_accuracy_pct": dir_acc,
        "quantile_coverage_pct": coverage
    }
    print(f"\n--- Result for {exp_name} ---")
    print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | MAPE: {mape:.2f}% | Dir Acc: {dir_acc:.1f}% | 80% CI Coverage: {coverage:.1f}%")

# Multivariate Experiment with TimesFM 3.0:
for ctx_len in [64, 128, 256]:
    sub_df = train_df.iloc[-ctx_len:]
    # Channels: Close, Open, High, Low, Volume
    mv_context = np.stack([
        sub_df['Close'].values.astype(np.float32),
        sub_df['Open'].values.astype(np.float32),
        sub_df['High'].values.astype(np.float32),
        sub_df['Low'].values.astype(np.float32),
        sub_df['Volume'].values.astype(np.float32)
    ], axis=0) # shape (5, seq_len)
    
    try:
        res_mv = forecaster.predict(
            context=mv_context,
            horizon=horizon,
            return_quantiles=True,
            make_positive=True
        )
        pred_mv = res_mv.forecast
        if pred_mv.ndim == 2:
            close_pred = pred_mv[0, :horizon].astype(float)
            q10 = res_mv.quantiles[0, :horizon, 0].astype(float)
            q90 = res_mv.quantiles[0, :horizon, 8].astype(float)
        else:
            close_pred = pred_mv[:horizon].astype(float)
            q10 = res_mv.quantiles[:horizon, 0].astype(float)
            q90 = res_mv.quantiles[:horizon, 8].astype(float)
            
        mae = float(np.mean(np.abs(close_pred - actual_closes)))
        rmse = float(np.sqrt(np.mean((close_pred - actual_closes) ** 2)))
        mape = float(np.mean(np.abs((actual_closes - close_pred) / actual_closes)) * 100)
        actual_dir = np.sign(np.diff(np.insert(actual_closes, 0, train_df.iloc[-1]['Close'])))
        pred_dir = np.sign(np.diff(np.insert(close_pred, 0, train_df.iloc[-1]['Close'])))
        dir_acc = float(np.mean(actual_dir == pred_dir) * 100)
        coverage = float(np.mean((actual_closes >= q10) & (actual_closes <= q90)) * 100)
        
        exp_name = f"multivariate_ohlcv_ctx_{ctx_len}"
        results_dict["experiments"][exp_name] = {
            "context_length": ctx_len,
            "type": "multivariate_ohlcv",
            "predicted_close": [float(x) for x in close_pred],
            "q10": [float(x) for x in q10],
            "q50": [float(x) for x in close_pred],
            "q90": [float(x) for x in q90],
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "directional_accuracy_pct": dir_acc,
            "quantile_coverage_pct": coverage
        }
        print(f"\n--- Result for {exp_name} ---")
        print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | MAPE: {mape:.2f}% | Dir Acc: {dir_acc:.1f}% | 80% CI Coverage: {coverage:.1f}%")
    except Exception as e:
        print(f"Multivariate experiment ctx={ctx_len} failed: {e}")

# Save results to JSON
with open("/content/timesfm_results.json", "w") as f:
    json.dump(results_dict, f, indent=2)
print("\nResults successfully saved to /content/timesfm_results.json!")
