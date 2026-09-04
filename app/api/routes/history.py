from fastapi import APIRouter, HTTPException, Query
from app.services.yahoo_finance import fetch_history

router = APIRouter()

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
VALID_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}

@router.get("/history/{ticker}")
def get_history(
    ticker: str,
    period: str = Query("1mo", description="e.g. 1d, 5d, 1mo, 6mo, 1y, 5y, max"),
    interval: str = Query("1d", description="e.g. 1m, 1h, 1d, 1wk, 1mo"),
):
    """
    Get historical price data for a stock over a given period.
    Example: /history/AAPL?period=6mo&interval=1d
    """
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period '{period}'")

    if interval not in VALID_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Invalid interval '{interval}'")

    data = fetch_history(ticker, period, interval)

    if not data:
        raise HTTPException(status_code=404, detail=f"No history found for '{ticker}'")

    return {
        "symbol": ticker.upper(),
        "period": period,
        "interval": interval,
        "count": len(data),
        "data": data,
    }
