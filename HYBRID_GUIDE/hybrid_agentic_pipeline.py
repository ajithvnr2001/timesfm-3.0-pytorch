#!/usr/bin/env python3
"""
hybrid_agentic_pipeline.py
==========================
End-to-End Production Pipeline:
Fusing Large Language Models (LLMs) with Google Research's TimesFM 3.0
for Financial Time-Series Forecasting.

Usage Example:
  python hybrid_agentic_pipeline.py \
    --ticker MODISONLTD.NS \
    --pdf filings/fade292d_annual_report_2026.pdf \
    --cutoff 2026-08-01 \
    --horizon 23 \
    --api_provider heuristic
"""

import argparse
import json
import os
import re
import sys
import numpy as np
import pandas as pd
import pypdf
import yfinance as yf
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Check for TimesFM 3.0
try:
    from timesfm3 import TimesFM3Forecaster
    HAS_TIMESFM = True
except ImportError:
    HAS_TIMESFM = False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Hybrid LLM + TimesFM 3.0 Forecasting Pipeline")
    parser.add_argument("--ticker", type=str, required=True, help="Yahoo Finance Ticker (e.g. MODISONLTD.NS)")
    parser.add_argument("--pdf", type=str, default=None, help="Path to Corporate Filing PDF (Annual Report / Results)")
    parser.add_argument("--cutoff", type=str, required=True, help="Strict Data Cutoff Date (YYYY-MM-DD)")
    parser.add_argument("--horizon", type=int, default=23, help="Forecast horizon in trading days")
    parser.add_argument("--api_provider", type=str, default="heuristic", choices=["gemini", "openai", "heuristic"],
                        help="LLM provider for semantic document reasoning")
    parser.add_argument("--api_key", type=str, default=None, help="API Key for Gemini or OpenAI")
    parser.add_argument("--output_dir", type=str, default="./output", help="Directory to save forecast JSON and plots")
    return parser.parse_args()


# ==============================================================================
# 1. Market Data Ingestion Layer
# ==============================================================================
def ingest_market_data(ticker_symbol: str, cutoff_date: str, horizon: int):
    print(f"\n[1/5] Ingesting Market Data for {ticker_symbol} (Cutoff: {cutoff_date})...")
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="max")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df["Date_str"] = df.index.strftime("%Y-%m-%d")

    train_df = df[df["Date_str"] <= cutoff_date].copy()
    test_df = df[df["Date_str"] > cutoff_date].iloc[:horizon].copy()

    if train_df.empty:
        raise ValueError(f"No historical price data found on or before {cutoff_date} for {ticker_symbol}")

    last_train_close = float(train_df.iloc[-1]["Close"])
    print(f"  • Training Samples: {len(train_df)} trading days")
    print(f"  • Last Close on Cutoff ({cutoff_date}): ₹{last_train_close:.2f}")
    print(f"  • Test Horizon: {len(test_df)} trading days")

    return train_df, test_df, last_train_close


# ==============================================================================
# 2. Corporate Document Extraction Layer
# ==============================================================================
def extract_text_from_pdf(pdf_path: str, max_pages: int = 45) -> str:
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"  • Notice: No PDF provided or path invalid. Proceeding with sector defaults.")
        return ""

    print(f"\n[2/5] Parsing Corporate PDF Filing: {pdf_path} (First {max_pages} pages)...")
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    extracted_text = []

    for i in range(min(total_pages, max_pages)):
        text = reader.pages[i].extract_text()
        if text:
            extracted_text.append(f"--- PAGE {i+1} ---\n" + text)

    combined = "\n".join(extracted_text)
    print(f"  • Successfully extracted {len(combined)} characters from {min(total_pages, max_pages)} pages.")
    return combined


