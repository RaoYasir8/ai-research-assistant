import AuthForm from "@/components/AuthForm";
export default function RegisterPage() { return <main className="auth-wrap"><div className="card auth-card"><div className="kicker">Local-first workspace</div><h2 style={{marginTop: 10}}>Create account</h2><p className="muted">Keep your research history organized.</p><AuthForm mode="register" /></div></main>; }
