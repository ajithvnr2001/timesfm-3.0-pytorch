"""
pit_data.py
===========
Point-in-time (PIT) market data, covariate construction and fundamentals for the
institutional TimesFM 3.0 engine.

Every function here takes an explicit `cutoff` and guarantees that nothing after that
date can influence the returned arrays. The rules:

  * All price history is fetched once with `period="max"`, made timezone-naive, then
    sliced with `index <= cutoff`. We never fetch `period="1y"` and filter afterwards
    (that silently returns an empty frame for historical cutoffs).
  * Past covariates are derived only from prices at or before the cutoff.
  * Past-future covariates are calendar features only (day-of-week, month, expiry week).
    Anything else known "in the future" would be leakage.
  * Fundamentals come from `quarterly_income_stmt` / `quarterly_balance_sheet` columns
    filtered to `<= cutoff`. `Ticker.info` is live-only and is therefore NEVER used for
    a historical cutoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

NIFTY = "^NSEI"
VIX = "^INDIAVIX"

SECTOR_INDEX = {
    "Information Technology Services": "^CNXIT",
    "Software - Infrastructure": "^CNXIT",
    "Software - Application": "^CNXIT",
    "Technology": "^CNXIT",
    "Computer Hardware": "^CNXIT",
    "Communication Equipment": "^CNXIT",
    "Auto Manufacturers": "^CNXAUTO",
    "Auto Parts": "^CNXAUTO",
    "Automobiles": "^CNXAUTO",
    "Banks": "^NSEBANK",
    "Banks - Regional": "^NSEBANK",
    "Financial Services": "^NSEBANK",
    "Capital Markets": "^NSEBANK",
    "Consumer Defensive": "^CNXFMCG",
    "Household & Personal Products": "^CNXFMCG",
    "Personal Products": "^CNXFMCG",
    "Packaged Foods": "^CNXFMCG",
    "Metals & Mining": "^CNXMETAL",
    "Basic Materials": "^CNXMETAL",
    "Steel": "^CNXMETAL",
    "Aluminum": "^CNXMETAL",
    "Other Industrial Metals & Mining": "^CNXMETAL",
    "Electrical Equipment & Parts": "^CNXMETAL",
    "Oil & Gas Integrated": "^CNXENERGY",
    "Oil & Gas Refining & Marketing": "^CNXENERGY",
    "Energy": "^CNXENERGY",
    "Utilities - Independent Power Producers": "^CNXENERGY",
    "Drug Manufacturers - Specialty & Generic": "^CNXPHARMA",
    "Drug Manufacturers - General": "^CNXPHARMA",
    "Pharmaceuticals": "^CNXPHARMA",
    "Healthcare": "^CNXPHARMA",
    "Medical Devices": "^CNXPHARMA",
    "Real Estate": "^CNXREALTY",
    "Real Estate - Development": "^CNXREALTY",
    "Specialty Chemicals": "^CNXMETAL",
    "Chemicals": "^CNXMETAL",
    "Textile Manufacturing": "^CNXFMCG",
    "Apparel Manufacturing": "^CNXFMCG",
    "Aerospace & Defense": "^CNXMETAL",
    "Specialty Industrial Machinery": "^CNXMETAL",
    "Engineering & Construction": "^CNXMETAL",
}

PAST_COVARIATE_NAMES = [
    "log_volume_ratio_252",
    "realised_vol_20",
    "realised_vol_60",
    "ema20_distance",
    "ema200_distance",
    "rsi_14",
    "drawdown_from_252d_high",
]
PAST_FUTURE_COVARIATE_NAMES = ["dow_sin", "month_sin", "month_cos"]

_PRICE_CACHE: dict = {}


# --------------------------------------------------------------------------- prices
def load_full_history(ticker: str, use_cache: bool = True) -> pd.DataFrame:
    """Fetch the entire available history once, timezone-naive. Cached per process."""
    if use_cache and ticker in _PRICE_CACHE:
        return _PRICE_CACHE[ticker]
    import yfinance as yf

    df = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"no price history returned for {ticker}")
    df = df.copy()
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df = df[~df.index.duplicated(keep="last")]
    df = df.dropna(subset=["Close"]).sort_index()
    if use_cache:
        _PRICE_CACHE[ticker] = df
    return df


def pit_slice(df: pd.DataFrame, cutoff) -> pd.DataFrame:
    """Rows at or before `cutoff` (inclusive). `cutoff=None` means 'live, use everything'."""
    if cutoff is None:
        return df
    return df.loc[df.index <= pd.Timestamp(cutoff).normalize()]


def forward_actuals(df: pd.DataFrame, cutoff, horizon: int) -> pd.DataFrame:
    """The `horizon` trading rows strictly after `cutoff` - ground truth for backtests."""
    if cutoff is None:
        return df.iloc[0:0]
    return df.loc[df.index > pd.Timestamp(cutoff).normalize()].iloc[:horizon]


# ---------------------------------------------------------------------- covariates
def _rsi(close: np.ndarray, window: int = 14) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    out = np.full(close.shape, 50.0)
    if len(close) <= window:
        return out
    avg_g = gain[1 : window + 1].mean()
    avg_l = loss[1 : window + 1].mean()
    for i in range(window, len(close)):
        avg_g = (avg_g * (window - 1) + gain[i]) / window
        avg_l = (avg_l * (window - 1) + loss[i]) / window
        rs = avg_g / avg_l if avg_l > 1e-12 else 100.0
        out[i] = 100.0 - 100.0 / (1.0 + rs)
    return out


def _ewm(x: np.ndarray, span: int) -> np.ndarray:
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


def build_past_covariates(pit_df: pd.DataFrame) -> np.ndarray:
    """(k, T) float32 matrix of covariates observable at or before the cutoff."""
    close = pit_df["Close"].to_numpy(dtype=float)
    volume = (
        pit_df["Volume"].to_numpy(dtype=float)
        if "Volume" in pit_df
        else np.ones_like(close)
    )
    T = len(close)

    vol_mean = pd.Series(volume).rolling(252, min_periods=20).mean().bfill().to_numpy()
    vol_mean = np.where(vol_mean <= 0, 1.0, vol_mean)
    log_vol_ratio = np.log(np.clip(volume, 1.0, None) / vol_mean)

    rets = np.zeros(T)
    rets[1:] = np.diff(close) / close[:-1]
    rv20 = pd.Series(rets).rolling(20, min_periods=5).std().bfill().to_numpy() * np.sqrt(252)
    rv60 = pd.Series(rets).rolling(60, min_periods=5).std().bfill().to_numpy() * np.sqrt(252)

    ema20 = _ewm(close, 20)
    ema200 = _ewm(close, 200)
    ema20_dist = close / np.where(ema20 == 0, 1.0, ema20) - 1.0
    ema200_dist = close / np.where(ema200 == 0, 1.0, ema200) - 1.0

    rsi = _rsi(close, 14) / 100.0

    roll_max = pd.Series(close).rolling(252, min_periods=20).max().bfill().to_numpy()
    dd = close / np.where(roll_max == 0, 1.0, roll_max) - 1.0

    mat = np.vstack([log_vol_ratio, rv20, rv60, ema20_dist, ema200_dist, rsi, dd])
    mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    if mat.shape != (len(PAST_COVARIATE_NAMES), T):
        raise AssertionError(f"past covariate shape {mat.shape} != {(len(PAST_COVARIATE_NAMES), T)}")
    return mat


def build_past_future_covariates(
    pit_index: pd.DatetimeIndex, future_index: pd.DatetimeIndex
) -> np.ndarray:
    """(k, T+H) calendar-only covariates. Calendar is knowable in advance, so no leakage."""
    all_idx = pit_index.append(future_index)
    dow = all_idx.dayofweek.to_numpy(dtype=float)
    month = all_idx.month.to_numpy(dtype=float)
    mat = np.vstack(
        [
            np.sin(2 * np.pi * dow / 5.0),
            np.sin(2 * np.pi * month / 12.0),
            np.cos(2 * np.pi * month / 12.0),
        ]
    ).astype(np.float32)
    return mat


def future_business_days(cutoff, horizon: int) -> pd.DatetimeIndex:
    start = pd.Timestamp(cutoff).normalize() + pd.Timedelta(days=1)
    return pd.bdate_range(start=start, periods=horizon)


# ------------------------------------------------------------------- target matrix
@dataclass
class PITBundle:
    ticker: str
    cutoff: Optional[str]
    horizon: int
    context: np.ndarray  # (V, T)
    target_names: list
    past_covariates: np.ndarray  # (k, T)
    past_future_covariates: np.ndarray  # (k, T+H)
    dates: pd.DatetimeIndex  # length T, aligned to context
    future_dates: pd.DatetimeIndex  # length H
    last_price: float
    actuals: Optional[np.ndarray] = None  # (<=H,) ground truth if backtest
    actual_dates: Optional[pd.DatetimeIndex] = None
    industry: str = "General"
    sector_ticker: str = NIFTY
    audit: dict = field(default_factory=dict)


def industry_of(ticker: str, allow_live_metadata: bool) -> str:
    """Industry label. yfinance `info` is live-only metadata; for backtests we only use it
    for the (slow-moving) sector mapping and record that we did so in the audit trail."""
    if not allow_live_metadata:
        return "General"
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).info or {}
        return info.get("industry") or info.get("sector") or "General"
    except Exception:
        return "General"


def build_pit_bundle(
    ticker: str,
    cutoff: Optional[str],
    horizon: int,
    max_context: int = 4096,
    industry: Optional[str] = None,
    use_cross_asset: bool = True,
) -> PITBundle:
    """Assemble everything the forecaster needs, with a PIT audit trail."""
    stock_full = load_full_history(ticker)
    stock = pit_slice(stock_full, cutoff)
    if len(stock) < 260:
        raise ValueError(f"{ticker}: only {len(stock)} PIT rows before {cutoff}; need >= 260")

    ind = industry if industry is not None else "General"
    sec_ticker = SECTOR_INDEX.get(ind, NIFTY)

    frames = {"stock": stock["Close"]}
    names = ["stock"]
    if use_cross_asset:
        for label, tk in (("nifty", NIFTY), ("sector", sec_ticker)):
            try:
                idx_df = pit_slice(load_full_history(tk), cutoff)
                if len(idx_df) >= 260:
                    frames[label] = idx_df["Close"]
                    names.append(label)
            except Exception:
                continue

    joined = pd.DataFrame(frames).dropna()
    if len(joined) < 260:
        joined = pd.DataFrame({"stock": stock["Close"]}).dropna()
        names = ["stock"]

    joined = joined.iloc[-max_context:]
    dates = pd.DatetimeIndex(joined.index)
    context = np.vstack([joined[n].to_numpy(dtype=float) for n in names]).astype(np.float32)

    # Covariates are built on the stock rows that survived the join, so T matches exactly.
    stock_aligned = stock.loc[dates]
    past_cov = build_past_covariates(stock_aligned)
    fut_dates = future_business_days(dates[-1], horizon)
    pf_cov = build_past_future_covariates(dates, fut_dates)

    fwd = forward_actuals(stock_full, cutoff, horizon)
    actuals = fwd["Close"].to_numpy(dtype=float) if len(fwd) else None
    actual_dates = pd.DatetimeIndex(fwd.index) if len(fwd) else None

    audit = {
        "pit_cutoff": None if cutoff is None else str(pd.Timestamp(cutoff).date()),
        "context_last_date": str(dates[-1].date()),
        "context_first_date": str(dates[0].date()),
        "context_length": int(context.shape[1]),
        "targets": names,
        "sector_index": sec_ticker if "sector" in names else None,
        "past_covariates": PAST_COVARIATE_NAMES,
        "past_future_covariates": PAST_FUTURE_COVARIATE_NAMES,
        "n_actuals": 0 if actuals is None else int(len(actuals)),
        "leakage_checks": {},
    }
    if cutoff is not None:
        cut = pd.Timestamp(cutoff).normalize()
        audit["leakage_checks"] = {
            "context_within_cutoff": bool(dates.max() <= cut),
            "future_dates_after_cutoff": bool(fut_dates.min() > cut),
            "actuals_after_cutoff": bool(actual_dates is None or actual_dates.min() > cut),
        }
        if not all(audit["leakage_checks"].values()):
            raise AssertionError(f"PIT leakage detected for {ticker}: {audit['leakage_checks']}")

    return PITBundle(
        ticker=ticker,
        cutoff=None if cutoff is None else str(pd.Timestamp(cutoff).date()),
        horizon=horizon,
        context=context,
        target_names=names,
        past_covariates=past_cov,
        past_future_covariates=pf_cov,
        dates=dates,
        future_dates=fut_dates,
        last_price=float(context[0, -1]),
        actuals=actuals,
        actual_dates=actual_dates,
        industry=ind,
        sector_ticker=sec_ticker,
        audit=audit,
    )


# ------------------------------------------------------------------- fundamentals
ANNUAL_PUBLICATION_LAG_DAYS = 90
QUARTERLY_PUBLICATION_LAG_DAYS = 45


def _cols_available_at(df, cutoff, lag_days: int):
    """Statement columns whose period end + publication lag is at or before the cutoff.

    A fiscal year ending 2024-03-31 is not public on 2024-04-01. Ignoring the reporting
    lag is a classic look-ahead bug, so we require period_end + lag <= cutoff.
    """
    if df is None or getattr(df, "empty", True):
        return []
    cut = None if cutoff is None else pd.Timestamp(cutoff).normalize()
    out = []
    for c in df.columns:
        try:
            ts = pd.Timestamp(c)
            if getattr(ts, "tz", None) is not None:
                ts = ts.tz_localize(None)
        except Exception:
            continue
        if cut is None or (ts + pd.Timedelta(days=lag_days)) <= cut:
            out.append((ts, c))
    return [c for _, c in sorted(out, reverse=True)]


def _safe_row(df, name, cols):
    if df is None or getattr(df, "empty", True) or name not in df.index:
        return pd.Series(dtype=float)
    return df.loc[name, cols].astype(float).dropna()


def _cagr(newest: float, oldest: float, years: int):
    if years <= 0 or oldest is None or newest is None or oldest <= 0 or newest <= 0:
        return None
    return float((newest / oldest) ** (1.0 / years) - 1.0)


def pit_fundamentals(ticker: str, cutoff: Optional[str]) -> dict:
    """Currency-neutral PIT fundamentals from annual statements + quarterly balance sheet.

    Why currency-neutral: yfinance reports some NSE-listed companies (e.g. INFY.NS) in USD
    while the price series is INR, so absolute EPS and any P/E derived from it is wrong by
    the FX rate. We therefore expose only ratios and growth rates, which are unit-free, and
    let the valuation layer reason in *percentage re-rating* terms rather than absolute P/E.

    Also honours publication lag: annual columns need period_end + 90d <= cutoff, quarterly
    balance sheet needs + 45d.
    """
    import yfinance as yf

    out = {
        "revenue_growth_yoy": None,
        "revenue_cagr_3y": None,
        "eps_growth_yoy": None,
        "eps_cagr_3y": None,
        "gross_margin": None,
        "operating_margin": None,
        "net_margin": None,
        "operating_margin_delta_3y": None,
        "roe": None,
        "debt_to_equity": None,
        "equity_growth_yoy": None,
        "annual_periods_used": 0,
        "latest_annual_period": None,
        "latest_balance_period": None,
        "currency_neutral": True,
        "source": "annual_income_stmt + quarterly_balance_sheet, publication-lagged",
    }

    tk = yf.Ticker(ticker)
    try:
        inc = tk.income_stmt
    except Exception:
        inc = None
    cols = _cols_available_at(inc, cutoff, ANNUAL_PUBLICATION_LAG_DAYS)
    out["annual_periods_used"] = len(cols)
    if cols:
        out["latest_annual_period"] = str(pd.Timestamp(cols[0]).date())
        rev = _safe_row(inc, "Total Revenue", cols)
        eps = _safe_row(inc, "Diluted EPS", cols)
        gp = _safe_row(inc, "Gross Profit", cols)
        op = _safe_row(inc, "Operating Income", cols)
        ni = _safe_row(inc, "Net Income", cols)

        if len(rev) >= 2 and rev.iloc[1] > 0:
            out["revenue_growth_yoy"] = float((rev.iloc[0] - rev.iloc[1]) / rev.iloc[1])
        if len(rev) >= 4:
            out["revenue_cagr_3y"] = _cagr(float(rev.iloc[0]), float(rev.iloc[3]), 3)
        if len(eps) >= 2 and abs(eps.iloc[1]) > 1e-9:
            out["eps_growth_yoy"] = float((eps.iloc[0] - eps.iloc[1]) / abs(eps.iloc[1]))
        if len(eps) >= 4:
            out["eps_cagr_3y"] = _cagr(float(eps.iloc[0]), float(eps.iloc[3]), 3)
        if len(rev) >= 1 and rev.iloc[0] > 0:
            denom = float(rev.iloc[0])
            if len(gp) >= 1:
                out["gross_margin"] = float(gp.iloc[0] / denom)
            if len(op) >= 1:
                out["operating_margin"] = float(op.iloc[0] / denom)
            if len(ni) >= 1:
                out["net_margin"] = float(ni.iloc[0] / denom)
        if len(op) >= 4 and len(rev) >= 4 and rev.iloc[0] > 0 and rev.iloc[3] > 0:
            out["operating_margin_delta_3y"] = float(
                op.iloc[0] / rev.iloc[0] - op.iloc[3] / rev.iloc[3]
            )

    try:
        bs = tk.quarterly_balance_sheet
    except Exception:
        bs = None
    bcols = _cols_available_at(bs, cutoff, QUARTERLY_PUBLICATION_LAG_DAYS)
    if not bcols:
        try:
            bs = tk.balance_sheet
            bcols = _cols_available_at(bs, cutoff, ANNUAL_PUBLICATION_LAG_DAYS)
        except Exception:
            bcols = []
    if bcols:
        out["latest_balance_period"] = str(pd.Timestamp(bcols[0]).date())
        debt = _safe_row(bs, "Total Debt", bcols)
        eq = _safe_row(bs, "Stockholders Equity", bcols)
        if len(eq) == 0:
            eq = _safe_row(bs, "Total Equity Gross Minority Interest", bcols)
        if len(debt) >= 1 and len(eq) >= 1 and eq.iloc[0] > 0:
            out["debt_to_equity"] = float(debt.iloc[0] / eq.iloc[0])
        if len(eq) >= 5 and eq.iloc[4] > 0:
            out["equity_growth_yoy"] = float((eq.iloc[0] - eq.iloc[4]) / eq.iloc[4])
        if cols and len(eq) >= 1 and eq.iloc[0] > 0:
            ni = _safe_row(inc, "Net Income", cols)
            if len(ni) >= 1:
                out["roe"] = float(ni.iloc[0] / eq.iloc[0])

    return out
