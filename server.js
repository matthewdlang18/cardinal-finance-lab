const express = require('express');
const cors = require('cors');
const YahooFinance = require('yahoo-finance2').default;

const app = express();
const PORT = process.env.PORT || 3001;

// Create Yahoo Finance instance
const yahooFinance = new YahooFinance({ suppressNotices: ['ripHistorical'] });

// Enable CORS for all origins
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type']
}));

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        dataSource: 'Yahoo Finance',
        timestamp: new Date().toISOString()
    });
});

// Helper function to calculate annual returns from price data
function calculateAnnualReturns(prices) {
    const annualReturns = [];
    const yearlyPrices = {};

    // Group prices by year
    prices.forEach(price => {
        const date = new Date(price.date);
        const year = date.getFullYear();
        if (!yearlyPrices[year]) {
            yearlyPrices[year] = [];
        }
        yearlyPrices[year].push(price);
    });

    const years = Object.keys(yearlyPrices).sort();

    // Calculate annual returns (year-over-year)
    for (let i = 1; i < years.length; i++) {
        const prevYear = years[i - 1];
        const currYear = years[i];

        // Use last price of previous year and last price of current year
        const prevYearPrices = yearlyPrices[prevYear];
        const currYearPrices = yearlyPrices[currYear];

        if (prevYearPrices.length > 0 && currYearPrices.length > 0) {
            const startPrice = prevYearPrices[prevYearPrices.length - 1].close;
            const endPrice = currYearPrices[currYearPrices.length - 1].close;

            const annualReturn = ((endPrice - startPrice) / startPrice) * 100;
            annualReturns.push({ year: currYear, return: annualReturn });
        }
    }

    return annualReturns;
}

// Helper function to normalize returns to starting date
function normalizeReturns(prices) {
    if (prices.length === 0) return [];
    const startPrice = prices[0].close;
    return prices.map(price => (price.close - startPrice) / startPrice);
}

// Helper function to calculate statistics
function calculateStats(returns) {
    const values = returns.map(r => r.return);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    const max = Math.max(...values);
    const min = Math.min(...values);

    return { mean, stdDev, max, min };
}

// Fetch stock data from Yahoo Finance
async function fetchStockData(ticker, startDate, endDate) {
    try {
        console.log(`Fetching ${ticker} from ${startDate} to ${endDate}...`);

        const result = await yahooFinance.historical(ticker, {
            period1: startDate,
            period2: endDate,
            interval: '1d'
        });

        console.log(`Successfully fetched ${result.length} data points for ${ticker}`);
        return result;
    } catch (error) {
        console.error(`Error fetching ${ticker}:`, error.message);
        throw new Error(`Failed to fetch data for ${ticker}. Please check the ticker symbol.`);
    }
}

// Single stock analysis endpoint
app.get('/api/stock-analysis', async (req, res) => {
    try {
        const { ticker, startDate } = req.query;

        if (!ticker) {
            return res.status(400).json({ error: 'Ticker is required' });
        }

        const start = startDate || '2010-01-01';
        const end = '2024-12-31';

        console.log(`Analyzing ${ticker} from ${start} to ${end}`);

        // Fetch stock data
        const stockPrices = await fetchStockData(ticker, start, end);

        // Fetch S&P 500 data (using SPY as proxy)
        const sp500Prices = await fetchStockData('SPY', start, end);

        // Calculate annual returns
        const annualReturns = calculateAnnualReturns(stockPrices);

        // Calculate normalized returns
        const normalizedReturns = normalizeReturns(stockPrices);
        const sp500Normalized = normalizeReturns(sp500Prices);

        // Calculate statistics
        const stats = calculateStats(annualReturns);

        res.json({
            ticker,
            startDate: start,
            annualReturns,
            normalizedReturns,
            sp500Normalized,
            stats
        });
    } catch (error) {
        console.error('Error in stock analysis:', error);
        res.status(500).json({ error: error.message || 'Failed to analyze stock' });
    }
});

