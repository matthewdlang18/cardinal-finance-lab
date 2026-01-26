#!/usr/bin/env python3
"""
Create comprehensive stock data file combining individual stocks and market indices.
"""

import json
import pandas as pd

# Read the existing stock data
print("Loading stock data...")
with open('stock_data.json', 'r') as f:
    stock_data = json.load(f)

print(f"Loaded {len(stock_data)} stocks")

# Read S&P returns data
print("\nLoading S&P returns data...")
df = pd.read_csv('spreturns.csv')

# Convert to annual returns format
sp_returns = []
sp_quarterly = []
prev_value = None
quarters_data = []

for _, row in df.iterrows():
    date = pd.to_datetime(row['Date'])
    year = date.year
    sp_return = row['SP Returns'] * 100  # Convert to percentage
    sp_returns.append({
        'year': str(year),
        'return': round(sp_return, 2)
    })

    # Group by quarter for quarterly returns
    quarter = (date.month - 1) // 3 + 1
    quarter_key = f"{year}Q{quarter}"
    quarters_data.append({
        'quarter': quarter_key,
        'return': sp_return
    })

# Calculate quarterly returns for S&P
# Since we have annual data, approximate quarterly by dividing by 4
for i in range(1, len(sp_returns)):
    year = int(sp_returns[i]['year'])
    annual_ret = sp_returns[i]['return']
    # Approximate quarterly return (not compounded)
    quarterly_approx = annual_ret / 4
    for q in range(1, 5):
        sp_quarterly.append({
            'quarter': f"{year}Q{q}",
            'return': round(quarterly_approx, 2)
        })

# Calculate stats for S&P
returns_values = [r['return'] for r in sp_returns]
mean = sum(returns_values) / len(returns_values)
variance = sum((r - mean) ** 2 for r in returns_values) / len(returns_values)
std_dev = variance ** 0.5

sp_stats = {
    'mean': round(mean, 2),
    'stdDev': round(std_dev, 2),
    'min': round(min(returns_values), 2),
    'max': round(max(returns_values), 2),
    'count': len(returns_values)
}

# Add S&P 500 index data (overwrite if exists)
stock_data['SPX'] = {
    'name': 'S&P 500 Index',
    'sector': 'Market Index',
    'annualReturns': sp_returns,
    'quarterlyReturns': sp_quarterly,
    'stats': sp_stats,
    'dataPoints': len(sp_returns),
    'startYear': sp_returns[0]['year'],
    'endYear': sp_returns[-1]['year']
}

print(f"✓ Added S&P 500 Index: {len(sp_returns)} years ({sp_returns[0]['year']}-{sp_returns[-1]['year']})")

# Add bond data
bond_types = {
    '3-month T.Bill': ('TBILL', '3-Month Treasury Bill'),
    'US T. Bond (10-year)': ('TBOND10', '10-Year Treasury Bond'),
    ' Baa Corporate Bond': ('BAACORP', 'Baa Corporate Bond')
}

for col_name, (ticker, full_name) in bond_types.items():
    returns = []
    quarterly = []

    for _, row in df.iterrows():
        year = pd.to_datetime(row['Date']).year
        ret = row[col_name] * 100  # Convert to percentage
        returns.append({
            'year': str(year),
            'return': round(ret, 2)
        })

    # Create synthetic quarterly data (approximate by dividing annual by 4)
    for i in range(1, len(returns)):
        year = int(returns[i]['year'])
        annual_ret = returns[i]['return']
        quarterly_approx = annual_ret / 4
        for q in range(1, 5):
            quarterly.append({
                'quarter': f"{year}Q{q}",
                'return': round(quarterly_approx, 2)
            })

    # Calculate stats
    ret_values = [r['return'] for r in returns]
    mean = sum(ret_values) / len(ret_values)
    variance = sum((r - mean) ** 2 for r in ret_values) / len(ret_values)
    std_dev = variance ** 0.5

    stats = {
        'mean': round(mean, 2),
        'stdDev': round(std_dev, 2),
        'min': round(min(ret_values), 2),
        'max': round(max(ret_values), 2),
        'count': len(ret_values)
    }

    stock_data[ticker] = {
        'name': full_name,
        'sector': 'Fixed Income',
        'annualReturns': returns,
        'quarterlyReturns': quarterly,
        'stats': stats,
        'dataPoints': len(returns),
        'startYear': returns[0]['year'],
        'endYear': returns[-1]['year']
    }

    print(f"✓ Added {full_name}: {len(returns)} years, {len(quarterly)} quarters")

# Calculate rolling returns for S&P 500
print("\nCalculating rolling returns for S&P 500...")

# Get annual returns as a list
annual_returns = [r['return'] for r in sp_returns]

rolling_data = {}
periods = [1, 5, 10, 20, 30]

for period in periods:
    rolling_returns = []

    for i in range(period, len(annual_returns) + 1):
        # Get the returns for this period
        period_returns = annual_returns[i-period:i]

        # Calculate annualized return
        # Convert percentages to decimal, compound, then annualize
        cumulative = 1.0
        for ret in period_returns:
            cumulative *= (1 + ret / 100)

        annualized = (cumulative ** (1/period) - 1) * 100
        rolling_returns.append(round(annualized, 2))

    rolling_data[f'period{period}'] = rolling_returns
    print(f"  ✓ {period}-year rolling: {len(rolling_returns)} data points")

# Add rolling returns to the data structure
stock_data['_ROLLING_RETURNS_'] = {
    'name': 'S&P 500 Rolling Returns',
    'description': 'Pre-calculated rolling returns for S&P 500',
    'periods': rolling_data,
    'startYear': sp_returns[0]['year'],
    'endYear': sp_returns[-1]['year']
}

# Save comprehensive data
output_file = 'comprehensive_stock_data.json'
with open(output_file, 'w') as f:
    json.dump(stock_data, f, indent=2)

print(f"\n✓ Saved comprehensive data to {output_file}")
print(f"📊 Total entries: {len(stock_data)} (stocks + indices + bonds)")
print(f"📈 S&P 500: {len(sp_returns)} years (1928-2025)")
print(f"🔄 Rolling returns: {sum(len(v) for v in rolling_data.values())} total data points")
