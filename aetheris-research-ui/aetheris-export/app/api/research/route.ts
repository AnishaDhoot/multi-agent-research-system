import { NextRequest, NextResponse } from "next/server";

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
const DEMO_MODE = process.env.DEMO_MODE === "true";

// Starts a research job on the Python backend and returns its id.
// The client then polls GET /api/research/[id] for progress and the result.
export async function POST(req: NextRequest) {
  const { topic } = await req.json();

  if (!topic || typeof topic !== "string" || topic.trim().length === 0) {
    return NextResponse.json({ error: "Topic is required" }, { status: 400 });
  }

  if (DEMO_MODE) {
    return NextResponse.json({ job_id: `demo:${encodeURIComponent(topic.trim())}` }, { status: 202 });
  }

  try {
    const res = await fetch(`${PYTHON_BACKEND_URL}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topic.trim() }),
      signal: AbortSignal.timeout(15000),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      return NextResponse.json(
        { error: body?.detail ?? `Backend error (${res.status})` },
        { status: res.status }
      );
    }
    return NextResponse.json(await res.json(), { status: 202 });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach the research backend. Is the Python server running? (Set DEMO_MODE=true for demo data.)" },
      { status: 502 }
    );
  }
}
