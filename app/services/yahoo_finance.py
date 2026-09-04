# app/services/yahoo_finance.py
import yfinance as yf


def fetch_quote(ticker: str) -> dict:
    """
    Returns a snapshot of current price/info for a ticker.
    Returns dict with price=None if ticker is invalid.
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "symbol": ticker.upper(),
        "name": info.get("shortName"),
        "price": info.get("regularMarketPrice"),
        "currency": info.get("currency"),
        "previous_close": info.get("previousClose"),
        "open": info.get("open"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "market_cap": info.get("marketCap"),
        "volume": info.get("volume"),
        "pe_ratio": info.get("trailingPE"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
    }


def fetch_history(ticker: str, period: str = "1mo", interval: str = "1d") -> list[dict]:
    """
    Returns historical OHLCV data as a list of dicts.
    Returns [] if no data found.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)

    if hist.empty:
        return []

    hist.reset_index(inplace=True)
    # yfinance names the date column "Date" or "Datetime" depending on interval
    date_col = "Date" if "Date" in hist.columns else "Datetime"
    hist[date_col] = hist[date_col].astype(str)

    return hist.to_dict(orient="records")
# app/services/yahoo_finance.py

def fetch_multiple_quotes(tickers: list[str]) -> list[dict]:
    """
    Returns quote data for multiple tickers at once.
    """
    results = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        results.append({
            "symbol": ticker.upper(),
            "price": info.get("regularMarketPrice"),
            "currency": info.get("currency", "USD"),
        })
    return results
