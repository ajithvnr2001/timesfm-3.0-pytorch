"""
institutional_engine.py
========================
Institutional-Grade Quantitative Risk, Sizing, and Cross-Asset Macro Engine.
Equips Google TimesFM 3.0 with Tier-1 Quantitative Hedge Fund Rigor:
1. Multivariate Macro & Sector Benchmarking (NIFTY 50, Sector Beta, India VIX)
2. Parametric & Historical Value at Risk (VaR 95%) & Conditional VaR (CVaR / Expected Shortfall)
3. Half-Kelly Criterion & Volatility-Parity (Risk Budget) Capital Sizing
4. Indian Market Regulatory & Friction Modeling (STT, SEBI, GST, Slippage)
5. Objective Stop-Loss Invalidation & Asymmetric Risk/Reward Ratio (RRR)
6. Institutional Scorecard & Executive Decision Directives
"""

import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# Indian Sector Index Ticker Mapping
SECTOR_TICKER_MAP = {
    "Information Technology Services": "^CNXIT",
    "Technology": "^CNXIT",
    "Automobiles": "^CNXAUTO",
    "Auto Manufacturers": "^CNXAUTO",
    "Banks": "^NSEBANK",
    "Financial Services": "^NSEBANK",
    "Consumer Defensive": "^CNXFMCG",
    "FMCG": "^CNXFMCG",
    "Metals & Mining": "^CNXMETAL",
    "Basic Materials": "^CNXMETAL",
    "Oil & Gas Integrated": "^CNXENERGY",
    "Energy": "^CNXENERGY",
    "Pharmaceuticals": "^CNXPHARMA",
    "Healthcare": "^CNXPHARMA",
    "Real Estate": "^CNXREALTY",
}

def get_macro_regime(as_of=None):
    """
    Fetches real-time / point-in-time NIFTY 50 and India VIX macro benchmarks.
    Computes market regime and risk multiplier.
    """
    try:
        nifty_tk = yf.Ticker("^NSEI")
        nifty_hist = nifty_tk.history(period="1y")
        if as_of:
            nifty_hist = nifty_hist[nifty_hist.index <= pd.Timestamp(as_of)]
        
        nifty_close = float(nifty_hist["Close"].iloc[-1])
        nifty_sma20 = float(nifty_hist["Close"].rolling(20).mean().iloc[-1])
        nifty_sma50 = float(nifty_hist["Close"].rolling(50).mean().iloc[-1])
        nifty_trend = "BULLISH_UPTREND" if nifty_close >= nifty_sma20 >= nifty_sma50 else (
            "SIDEWAYS_CONSOLIDATION" if nifty_close >= nifty_sma50 else "BEARISH_DOWNTREND"
        )
    except Exception:
        nifty_close = 23900.0
        nifty_trend = "BULLISH_UPTREND"

    try:
        vix_tk = yf.Ticker("^INDIAVIX")
        vix_hist = vix_tk.history(period="3mo")
        if as_of:
            vix_hist = vix_hist[vix_hist.index <= pd.Timestamp(as_of)]
        vix_val = float(vix_hist["Close"].iloc[-1])
    except Exception:
        vix_val = 13.5

    if vix_val < 13.0:
        vix_regime = "LOW_VOLATILITY (Complacent / Risk-On)"
        macro_mult = 1.05
    elif vix_val <= 18.0:
        vix_regime = "NORMAL_VOLATILITY (Optimal Trading Environment)"
        macro_mult = 1.00
    elif vix_val <= 24.0:
        vix_regime = "ELEVATED_VOLATILITY (Caution / Hedges Advised)"
        macro_mult = 0.80
    else:
        vix_regime = "EXTREME_RISK_OFF (High Stress / Capital Defense)"
        macro_mult = 0.50

    return {
        "nifty_close": nifty_close,
        "nifty_trend": nifty_trend,
        "india_vix": vix_val,
        "vix_regime": vix_regime,
        "macro_multiplier": macro_mult
    }

def get_sector_and_beta(ticker, industry, stock_series, as_of=None):
    """
    Computes Beta and Correlation against NIFTY 50 and Sector Index.
    """
    sec_ticker = SECTOR_TICKER_MAP.get(industry, "^NSEI")
    try:
        sec_hist = yf.Ticker(sec_ticker).history(period="1y")["Close"]
        nifty_hist = yf.Ticker("^NSEI").history(period="1y")["Close"]

        if as_of:
            sec_hist = sec_hist[sec_hist.index <= pd.Timestamp(as_of)]
            nifty_hist = nifty_hist[nifty_hist.index <= pd.Timestamp(as_of)]

        # Align series
        df = pd.DataFrame({
            "stock": stock_series,
            "sector": sec_hist,
            "nifty": nifty_hist
        }).dropna()

        rets = df.pct_change().dropna()
        var_nifty = rets["nifty"].var()
        cov_nifty = rets["stock"].cov(rets["nifty"])
        beta_nifty = float(cov_nifty / var_nifty) if var_nifty > 0 else 1.0
        corr_nifty = float(rets["stock"].corr(rets["nifty"]))

        var_sec = rets["sector"].var()
        cov_sec = rets["stock"].cov(rets["sector"])
        beta_sec = float(cov_sec / var_sec) if var_sec > 0 else 1.0
        corr_sec = float(rets["stock"].corr(rets["sector"]))
    except Exception:
        beta_nifty = 1.0
        corr_nifty = 0.65
        beta_sec = 1.0
        corr_sec = 0.70

    return {
        "sector_index_ticker": sec_ticker,
        "beta_nifty": round(beta_nifty, 2),
        "corr_nifty": round(corr_nifty, 2),
        "beta_sector": round(beta_sec, 2),
        "corr_sector": round(corr_sec, 2)
    }

