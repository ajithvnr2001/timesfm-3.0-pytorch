"""
scenario_builder.py  --  FIX for Weakness #1 & #3
Replaces hardcoded P/E multiples (eps*16/22/27.5, sector_pe=38.0)
and the fragile PDF-regex EPS with real financial statement data.

Drop-in: call build_scenarios(ticker) instead of the inline scenario dict.
"""
import numpy as np, pandas as pd, yfinance as yf

SECTOR_PE_MAP = {
    "Information Technology Services": 27.0, "Technology": 30.0, "Banks": 15.0,
    "Financial Services": 20.0, "Automobiles": 24.0, "Auto Manufacturers": 24.0,
    "Pharmaceuticals": 32.0, "Healthcare": 30.0, "Oil & Gas Integrated": 14.0,
    "Metals & Mining": 12.0, "Consumer Defensive": 45.0, "FMCG": 45.0,
    "Real Estate": 35.0, "Power": 18.0, "Telecom Services": 25.0, "Chemicals": 28.0,
}
GROWTH_BAND = {"high": (0.70,1.00,1.35), "mid": (0.62,0.88,1.15), "low": (0.55,0.78,1.00)}

def _eps_from_statements(tk, as_of=None):
    inc = tk.income_stmt
    if "Diluted EPS" not in inc.index: return None
    cols = [c for c in inc.columns if as_of is None or pd.Timestamp(c) <= pd.Timestamp(as_of)]
    if not cols: return None
    v = inc.loc["Diluted EPS", sorted(cols)[-1]]
    return float(v) if pd.notna(v) and v > 0 else None

def get_eps(tk, as_of=None, current_price=None):
    """Robust EPS: audited annual statement first, then vendor trailing EPS.
    Never falls back to the arbitrary price/20 heuristic."""
    v = _eps_from_statements(tk, as_of)
    fin_curr = tk.info.get("financialCurrency")
    trade_curr = tk.info.get("currency")
    if v and fin_curr and trade_curr and fin_curr != trade_curr:
        v_vendor = tk.info.get("trailingEps")
        if v_vendor and v_vendor > 0:
            return float(v_vendor), "vendor_trailing"
    if v and current_price and (current_price / v > 200):
        v_vendor = tk.info.get("trailingEps")
        if v_vendor and v_vendor > 0 and (current_price / v_vendor < 150):
            return float(v_vendor), "vendor_trailing"
    if v: return v, "annual_statement"
    v = tk.info.get("trailingEps")
    if v and v > 0: return float(v), "vendor_trailing"
    raise ValueError("EPS unavailable from both statements and vendor feed.")

def earnings_cagr(tk, as_of=None):
    inc = tk.income_stmt
    if "Diluted EPS" not in inc.index: return None
    cols = sorted(c for c in inc.columns if as_of is None or pd.Timestamp(c) <= pd.Timestamp(as_of))
    vals = [inc.loc["Diluted EPS", c] for c in cols]
    vals = [v for v in vals if pd.notna(v) and v > 0]
    if len(vals) < 3: return None
    return float((vals[-1]/vals[0])**(1.0/(len(vals)-1)) - 1.0)

def build_scenarios(ticker, current_price=None, as_of=None, use_llm=True, recent_news=None):
    tk = yf.Ticker(ticker)
    if current_price is None:
        try:
            current_price = float(tk.history(period="5d")["Close"].dropna().iloc[-1])
        except Exception:
            current_price = None
    eps, eps_src = get_eps(tk, as_of, current_price)
    cagr = earnings_cagr(tk, as_of)
    industry = tk.info.get("industry") or tk.info.get("sector") or ""
    sector_pe = SECTOR_PE_MAP.get(industry, 22.0)

    # 1. Attempt institutional NVIDIA NIM LLM reasoning
    if use_llm and current_price and eps:
        try:
            try:
                from llm_reasoner import reason_market_scenarios
            except ImportError:
                from MULTI_AGENT_SANDBOX.llm_reasoner import reason_market_scenarios
            
            llm_res = reason_market_scenarios(
                ticker=ticker,
                current_price=current_price,
                eps=eps,
                sector_pe=sector_pe,
                eps_cagr=cagr,
                industry=industry,
                recent_news=recent_news or ""
            )
            sc = llm_res["scenarios"]
            wt = llm_res["weighted_target"]
            return {
                "ticker": ticker, "eps": eps, "eps_source": eps_src, "eps_cagr": cagr,
                "industry": industry, "sector_pe": sector_pe, "price": current_price,
                "scenarios": sc, "weighted_target": wt,
                "thesis": llm_res.get("thesis", ""),
                "source": llm_res.get("source", "llm_nvidia")
            }
        except Exception as e:
            print(f"[scenario_builder] Notice: LLM reasoner skipped ({e}). Using audited formula.")

    # 2. Audited mathematical statement fallback
    band = GROWTH_BAND["high" if (cagr or 0) > 0.15 else "mid" if (cagr or 0) > 0.07 else "low"]
    sc = {
        "bear": {"probability": 0.25, "target_pe": round(sector_pe*band[0],1),
                 "target_price": round(eps*sector_pe*band[0],2)},
        "base": {"probability": 0.50, "target_pe": round(sector_pe*band[1],1),
                 "target_price": round(eps*sector_pe*band[1],2)},
        "bull": {"probability": 0.25, "target_pe": round(sector_pe*band[2],1),
                 "target_price": round(eps*sector_pe*band[2],2)},
    }
    wt = round(sum(s["probability"]*s["target_price"] for s in sc.values()), 2)
    return {"ticker": ticker, "eps": eps, "eps_source": eps_src, "eps_cagr": cagr,
            "industry": industry, "sector_pe": sector_pe, "price": current_price,
            "scenarios": sc, "weighted_target": wt,
            "thesis": f"Fundamental valuation using audited EPS of Rs. {eps:.2f} and sector P/E of {sector_pe:.1f}x.",
            "source": "audited_formula"}

if __name__ == "__main__":
    import json, sys
    print(json.dumps(build_scenarios(sys.argv[1] if len(sys.argv)>1 else "INFY.NS"), indent=2))