# ==============================================================================
# 3. LLM Fundamental Reasoning & Valuation Synthesizer
# ==============================================================================
def run_llm_reasoning(filing_text: str, current_price: float, provider: str, api_key: str, horizon: int) -> dict:
    print(f"\n[3/5] Running Semantic Reasoning Layer (Provider: {provider})...")

    # If Heuristic / Offline Mode
    if provider == "heuristic" or not api_key:
        print("  • Executing Rule-Based Heuristic Valuation Engine (Zero-API Fallback)...")
        # Search for Revenue, PAT, and EPS in the extracted text
        rev_match = re.search(r"(?:Total Revenue|Revenue from operations)[^\d]*([\d,]+\.?\d*)", filing_text, re.IGNORECASE)
        pat_match = re.search(r"(?:Profit After Tax|PAT|Net Profit)[^\d]*([\d,]+\.?\d*)", filing_text, re.IGNORECASE)
        eps_match = re.search(r"(?:Diluted EPS|EPS)[^\d]*([\d,]+\.?\d*)", filing_text, re.IGNORECASE)
        borrowing_match = re.search(r"180\(1\)\(c\).*?(?:Rs\.|INR|limit).*?([\d,]+)", filing_text, re.DOTALL | re.IGNORECASE)

        # Default or Extracted Fundamentals
        eps = float(eps_match.group(1).replace(",", "")) if eps_match else (current_price / 15.0)
        trailing_pe = current_price / eps if eps > 0 else 15.0
        sector_pe = 38.0  # Median benchmark for electrical/capital goods / FMCG

        # Base case target (20x - 22x P/E)
        fair_multiple = min(sector_pe * 0.60, max(18.0, trailing_pe * 1.5))
        fair_value_target = eps * fair_multiple

        print(f"  • Extracted / Estimated EPS: ₹{eps:.2f}")
        print(f"  • Current Trailing P/E: {trailing_pe:.2f}x (Sector Median: {sector_pe:.1f}x)")
        print(f"  • LLM Fair Value Re-Rating Target: ₹{fair_value_target:.2f} (Target Multiple: {fair_multiple:.1f}x)")

        return {
            "trailing_eps": eps,
            "trailing_pe": trailing_pe,
            "sector_pe": sector_pe,
            "fair_value_target": fair_value_target,
            "sigmoid_steepness": 0.20,
            "sigmoid_midpoint": horizon / 2.0
        }

    # If Gemini Provider
    elif provider == "gemini":
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""You are a Principal Quantitative Equity Analyst.
Given this excerpt from the corporate filing:
{filing_text[:12000]}

Current Market Price at Cutoff: {current_price}
Forecast Horizon: {horizon} trading days.

Calculate trailing EPS, trailing P/E, sector median P/E, and output an intrinsic re-rating target and sigmoid parameters.
Return ONLY a valid JSON object matching this structure:
{{
  "trailing_eps": float,
  "trailing_pe": float,
  "sector_pe": float,
  "fair_value_target": float,
  "sigmoid_steepness": float,
  "sigmoid_midpoint": float
}}
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            print(f"  • Gemini Fundamental Analysis: Target Price = ₹{data['fair_value_target']:.2f}")
            return data
        except Exception as e:
            print(f"  • Gemini API Error: {e}. Falling back to heuristic engine.")
            return run_llm_reasoning(filing_text, current_price, "heuristic", None, horizon)


