from fastapi import APIRouter, HTTPException
from app.services.yahoo_finance import fetch_quote

router = APIRouter()

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
