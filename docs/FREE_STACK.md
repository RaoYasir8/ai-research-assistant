# Zero-paid runtime policy

The project is designed to run without a commercial AI or search API key.

| Capability | Implementation | Cost model |
| --- | --- | --- |
| LLM inference | Ollama + `qwen3:1.7b` | local/open model runtime |
| Agent orchestration | LangGraph | open-source package |
| Web search | self-hosted SearXNG | self-hosted/open-source |
| Article extraction | Trafilatura | open-source package |
| API | FastAPI | open-source package |
| Database | PostgreSQL | open-source |
| Queue | Redis-compatible server | local container |
| Frontend | Next.js + React | open-source packages |
| Deployment | Docker Compose | local/self-hosted |

No OpenAI, Anthropic, Tavily, SerpAPI, Pinecone, ElevenLabs or other paid-provider client is required by the codebase.

"Free" here means there is no paid API requirement. Running containers still uses your own computer, electricity, bandwidth and storage. Cloud hosting can introduce provider costs depending on where you choose to deploy it.