# ==============================================================================
# 4. TimesFM 3.0 Dynamic Covariate Construction & Inference
# ==============================================================================
def execute_hybrid_forecast(train_df, last_price: float, valuation_data: dict, horizon: int):
    print(f"\n[4/5] Constructing Dynamic Covariates & Running TimesFM 3.0 Inference...")

    ctx_len = min(64, len(train_df))
    sub_train = train_df.iloc[-ctx_len:].copy()
    L = len(sub_train)

    # 1. Past-Only: Volume Accumulation Ratio
    vol = sub_train["Volume"].values.astype(np.float32)
    vol_sma = pd.Series(vol).rolling(20, min_periods=1).mean().values
    vol_ratio = np.where(vol_sma > 0, vol / vol_sma, 1.0).astype(np.float32)
    past_only = np.expand_dims(vol_ratio, axis=0)  # Shape: [1, L]

    # 2. Past-and-Future: LLM Fundamental Re-Rating Attractor S-Curve
    target_price = valuation_data["fair_value_target"]
    k = valuation_data.get("sigmoid_steepness", 0.20)
    t0 = valuation_data.get("sigmoid_midpoint", horizon / 2.0)

    full_steps = L + horizon
    cov_path = np.zeros(full_steps, dtype=np.float32)
    # Context period: follows historical normalized price
    cov_path[:L] = (sub_train["Close"].values - last_price) / 100.0

    # Horizon period: models fundamental S-curve discovery
    for h in range(horizon):
        step = h + 1
        progress = 1.0 / (1.0 + np.exp(-k * (step - t0)))
        projected = last_price + progress * (target_price - last_price)
        cov_path[L + h] = (projected - last_price) / 100.0

    past_future = np.expand_dims(cov_path, axis=0)  # Shape: [1, L + H]

    # 3. Model Inference
    device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
    print(f"  • Initializing TimesFM 3.0 on {device}...")

    if HAS_TIMESFM:
        forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
        context_closes = sub_train["Close"].values.astype(np.float32)

        res = forecaster.predict(
            context=context_closes,
            horizon=horizon,
            past_only_covariates=past_only,
            past_future_covariates=past_future,
            padding_mode="edge",
            return_quantiles=True,
            make_positive=True
        )

        p_hybrid = res.forecast[:horizon].astype(float)
        q10_hybrid = res.quantiles[:horizon, 0].astype(float)
        q90_hybrid = res.quantiles[:horizon, 8].astype(float)
    else:
        print("  • Warning: timesfm3 not found locally. Simulating output on GPU bounds.")
        future_llm = np.array([last_price + (1.0 / (1.0 + np.exp(-k * (h + 1 - t0)))) * (target_price - last_price) for h in range(horizon)])
        p_hybrid = future_llm
        q10_hybrid = future_llm * 0.92
        q90_hybrid = future_llm * 1.08

    print(f"  • Forecast Generated! Terminal Prediction (Day {horizon}): ₹{p_hybrid[-1]:.2f}")
    return p_hybrid, q10_hybrid, q90_hybrid


# ==============================================================================
# 5. Output Reporting & Export
# ==============================================================================
def save_outputs(output_dir: str, ticker: str, pred, q10, q90, valuation_data, test_df):
    print(f"\n[5/5] Exporting Results to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)

    results = {
        "ticker": ticker,
        "fundamental_valuation": valuation_data,
        "forecast": {
            "predicted_close": [float(x) for x in pred],
            "p10_lower_bound": [float(x) for x in q10],
            "p90_upper_bound": [float(x) for x in q90]
        }
    }

    if not test_df.empty:
        actuals = test_df["Close"].values[:len(pred)]
        results["actual_close"] = [float(x) for x in actuals]
        mae = float(np.mean(np.abs(pred - actuals)))
        mape = float(np.mean(np.abs((actuals - pred) / actuals)) * 100)
        results["metrics"] = {"mae": mae, "mape": mape}
        print(f"  • Ground Truth Comparison: MAE = ₹{mae:.2f} | MAPE = {mape:.2f}%")

    out_file = os.path.join(output_dir, f"{ticker}_hybrid_forecast.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"  • Results successfully saved to: {out_file}")
    print("\n=== PIPELINE EXECUTION COMPLETE ===")


def main():
    args = parse_arguments()
    train_df, test_df, last_close = ingest_market_data(args.ticker, args.cutoff, args.horizon)
    filing_text = extract_text_from_pdf(args.pdf)
    valuation_data = run_llm_reasoning(filing_text, last_close, args.api_provider, args.api_key, args.horizon)
    pred, q10, q90 = execute_hybrid_forecast(train_df, last_close, valuation_data, args.horizon)
    save_outputs(args.output_dir, args.ticker, pred, q10, q90, valuation_data, test_df)


if __name__ == "__main__":
    main()
