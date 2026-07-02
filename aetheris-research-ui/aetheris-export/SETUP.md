# AETHERIS — Setup Guide

## 1. Python Backend

Place `server.py` next to your `pipeline.py`, `agents.py`, `tools.py` files.

```bash
pip install fastapi uvicorn
uvicorn server:app --reload --port 8000
```

## 2. Next.js Frontend

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Visit http://localhost:3000

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PYTHON_BACKEND_URL` | `http://localhost:8000` | URL of your FastAPI server |

## Without the backend

The UI runs in demo mode with mock data if the Python backend isn't reachable.
