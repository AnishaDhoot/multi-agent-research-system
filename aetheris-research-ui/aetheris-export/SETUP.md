# AETHERIS UI — Setup

The UI starts a research job on the Python backend (`POST /api/research`) and polls it (`GET /api/research/[id]`) so the progress cards show the real pipeline stage.

## 1. Backend (from the repo root)

```bash
pip install -r requirements.txt
cp .env.example .env        # add GOOGLE_API_KEY and TAVILY_API_KEY
uvicorn server:app --port 8000
```

## 2. Frontend

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Visit http://localhost:3000

## Environment variables (`.env.local`)

| Variable | Default | Description |
|---|---|---|
| `PYTHON_BACKEND_URL` | `http://localhost:8000` | URL of the FastAPI server |
| `DEMO_MODE` | unset | `true` serves sample data instead of calling the backend |

If the backend is unreachable and `DEMO_MODE` is not set, the UI shows an error (it no longer silently shows fake results).
