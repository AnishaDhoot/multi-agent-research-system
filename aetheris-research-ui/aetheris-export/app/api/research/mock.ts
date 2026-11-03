// Demo data, only served when DEMO_MODE=true in .env.local.
export function getMockData(topic: string) {
  const sources = [
    { title: `${topic} — Overview`, url: "https://example.com/overview", scraped: true },
    { title: `Recent Advances in ${topic}`, url: "https://example.com/advances", scraped: false },
  ];
  return {
    plan: [`${topic} fundamentals`, `${topic} recent developments`, `${topic} challenges`],
    sources,
    score: 8,
    revisions: 0,
    search_results: sources
      .map((s, i) => `[${i + 1}] ${s.title}\nURL: ${s.url}\nSnippet: Demo snippet about ${topic}.`)
      .join("\n\n"),
    scraped_content: `Demo scraped content about "${topic}". Start the Python backend and unset DEMO_MODE to see real results.`,
    report: `# Research Report: ${topic}\n\n## Introduction\n\nThis is demo data for ${topic} [1].\n\n## Key Findings\n\n### 1. Demo finding\nThe UI is running without the Python backend [1, 2].\n\n## Conclusion\n\nSet up the backend to get a real report.\n\n## Sources\n${sources.map((s, i) => `[${i + 1}] ${s.title} - ${s.url}`).join("\n")}`,
    feedback: "Score: 8/10\n\nStrengths:\n- Demo strength\n\nAreas to Improve:\n- This is demo data\n\nOne line verdict:\nDemo only.",
  };
}
