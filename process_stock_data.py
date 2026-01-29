#!/usr/bin/env python3
"""
Process daily stock data and calculate annual returns for S&P 500 companies.
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict
import glob

# Paths
DATA_DIR = "data/daily/us"
SP500_CSV = "sp500.csv"
OUTPUT_JSON = "stock_data.json"

def read_sp500_companies():
    """Read S&P 500 companies from CSV."""
    companies = {}
    with open(SP500_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row['Symbol'].upper()
            companies[symbol] = {
                'name': row['Name'],
                'sector': row['Sector']
            }
    return companies

def find_stock_file(ticker):
    """Find the stock data file for a given ticker."""
    # Check stocks and ETFs in nasdaq, nyse, and nysemkt
    patterns = [
        f"{DATA_DIR}/nasdaq stocks/*/{ticker.lower()}.us.txt",
        f"{DATA_DIR}/nyse stocks/*/{ticker.lower()}.us.txt",
        f"{DATA_DIR}/nysemkt stocks/*/{ticker.lower()}.us.txt",
        f"{DATA_DIR}/nasdaq etfs/*/{ticker.lower()}.us.txt",
        f"{DATA_DIR}/nyse etfs/*/{ticker.lower()}.us.txt",
        f"{DATA_DIR}/nysemkt etfs/*/{ticker.lower()}.us.txt"
    ]

    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

def parse_date(date_str):
    """Parse date string YYYYMMDD to datetime."""
    return datetime.strptime(date_str, '%Y%m%d')

def read_stock_data(filepath):
    """Read stock data from file."""
    prices = []
    with open(filepath, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 8:
                try:
                    date = parse_date(parts[2])
                    close = float(parts[7])
                    prices.append({'date': date, 'close': close})
                except (ValueError, IndexError):
                    continue
    return sorted(prices, key=lambda x: x['date'])

def calculate_quarterly_returns(prices):
    """Calculate quarterly returns (annualized)."""
    if not prices:
        return []

    # Group prices by quarter
    quarterly_prices = defaultdict(list)
    for price in prices:
        year = price['date'].year
        quarter = (price['date'].month - 1) // 3 + 1
        key = f"{year}Q{quarter}"
        quarterly_prices[key].append(price)

    # Calculate quarterly returns (annualized)
    quarters = sorted(quarterly_prices.keys())
    quarterly_returns = []

    for i in range(1, len(quarters)):
        prev_quarter = quarters[i-1]
        curr_quarter = quarters[i]

        # Use last price of each quarter
        prev_price = quarterly_prices[prev_quarter][-1]['close']
        curr_price = quarterly_prices[curr_quarter][-1]['close']

        if prev_price > 0:
            # Calculate quarterly return as percentage (not annualized to avoid extreme values)
            quarterly_return = ((curr_price - prev_price) / prev_price) * 100
            quarterly_returns.append({
                'quarter': curr_quarter,
                'return': round(quarterly_return, 2)
            })

    return quarterly_returns

def calculate_annual_returns(prices):
    """Calculate year-over-year returns."""
    if not prices:
        return []

    # Group prices by year
    yearly_prices = defaultdict(list)
    for price in prices:
        year = price['date'].year
        yearly_prices[year].append(price)

    # Calculate annual returns
    years = sorted(yearly_prices.keys())
    annual_returns = []

    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]

        # Use last price of each year
        prev_price = yearly_prices[prev_year][-1]['close']
        curr_price = yearly_prices[curr_year][-1]['close']

        if prev_price > 0:
            annual_return = ((curr_price - prev_price) / prev_price) * 100
            annual_returns.append({
                'year': str(curr_year),
                'return': round(annual_return, 2)
            })

    return annual_returns

def calculate_stats(annual_returns):
    """Calculate statistics from annual returns."""
    if not annual_returns:
        return None

    returns = [r['return'] for r in annual_returns]
    mean = sum(returns) / len(returns)

    # Calculate standard deviation (sample std dev with n-1)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = variance ** 0.5

    return {
        'mean': round(mean, 2),
        'stdDev': round(std_dev, 2),
        'min': round(min(returns), 2),
        'max': round(max(returns), 2),
        'count': len(returns)
    }

def main():
    print("Processing S&P 500 stock data...")

    # Read S&P 500 companies
    companies = read_sp500_companies()
    print(f"Found {len(companies)} S&P 500 companies")

    # Add SPY (S&P 500 ETF) as benchmark
    companies['SPY'] = {'name': 'S&P 500 ETF', 'sector': 'ETF'}

    # Add some important historical companies that may have been delisted
    additional_tickers = ['GE', 'T', 'XOM', 'WMT', 'JPM', 'BAC', 'C', 'PG', 'KO', 'PEP']
    for ticker in additional_tickers:
        if ticker not in companies:
            companies[ticker] = {'name': f'{ticker}', 'sector': 'Historical'}

    stock_data = {}
    processed = 0
    skipped = 0

    for ticker, info in sorted(companies.items()):
        filepath = find_stock_file(ticker)

        if not filepath:
            print(f"  ✗ {ticker}: File not found")
            skipped += 1
            continue

        try:
            prices = read_stock_data(filepath)

            if len(prices) < 252:  # Less than 1 year of data
                print(f"  ✗ {ticker}: Insufficient data ({len(prices)} days)")
                skipped += 1
                continue

            annual_returns = calculate_annual_returns(prices)
            quarterly_returns = calculate_quarterly_returns(prices)

            if len(annual_returns) < 2:  # Need at least 2 years
                print(f"  ✗ {ticker}: Insufficient annual data ({len(annual_returns)} years)")
                skipped += 1
                continue

            stats = calculate_stats(annual_returns)

            stock_data[ticker] = {
                'name': info['name'],
                'sector': info['sector'],
                'annualReturns': annual_returns,
                'quarterlyReturns': quarterly_returns,
                'stats': stats,
                'dataPoints': len(prices),
                'startYear': annual_returns[0]['year'],
                'endYear': annual_returns[-1]['year']
            }

            print(f"  ✓ {ticker}: {len(annual_returns)} years, {len(quarterly_returns)} quarters ({annual_returns[0]['year']}-{annual_returns[-1]['year']})")
            processed += 1

        except Exception as e:
            print(f"  ✗ {ticker}: Error - {str(e)}")
            skipped += 1

    # Save to JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(stock_data, f, indent=2)

    print(f"\n✓ Processed {processed} stocks")
    print(f"✗ Skipped {skipped} stocks")
    print(f"📁 Saved to {OUTPUT_JSON}")

    # Print summary statistics
    if stock_data:
        total_returns = sum(len(data['annualReturns']) for data in stock_data.values())
        avg_years = total_returns / len(stock_data)
        print(f"\n📊 Average years of data per stock: {avg_years:.1f}")

if __name__ == '__main__':
    main()
