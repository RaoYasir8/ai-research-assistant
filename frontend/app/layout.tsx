import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Research Assistant",
  description: "Local-first multi-agent research with source-aware reports.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="nav">
          <div className="shell nav-inner">
            <Link className="brand" href="/">
              <span className="brand-mark">AR</span>
              <span>AI Research Assistant</span>
            </Link>
            <nav className="nav-links">
              <Link className="hide-mobile" href="/dashboard">Dashboard</Link>
              <Link className="hide-mobile" href="/research">Research</Link>
              <Link className="btn btn-primary" href="/research/new">New research</Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
