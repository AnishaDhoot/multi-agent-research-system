"""
FastAPI server that wraps your existing research_pipeline.
Run: pip install fastapi uvicorn
     uvicorn server:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AETHERIS Research Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST","GET"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/research")
def run_research(req: ResearchRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    try:
        from pipeline import research_pipeline
        state = research_pipeline(req.topic.strip())
        return {
            "search_results": state.get("search_results", ""),
            "scraped_content": state.get("scraped_content", ""),
            "report": state.get("report", ""),
            "feedback": state.get("feedback", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
