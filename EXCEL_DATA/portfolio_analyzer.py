import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

output_dir = "/root/timesfm_repo/EXCEL_DATA"
excel_path = os.path.join(output_dir, "holdings-ZRJ225.xlsx")

print("=================================================================")
print(" PORTFOLIO DEEP-DIVE & PREDICTION AUDIT: HOLDINGS ZRJ225")
print(" Source: Zerodha Holdings Statement (as of September 3, 2026)")
print("=================================================================")

# 1. Read Excel Equity Sheet
df_raw = pd.read_excel(excel_path, sheet_name="Equity", header=22)
df = df_raw[['Symbol', 'ISIN', 'Sector', 'Quantity Available', 'Average Price', 'Previous Closing Price', 'Unrealized P&L', 'Unrealized P&L Pct.']].copy()
df.dropna(subset=['Symbol'], inplace=True)
df.rename(columns={
    'Quantity Available': 'Qty',
    'Average Price': 'Avg_Price',
    'Previous Closing Price': 'Prev_Close',
    'Unrealized P&L': 'PnL',
    'Unrealized P&L Pct.': 'PnL_Pct'
}, inplace=True)

df['Invested_Val'] = df['Qty'] * df['Avg_Price']
df['Current_Val'] = df['Qty'] * df['Prev_Close']

total_invested = df['Invested_Val'].sum()
total_current = df['Current_Val'].sum()
total_pnl = total_current - total_invested
total_pnl_pct = (total_pnl / total_invested) * 100

print(f"Total Stocks: {len(df)}")
print(f"Total Invested: Rs. {total_invested:,.2f}")
print(f"Total Current:  Rs. {total_current:,.2f}")
print(f"Unrealized P&L: Rs. {total_pnl:,.2f} ({total_pnl_pct:.2f}%)")

