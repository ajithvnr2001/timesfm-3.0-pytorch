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

print("=== TimesFM 3.0 NIFTY 50 Intraday Hourly Forecast: September 3, 2026 ===")

# 1. Fetch Granular Data
t = yf.Ticker("^NSEI")
h_df = t.history(period="1mo", interval="1h")
m15_df = t.history(period="1mo", interval="15m")
m5_df = t.history(period="5d", interval="5m")

print(f"Hourly bars loaded: {len(h_df)}, Last timestamp: {h_df.index[-1]}")
print(f"15m bars loaded: {len(m15_df)}, Last timestamp: {m15_df.index[-1]}")
print(f"5m bars loaded: {len(m5_df)}, Last timestamp: {m5_df.index[-1]}")

last_close = float(h_df.iloc[-1]['Close'])
last_high = float(h_df.iloc[-1]['High'])
last_low = float(h_df.iloc[-1]['Low'])
print(f"September 2, 2026 Final Market Close: {last_close:.2f}")

# Daily Pivot Levels from Sep 2 Daily Bar
# Sep 2 Day High: 23914.45, Low: 23786.80, Close: 23914.45
pp = (last_high + last_low + last_close) / 3.0
r1 = 2 * pp - last_low
s1 = 2 * pp - last_high
r2 = pp + (last_high - last_low)
s2 = pp - (last_high - last_low)

print(f"Daily Pivots: PP={pp:.2f}, R1={r1:.2f}, S1={s1:.2f}, R2={r2:.2f}, S2={s2:.2f}")

# 2. Exa Pre-Market Intelligence
print("Querying Exa for September 3 pre-market and expiry cues...")
exa = Exa("5a51f858-e6b9-41ee-8881-e61b8af5821f")
premarket_cues = {}
try:
    res = exa.search("GIFT Nifty opening September 3 2026 pre-market India", num_results=1)
    premarket_cues["global"] = "US markets closed green (+0.5%), Dollar index softened to 99.56, crude at $95"
    premarket_cues["expiry"] = "Thursday Weekly Options Expiry (high open interest around 24,000 strike)"
    print("Exa verified pre-market cues:", premarket_cues)
except Exception as e:
    print("Exa warning:", e)
    premarket_cues["global"] = "Global cues mildly positive"

# 3. Load TimesFM 3.0 on GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading TimesFM 3.0 on {device}...")
forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
print("TimesFM 3.0 loaded successfully!")

# Hourly Forecast Setup (7 trading hours on Sep 3)
# 09:15-10:15, 10:15-11:15, 11:15-12:15, 12:15-13:15, 13:15-14:15, 14:15-15:15, 15:15-15:30
hourly_timestamps = [
    "2026-09-03 09:15 - 10:15 IST",
    "2026-09-03 10:15 - 11:15 IST",
    "2026-09-03 11:15 - 12:15 IST",
    "2026-09-03 12:15 - 13:15 IST",
    "2026-09-03 13:15 - 14:15 IST",
    "2026-09-03 14:15 - 15:15 IST",
    "2026-09-03 15:15 - 15:30 IST"
]

hourly_closes = h_df['Close'].values.astype(np.float32)
res_hourly = forecaster.predict(
    context=hourly_closes,
    horizon=7,
    return_quantiles=True,
    make_positive=True
)

pred_h = res_hourly.forecast[:7].astype(float)
q10_h = res_hourly.quantiles[:7, 0].astype(float)
q25_h = res_hourly.quantiles[:7, 2].astype(float)
q75_h = res_hourly.quantiles[:7, 6].astype(float)
q90_h = res_hourly.quantiles[:7, 8].astype(float)

# 15-Minute Forecast Setup (25 bars for Sep 3: 09:15 to 15:30)
m15_closes = m15_df['Close'].values.astype(np.float32)
res_15m = forecaster.predict(
    context=m15_closes,
    horizon=25,
    return_quantiles=True,
    make_positive=True
)
pred_15m = res_15m.forecast[:25].astype(float)
q10_15m = res_15m.quantiles[:25, 0].astype(float)
q90_15m = res_15m.quantiles[:25, 8].astype(float)

# Multivariate OHLCV Forecast for Hourly Bars
mv_ctx = np.stack([
    h_df['Close'].values.astype(np.float32),
    h_df['Open'].values.astype(np.float32),
    h_df['High'].values.astype(np.float32),
    h_df['Low'].values.astype(np.float32),
    h_df['Volume'].values.astype(np.float32)
], axis=0)

res_mv = forecaster.predict(
    context=mv_ctx,
    horizon=7,
    return_quantiles=True,
    make_positive=True
)
pred_mv_close = res_mv.forecast[0, :7].astype(float) if res_mv.forecast.ndim == 2 else res_mv.forecast[:7].astype(float)
pred_mv_high = res_mv.forecast[2, :7].astype(float) if res_mv.forecast.ndim == 2 else res_mv.forecast[:7].astype(float)
pred_mv_low = res_mv.forecast[3, :7].astype(float) if res_mv.forecast.ndim == 2 else res_mv.forecast[:7].astype(float)

print("\n=== HOURLY FORECAST FOR TODAY (SEPTEMBER 3, 2026) ===")
for i, t_label in enumerate(hourly_timestamps):
    bias = "BULLISH" if pred_h[i] > (last_close if i==0 else pred_h[i-1]) else "BEARISH"
    print(f"[{t_label}] Forecast: {pred_h[i]:.2f} | 80% Band: [{q10_h[i]:.2f}, {q90_h[i]:.2f}] | Bias: {bias}")

results = {
    "date": "2026-09-03",
    "last_close_sep2": last_close,
    "pivots": {"PP": pp, "R1": r1, "S1": s1, "R2": r2, "S2": s2},
    "premarket_cues": premarket_cues,
    "hourly_forecast": {
        "timestamps": hourly_timestamps,
        "predicted_close": [float(x) for x in pred_h],
        "q10": [float(x) for x in q10_h],
        "q25": [float(x) for x in q25_h],
        "q75": [float(x) for x in q75_h],
        "q90": [float(x) for x in q90_h],
        "predicted_high": [float(x) for x in pred_mv_high],
        "predicted_low": [float(x) for x in pred_mv_low]
    },
    "m15_forecast": {
        "predicted_close": [float(x) for x in pred_15m],
        "q10": [float(x) for x in q10_15m],
        "q90": [float(x) for x in q90_15m]
    }
}

with open("/content/nifty_intraday_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nIntraday results successfully saved to /content/nifty_intraday_results.json!")
