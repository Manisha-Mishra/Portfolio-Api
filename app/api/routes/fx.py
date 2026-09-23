from fastapi import APIRouter, HTTPException, Query

import yfinance as yf

router = APIRouter()


@router.get("/fx/rates")
def get_fx_rates(
    base: str = Query(..., min_length=3, max_length=3),
    currencies: str = Query(..., min_length=3),
):
    base_currency = base.upper()
    requested = {item.strip().upper() for item in currencies.split(",") if item.strip()}
    requested.add(base_currency)
    rates = {base_currency: 1.0}

    for currency in requested:
        if currency == base_currency:
            continue
        try:
            pair = yf.Ticker(f"{currency}{base_currency}=X")
            rate = pair.fast_info.get("lastPrice")
            if rate and float(rate) > 0:
                rates[currency] = float(rate)
        except Exception:
            continue

    if len(rates) == 1 and len(requested) > 1:
        raise HTTPException(status_code=502, detail="Unable to fetch currency rates.")
    return {"base": base_currency, "rates": rates}