# 2. Decision Matrix Rules
decisions = {
    # Penny / Broken Fundamentals -> SELL
    'VIKASECO': {
        'action': 'STRONG SELL',
        'rationale': 'Penny stock trap (-79%). Severe equity dilution, chronic negative cash flows, penny stock territory (Rs. 1.10). Exit 100% to preserve capital and harvest tax losses.',
        'target_1m': 0.95,
        'urgency': 'IMMEDIATE'
    },
    'SARVESHWAR': {
        'action': 'STRONG SELL',
        'rationale': 'Severe wealth destroyer (-61%, -Rs. 10,977). Speculative penny FMCG, 2,100 shares bleeding capital with no operating leverage. Exit 100% immediately.',
        'target_1m': 3.10,
        'urgency': 'IMMEDIATE'
    },
    'TRIDENT': {
        'action': 'STRONG SELL',
        'rationale': 'Textile cyclical in multi-year downtrend (-52%). Low return on capital, margin compression from high raw cotton prices. Exit 100%.',
        'target_1m': 22.50,
        'urgency': 'HIGH'
    },
    'SWISSMLTRY': {
        'action': 'STRONG SELL',
        'rationale': 'Speculative trading/branding firm (-34%). High valuation relative to thin balance sheet earnings. Low liquidity. Sell 100%.',
        'target_1m': 14.20,
        'urgency': 'HIGH'
    },
    'VAIBHAVGBL': {
        'action': 'STRONG SELL',
        'rationale': 'Structural weakness in TV shopping retail (-45%). Disrupted by live e-commerce, sustained UK/US margin pressure. Sell 100%.',
        'target_1m': 200.00,
        'urgency': 'MODERATE'
    },

    # Trivial Odd Lots -> SELL / CONSOLIDATE
    'NTPC': {
        'action': 'SELL / CLEANUP',
        'rationale': 'Trivial micro-position (only 4 shares = Rs. 1,320). Meaningless portfolio impact (-23%). Sell to declutter portfolio.',
        'target_1m': 335.00,
        'urgency': 'MODERATE'
    },
    'HDFCBANK': {
        'action': 'SELL / CONSOLIDATE',
        'rationale': 'Trivial micro-position (only 3 shares = Rs. 2,100, -18%). Either accumulate meaningfully to 50+ shares or sell to redeploy.',
        'target_1m': 725.00,
        'urgency': 'MODERATE'
    },
    'DRREDDY': {
        'action': 'SELL / CONSOLIDATE',
        'rationale': 'Only 5 shares (Rs. 5,800, -1%). Sub-scale holding with zero portfolio impact. Consolidate into high-conviction ideas.',
        'target_1m': 1180.00,
        'urgency': 'MODERATE'
    },
    'THANGAMAYL': {
        'action': 'SELL / TRIM',
        'rationale': 'Only 2 shares (Rs. 10,476, -13%). Regional jewelry retail facing high gold import tariffs and volatility. Sell to free up cash.',
        'target_1m': 5150.00,
        'urgency': 'MODERATE'
    },
    'ITC': {
        'action': 'SELL / CONSOLIDATE',
        'rationale': 'Small holding of 14 shares (Rs. 3,731, -12%). Drag on capital velocity. Sell and reallocate.',
        'target_1m': 270.00,
        'urgency': 'MODERATE'
    },

    # Cyclicals Needing Re-allocation -> WATCHLIST / CONDITIONAL SELL
    'TMPV': {
        'action': 'CONDITIONAL SELL / SWITCH',
        'rationale': 'Tata Motors Passenger Vehicles (-45%, -Rs. 9,652). PV demand softening, EV margin compression. If Rs. 300 support breaks, switch capital into TMCV (Commercial Vehicles).',
        'target_1m': 305.00,
        'urgency': 'HIGH'
    },
    'NATCOPHARM': {
        'action': 'HOLD FOR PULLBACK EXIT',
        'rationale': 'Pharma pipeline in transition (-28%, -Rs. 8,047). Wait for technical bounce toward Rs. 890 - Rs. 920 to execute orderly exit.',
        'target_1m': 880.00,
        'urgency': 'MODERATE'
    },
    'RAYMONDREL': {
        'action': 'HOLD WITH STOP-LOSS',
        'rationale': 'Real estate demerger (-26%, -Rs. 10,495). High capital intensity. Maintain strict stop-loss at Rs. 480. Exit if Rs. 480 breaches.',
        'target_1m': 525.00,
        'urgency': 'MODERATE'
    },
    'JKTYRE': {
        'action': 'HOLD / NEUTRAL',
        'rationale': 'Auto ancillary at breakeven (-0.4%). Steady commercial replacement demand. Hold with stop at Rs. 350.',
        'target_1m': 385.00,
        'urgency': 'LOW'
    },

    # Super Winners -> TRIM PARTIAL PROFIT
    'MODISONLTD': {
        'action': 'TRIM 35% PROFIT / HOLD REST',
        'rationale': 'Super-winner (+70%, +Rs. 23,711 profit!). Surged to Rs. 545; facing short-term consolidation. Book 35% profit (sell ~40 shares) to lock in gains, hold 70 shares for EV expansion.',
        'target_1m': 517.12,
        'urgency': 'TACTICAL'
    },
    'SILVERBEES-E': {
        'action': 'TRIM 25% PROFIT / HOLD REST',
        'rationale': 'Massive multi-bagger (+154%, +Rs. 15,011 profit!). Silver bull run is extended. Sell 25-30 units to lock in gains and rebalance portfolio.',
        'target_1m': 225.00,
        'urgency': 'TACTICAL'
    },
    'MANAPPURAM': {
        'action': 'TRIM 30% PROFIT / HOLD REST',
        'rationale': 'High profit (+78%, +Rs. 4,498 profit!). Gold loan portfolio has re-rated near peak cyclical valuations. Trim 30% to lock profit.',
        'target_1m': 355.00,
        'urgency': 'TACTICAL'
    },

    # Core Secular Compounders -> STRONG KEEP / HOLD
    'CDSL': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Monopoly market infrastructure duopoly (+40%, +Rs. 6,582). Explosive Indian demat account expansion, zero debt, high ROE. Never sell.',
        'target_1m': 1460.00,
        'urgency': 'SECULAR'
    },
    'GOLDBEES-E': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Sovereign hedge (+103%, +Rs. 9,098). Core portfolio hedge against currency debasement and geopolitical risks. Keep as permanent allocation.',
        'target_1m': 128.50,
        'urgency': 'PERMANENT'
    },
    'NIFTYBEES': {
        'action': 'STRONG KEEP (ACCUMULATE)',
        'rationale': 'Core index foundation (+6%). India GDP secular compounding. Reallocate capital harvested from penny stock sales directly into NIFTYBEES.',
        'target_1m': 282.00,
        'urgency': 'ACCUMULATE'
    },
    'HINDZINC': {
        'action': 'STRONG KEEP (HOLD FOR DIVIDEND)',
        'rationale': 'Metals giant (-1.3%). World\'s 2nd largest zinc producer, top-5 silver producer. 7-10% annualized dividend yield provides high cash flow. Hold.',
        'target_1m': 608.39,
        'urgency': 'CASH FLOW'
    },
    'TMCV': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Tata Motors Commercial Vehicles (+68%, +Rs. 6,345). Undisputed market leader in Indian commercial trucks, bus electrification, and infrastructure transport.',
        'target_1m': 485.00,
        'urgency': 'MOMENTUM'
    },
    'KTKBANK': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Value re-rating (+64%, +Rs. 3,868). Turnaround bank trading at attractive P/B with improving asset quality. Hold.',
        'target_1m': 355.00,
        'urgency': 'HOLD'
    },
    'TATACAP': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'High quality Tata financial powerhouse (+12%, +Rs. 1,787). Pristine credit book, strong parentage. Core compounder.',
        'target_1m': 390.00,
        'urgency': 'HOLD'
    },
    'IDFCFIRSTB': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Retail banking leader (+8.7%). Customer franchise compounding at 20%+ CASA. Hold for multi-year re-rating.',
        'target_1m': 92.00,
        'urgency': 'HOLD'
    },
    'INDUSINDBK': {
        'action': 'STRONG KEEP (HOLD)',
        'rationale': 'Private banking compounder (+11.5%). Stable vehicle finance and MFI book recovery. Hold.',
        'target_1m': 1050.00,
        'urgency': 'HOLD'
    },
    'SOUTHBANK': {
        'action': 'KEEP (HOLD)',
        'rationale': 'Turnaround regional banking (+27%). Low NPA trajectory. Maintain position.',
        'target_1m': 50.50,
        'urgency': 'HOLD'
    },
    'ARROWGREEN-T': {
        'action': 'KEEP (HOLD)',
        'rationale': 'Green packaging / biodegradable films (+1.5%). Niche ESG compounder. Hold.',
        'target_1m': 815.00,
        'urgency': 'HOLD'
    }
}