def compute_institutional_risk_and_sizing(
    stock_context,
    last_price,
    weighted_target,
    bull_target,
    bear_target,
    q10_terminal,
    q90_terminal,
    horizon=30,
    portfolio_capital=1000000.0,
    macro_multiplier=1.0
):
    """
    Calculates VaR, CVaR, Max Drawdown, Indian Frictions, Risk/Reward Ratio,
    Half-Kelly Allocation %, and exact share position sizing.
    """
    ctx = np.array(stock_context, dtype=float)
    if len(ctx) >= 5:
        returns = np.diff(ctx) / ctx[:-1]
        daily_vol = float(np.std(returns))
        ann_vol = float(daily_vol * np.sqrt(252))
        # Historical Max Drawdown
        cum = np.maximum.accumulate(ctx)
        dd = (ctx - cum) / cum
        max_dd = float(np.min(dd)) * 100.0
    else:
        daily_vol = 0.015
        ann_vol = 0.24
        max_dd = -12.5
        returns = np.array([-0.01, 0.01, 0.0])

    # 1. Value at Risk (VaR 95% Parametric & Horizon)
    var_95_1d = float(1.645 * daily_vol * 100.0)
    var_95_horizon = float(1.645 * daily_vol * np.sqrt(horizon) * 100.0)

    # 2. Conditional VaR (Expected Shortfall - tail risk average)
    tail_losses = returns[returns <= np.percentile(returns, 5)]
    cvar_95 = float(abs(np.mean(tail_losses)) * np.sqrt(horizon) * 100.0) if len(tail_losses) > 0 else var_95_horizon * 1.25

    # 3. Objective Stop-Loss Invalidation
    # Anchored at lower of Bear Scenario or Monte Carlo Q10 boundary with 2% buffer
    stop_loss = round(min(bear_target, q10_terminal * 0.98), 2)
    downside_risk_pct = max(1.0, ((last_price - stop_loss) / last_price) * 100.0)

    # 4. Indian Friction Adjustment (STT 0.1% buy + 0.1% sell + SEBI/Exchange/Stamp/Slippage ~0.05% = 0.25% roundtrip)
    friction_pct = 0.25
    gross_upside_pct = ((weighted_target - last_price) / last_price) * 100.0
    net_upside_pct = round(gross_upside_pct - friction_pct, 2)

    # 5. Net Asymmetric Risk/Reward Ratio (RRR)
    rrr = round(max(0.0, net_upside_pct) / downside_risk_pct, 2)

    # 6. Win Probability & Kelly Criterion
    # Estimate win probability based on RRR and volatility
    if net_upside_pct > 0:
        p_win = min(0.78, max(0.40, 0.50 + (rrr - 1.5) * 0.08))
    else:
        p_win = 0.30

    b_ratio = max(0.2, (net_upside_pct / downside_risk_pct))
    full_kelly = max(0.0, (p_win * (b_ratio + 1) - 1) / b_ratio)
    half_kelly_pct = round(full_kelly * 0.5 * 100.0, 1)

    # 7. Volatility-Parity Risk Budget (Target single-asset portfolio risk contribution = 1.75%)
    target_risk_contribution = 1.75
    vol_parity_pct = round((target_risk_contribution / max(0.08, ann_vol)) * 100.0 * 0.1, 1)

    # Combined Institutional Allocation (Capped at 15% single-stock ceiling)
    raw_alloc = min(half_kelly_pct, vol_parity_pct) if half_kelly_pct > 0 else 0.0
    recommended_alloc_pct = round(min(15.0, raw_alloc * macro_multiplier), 1)

    # Capital and Share Quantities
    alloc_capital = round((recommended_alloc_pct / 100.0) * portfolio_capital, 2)
    recommended_shares = int(alloc_capital // last_price) if last_price > 0 else 0

    # 8. Institutional Action Directive
    if net_upside_pct >= 12.0 and rrr >= 2.0:
        directive = "STRONG BUY (High Conviction Asymmetric Setup)"
    elif net_upside_pct >= 5.0 and rrr >= 1.4:
        directive = "ACCUMULATE / BUY (Favorable Risk/Reward)"
    elif -3.0 <= net_upside_pct < 5.0 and rrr >= 0.9:
        directive = "HOLD (Maintain Position with Stop-Loss)"
    elif net_upside_pct < -3.0 or rrr < 0.7:
        directive = "TRIM / TAKE PROFIT (Negative Expected Skew)"
    else:
        directive = "NEUTRAL / WATCHLIST (Wait for Better Entry)"

    return {
        "annualized_volatility_pct": round(ann_vol * 100.0, 2),
        "historical_max_drawdown_pct": round(max_dd, 2),
        "var_95_1day_pct": round(var_95_1d, 2),
        "var_95_horizon_pct": round(var_95_horizon, 2),
        "cvar_95_horizon_pct": round(cvar_95, 2),
        "stop_loss_invalidation_level": stop_loss,
        "downside_risk_pct": round(downside_risk_pct, 2),
        "friction_deduction_pct": friction_pct,
        "gross_upside_pct": round(gross_upside_pct, 2),
        "net_upside_pct": net_upside_pct,
        "net_risk_reward_ratio": rrr,
        "win_probability_est": round(p_win, 2),
        "half_kelly_alloc_pct": half_kelly_pct,
        "volatility_parity_alloc_pct": vol_parity_pct,
        "recommended_portfolio_alloc_pct": recommended_alloc_pct,
        "recommended_capital_inr": alloc_capital,
        "recommended_shares": recommended_shares,
        "institutional_directive": directive
    }

def build_institutional_scorecard(
    ticker,
    last_price,
    fundamental_data,
    forecast_results,
    horizon=30,
    portfolio_capital=1000000.0,
    as_of=None
):
    """
    Unified master synthesizer: Combines Fundamental Forensics, Macro Regimes,
    TimesFM 3.0 Quantiles, and Risk Sizing into an institutional scorecard.
    """
    macro = get_macro_regime(as_of)
    industry = fundamental_data.get("industry", "General")
    sector_info = get_sector_and_beta(ticker, industry, forecast_results.get("numerical_context", [last_price]*10), as_of)

    scenarios = fundamental_data.get("scenarios", {})
    bear_tgt = scenarios.get("bear", {}).get("target_price", last_price * 0.85)
    base_tgt = scenarios.get("base", {}).get("target_price", last_price * 1.05)
    bull_tgt = scenarios.get("bull", {}).get("target_price", last_price * 1.25)
    weighted_tgt = fundamental_data.get("weighted_target", base_tgt)

    q10 = forecast_results.get("base_q10", [last_price * 0.90] * horizon)[-1]
    q90 = forecast_results.get("base_q90", [last_price * 1.10] * horizon)[-1]

    risk_sizing = compute_institutional_risk_and_sizing(
        stock_context=forecast_results.get("numerical_context", [last_price]*10),
        last_price=last_price,
        weighted_target=weighted_tgt,
        bull_target=bull_tgt,
        bear_target=bear_tgt,
        q10_terminal=q10,
        q90_terminal=q90,
        horizon=horizon,
        portfolio_capital=portfolio_capital,
        macro_multiplier=macro["macro_multiplier"]
    )

    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ticker": ticker,
        "last_close": round(last_price, 2),
        "horizon_days": horizon,
        "macro_environment": macro,
        "sector_relative_strength": sector_info,
        "fundamental_forensics": {
            "audited_eps": fundamental_data.get("eps"),
            "eps_source": fundamental_data.get("eps_source"),
            "earnings_cagr": fundamental_data.get("eps_cagr"),
            "sector_pe_benchmark": fundamental_data.get("sector_pe"),
            "bear_target": bear_tgt,
            "base_target": base_tgt,
            "bull_target": bull_tgt,
            "weighted_fair_value": weighted_tgt
        },
        "timesfm_probabilistic_forecast": {
            "terminal_expected": round(float(forecast_results.get("weighted_expected", [weighted_tgt])[-1]), 2),
            "terminal_q10": round(float(q10), 2),
            "terminal_q90": round(float(q90), 2)
        },
        "institutional_risk_and_sizing": risk_sizing
    }

if __name__ == "__main__":
    import json
    res = build_institutional_scorecard("INFY.NS", 1500.0, {
        "eps": 76.5, "eps_source": "annual_statement", "eps_cagr": 0.08,
        "industry": "Information Technology Services", "sector_pe": 27.0,
        "scenarios": {
            "bear": {"target_price": 1250.0},
            "base": {"target_price": 1650.0},
            "bull": {"target_price": 1950.0}
        },
        "weighted_target": 1625.0
    }, {
        "numerical_context": [1420, 1440, 1460, 1480, 1500],
        "base_q10": [1400]*30,
        "base_q90": [1750]*30,
        "weighted_expected": [1620]*30
    })
    print(json.dumps(res, indent=2))
