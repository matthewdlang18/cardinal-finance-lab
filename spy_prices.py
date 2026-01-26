import pandas as pd
import numpy as np
import requests
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_sp500_tickers_local(path="sp500.csv"):
    df = pd.read_csv(path)  # local file, no SSL
    tickers = df["Symbol"].astype(str).str.strip().tolist()
    return [t.replace(".", "-") for t in tickers]  # BRK.B -> BRK-B

def to_stooq_symbol(ticker: str) -> str:
    t = ticker.strip()
    # normalize BRK.B -> BRK-B for most free data sources
    t = t.replace(".", "-")
    # indices you pass in like "^SPX" should stay as-is (but lower for stooq URL)
    if t.startswith("^"):
        return t.lower()
    return (t + ".us").lower()

def stooq_daily_close(stooq_symbol: str) -> pd.Series:
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))
    # Stooq standard columns: Date, Open, High, Low, Close, Volume
    if df.empty or "Date" not in df.columns or "Close" not in df.columns:
        return pd.Series(dtype=float)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    close = pd.to_numeric(df["Close"], errors="coerce").dropna()
    return close

def annual_returns_from_close(close: pd.Series) -> pd.Series:
    # last trading day in each calendar year
    year_end = close.resample("YE").last()
    ann = year_end.pct_change().dropna()
    ann.index = ann.index.year
    return ann

def process_ticker(ticker: str) -> pd.DataFrame:
    stooq = to_stooq_symbol(ticker)
    close = stooq_daily_close(stooq)
    if close.empty:
        return pd.DataFrame(columns=["ticker", "year", "annual_return"])
    ann = annual_returns_from_close(close)
    out = pd.DataFrame({"ticker": ticker, "year": ann.index, "annual_return": ann.values})
    return out

# --- load tickers from your CSV ---
sp = pd.read_csv(SP500_CSV)              # expects column named Symbol [file:110]
tickers = sp["Symbol"].astype(str).tolist()

# Add SPX + BND explicitly
extra = ["^SPX", "BND"]
tickers_all = extra + tickers

results = []
failures = []

with ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(process_ticker, t): t for t in tickers_all}
    for fut in as_completed(futs):
        t = futs[fut]
        try:
            df = fut.result()
            if df.empty:
                failures.append(t)
            else:
                results.append(df)
        except Exception as e:
            failures.append(t)

panel = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
panel.to_csv(OUT_CSV, index=False)

print("Wrote:", OUT_CSV, "rows:", len(panel), "tickers_failed:", len(failures))