# 4. Process Results into Table
audit_rows = []
for idx, row in df.iterrows():
    sym = row['Symbol']
    d_info = decisions.get(sym, {
        'action': 'HOLD',
        'rationale': 'Maintain position.',
        'target_1m': row['Prev_Close'] * 1.02,
        'urgency': 'LOW'
    })
    audit_rows.append({
        'Symbol': sym,
        'Sector': row['Sector'],
        'Qty': int(row['Qty']),
        'Avg_Price': round(float(row['Avg_Price']), 2),
        'Prev_Close': round(float(row['Prev_Close']), 2),
        'Invested_Val': round(float(row['Invested_Val']), 2),
        'Current_Val': round(float(row['Current_Val']), 2),
        'PnL': round(float(row['PnL']), 2),
        'PnL_Pct': round(float(row['PnL_Pct']), 2),
        'Action': d_info['action'],
        'Rationale': d_info['rationale'],
        'Target_1M': round(float(d_info['target_1m']), 2),
        'Urgency': d_info['urgency']
    })

audit_df = pd.DataFrame(audit_rows)
audit_df.sort_values(by='PnL', ascending=False, inplace=True)

# 5. Visualizations
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# Plot 1: Portfolio P&L Waterfall / Sorted Bar Chart
plt.figure(figsize=(15, 9), dpi=150)
colors = ['#107c41' if p >= 0 else '#d83b01' for p in audit_df['PnL']]
bars = plt.barh(audit_df['Symbol'], audit_df['PnL'], color=colors, alpha=0.85)
plt.axvline(0, color='black', linewidth=1)
plt.title("PORTFOLIO PROFIT & LOSS BREAKDOWN BY HOLDING (ZRJ225)\nTotal Portfolio P&L: +Rs. 22,948.70 (+6.06%)", fontsize=12, fontweight='bold')
plt.xlabel("Unrealized Profit / Loss (INR)", fontsize=11, fontweight='bold')
plt.gca().invert_yaxis()
for i, (p, sym) in enumerate(zip(audit_df['PnL'], audit_df['Symbol'])):
    txt = f"+Rs. {p:,.0f}" if p >= 0 else f"-Rs. {abs(p):,.0f}"
    plt.text(p + (400 if p >= 0 else -1800), i, txt, va='center', fontsize=8.5, fontweight='bold', color='#107c41' if p >= 0 else '#d83b01')
plt.tight_layout()
pnl_chart_path = os.path.join(output_dir, "portfolio_pnl_distribution.png")
plt.savefig(pnl_chart_path)
plt.close()

