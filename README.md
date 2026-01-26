# Cardinal Finance Lab

Educational finance tools for Stanford's IFDM (Initiative for Financial Decision-Making).

**Live Demo**: [View on GitHub Pages](https://matthewdlang18.github.io/cardinal-finance-lab/)

## Pages

### 1. Personal Finance Planner (`index.html`)
Interactive budgeting, debt payoff, portfolio simulation, and financial dashboard.
- Open directly in browser (no server required)

### 2. Stock Analysis Lab (`stock-analysis.html`)
Historical stock analysis and portfolio builder using comprehensive dataset (1928-2025).
- **No server required** - standalone HTML with pre-loaded data
- 490 S&P 500 stocks, market indices, and bonds
- 98 years of S&P 500 historical data
- **Try it live**: Open `stock-analysis.html` directly or visit the GitHub Pages demo

## Stock Analysis Lab Usage

The Stock Analysis Lab is a **standalone application** - no server or installation required!

### Quick Start

Simply open `stock-analysis.html` in any modern web browser:

```bash
# Option 1: Open directly in browser
open stock-analysis.html

# Option 2: Use Python HTTP server (recommended for local testing)
python3 -m http.server 8080
# Then visit: http://localhost:8080/stock-analysis.html
```

The page automatically loads `comprehensive_stock_data.json` containing:
- 490 S&P 500 stocks (average 28.3 years, ~113 quarters per stock)
- S&P 500 Index (SPX): 98 years, 388 quarters (1928-2025)
- Bond indices: TBILL, TBOND10, BAACORP (98 years, 388 quarters each)
- Pre-calculated rolling returns for all periods
- Quarterly returns (annualized) for more granular analysis

### Available Tickers

- **S&P 500 stocks**: AAPL, MSFT, GOOGL, AMZN, and 486 others
- **S&P 500 Index**: SPX
- **Bonds**: TBILL (3-Month T-Bill), TBOND10 (10-Year Treasury), BAACORP (Baa Corporate)

### Features

#### Single Stock Analysis
- Enter any stock ticker (e.g., AAPL, MSFT, TSLA)
- **Custom date ranges** - select start and end years for analysis
- **Time-series histogram** showing quarterly returns (annualized)
- **Interactive tooltips** - hover over bars to see exact quarter and return
- Color-coded bars: red (<0%), yellow (0-7%), green (>7%)
- Statistics: mean, std dev, min, max
- **Sharpe Ratio** - toggle to view risk-adjusted returns (4% risk-free rate)
- Compare performance against S&P 500 (normalized)
- **Year range warnings** - alerts when stock data doesn't cover full selected period
- Up to 4x more data points than annual returns

#### Portfolio Builder
- Create custom portfolios with multiple stocks
- **Custom date ranges** - select start and end years for analysis
- Set weights for each holding
- **One-click presets**:
  - "Equal Weight All" - automatically balance all holdings
  - "2000 Top Picks" - load pre-selected portfolio (CSCO, IBM, HD, JNJ, XOM, DAL, VZ, CCL)
- **Sharpe Ratio** - toggle to view portfolio risk-adjusted returns vs S&P 500
- Analyze portfolio returns distribution
- Compare portfolio performance vs S&P 500
- **Year range warnings** - explains when analysis uses different dates than selected (e.g., when stocks have limited history)

#### Rolling Returns Analysis
- View S&P 500 rolling returns over time (default: 1982-2025)
- **Custom date ranges** - select start and end years for analysis
- Toggle between 1, 5, 10, 20, 30 year periods
- **Detailed statistics** - mean, standard deviation, and count of negative return years for each period
- **Combined distribution density chart** - all periods overlaid with high-contrast colors
- Visualizes how variance "tightens up" with longer time horizons
- 1-year: wide distribution → 30-year: narrow distribution
- Demonstrates "time in market" principle
- Timeline chart shows historical rolling returns
- **Dotted lines** for bond data vs solid for S&P 500
- Compare against Treasury Bills, 10-Year Treasuries, and Corporate Bonds

### Data Processing (Optional)

The comprehensive dataset is pre-built, but if you need to regenerate it:

```bash
# Step 1: Process S&P 500 stocks from daily data
python3 process_stock_data.py
# Output: stock_data.json (490 stocks)

# Step 2: Combine with S&P historical data and bonds
python3 create_comprehensive_data.py
# Output: comprehensive_stock_data.json (final dataset)
```

Required source files:
- `data/daily/us/` - Daily stock price files
- `../sp500.csv` - S&P 500 companies list
- `spreturns.csv` - S&P 500 and bond returns (1928-2025)

### Technical Details

- **Quarterly Returns**: Quarter-over-quarter returns, annualized ((1 + r)^4 - 1)
- **Annual Returns**: Year-over-year percentage change using end-of-year prices
- **Rolling Returns**: Compounded annualized returns over moving windows
- **Normalized Returns**: Cumulative returns from chosen start date
- **Distribution Density**: Kernel density estimation with 30 bins
- **Interactive Charts**: HTML5 Canvas with hover tooltips
- **No external libraries**: Pure JavaScript implementation
- **File size**: 2.77MB (includes all quarterly data)

## Setup Instructions

### Quick Start (Local)
1. Clone or download this repository
2. Open `stock-analysis.html` directly in your browser
3. No installation or server required!

### GitHub Pages Setup
1. Fork this repository
2. Go to repository Settings → Pages
3. Set Source to "Deploy from a branch"
4. Select branch: `main` (or `master`), folder: `/ (root)`
5. Click Save
6. Your site will be live at `https://matthewdlang18.github.io/cardinal-finance-lab/`
7. Update the live demo link in this README with your actual URL

### File Structure
```
personal-finance/
├── stock-analysis.html              # Main Stock Analysis Lab application
├── comprehensive_stock_data.json    # Complete dataset (2.77MB)
├── index.html                       # Personal Finance Planner
├── README.md                        # This file
└── .gitignore                       # Git exclusions
```

## Credits

Created for Stanford IFDM
Professors Annamaria Lusardi and Michael Boskin

Data sources:
- Stock data: Daily price files processed to quarterly returns
- S&P 500 historical data and bond returns: Aswath Damodaran, NYU Stern
