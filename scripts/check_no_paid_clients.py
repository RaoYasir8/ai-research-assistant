from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'node_modules', '.next', '__pycache__'}
NEEDLES = {
    'openai', 'anthropic', 'tavily', 'serpapi', 'perplexity',
    'elevenlabs', 'pinecone', 'cohere', 'mistralai', 'google.generativeai'
}

hits = []
for path in ROOT.rglob('*'):
    if path.resolve() == Path(__file__).resolve():
        continue
    if not path.is_file() or any(part in SKIP for part in path.parts):
        continue
    if path.suffix.lower() not in {'.py', '.ts', '.tsx', '.json', '.toml'}:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore').lower()
    for needle in NEEDLES:
        if needle in text:
            hits.append(f'{path.relative_to(ROOT)}: {needle}')

if hits:
    raise SystemExit('Paid-provider client reference found:\n' + '\n'.join(sorted(set(hits))))

print('No paid-provider runtime client references found.')
