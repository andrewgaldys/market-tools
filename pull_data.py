import yfinance as yf

data = yf.download("AAPL", start="2020-01-01")
data["Return"] = data["Adj Close"].pct_change()
data["SMA_50"] = data["Adj Close"].rolling(window=50).mean()

print(data.tail())