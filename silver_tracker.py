import sys
import datetime as dt
import yfinance as yf

# You can switch this between spot proxy and ETF
# "SI=F" = Silver futures (good proxy for spot)
# "SLV"  = iShares Silver Trust ETF
TICKER = "SI=F"

# Set a lookback period for moving averages
END = dt.datetime.today()
START = END - dt.timedelta(days=180)  # last 6 months

print(f"Downloading data for {TICKER} from {START.date()} to {END.date()}")

try:
    data = yf.download(TICKER, start=START, end=END, auto_adjust=False)
except Exception as e:
    print(f"Error downloading data: {e}", file=sys.stderr)
    sys.exit(1)

if data.empty:
    print(f"No data downloaded for ticker '{TICKER}' - check network/ticker/date range", file=sys.stderr)
    sys.exit(1)

# Handle different column names
if "Adj Close" in data.columns:
    price_col = "Adj Close"
elif "Close" in data.columns:
    price_col = "Close"
else:
    print(f"Unexpected columns in downloaded data: {list(data.columns)}", file=sys.stderr)
    raise KeyError("No suitable price column found ('Adj Close' or 'Close').")

import pandas as pd

# Basic analytics
# yfinance sometimes returns MultiIndex columns (e.g. ('SI=F','Close') or ('Close','SI=F')).
# Build a clean price series (scalar values) regardless of column index type.
def _get_price_series(df: pd.DataFrame, col_name: str) -> pd.Series:
    cols = df.columns
    # direct single-level access
    if col_name in cols:
        return df[col_name]
    # handle MultiIndex: find a column tuple that contains the name
    if isinstance(cols, pd.MultiIndex):
        matches = [c for c in cols if col_name in c]
        if matches:
            return df[matches[0]]
    raise KeyError(f"Could not locate price column '{col_name}' in DataFrame columns: {list(cols)}")

price_series = _get_price_series(data, price_col)

returns = price_series.pct_change()
sma_20_series = price_series.rolling(window=20).mean()
sma_50_series = price_series.rolling(window=50).mean()

# Attach new columns to the DataFrame (these will be single-level columns)
data["Return"] = returns
data["SMA_20"] = sma_20_series
data["SMA_50"] = sma_50_series

# Ensure we have at least one row where SMA_50 is available
valid_idx = price_series.dropna().index.intersection(sma_50_series.dropna().index)
if len(valid_idx) == 0:
    print("Not enough data to compute SMA_50; try a longer lookback period", file=sys.stderr)
    sys.exit(1)

# Get latest scalar values
latest_idx = valid_idx[-1]
latest_price = float(price_series.loc[latest_idx])
sma_20 = float(sma_20_series.loc[latest_idx])
sma_50 = float(sma_50_series.loc[latest_idx])

# Percent distance from the moving averages
dist_20 = (latest_price - sma_20) / sma_20 * 100
dist_50 = (latest_price - sma_50) / sma_50 * 100

print("\n===== Silver Tracker =====")
print(f"Ticker: {TICKER}")
print(f"Date:   {latest_idx.date()}")
print(f"Price:  {latest_price:,.2f}")
print(f"SMA 20: {sma_20:,.2f}  ({dist_20:+.2f}% from price)")
print(f"SMA 50: {sma_50:,.2f}  ({dist_50:+.2f}% from price)")

# Simple recent performance
last_5 = data.tail(5)[price_col]
print("\nLast 5 closing prices:")
print(last_5.to_string())