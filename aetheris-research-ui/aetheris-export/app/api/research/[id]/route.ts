import { NextRequest, NextResponse } from "next/server";
import { getMockData } from "../mock";

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
const DEMO_MODE = process.env.DEMO_MODE === "true";

// Proxies job status/result from the Python backend.
export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  if (DEMO_MODE && id.startsWith("demo:")) {
    const topic = decodeURIComponent(id.slice(5));
    return NextResponse.json({ status: "done", stage: "done", result: getMockData(topic) });
  }

  try {
    const res = await fetch(`${PYTHON_BACKEND_URL}/jobs/${encodeURIComponent(id)}`, {
      signal: AbortSignal.timeout(15000),
      cache: "no-store",
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      return NextResponse.json(
        { error: body?.detail ?? `Backend error (${res.status})` },
        { status: res.status }
      );
    }
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: "Cannot reach the research backend." }, { status: 502 });
  }
}
