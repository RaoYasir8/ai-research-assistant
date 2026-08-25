export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type ResearchListItem = {
  id: string;
  question: string;
  depth: string;
  status: string;
  stage: string;
  progress: number;
  summary: string | null;
  created_at: string;
  completed_at: string | null;
};

export type Source = {
  source_key: string;
  title: string;
  url: string;
  domain: string;
  snippet: string | null;
  fetch_status: string;
};

export type Claim = {
  claim_text: string;
  verdict: string;
  confidence: number;
  grounding_score: number;
  source_keys: string[];
  note: string | null;
};

export type ResearchRun = ResearchListItem & {
  plan: string[] | null;
  report_markdown: string | null;
  warnings: string[] | null;
  model_name: string | null;
  error_message: string | null;
  started_at: string | null;
  sources: Source[];
  claims: Claim[];
};

export type Stats = {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  total_sources: number;
};
