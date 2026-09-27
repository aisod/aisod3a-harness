# aisod3a-harness

**AISOD 3A Harness — AI Automation Agent**

Model-agnostic AI orchestration built on Hermes Agent. Use any AI model until AISOD 3A models are ready. Local African languages available as the Corpus grows.

**Live:** https://github.com/aisod/aisod3a-harness

---

## What it is

The AISOD 3A Harness is the orchestration engine from Founder's Directive IV (the AISOD 3A Charter, September 2026). It wires four agent roles — **Planner → Coder + Researcher → Evaluator** — into a single pipeline that takes a goal and carries it out across multiple steps.

It's built **on top of Hermes Agent**, so when you run it inside Hermes, every role gets the full Hermes toolset: file read/write, terminal commands, web search, and more. When you run it standalone, it falls back to direct model calls.

**Three layers (Charter Article II):**
1. **Model Family** — AISOD's own models (LRLM) preferred; any model as bridge
2. **Harness** — this repo: the Planner/Coder/Researcher/Evaluator orchestration
3. **Agent** — the product surface: web dashboard, CLI, API

**Model-agnostic by design:** Use *any* AI model via the `model` field — Hermes provider pool, OpenRouter, OpenAI, or your own. When AISOD 3A models are ready, they slot in as the default. No code changes needed.

**Local languages:** As the AISOD African Corpus grows (5M+ words, 50 languages, 6 countries), more local languages become available. The harness integrates with the corpus pipeline — OCR extraction, automated cleaning, language detection, and instruction-pair drafting — and gets better as the data grows.

---

## Quick start

### Web dashboard (Vercel)

```bash
# Clone and run the web dashboard locally
git clone https://github.com/aisod/aisod3a-harness.git
cd aisod3a-harness/web
npm install
npm run dev
# Open http://localhost:3000
```

### API server

```bash
# Run the model-agnostic API
pip install fastapi uvicorn pydantic httpx
python api_server.py
# API docs: http://localhost:8000/docs
```

### CLI (installable, like Hermes)

```bash
# Install the CLI
pip install -e .

# Run the harness
aisod3a "OCR-extract and clean the Oshindonga PDFs"
aisod3a status
aisod3a corpus
```

---

## Deployment

### Vercel — Web Dashboard

1. Push to GitHub
2. Import `web/` as a Vercel project
3. Set environment variables:
   - `AISOD_API_URL` — URL of your API server (e.g. `https://api.yourdomain.com`)
4. Deploy

### Any host — API Server

```bash
# Docker
docker build -t aisod3a-harness -f Dockerfile.api .
docker run -p 8000:8000 aisod3a-harness

# Or bare metal
pip install -r api-requirements.txt
python api_server.py
```

### Vercel + API combo

Run the API on any host (Railway, Render, Heroku, your own server) and point the Vercel web dashboard at it via `AISOD_API_URL`.

---

## Model routing

| Model field | What it does |
|---|---|
| `hermes` | Uses your Hermes provider pool — any model you've configured (OpenAI, OpenRouter, Anthropic, etc.) |
| `aisod-local` | Uses AISOD's own LRLM local models (mistral-7b, llama-3.2-3b) — the sovereign path |
| `openrouter` | Any model on OpenRouter |
| *any string* | Passed through for future provider expansion |

Set `AISOD_HARNESS_FALLBACK_MODEL` to pick the default when using the Hermes pool.

**Until AISOD 3A models are ready:** use `hermes` or `openrouter` — any model works. The harness is model-agnostic by design.

**When AISOD 3A models are ready:** they replace the default. The Dependency Rule (Charter Article III) ensures our models are the primary engine, with third-party models as an explicit fallback.

---

## Local languages

The AISOD African Corpus powers language integration. As it grows:

- **More languages** become available for detection, translation, and generation
- **Better accuracy** on low-resource languages (Oshikwanyama, Rugciriku, Ju/'hoan, etc.)
- **More instruction pairs** for fine-tuning

The harness integrates with the Corpus pipeline (Charter Article IV, FIRST): OCR extraction → automated cleaning → language detection → instruction-pair drafting. Human still certifies every decision.

Current corpus scope: 5M+ words, 50 languages, 6 countries. Growing.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 Web Dashboard (Vercel)           │
│  React + Tailwind  →  AISOD_API_URL  →  API     │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│              API Server (FastAPI / Python)       │
│  /v1/chat/completions  /v1/harness/run          │
│  /v1/models            /v1/harness/status        │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│              AISOD 3A Harness (Python)           │
│  Planner → Coder + Researcher → Evaluator       │
│  (delegate_task subagents when inside Hermes)   │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│           Model Layer — Any Model               │
│  Hermes pool / OpenRouter / OpenAI / AISOD LRLM │
└─────────────────────────────────────────────────┘
```

---

## License

MIT — same as Hermes Agent.

---

## Documentation index

- `web/` — Next.js web dashboard (Vercel deployment)
- `api_server.py` — Model-agnostic FastAPI server
- `aisod3a_harness.py` — Core harness (Planner/Coder/Researcher/Evaluator)
- `cli/` — Installable CLI tool
- `docs/` — Full documentation (setup, deployment, model routing, corpus integration)
- `Dockerfile.api` — Docker build for the API server
- `requirements.txt` — Python dependencies

---

*Built on Hermes Agent. AISOD 3A — AI Automation Agent. Founder's Directive IV.*
