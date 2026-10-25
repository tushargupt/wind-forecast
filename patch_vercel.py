"""Run from repo root: python3 patch_vercel.py
Adds Vercel config: React as static site + FastAPI as a Python serverless function.
Docker/Heroku files are untouched."""
import json, pathlib

root = pathlib.Path(".")
(root / "api").mkdir(exist_ok=True)

(root / "api" / "index.py").write_text('''"""Vercel entry point: exposes the FastAPI app from backend/app as a serverless function."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401  (Vercel looks for the `app` variable)
''')

# Slim runtime deps for the function (no pytest/httpx/uvicorn needed on Vercel)
(root / "requirements.txt").write_text("fastapi>=0.115\npandas>=2.2.3\n")

(root / "vercel.json").write_text(json.dumps({
    "buildCommand": "cd frontend && npm install && npm run build",
    "outputDirectory": "frontend/dist",
    "functions": {"api/index.py": {"includeFiles": "backend/**"}},
    "rewrites": [{"source": "/api/(.*)", "destination": "/api/index"}],
}, indent=2) + "\n")

(root / ".vercelignore").write_text(".venv\nnode_modules\n**/__pycache__\n.pytest_cache\nfrontend/dist\n")
print("Vercel files written: api/index.py, requirements.txt, vercel.json, .vercelignore")