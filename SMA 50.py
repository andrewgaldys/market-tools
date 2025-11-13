import sys
import yfinance as yf

try:
	data = yf.download("AAPL", start="2020-01-01", auto_adjust=False)
except Exception as e:
	print(f"Error downloading data: {e}", file=sys.stderr)
	raise

if data.empty:
	print("No data downloaded for ticker 'AAPL' - check network/ticker/date range", file=sys.stderr)
	sys.exit(1)

# yfinance may return 'Adj Close' or just 'Close' depending on auto-adjust settings/version
if "Adj Close" in data.columns:
	price_col = "Adj Close"
elif "Close" in data.columns:
	price_col = "Close"
else:
	print(f"Unexpected columns in downloaded data: {list(data.columns)}", file=sys.stderr)
	raise KeyError("No suitable price column found ('Adj Close' or 'Close').")

data["Return"] = data[price_col].pct_change()
data["SMA_50"] = data[price_col].rolling(window=50).mean()

print(data.tail())