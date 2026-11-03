"""
FastAPI server that wraps research_pipeline.
Run: uvicorn server:app --reload --port 8000

POST /research        blocking: returns the finished result (used by the Next.js UI)
POST /jobs            starts a run in the background, returns {"job_id": ...}
GET  /jobs/{job_id}   poll: {"status": "running"|"done"|"error", "stage": ..., "result": ...}
"""
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from settings import CORS_ORIGINS, MAX_CONCURRENT_RUNS, MAX_TOPIC_CHARS, RATE_LIMIT_PER_MINUTE

logger = logging.getLogger("server")

app = FastAPI(title="AETHERIS Research Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

JOB_TTL_SECONDS = 3600

_run_slots = threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)
_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_RUNS)
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


class ResearchRequest(BaseModel):
    topic: str


def _check_rate_limit(request: Request) -> None:
    """Sliding one-minute window per client IP (in-memory, single process)."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _hits_lock:
        hits = _hits[ip]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Too many requests. Try again in a minute.")
        hits.append(now)


def _clean_topic(req: ResearchRequest) -> str:
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    if len(topic) > MAX_TOPIC_CHARS:
        raise HTTPException(status_code=400, detail=f"Topic must be at most {MAX_TOPIC_CHARS} characters")
    return topic


def _acquire_slot() -> None:
    if not _run_slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Server is busy. Try again shortly.")


def _response(state: dict) -> dict:
    return {
        "search_results": state.get("search_results", ""),
        "scraped_content": state.get("scraped_content", ""),
        "report": state.get("report", ""),
        "feedback": state.get("feedback", ""),
        "plan": state.get("plan", []),
        "sources": state.get("sources", []),
        "score": state.get("score"),
        "revisions": state.get("revisions", 0),
    }


def _run(topic: str, on_progress=None) -> dict:
    from pipeline import research_pipeline

    return _response(research_pipeline(topic, on_progress=on_progress))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research")
def run_research(req: ResearchRequest, request: Request):
    _check_rate_limit(request)
    topic = _clean_topic(req)
    _acquire_slot()
    try:
        return _run(topic)
    except Exception:
        logger.exception("Research run failed for topic %r", topic)
        raise HTTPException(status_code=500, detail="Research failed. Please try again.")
    finally:
        _run_slots.release()


def _prune_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    for job_id in [j for j, job in _jobs.items() if job["created"] < cutoff]:
        del _jobs[job_id]


def _job_worker(job_id: str, topic: str) -> None:
    def set_stage(stage: str) -> None:
        with _jobs_lock:
            _jobs[job_id]["stage"] = stage

    try:
        result = _run(topic, on_progress=set_stage)
        update = {"status": "done", "stage": "done", "result": result}
    except Exception:
        logger.exception("Research job %s failed for topic %r", job_id, topic)
        update = {"status": "error", "stage": "error", "error": "Research failed. Please try again."}
    finally:
        _run_slots.release()
    with _jobs_lock:
        _jobs[job_id].update(update)


@app.post("/jobs", status_code=202)
def start_job(req: ResearchRequest, request: Request):
    _check_rate_limit(request)
    topic = _clean_topic(req)
    _acquire_slot()
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _prune_jobs()
        _jobs[job_id] = {"status": "running", "stage": "queued", "created": time.time()}
    try:
        _executor.submit(_job_worker, job_id, topic)
    except Exception:
        _run_slots.release()
        raise
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown job")
        return {k: v for k, v in job.items() if k != "created"}
