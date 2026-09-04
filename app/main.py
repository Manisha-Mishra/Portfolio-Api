from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import quotes, history

app = FastAPI(
    title="Stock Profile Tracker API",
    description="Fetch real-time quotes and historical price data via Yahoo Finance",
    version="1.0.0",
)

# Allow your frontend (React, etc.) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this to your actual frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers — this is what actually "plugs in" quotes.py and history.py
app.include_router(quotes.router, prefix="/api", tags=["quotes"])
app.include_router(history.router, prefix="/api", tags=["history"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Stock Profile Tracker API is running"}
