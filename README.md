# Wind cover desk

Web app for a UK energy utility's day-ahead buying team. It shows the wind forecast that was
available when the day-ahead decision had to be made, and quantifies how accurate that
forecast has been (national wind, Elexon FUELHH actuals and WINDFOR forecasts, January 2026).

**Live app:** _add Vercel/Heroku/Render link here_
**AI tools:** this project was built with help from Claude (Anthropic) for code, analysis design and documentation.

## Key idea
For each half-hour of a delivery day D, the "decision-time forecast" is the latest WINDFOR record
published at or before the cut-off on D-1 (default 09:00 UK time, user-selectable).
Error = forecast - actual (positive = forecast too high, so the buyer under-procured).

## Files
- `backend/app/elexon.py` - Elexon API client (FUELHH wind, WINDFOR)
- `backend/app/analysis.py` - decision-time selection and error metrics
- `backend/app/main.py` - FastAPI endpoints (`/api/forecast`, `/api/accuracy`, `/api/errors`) and static hosting
- `backend/scripts_fetch.py` - downloads January 2026 data into `backend/data/*.csv`
- `backend/tests/` - unit tests (`pytest`)
- `frontend/` - React (Vite + Recharts) UI
- `Dockerfile` - builds frontend, then serves everything from one Python container

## Run
```bash
# 1. get data (once)
cd backend && pip install -r requirements.txt && python scripts_fetch.py
# 2a. docker (from repo root)
docker build -t wind-portal . && docker run -p 8000:8000 wind-portal   # http://localhost:8000
# 2b. or dev mode
uvicorn app.main:app --reload --port 8000          # in backend/
cd ../frontend && npm install && npm run dev       # http://localhost:5173
# tests
cd backend && pytest
```

## Limitations
- Cut-off default (09:00) is an assumption; check against the actual day-ahead gate closure.
- MAPE ignores periods under 100 MW of wind because percentage error explodes near zero.
- Error band is estimated from January only, so it is a historical guide, not a guarantee.
