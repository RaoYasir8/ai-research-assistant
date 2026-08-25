import Link from "next/link";

const agents = [
  ["Planner", "breaks the question into focused searches"],
  ["Researcher", "collects and cleans source evidence"],
  ["Fact checker", "flags weak or unsupported claims"],
  ["Writer", "produces a cited research brief"],
];

export default function Home() {
  return (
    <main>
      <section className="shell hero">
        <div>
          <div className="kicker">Local-first research workflow</div>
          <h1>Research the web without handing your work to a paid AI API.</h1>
          <p className="lead">
            A multi-agent research workspace that plans, searches, checks evidence and writes source-aware reports using a local model and self-hosted search.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" href="/register">Create an account</Link>
            <Link className="btn" href="/login">Sign in</Link>
          </div>
        </div>
        <div className="hero-card">
          <div className="kicker">Research pipeline</div>
          {agents.map(([name, copy], index) => (
            <div className="agent-row" key={name}>
              <div>
                <div className="agent-name">{index + 1}. {name}</div>
                <div className="muted" style={{fontSize: 12, marginTop: 4}}>{copy}</div>
              </div>
              <span className="agent-state">isolated stage</span>
            </div>
          ))}
        </div>
      </section>
      <section className="shell section">
        <div className="grid-3">
          <div className="card"><h3>Evidence first</h3><p>Sources are deduplicated, public URLs are safety-checked, and generated citations are validated against collected evidence.</p></div>
          <div className="card"><h3>Local model</h3><p>Ollama runs the language model on your own machine. No commercial inference key is required by the application.</p></div>
          <div className="card"><h3>Traceable output</h3><p>Every run keeps its plan, source list, fact-check results, warnings and final Markdown report in one workspace.</p></div>
        </div>
      </section>
      <footer className="footer"><div className="shell">Built as a practical, inspectable research system.</div></footer>
    </main>
  );
}
