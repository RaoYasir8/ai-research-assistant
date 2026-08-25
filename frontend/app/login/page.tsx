import AuthForm from "@/components/AuthForm";
export default function LoginPage() { return <main className="auth-wrap"><div className="card auth-card"><div className="kicker">Welcome back</div><h2 style={{marginTop: 10}}>Sign in</h2><p className="muted">Open your research workspace.</p><AuthForm mode="login" /></div></main>; }
