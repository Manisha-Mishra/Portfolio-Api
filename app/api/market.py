from fastapi.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from fastapi import HTTPException
from app.services.market import fetch_quote, TickerNotFound
from fastapi import APIRouter

router = APIRouter()

@router.get("/quote/{ticker}")
async def get_quote(ticker: str):
    try:
        return await run_in_threadpool(fetch_quote, ticker)
    except TickerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
