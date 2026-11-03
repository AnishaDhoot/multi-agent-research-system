# Multi-Agent Research System

Give it a topic and it plans searches, reads several web sources, writes a cited report, and has a critic score and (if needed) revise it. Built with LangChain, Tavily and Gemini or Groq, with a FastAPI backend and a Next.js UI.

## How it works

```
topic
  │
  ▼
Planner ──► 3–4 focused search queries
  │
  ▼
Search & Reader ──► Tavily search (parallel) ─► rank by source quality ─► dedupe
  │                 read up to 6 pages in parallel
  │                 (trafilatura; Tavily Extract fallback for blocked sites)
  ▼
Writer ──► report with inline [n] citations
  │
  ▼
Critic ──► structured review: score 0–10, strengths, improvements
  │            score < 8 ─► Writer revises using the feedback (max 2 times)
  ▼
Final report + Sources list (only sources the report actually cites)
```

| Stage | Where | What it does |
|---|---|---|
| Planner | `agents.plan_topic` | Structured LLM output → sub-questions; falls back to the raw topic if planning fails |
| Search & Reader | `pipeline.py`, `tools.py` | Parallel Tavily searches, domain-based ranking, parallel page reads, snippet fallback |
| Writer / Revision | `agents.writer_chain`, `agents.revision_chain` | Cited report; revision prompt addresses critic feedback |
| Critic | `agents.critic_chain` | Returns a `CriticReview` (bounded score + lists) via structured output |

Search and reading are plain code, not LLM agents: that is faster, cheaper and predictable. Only planning, writing, revising and critiquing call the LLM.

## Setup

Requires Python 3.12+ and Node 20+.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in GOOGLE_API_KEY and TAVILY_API_KEY
```

API keys: [Tavily](https://tavily.com) plus one LLM provider: [Google AI Studio](https://aistudio.google.com/apikey) (Gemini) or [Groq](https://console.groq.com). Choose with `LLM_PROVIDER` in `.env`. One report makes 3–6 LLM calls, and free tiers have daily limits, so if you hit a quota, switch provider rather than enabling billing. Free-tier limits and available models change; if a model is rejected, set `LLM_MODEL`.

## Run it

**Command line**

```bash
python pipeline.py
```

**Backend + UI**

```bash
uvicorn server:app --port 8000
```

```bash
cd aetheris-research-ui/aetheris-export
npm install
cp .env.local.example .env.local
npm run dev                     # http://localhost:3000
```

Set `DEMO_MODE=true` in the UI's `.env.local` to try the interface with sample data and no backend.

## API

| Endpoint | Description |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `POST /jobs` | Body `{"topic": "..."}` → `202 {"job_id": "..."}`. Starts a run in the background. |
| `GET /jobs/{job_id}` | `{"status": "running"\|"done"\|"error", "stage": "...", "result": {...}}`. Stages: `queued`, `planning`, `reading sources`, `writing`, `reviewing`, `revising`. |
| `POST /research` | Blocking version of `/jobs`; returns the result directly. |

Result fields: `report`, `feedback`, `score`, `revisions`, `plan` (search queries), `sources` (`title`, `url`, `scraped`), `search_results`, `scraped_content`.

Errors: `400` empty or too-long topic, `429` rate limit, `503` server busy, `500` run failed (details are logged server-side, not returned).

Jobs are kept in memory for an hour and the rate limit is per process, so run a single worker.

## Configuration

Everything is optional except the two API keys. Set in `.env` (see `.env.example`):

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` or `groq` |
| `LLM_MODEL` | provider default | Overrides the model (`gemini-2.5-flash` / `openai/gpt-oss-120b`) |
| `GOOGLE_API_KEY` | — | Needed when `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | — | Needed when `LLM_PROVIDER=groq` |
| `TAVILY_API_KEY` | — | Search and Extract |
| `MAX_SOURCES` | 6 | Pages read per report |
| `RESULTS_PER_QUESTION` | 3 | Tavily results per planned query |
| `MAX_REVISIONS` | 2 | Writer revisions after critic review |
| `PASS_SCORE` | 8.0 | Critic score that ends the revision loop |
| `MAX_SCRAPE_CHARS` | 6000 | Text kept per page |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `MAX_TOPIC_CHARS` | 300 | Longest accepted topic |
| `RATE_LIMIT_PER_MINUTE` | 5 | Requests per IP per minute |
| `MAX_CONCURRENT_RUNS` | 2 | Simultaneous research runs |

## Project structure

```
agents.py        LLM provider selection, prompts, planner, writer, revision and critic chains
pipeline.py      Orchestration: plan → gather → write → review/revise → cite
tools.py         Tavily search/extract, safe page fetching, text extraction
settings.py      Environment-based configuration
server.py        FastAPI app: jobs, rate limit, concurrency cap, CORS
test_*.py        Unit tests (everything external is mocked)
aetheris-research-ui/aetheris-export/   Next.js UI (polls /jobs through /api/research)
.github/workflows/ci.yml                Runs the tests on every push
```

## Security notes

- Pages are fetched only over http(s) from hosts that resolve to public IP addresses, and every redirect hop is re-checked, so the scraper can't be pointed at localhost or cloud metadata addresses. Known gap: the hostname is resolved once to check and again to connect, so a hostile DNS server could still rebind between the two.
- The UI escapes the report before rendering it as HTML, since it is built from scraped web content.
- API keys live in `.env` / `.env.local`, which are git-ignored.

## Tests

```bash
python -m unittest -v
```

The tests mock the LLM, Tavily and HTTP, so they need no keys or network. A change to a prompt or output format is only caught by a real run (`python pipeline.py`).

## Known limitations

- Reports are only as good as what Tavily finds and the pages allow; paywalled sites fall back to Tavily Extract or the search snippet.
- The critic is an LLM, so scores are a rough signal, not a measurement.
- There is no fact-checking agent yet: citations are checked for use, not for accuracy.
- Job state and rate limits are in memory (single process, lost on restart).

## Contributing

Fork, create a branch, make your change with tests, and open a pull request.
