from fastapi import APIRouter, HTTPException, Query

from app.services.yahoo_finance import search_funds

router = APIRouter()


@router.get("/funds/search")
def search_funds_route(
    query: str = Query(..., min_length=1, max_length=50),
):
    """Search Yahoo Finance symbols and return funds in the app's Fund shape."""
    try:
        results = search_funds(query)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Yahoo Finance search is currently unavailable.",
        ) from error

    return {"results": results}