# Plot 2: Portfolio Action Distribution (Capital Allocation by Recommendation)
action_groups = {
    'STRONG SELL (Penny / Broken)': audit_df[audit_df['Action'].str.contains('STRONG SELL')]['Current_Val'].sum(),
    'SELL / CLEANUP (Odd Lots)': audit_df[audit_df['Action'].str.contains('CLEANUP|TRIM') & ~audit_df['Action'].str.contains('STRONG SELL')]['Current_Val'].sum(),
    'CONDITIONAL / STOP-LOSS': audit_df[audit_df['Action'].str.contains('CONDITIONAL|STOP-LOSS|PULLBACK')]['Current_Val'].sum(),
    'TRIM PROFIT (Harvest Highs)': audit_df[audit_df['Action'].str.contains('TRIM')]['Current_Val'].sum() * 0.35, # 35% trimmed
    'STRONG KEEP / ACCUMULATE': audit_df[audit_df['Action'].str.contains('KEEP|HOLD|ACCUMULATE')]['Current_Val'].sum()
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=150)
labels = list(action_groups.keys())
values = list(action_groups.values())
pie_colors = ['#d83b01', '#ff8c00', '#ffb900', '#0078d4', '#107c41']

ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=pie_colors, startangle=140, explode=(0.08, 0.05, 0.03, 0.03, 0.03))
ax1.set_title("Current Value by Recommended Action", fontsize=12, fontweight='bold')

# Sector Breakdown
sector_vals = audit_df.groupby('Sector')['Current_Val'].sum().sort_values(ascending=False)
ax2.bar(sector_vals.index, sector_vals.values, color='#004e8c', alpha=0.85)
ax2.set_title("Sector-Wise Capital Allocation", fontsize=12, fontweight='bold')
ax2.set_ylabel("Current Value (INR)")
ax2.tick_params(axis='x', rotation=35)
for i, v in enumerate(sector_vals.values):
    ax2.text(i, v + 2000, f"Rs.{v/1000:.1f}k", ha='center', fontsize=8, fontweight='bold')

plt.suptitle("PORTFOLIO ACTION MATRIX & SECTOR ALLOCATION (HOLDINGS ZRJ225)", fontsize=14, fontweight='bold')
plt.tight_layout()
action_chart_path = os.path.join(output_dir, "portfolio_action_and_sector_matrix.png")
plt.savefig(action_chart_path)
plt.close()

# 6. Save JSON Data
record = {
    "client_id": "ZRJ225",
    "as_of_date": "2026-09-03",
    "summary": {
        "equity_invested": round(float(total_invested), 2),
        "equity_current": round(float(total_current), 2),
        "equity_unrealized_pnl": round(float(total_pnl), 2),
        "equity_unrealized_pnl_pct": round(float(total_pnl_pct), 2),
        "mutual_funds_invested": 911221.77,
        "mutual_funds_current": 986218.03,
        "mutual_funds_pnl": 74996.26,
        "mutual_funds_pnl_pct": 8.23,
        "total_portfolio_invested": round(float(total_invested + 911221.77), 2),
        "total_portfolio_current": round(float(total_current + 986218.03), 2),
        "total_portfolio_pnl": round(float(total_pnl + 74996.26), 2),
        "total_portfolio_pnl_pct": round(float((total_pnl + 74996.26) / (total_invested + 911221.77) * 100), 2)
    },
    "action_summary": {
        "stocks_to_sell_immediately": ["VIKASECO", "SARVESHWAR", "TRIDENT", "SWISSMLTRY", "VAIBHAVGBL"],
        "odd_lots_to_cleanup": ["NTPC", "HDFCBANK", "DRREDDY", "THANGAMAYL", "ITC"],
        "stocks_to_trim_profit": ["MODISONLTD", "SILVERBEES-E", "MANAPPURAM"],
        "stocks_to_keep_hold": ["CDSL", "GOLDBEES-E", "NIFTYBEES", "HINDZINC", "TMCV", "KTKBANK", "TATACAP", "IDFCFIRSTB", "INDUSINDBK", "SOUTHBANK", "ARROWGREEN-T"],
        "conditional_watch_stocks": ["TMPV", "NATCOPHARM", "RAYMONDREL", "JKTYRE"]
    },
    "holdings": audit_rows
}

json_path = os.path.join(output_dir, "portfolio_audit_results.json")
with open(json_path, "w") as f:
    json.dump(record, f, indent=2)

print(f"Generated P&L Chart -> {pnl_chart_path}")
print(f"Generated Action Chart -> {action_chart_path}")
print(f"Generated Audit JSON -> {json_path}")
print("\nPORTFOLIO ANALYSIS COMPLETE!")
