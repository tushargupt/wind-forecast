# Wind cover desk

Web app for a UK energy utility's day-ahead buying team. It shows the wind forecast that was
available when the day-ahead decision had to be made, and quantifies how accurate that forecast
has been. Scope: national wind, Elexon FUELHH (actuals) and WINDFOR (forecasts), January 2026.

- **Live app:** https://wind-forecast-seven.vercel.app/
- **Video demo (unlisted):** https://www.loom.com/share/52a8746894534f09b1a5b16b2612f698
- **Architecture demo:** https://www.loom.com/share/89c8cddb387346869de047a6a946ac9f
- **AI tools:** this project was built with help from Claude (Anthropic) for code, analysis design and documentation.

## How it works
For each half-hour of a delivery day D, the "decision-time forecast" is the latest WINDFOR record
published at or before the cut-off on D-1 (default 09:00 UK time, user-selectable).
Error = forecast - actual (positive = forecast too high, so the buyer under-procured).
WINDFOR is hourly and FUELHH is half-hourly, so each hourly forecast is applied to both half-hours it covers.

## Key findings (January 2026, 09:00 cut-off)
- Typical miss (MAE) is about 2,100 MW, about 18% of average wind (about 11,600 MW).
- The forecast runs about 1,850 MW above actual on average (too high in about 85% of half-hours), at every lead time.
  This is a steady lean, not random noise: removing it cuts the typical miss to about 1,440 MW.
  The cause is unconfirmed (possibly different wind-farm coverage in the two datasets).
- In 1 half-hour out of 20 the forecast was too high by more than about 5,300 MW.

## Files and directories
- `backend/app/elexon.py` - Elexon API client (FUELHH wind, WINDFOR)
- `backend/app/analysis.py` - decision-time selection, actual/forecast alignment, error metrics
- `backend/app/main.py` - FastAPI endpoints: `/api/forecast`, `/api/accuracy`, `/api/errors`, `/api/health`
- `backend/scripts_fetch.py` - downloads January 2026 data into `backend/data/`
- `backend/data/` - `actuals.csv`, `forecasts.csv` (committed snapshot used by the app)
- `backend/tests/` - unit tests; `backend/pytest.ini` - test config
- `backend/requirements.txt` - Python dependencies for local/Docker use
- `frontend/` - React (Vite + Recharts) UI
- `Dockerfile` - builds the frontend, then serves everything from one Python container
- `api/index.py` - Vercel serverless entry point exposing the FastAPI app
- `vercel.json`, `requirements.txt` (root, slim, for Vercel) - Vercel deployment config
- `heroku.yml` - alternative container deployment on Heroku

## Start the application
Docker (from repo root):
```bash
docker build -t wind-portal .
docker run --rm -p 8000:8000 wind-portal      # http://localhost:8000
```
Local development (two terminals):
```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# second terminal
cd frontend && npm install && npm run dev      # http://localhost:5173
```
Refresh the data (optional, needs internet): `cd backend && python scripts_fetch.py`
Tests: `cd backend && pytest`

## Deployment
Deployed on Vercel: the React build is served as static files and FastAPI runs as a Python serverless function
with the CSV data bundled. Docker is used for local packaging; `heroku.yml` supports container deployment on Heroku.

## Limitations
- The 09:00 default cut-off is an assumption; check it against the actual day-ahead gate closure.
- MAPE ignores periods under 100 MW of wind because percentage error explodes near zero.
- The error band is estimated from January only, so it is a historical guide, not a guarantee.
