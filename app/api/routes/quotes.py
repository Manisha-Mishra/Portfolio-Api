from fastapi import APIRouter, HTTPException, Query

from app.services.yahoo_finance import fetch_fund_summary, fetch_multiple_quotes, fetch_quote

router = APIRouter()


@router.get("/quotes")
def get_quotes(symbols: str = Query(..., min_length=1)):
    tickers = [ticker.strip().upper() for ticker in symbols.split(",") if ticker.strip()]
    if not tickers:
        raise HTTPException(status_code=400, detail="At least one symbol is required.")
    return fetch_multiple_quotes(tickers)

@router.get("/quote/{ticker}")
def get_quote(ticker: str):
    """
    Get a real-time snapshot for a single stock.
    Example: /quote/AAPL
    """
    data = fetch_quote(ticker)

    if data["price"] is None:
        raise HTTPException(status_code=404, detail=f"No data found for '{ticker}'")

    return data


@router.get("/fund/{ticker}/summary")
def get_fund_summary(
    ticker: str,
    period: str = Query("1y"),
    interval: str = Query("1d"),
    target_price: float | None = Query(None, gt=0),
):
    data = fetch_fund_summary(ticker, period, interval, target_price)
    if data["quote"].get("price") is None:
        raise HTTPException(status_code=404, detail=f"No data found for '{ticker}'")
    return data
