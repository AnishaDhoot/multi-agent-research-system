import { NextRequest, NextResponse } from "next/server";

// This is the Next.js API route that connects to your Python backend.
// Update PYTHON_BACKEND_URL to point to your running pipeline server.
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const { topic } = await req.json();

  if (!topic || typeof topic !== "string" || topic.trim().length === 0) {
    return NextResponse.json({ error: "Topic is required" }, { status: 400 });
  }

  try {
    // Attempt to call the Python backend
    const res = await fetch(`${PYTHON_BACKEND_URL}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topic.trim() }),
      // 3-minute timeout for long-running research
      signal: AbortSignal.timeout(180000),
    });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json(
        { error: `Backend error: ${errorText}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    // If the backend is not running, return mock data for UI development
    const errorMessage = err instanceof Error ? err.message : "Unknown error";
    console.warn("Python backend not reachable, returning mock data:", errorMessage);
    return NextResponse.json(getMockData(topic));
  }
}

function getMockData(topic: string) {
  return {
    search_results: `Mock search results for "${topic}":\n\nTitle: ${topic} — Overview\nURL: https://example.com/overview\nSnippet: A comprehensive look at ${topic} covering the latest developments, key players, and future trajectory.\n\n-------\n\nTitle: Recent Advances in ${topic}\nURL: https://example.com/advances\nSnippet: Researchers and industry leaders have made significant strides in ${topic} over the past year, with several breakthroughs reshaping how we understand the field.`,
    scraped_content: `Detailed scraped content from the top result on "${topic}":\n\nThe field of ${topic} has evolved dramatically. Key developments include: improved methodologies, wider adoption across industries, and growing academic interest. Experts agree that ${topic} represents a paradigm shift in how we approach complex problems. The main challenges going forward involve scalability, interpretability, and ensuring ethical deployment.`,
    report: `# Research Report: ${topic}\n\n## Introduction\n\n${topic} is a rapidly evolving domain with significant implications across multiple sectors. This report synthesizes the latest available information to provide a comprehensive overview of the current state, key findings, and future outlook.\n\n## Key Findings\n\n### 1. Rapid Ecosystem Growth\nThe ${topic} ecosystem has seen exponential growth, with an increasing number of contributors, tools, and real-world applications emerging. Major tech companies and startups alike are investing heavily in this space.\n\n### 2. Interdisciplinary Convergence\nOne of the most notable trends is the convergence of ${topic} with adjacent fields. This cross-pollination is accelerating innovation and creating entirely new sub-disciplines that were not anticipated even a few years ago.\n\n### 3. Regulatory and Ethical Considerations\nAs ${topic} matures, regulatory frameworks are beginning to catch up. Policymakers worldwide are grappling with how to govern this technology responsibly, balancing innovation with safety and equity.\n\n## Conclusion\n\nThe trajectory of ${topic} points toward continued rapid development. Stakeholders across academia, industry, and government will need to collaborate to harness its potential while mitigating risks. This is a pivotal moment for the field.\n\n## Sources\n- https://example.com/overview\n- https://example.com/advances\n- https://example.com/research`,
    feedback: `Score: 8/10\n\nStrengths:\n- Well-structured with clear sections\n- Covers both technical and policy dimensions\n- Balanced perspective without undue bias\n\nAreas to Improve:\n- Could include more quantitative data and statistics\n- Specific case studies would strengthen key findings\n- Future outlook section could be more detailed\n\nOne line verdict:\nA solid, professional research report that covers the fundamentals well but would benefit from deeper empirical grounding.`,
  };
}
