# app/services/yahoo_finance.py
import yfinance as yf


QUOTE_TYPE_CATEGORIES = {
    "EQUITY": "Stocks",
    "ETF": "ETFs",
    "MUTUALFUND": "Mutual Funds",
    "CRYPTOCURRENCY": "Crypto",
    "OPTION": "Options",
}


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
        "average_volume": info.get("averageVolume"),
        "pe_ratio": info.get("trailingPE"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "52_week_change": info.get("fiftyTwoWeekChange"),
        "sector": info.get("sector"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "trailing_dividend_rate": info.get("trailingAnnualDividendRate"),
        "eps": info.get("trailingEps"),
        "earnings_growth": info.get("earningsGrowth"),
        "market_state": info.get("marketState"),
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


def search_funds(query: str) -> list[dict]:
    """Search Yahoo Finance and normalize results for the frontend Fund model."""
    search = yf.Search(query.strip(), news_count=0)
    results = []

    for quote in search.quotes[:10]:
        symbol = quote.get("symbol")
        name = quote.get("shortname") or quote.get("longname")

        if not symbol or not name:
            continue

        quote_type = quote.get("quoteType", "EQUITY").upper()
        price = quote.get("regularMarketPrice")
        currency = quote.get("currency") or "USD"

        if price is None:
            try:
                fast_info = yf.Ticker(symbol).fast_info
                price = fast_info.get("lastPrice")
                currency = fast_info.get("currency") or currency
            except Exception:
                price = 0

        results.append(
            {
                "ticker": symbol,
                "name": name,
                "category": QUOTE_TYPE_CATEGORIES.get(quote_type, "Stocks"),
                "currentPrice": price or 0,
                "currency": currency,
            }
        )

    return results

def fetch_multiple_quotes(tickers: list[str]) -> list[dict]:
    """
    Returns quote data for multiple tickers at once.
    """
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            fast_info = stock.fast_info
            results.append({
                "symbol": ticker.upper(),
                "price": fast_info.get("lastPrice") or 0,
                "currency": fast_info.get("currency") or "USD",
            })
        except Exception:
            results.append({
                "symbol": ticker.upper(),
                "price": 0,
                "currency": "USD",
            })
    return results


def fetch_fund_summary(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    target_price: float | None = None,
) -> dict:
    quote = fetch_quote(ticker)
    history = fetch_history(ticker, period, interval)
    current_price = quote.get("price")

    if current_price is None:
        return {"quote": quote, "history": history, "performance": {}}

    closes = [
        float(point["Close"])
        for point in history
        if point.get("Close") is not None
    ]
    first_close = closes[0] if closes else None
    period_change = current_price - first_close if first_close is not None else None
    period_change_percent = (
        (period_change / first_close) * 100
        if period_change is not None and first_close
        else None
    )
    target_gap = current_price - target_price if target_price is not None else None
    target_gap_percent = (
        (target_gap / target_price) * 100
        if target_gap is not None and target_price
        else None
    )

    return {
        "symbol": ticker.upper(),
        "quote": quote,
        "history": history,
        "performance": {
            "period": period,
            "interval": interval,
            "start_price": first_close,
            "current_price": current_price,
            "period_change": period_change,
            "period_change_percent": period_change_percent,
            "period_high": max(closes) if closes else None,
            "period_low": min(closes) if closes else None,
            "target_price": target_price,
            "target_gap": target_gap,
            "target_gap_percent": target_gap_percent,
            "target_reached": current_price >= target_price if target_price is not None else None,
        },
    }
