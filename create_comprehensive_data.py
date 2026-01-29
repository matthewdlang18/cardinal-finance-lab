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

# Read raw S&P 500 data from Damodaran's Excel for price-only vs total returns
print("\nLoading S&P 500 raw data from histretSP.xls...")
df_raw = pd.read_excel('histretSP.xls', sheet_name='S&P 500 & Raw Data', header=None, skiprows=2)
df_raw.columns = ['Year', 'SP500', 'Dividends', 'DividendYield', 'TBondRate', 'BondReturn',
                  'AaaBondRate', 'AaaReturn', 'BaaBondRate', 'BaaReturn', 'RealEstateReturn']
df_raw = df_raw[df_raw['Year'].notna() & (df_raw['Year'] >= 1928)]
df_raw = df_raw.dropna(subset=['SP500'])

# Calculate both price-only and total returns from raw data
sp_price_returns = []  # Price-only returns (no dividends)
sp_total_returns = []  # Total returns (with dividends)

for i in range(1, len(df_raw)):
    year = int(df_raw.iloc[i]['Year'])
    prev_sp = df_raw.iloc[i-1]['SP500']
    curr_sp = df_raw.iloc[i]['SP500']
    dividends = df_raw.iloc[i]['Dividends']

    # Price-only return
    price_ret = ((curr_sp - prev_sp) / prev_sp) * 100
    sp_price_returns.append({
        'year': str(year),
        'return': round(price_ret, 2)
    })

    # Total return (with dividends)
    total_ret = ((curr_sp - prev_sp + dividends) / prev_sp) * 100
    sp_total_returns.append({
        'year': str(year),
        'return': round(total_ret, 2)
    })

print(f"  ✓ Calculated {len(sp_price_returns)} years of price-only returns")
print(f"  ✓ Calculated {len(sp_total_returns)} years of total returns (with dividends)")

# Read S&P returns data from CSV for bonds
print("\nLoading bond returns data...")
df = pd.read_csv('spreturns.csv')

# Use total returns for SPX (the CSV already has total returns now)
sp_returns = sp_total_returns  # Use the total returns we calculated
sp_quarterly = []
quarters_data = []

for r in sp_returns:
    year = int(r['year'])
    sp_return = r['return']

    # Group by quarter for quarterly returns
    for q in range(1, 5):
        quarter_key = f"{year}Q{q}"
        quarters_data.append({
            'quarter': quarter_key,
            'return': sp_return / 4  # Approximate quarterly
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
variance = sum((r - mean) ** 2 for r in returns_values) / (len(returns_values) - 1)
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
    variance = sum((r - mean) ** 2 for r in ret_values) / (len(ret_values) - 1)
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

# Calculate rolling returns for S&P 500 - BOTH price-only and total returns
print("\nCalculating rolling returns for S&P 500...")

def calculate_rolling_returns(returns_list, periods):
    """Calculate rolling returns for given periods."""
    rolling_data = {}
    for period in periods:
        rolling_returns = []
        for i in range(period, len(returns_list) + 1):
            period_returns = returns_list[i-period:i]
            cumulative = 1.0
            for ret in period_returns:
                cumulative *= (1 + ret / 100)
            annualized = (cumulative ** (1/period) - 1) * 100
            rolling_returns.append(round(annualized, 2))
        rolling_data[f'period{period}'] = rolling_returns
    return rolling_data

periods = [1, 5, 10, 20, 30]

# Total returns (with dividends) - the default
total_annual_returns = [r['return'] for r in sp_total_returns]
rolling_data_total = calculate_rolling_returns(total_annual_returns, periods)
print("  Total returns (with dividends):")
for period in periods:
    print(f"    ✓ {period}-year rolling: {len(rolling_data_total[f'period{period}'])} data points")

# Price-only returns (without dividends)
price_annual_returns = [r['return'] for r in sp_price_returns]
rolling_data_price = calculate_rolling_returns(price_annual_returns, periods)
print("  Price-only returns:")
for period in periods:
    print(f"    ✓ {period}-year rolling: {len(rolling_data_price[f'period{period}'])} data points")

# Use total returns as the primary rolling_data (backwards compatible)
rolling_data = rolling_data_total

# Add rolling returns to the data structure - includes both price-only and total returns
stock_data['_ROLLING_RETURNS_'] = {
    'name': 'S&P 500 Rolling Returns',
    'description': 'Pre-calculated rolling returns for S&P 500',
    'periods': rolling_data_total,  # Total returns (with dividends) - default
    'periodsTotal': rolling_data_total,  # Total returns (with dividends)
    'periodsPriceOnly': rolling_data_price,  # Price-only returns (no dividends)
    'startYear': sp_total_returns[0]['year'],
    'endYear': sp_total_returns[-1]['year']
}

# Also add the price-only annual returns to SPX for completeness
stock_data['SPX']['annualReturnsPriceOnly'] = sp_price_returns

# Save comprehensive data
output_file = 'comprehensive_stock_data.json'
with open(output_file, 'w') as f:
    json.dump(stock_data, f, indent=2)

print(f"\n✓ Saved comprehensive data to {output_file}")
print(f"📊 Total entries: {len(stock_data)} (stocks + indices + bonds)")
print(f"📈 S&P 500: {len(sp_total_returns)} years (1929-2025)")
print(f"🔄 Rolling returns (total): {sum(len(v) for v in rolling_data_total.values())} data points")
print(f"🔄 Rolling returns (price-only): {sum(len(v) for v in rolling_data_price.values())} data points")