// Portfolio analysis endpoint
app.post('/api/portfolio-analysis', async (req, res) => {
    try {
        const { stocks, startDate } = req.body;

        if (!stocks || stocks.length === 0) {
            return res.status(400).json({ error: 'Stocks array is required' });
        }

        const start = startDate || '2010-01-01';
        const end = '2024-12-31';

        console.log(`Analyzing portfolio from ${start} to ${end}`);

        // Fetch data for all stocks
        const stockDataPromises = stocks.map(stock =>
            fetchStockData(stock.ticker, start, end)
        );

        const sp500Promise = fetchStockData('SPY', start, end);

        const [stocksData, sp500Prices] = await Promise.all([
            Promise.all(stockDataPromises),
            sp500Promise
        ]);

        // Find common dates across all stocks
        const allDates = new Set(stocksData[0].map(p => p.date.toISOString().split('T')[0]));
        stocksData.forEach(stockPrices => {
            const dates = new Set(stockPrices.map(p => p.date.toISOString().split('T')[0]));
            allDates.forEach(date => {
                if (!dates.has(date)) allDates.delete(date);
            });
        });

        const commonDates = Array.from(allDates).sort();

        // Calculate portfolio daily values
        const portfolioPrices = commonDates.map(dateStr => {
            let portfolioValue = 0;

            stocksData.forEach((stockPrices, stockIdx) => {
                const priceData = stockPrices.find(p =>
                    p.date.toISOString().split('T')[0] === dateStr
                );
                if (priceData) {
                    portfolioValue += priceData.close * (stocks[stockIdx].weight / 100);
                }
            });

            return { date: new Date(dateStr), close: portfolioValue };
        });

        // Calculate annual returns
        const annualReturns = calculateAnnualReturns(portfolioPrices);

        // Calculate normalized returns
        const normalizedReturns = normalizeReturns(portfolioPrices);
        const sp500Normalized = normalizeReturns(sp500Prices);

        // Calculate statistics
        const stats = calculateStats(annualReturns);

        res.json({
            startDate: start,
            annualReturns,
            normalizedReturns,
            sp500Normalized,
            stats
        });
    } catch (error) {
        console.error('Error in portfolio analysis:', error);
        res.status(500).json({ error: error.message || 'Failed to analyze portfolio' });
    }
});

// Rolling returns endpoint
app.get('/api/rolling-returns', async (req, res) => {
    try {
        const { bond, equity } = req.query;

        // Fetch S&P 500 data (long history)
        const startDate = '1993-01-01'; // SPY inception
        const endDate = '2024-12-31';

        console.log(`Calculating rolling returns from ${startDate} to ${endDate}`);

        const sp500Prices = await fetchStockData('SPY', startDate, endDate);

        console.log(`Calculating rolling returns from ${sp500Prices.length} data points`);

        // Calculate rolling returns for different periods
        const periods = [1, 5, 10, 20, 30];
        const rollingReturns = {};

        periods.forEach(period => {
            const rollingData = [];
            const windowSize = period * 252; // Approximate trading days per year

            console.log(`Period ${period}: window=${windowSize}, dataPoints=${sp500Prices.length}`);

            if (windowSize >= sp500Prices.length) {
                console.log(`Skipping period ${period} - not enough data`);
                rollingReturns[`period${period}`] = [];
                return;
            }

            for (let i = windowSize; i < sp500Prices.length; i++) {
                const startPrice = sp500Prices[i - windowSize].close;
                const endPrice = sp500Prices[i].close;

                if (startPrice && endPrice && startPrice > 0) {
                    const annualizedReturn = (Math.pow(endPrice / startPrice, 1 / period) - 1) * 100;
                    rollingData.push(annualizedReturn);
                }
            }

            console.log(`Period ${period}: calculated ${rollingData.length} returns`);
            rollingReturns[`period${period}`] = rollingData;
        });

        // Fetch bond and equity data if provided
        if (bond) {
            try {
                const bondPrices = await fetchStockData(bond, startDate, endDate);
                rollingReturns.bondData = normalizeReturns(bondPrices);
            } catch (error) {
                console.warn('Could not fetch bond data:', error.message);
            }
        }

        if (equity) {
            try {
                const equityPrices = await fetchStockData(equity, startDate, endDate);
                rollingReturns.equityData = normalizeReturns(equityPrices);
            } catch (error) {
                console.warn('Could not fetch equity data:', error.message);
            }
        }

        res.json(rollingReturns);
    } catch (error) {
        console.error('Error in rolling returns:', error);
        res.status(500).json({ error: error.message || 'Failed to calculate rolling returns' });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Data source: Yahoo Finance`);
});
