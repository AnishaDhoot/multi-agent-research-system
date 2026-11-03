"use client";
import { useState, useRef, useEffect } from "react";

type ResearchState = {
  search_results: string;
  scraped_content: string;
  report: string;
  feedback: string;
  plan?: string[];
  sources?: { title: string; url: string; scraped: boolean }[];
  score?: number | null;
  revisions?: number;
};

type Phase = "idle" | "planning" | "reading" | "writing" | "critiquing" | "done" | "error";

const PHASES: { key: Phase; label: string; icon: string; desc: string }[] = [
  { key: "planning",  label: "Planner",         icon: "◎", desc: "Breaking the topic into focused search queries" },
  { key: "reading",   label: "Search & Reader", icon: "◈", desc: "Searching and reading several sources in parallel" },
  { key: "writing",   label: "Writer",          icon: "◆", desc: "Synthesizing a cited research report" },
  { key: "critiquing",label: "Critic",          icon: "◇", desc: "Scoring the report and requesting revisions" },
];

// Backend job stages -> UI phases
const STAGE_TO_PHASE: Record<string, Phase> = {
  queued: "planning",
  planning: "planning",
  "reading sources": "reading",
  writing: "writing",
  reviewing: "critiquing",
  revising: "critiquing",
};

const POLL_INTERVAL_MS = 2000;

