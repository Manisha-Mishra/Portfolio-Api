# Portfolio API

FastAPI service that retrieves market data from Yahoo Finance.

## Windows setup

From PowerShell, run:

```powershell
cd c:\Users\prash\project\Portfolio-Api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the API

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://192.168.1.5:8000`. Open
`http://192.168.1.5:8000/docs` for interactive API documentation.

Useful checks:

```text
GET http://192.168.1.5:8000/
GET http://192.168.1.5:8000/api/funds/search?query=AAPL
GET http://192.168.1.5:8000/api/quote/AAPL
GET http://192.168.1.5:8000/api/history/AAPL?period=1mo&interval=1d
```

## Deploying for free (Render)

This repo includes a `render.yaml` blueprint for [Render](https://render.com)'s free web service tier.

1. Push all local changes to GitHub (`git push`) — Render deploys from your GitHub repo.
2. Sign in to Render, click **New > Blueprint**, and pick this repo. Render will read `render.yaml` and create a free web service automatically, generating a random `AUTH_SECRET` for you.
3. Once deployed, your API is available at `https://<your-service-name>.onrender.com`.
4. Update `EXPO_PUBLIC_API_URL` in `Portfolio-Tracker/.env.development` (or `.env.production`) to point at that URL instead of your LAN IP.

Notes:
- The free tier spins the service down after 15 minutes of inactivity — the first request after idling will be slow (cold start).
- The filesystem is ephemeral: `portfolio.db` resets on every redeploy/restart, so registered users and saved data won't persist long-term. Move to a hosted database (e.g. Turso) later if you need real persistence.

## Connecting the Expo app

Set `EXPO_PUBLIC_API_URL` in `Portfolio-Tracker/.env.development`:

```text
EXPO_PUBLIC_API_URL=http://192.168.1.5:8000/api
```

For a physical phone, replace `192.168.1.5` with the computer's LAN IP, for
example `http://192.168.1.42:8000/api`. The phone and computer must be on the
same network, and Windows Firewall must allow port `8000`.