function escapeHtml(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export default function Home() {
  const [topic, setTopic]         = useState("");
  const [phase, setPhase]         = useState<Phase>("idle");
  const [result, setResult]       = useState<ResearchState | null>(null);
  const [error, setError]         = useState("");
  const [activeTab, setActiveTab] = useState<"report" | "search" | "scraped" | "feedback">("report");
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const [dots, setDots] = useState("");

  // animated dots
  useEffect(() => {
    if (phase === "idle" || phase === "done" || phase === "error") return;
    const i = setInterval(() => setDots(d => d.length >= 3 ? "" : d + "."), 400);
    return () => clearInterval(i);
  }, [phase]);

  // index of the stage currently running (0 when nothing is running)
  const phaseIndex = Math.max(0, PHASES.findIndex(p => p.key === phase));

  async function handleSubmit() {
    if (!topic.trim() || phase !== "idle") return;
    setError("");
    setResult(null);
    setPhase("planning");

    try {
      // Start a background job, then poll it so the progress cards reflect the real stage.
      const start = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      if (!start.ok) {
        const e = await start.json().catch(() => ({}));
        setError(e.error || "Could not start research");
        setPhase("error");
        return;
      }
      const { job_id } = await start.json();

      while (true) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
        const res = await fetch(`/api/research/${encodeURIComponent(job_id)}`, { cache: "no-store" });
        if (!res.ok) {
          const e = await res.json().catch(() => ({}));
          setError(e.error || "Lost contact with the research job");
          setPhase("error");
          return;
        }
        const job = await res.json();
        if (job.status === "done") {
          setResult(job.result as ResearchState);
          setPhase("done");
          setActiveTab("report");
          setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
          return;
        }
        if (job.status === "error") {
          setError(job.error || "Research failed");
          setPhase("error");
          return;
        }
        setPhase(STAGE_TO_PHASE[job.stage] ?? "planning");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Network error");
      setPhase("error");
    }
  }

  function formatReport(report: string) {
    // Escape first: the report is LLM output built from scraped web pages and is injected as HTML below.
    return escapeHtml(report)
      .replace(/^# (.+)$/gm, '<h1 class="rpt-h1">$1</h1>')
      .replace(/^## (.+)$/gm, '<h2 class="rpt-h2">$1</h2>')
      .replace(/^### (.+)$/gm, '<h3 class="rpt-h3">$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .split('\n\n').map(p => {
        if (p.startsWith('<h') || p.startsWith('<ul')) return p;
        if (p.trim() === '') return '';
        return `<p>${p.trim()}</p>`;
      }).join('');
  }

  const isRunning = phase !== "idle" && phase !== "done" && phase !== "error";
  const score = result?.score ?? null;

  return (
    <>
      {/* Ambient background */}
      <div className="noise-overlay" />
      <div className="glow-orb" style={{width:600,height:600,top:-200,left:-200,background:"rgba(124,109,250,0.07)"}} />
      <div className="glow-orb" style={{width:400,height:400,bottom:-150,right:-100,background:"rgba(45,212,191,0.05)"}} />

      <main style={{position:"relative",zIndex:1,minHeight:"100vh",fontFamily:"var(--font-body)"}}>

        {/* ── NAV ── */}
        <nav style={{
          borderBottom:"1px solid var(--border)",
          padding:"0 2rem",
          display:"flex",alignItems:"center",justifyContent:"space-between",
          height:64,backdropFilter:"blur(12px)",
          background:"rgba(10,10,15,0.7)",
          position:"sticky",top:0,zIndex:100
        }}>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <div style={{
              width:32,height:32,borderRadius:8,
              background:"linear-gradient(135deg,#7c6dfa,#2dd4bf)",
              display:"flex",alignItems:"center",justifyContent:"center",
              fontFamily:"var(--font-mono)",fontSize:14,fontWeight:700,color:"#fff"
            }}>Æ</div>
            <span style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:18,letterSpacing:"-0.02em",color:"var(--text-primary)"}}>
              AETHERIS
            </span>
            <span style={{
              marginLeft:8,padding:"2px 8px",borderRadius:4,
              background:"rgba(124,109,250,0.15)",
              color:"var(--accent-bright)",fontSize:11,
              fontFamily:"var(--font-mono)",letterSpacing:"0.08em"
            }}>RESEARCH v1.0</span>
          </div>
          <div style={{display:"flex",gap:24,alignItems:"center"}}>
            {["Agents","Pipeline","Tools"].map(l => (
              <span key={l} style={{fontSize:13,color:"var(--text-muted)",cursor:"pointer",fontFamily:"var(--font-body)",fontWeight:400}}>
                {l}
              </span>
            ))}
            <div style={{
              padding:"6px 16px",borderRadius:6,border:"1px solid var(--border-bright)",
              fontSize:12,fontFamily:"var(--font-mono)",color:"var(--accent-bright)",cursor:"pointer"
            }}>DOCS ↗</div>
          </div>
        </nav>

        {/* ── HERO ── */}
        <section style={{
          maxWidth:860,margin:"0 auto",padding:"80px 2rem 60px",
          textAlign:"center"
        }}>
          <div style={{
            display:"inline-flex",alignItems:"center",gap:8,
            padding:"6px 14px",borderRadius:20,
            border:"1px solid var(--border)",
            background:"rgba(124,109,250,0.08)",
            marginBottom:32,
            fontFamily:"var(--font-mono)",fontSize:11,
            color:"var(--text-secondary)",letterSpacing:"0.1em"
          }}>
            <span style={{width:6,height:6,borderRadius:"50%",background:"var(--teal)",display:"inline-block",boxShadow:"0 0 8px var(--teal)"}} />
            MULTI-AGENT RESEARCH INTELLIGENCE
          </div>

          <h1 style={{
            fontFamily:"var(--font-display)",
            fontSize:"clamp(42px,7vw,80px)",
            fontWeight:800,
            lineHeight:1.0,
            letterSpacing:"-0.04em",
            marginBottom:24,
            background:"linear-gradient(135deg,#f0eeff 0%,#a08bff 50%,#2dd4bf 100%)",
            WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",
            backgroundClip:"text"
          }}>
            Research at the<br/>speed of thought
          </h1>

          <p style={{
            fontSize:17,color:"var(--text-secondary)",maxWidth:520,margin:"0 auto 48px",
            lineHeight:1.7,fontWeight:300
          }}>
            A planner, reader, writer and critic work together — planning searches, reading several sources, writing a cited report and revising it until it passes review.
          </p>

          {/* ── INPUT BOX ── */}
          <div style={{
            background:"var(--bg-1)",
            border:"1px solid var(--border-bright)",
            borderRadius:16,padding:6,
            display:"flex",gap:8,alignItems:"center",
            maxWidth:660,margin:"0 auto",
            boxShadow:"0 0 60px rgba(124,109,250,0.12)"
          }}>
            <input
              ref={inputRef}
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSubmit()}
              placeholder="Enter a research topic…"
              disabled={isRunning}
              style={{
                flex:1,background:"transparent",border:"none",outline:"none",
                padding:"12px 16px",fontSize:16,color:"var(--text-primary)",
                fontFamily:"var(--font-body)",
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={isRunning || !topic.trim()}
              style={{
                padding:"12px 28px",borderRadius:10,border:"none",cursor:isRunning?"not-allowed":"pointer",
                background: isRunning ? "rgba(124,109,250,0.3)" : "linear-gradient(135deg,#7c6dfa,#4a3fb5)",
                color:"#fff",fontFamily:"var(--font-display)",fontWeight:700,
                fontSize:14,letterSpacing:"0.02em",
                transition:"all 0.2s",whiteSpace:"nowrap",
                opacity: isRunning || !topic.trim() ? 0.6 : 1
              }}
            >
              {isRunning ? `Running${dots}` : "RUN RESEARCH →"}
            </button>
          </div>

          {/* quick examples */}
          {phase === "idle" && !result && (
            <div style={{marginTop:20,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
              {["Quantum computing 2025","LLM agents","CRISPR gene therapy","Carbon capture tech"].map(ex => (
                <button key={ex} onClick={() => { setTopic(ex); inputRef.current?.focus(); }}
                  style={{
                    padding:"5px 12px",borderRadius:20,border:"1px solid var(--border)",
                    background:"transparent",color:"var(--text-muted)",
                    fontSize:12,fontFamily:"var(--font-mono)",cursor:"pointer",
                    transition:"all 0.15s"
                  }}
                  onMouseEnter={e=>(e.currentTarget.style.borderColor="var(--border-bright)")}
                  onMouseLeave={e=>(e.currentTarget.style.borderColor="var(--border)")}
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </section>

        {/* ── AGENT PIPELINE VISUALIZATION ── */}
        <section style={{maxWidth:900,margin:"0 auto",padding:"0 2rem 80px"}}>
          <div style={{
            display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12
          }}>
            {PHASES.map((p, i) => {
              const isDone = phase === "done" || phaseIndex > i;
              const isActive = isRunning && phaseIndex === i;

              return (
                <div key={p.key} style={{
                  borderRadius:12,padding:"20px 16px",
                  border:`1px solid ${isActive ? "var(--accent)" : isDone ? "rgba(45,212,191,0.3)" : "var(--border)"}`,
                  background: isActive
                    ? "rgba(124,109,250,0.12)"
                    : isDone
                      ? "rgba(45,212,191,0.06)"
                      : "var(--bg-1)",
                  transition:"all 0.4s",
                  position:"relative",
                  overflow:"hidden"
                }}>
                  {isActive && (
                    <div style={{
                      position:"absolute",top:0,left:"-100%",
                      width:"100%",height:2,
                      background:"linear-gradient(90deg,transparent,var(--accent),transparent)",
                      animation:"sweep 1.5s infinite"
                    }} />
                  )}
                  <div style={{
                    fontFamily:"var(--font-mono)",fontSize:22,
                    color: isActive ? "var(--accent-bright)" : isDone ? "var(--teal)" : "var(--text-muted)",
                    marginBottom:8,transition:"color 0.4s"
                  }}>{isDone ? "✓" : p.icon}</div>
                  <div style={{
                    fontFamily:"var(--font-display)",fontWeight:700,fontSize:13,
                    color: isActive ? "var(--text-primary)" : isDone ? "var(--teal)" : "var(--text-muted)",
                    marginBottom:4,transition:"color 0.4s"
                  }}>{p.label}</div>
                  <div style={{fontSize:11,color:"var(--text-muted)",lineHeight:1.4,fontWeight:300}}>
                    {p.desc}
                  </div>
                  {isActive && (
                    <div style={{
                      marginTop:10,display:"flex",gap:3
                    }}>
                      {[0,1,2].map(j => (
                        <div key={j} style={{
                          width:4,height:4,borderRadius:"50%",
                          background:"var(--accent)",
                          animation:`pulse 1s ${j*0.2}s infinite`
                        }} />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ── ERROR ── */}
        {phase === "error" && (
          <section style={{maxWidth:700,margin:"0 auto",padding:"0 2rem 60px"}}>
            <div style={{
              borderRadius:12,padding:24,
              border:"1px solid rgba(255,107,107,0.3)",
              background:"rgba(255,107,107,0.07)",
            }}>
              <div style={{fontFamily:"var(--font-mono)",color:"var(--coral)",marginBottom:8,fontSize:13}}>
                ✕ PIPELINE ERROR
              </div>
              <p style={{color:"var(--text-secondary)",fontSize:14}}>{error}</p>
              <button onClick={() => setPhase("idle")} style={{
                marginTop:16,padding:"8px 20px",borderRadius:8,
                border:"1px solid rgba(255,107,107,0.4)",
                background:"transparent",color:"var(--coral)",
                fontFamily:"var(--font-mono)",fontSize:12,cursor:"pointer"
              }}>RESET</button>
            </div>
          </section>
        )}

        {/* ── RESULTS ── */}
        {phase === "done" && result && (
          <section ref={resultRef} style={{maxWidth:900,margin:"0 auto",padding:"0 2rem 120px"}}>

            {/* Stats row */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:24}}>
              {[
                { label:"Search Queries", value: result.plan?.length ?? null, unit:"" },
                { label:"Sources Used", value: result.sources?.length ?? (result.search_results.match(/URL:/g)||[]).length, unit:"" },
                { label:"Revisions", value: result.revisions ?? null, unit:"" },
                { label:"Critic Score", value: score, unit:"/10" },
              ].map(s => (
                <div key={s.label} style={{
                  borderRadius:12,padding:"20px 24px",
                  background:"var(--bg-1)",border:"1px solid var(--border)"
                }}>
                  <div style={{fontSize:11,color:"var(--text-muted)",fontFamily:"var(--font-mono)",letterSpacing:"0.08em",marginBottom:8}}>
                    {s.label.toUpperCase()}
                  </div>
                  <div style={{
                    fontFamily:"var(--font-display)",fontWeight:700,fontSize:36,
                    color: s.label==="Critic Score" && score
                      ? score >= 8 ? "var(--teal)" : score >= 6 ? "var(--gold)" : "var(--coral)"
                      : "var(--accent-bright)"
                  }}>
                    {s.value ?? "—"}<span style={{fontSize:16,color:"var(--text-muted)"}}>{s.unit}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Tab bar */}
            <div style={{
              display:"flex",gap:2,marginBottom:0,
              background:"var(--bg-1)",borderRadius:"12px 12px 0 0",
              border:"1px solid var(--border)",borderBottom:"none",
              padding:"6px 6px 0"
            }}>
              {(["report","feedback","search","scraped"] as const).map(t => (
                <button key={t} onClick={() => setActiveTab(t)} style={{
                  padding:"10px 20px",borderRadius:"8px 8px 0 0",border:"none",cursor:"pointer",
                  background: activeTab===t ? "var(--bg-2)" : "transparent",
                  color: activeTab===t ? "var(--text-primary)" : "var(--text-muted)",
                  fontFamily:"var(--font-display)",fontWeight:activeTab===t?700:400,
                  fontSize:13,transition:"all 0.15s",letterSpacing:"0.01em",
                  borderBottom: activeTab===t ? "2px solid var(--accent)" : "2px solid transparent"
                }}>
                  {t === "report" ? "📄 Report" : t === "feedback" ? "⭐ Critique" : t === "search" ? "🔍 Sources" : "📌 Scraped Content"}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{
              background:"var(--bg-1)",border:"1px solid var(--border)",
              borderRadius:"0 0 12px 12px",minHeight:400,
            }}>
              {activeTab === "report" && (
                <div style={{padding:"32px 40px"}} className="report-content"
                  dangerouslySetInnerHTML={{__html: formatReport(result.report)}}
                />
              )}
              {activeTab === "feedback" && (
                <div style={{padding:"32px 40px"}}>
                  {/* Score visualization */}
                  {score && (
                    <div style={{
                      marginBottom:32,padding:"24px 28px",borderRadius:12,
                      border:"1px solid var(--border)",background:"var(--bg-2)",
                      display:"flex",alignItems:"center",gap:24
                    }}>
                      <div style={{
                        width:80,height:80,borderRadius:"50%",
                        border:`3px solid ${score>=8?"var(--teal)":score>=6?"var(--gold)":"var(--coral)"}`,
                        display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,
                        boxShadow:`0 0 24px ${score>=8?"rgba(45,212,191,0.3)":score>=6?"rgba(245,200,66,0.3)":"rgba(255,107,107,0.3)"}`
                      }}>
                        <span style={{
                          fontFamily:"var(--font-display)",fontWeight:800,fontSize:28,
                          color:score>=8?"var(--teal)":score>=6?"var(--gold)":"var(--coral)"
                        }}>{score}</span>
                      </div>
                      <div>
                        <div style={{fontFamily:"var(--font-mono)",fontSize:11,color:"var(--text-muted)",letterSpacing:"0.08em",marginBottom:4}}>
                          CRITIC SCORE
                        </div>
                        <div style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:20,color:"var(--text-primary)"}}>
                          {score >= 8 ? "Excellent Report" : score >= 6 ? "Good Report" : "Needs Improvement"}
                        </div>
                        <div style={{fontSize:13,color:"var(--text-muted)",marginTop:4}}>
                          Evaluated by the AI critic chain
                        </div>
                      </div>
                    </div>
                  )}
                  <pre style={{
                    fontFamily:"var(--font-mono)",fontSize:13,lineHeight:1.8,
                    color:"var(--text-secondary)",whiteSpace:"pre-wrap",wordBreak:"break-word"
                  }}>{result.feedback}</pre>
                </div>
              )}
              {activeTab === "search" && (
                <div style={{padding:"32px 40px"}}>
                  {result.plan && result.plan.length > 0 && (
                    <div style={{marginBottom:24}}>
                      <div style={{fontFamily:"var(--font-mono)",fontSize:11,color:"var(--text-muted)",letterSpacing:"0.08em",marginBottom:8}}>
                        SEARCH QUERIES PLANNED
                      </div>
                      <ul style={{margin:0,paddingLeft:18,color:"var(--text-secondary)",fontSize:13,lineHeight:1.8}}>
                        {result.plan.map(q => <li key={q}>{q}</li>)}
                      </ul>
                    </div>
                  )}
                  <pre style={{
                    fontFamily:"var(--font-mono)",fontSize:12,lineHeight:1.8,
                    color:"var(--text-secondary)",whiteSpace:"pre-wrap",wordBreak:"break-word"
                  }}>{result.search_results}</pre>
                </div>
              )}
              {activeTab === "scraped" && (
                <div style={{padding:"32px 40px"}}>
                  <pre style={{
                    fontFamily:"var(--font-mono)",fontSize:12,lineHeight:1.8,
                    color:"var(--text-secondary)",whiteSpace:"pre-wrap",wordBreak:"break-word"
                  }}>{result.scraped_content}</pre>
                </div>
              )}
            </div>

            {/* New research button */}
            <div style={{textAlign:"center",marginTop:32}}>
              <button onClick={() => { setPhase("idle"); setResult(null); setTopic(""); window.scrollTo({top:0,behavior:"smooth"}); }}
                style={{
                  padding:"12px 32px",borderRadius:8,
                  border:"1px solid var(--border-bright)",
                  background:"transparent",color:"var(--accent-bright)",
                  fontFamily:"var(--font-display)",fontWeight:700,fontSize:14,cursor:"pointer"
                }}>
                ← NEW RESEARCH
              </button>
            </div>
          </section>
        )}

        {/* ── HOW IT WORKS (idle state) ── */}
        {phase === "idle" && !result && (
          <section style={{maxWidth:900,margin:"0 auto",padding:"0 2rem 120px"}}>
            <div style={{
              textAlign:"center",marginBottom:40
            }}>
              <div style={{fontFamily:"var(--font-mono)",fontSize:11,color:"var(--text-muted)",letterSpacing:"0.12em",marginBottom:12}}>
                ARCHITECTURE
              </div>
              <h2 style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:28,letterSpacing:"-0.02em",color:"var(--text-primary)"}}>
                Four agents, one pipeline
              </h2>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
              {[
                { icon:"◎", title:"Planner", color:"#7c6dfa", body:"Breaks your topic into 3–4 focused search queries so the research covers fundamentals, recent developments, challenges and data — not just one angle." },
                { icon:"◈", title:"Search & Reader", color:"#2dd4bf", body:"Runs the queries through Tavily, ranks results by source quality, then reads up to 6 pages in parallel — falling back to Tavily Extract for sites that block scrapers." },
                { icon:"◆", title:"Writer", color:"#f5c842", body:"Synthesizes the sources into a structured report with inline [n] citations. Only sources the report actually cites appear in the final Sources list." },
                { icon:"◇", title:"Critic", color:"#ff6b6b", body:"Scores the report out of 10 with strengths and improvements. Below 8, the writer revises using the feedback — up to two times." },
              ].map(card => (
                <div key={card.title} style={{
                  borderRadius:14,padding:"28px 28px",
                  background:"var(--bg-1)",border:"1px solid var(--border)",
                }}>
                  <div style={{fontSize:28,marginBottom:12,color:card.color}}>{card.icon}</div>
                  <h3 style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:16,color:"var(--text-primary)",marginBottom:10}}>
                    {card.title}
                  </h3>
                  <p style={{fontSize:13,color:"var(--text-muted)",lineHeight:1.7,fontWeight:300}}>
                    {card.body}
                  </p>
                </div>
              ))}
            </div>

            {/* Python backend note */}
            <div style={{
              marginTop:24,borderRadius:12,padding:"20px 24px",
              border:"1px solid rgba(245,200,66,0.2)",
              background:"rgba(245,200,66,0.05)",
              display:"flex",gap:12,alignItems:"flex-start"
            }}>
              <span style={{fontSize:18,marginTop:1}}>⚡</span>
              <div>
                <div style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:13,color:"var(--gold)",marginBottom:6}}>
                  Backend Setup Required
                </div>
                <p style={{fontSize:12,color:"var(--text-muted)",lineHeight:1.7}}>
                  This UI starts a job on your Python backend via <code style={{fontFamily:"var(--font-mono)",background:"rgba(255,255,255,0.06)",padding:"1px 6px",borderRadius:4,fontSize:11}}>POST /api/research</code> and polls it until the report is ready.
                  Run <code style={{fontFamily:"var(--font-mono)",background:"rgba(255,255,255,0.06)",padding:"1px 6px",borderRadius:4,fontSize:11}}>uvicorn server:app --port 8000</code> and set <code style={{fontFamily:"var(--font-mono)",background:"rgba(255,255,255,0.06)",padding:"1px 6px",borderRadius:4,fontSize:11}}>PYTHON_BACKEND_URL</code> in <code style={{fontFamily:"var(--font-mono)",background:"rgba(255,255,255,0.06)",padding:"1px 6px",borderRadius:4,fontSize:11}}>.env.local</code>.
                  Set <code style={{fontFamily:"var(--font-mono)",background:"rgba(255,255,255,0.06)",padding:"1px 6px",borderRadius:4,fontSize:11}}>DEMO_MODE=true</code> to try the UI with sample data.
                </p>
              </div>
            </div>
          </section>
        )}
      </main>

      <style>{`
        @keyframes sweep {
          0% { left: -100%; }
          100% { left: 200%; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
        .report-content h1.rpt-h1 {
          font-family: var(--font-display);
          font-size: 28px;
          font-weight: 800;
          letter-spacing: -0.02em;
          color: var(--text-primary);
          margin: 0 0 24px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border);
        }
        .report-content h2.rpt-h2 {
          font-family: var(--font-display);
          font-size: 20px;
          font-weight: 700;
          color: var(--accent-bright);
          margin: 32px 0 14px;
          letter-spacing: -0.01em;
        }
        .report-content h3.rpt-h3 {
          font-family: var(--font-display);
          font-size: 16px;
          font-weight: 700;
          color: var(--teal);
          margin: 24px 0 10px;
        }
        .report-content p {
          font-size: 15px;
          line-height: 1.8;
          color: var(--text-secondary);
          margin: 0 0 16px;
        }
        .report-content strong {
          color: var(--text-primary);
          font-weight: 600;
        }
        .report-content em {
          color: var(--gold);
          font-style: normal;
        }
        .report-content ul {
          margin: 12px 0 20px 0;
          padding-left: 0;
          list-style: none;
        }
        .report-content li {
          font-size: 14px;
          color: var(--text-secondary);
          line-height: 1.7;
          padding: 8px 16px;
          margin-bottom: 6px;
          border-left: 2px solid var(--accent);
          background: rgba(124,109,250,0.05);
          border-radius: 0 6px 6px 0;
        }
      `}</style>
    </>
  );
}
