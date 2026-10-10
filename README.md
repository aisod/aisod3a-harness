# aisod3a-harness

**AISOD 3A — AI Automation Agent.** Founder's Directive IV (the AISOD 3A Charter, September 2026).

AISOD 3A is **Hermes Agent itself** — the full Nous Research engine, with every capability intact — branded and wired per the Charter. It is a focus layer ON Hermes, never a replacement. It runs as a dedicated Hermes **profile**, so nothing is stripped: all tools (file, terminal, web, browser, code execution, vision, delegation, cron, kanban, memory, skills), all surfaces (CLI, TUI, desktop app, dashboard, messaging gateway), all providers.

**Live:** https://github.com/aisod/aisod3a-harness

---

## What it is

AISOD 3A means **AI Automation Agent** — three words, three A's (Charter Article I). Not a slogan, an architecture. The name describes one system with three layers built to depend on each other:

1. **Model Family** — the intelligence: 1B/2B/3B/7B tiers fine-tuned on the AISOD African Corpus. On its own it understands language but doesn't act.
2. **Harness** — the orchestration engine: Planner, Coder, Researcher, Evaluator working together so a multi-step task is carried out, not just answered once.
3. **Agent** — the product: what a person or system calls to get an automated task done in a Namibian or African language.

None of the three is optional. A model with no harness talks but doesn't act; a harness with no model of our own orchestrates someone else's intelligence; an agent is only as trustworthy as the model and harness underneath.

## The Harness pipeline

Four agent roles, each a `delegate_task` subagent with the **full** Hermes toolset (never a stripped-down version):

- **Planner** — decomposes a goal into ordered, agent-assignable steps.
- **Coder** — produces artefacts: code, scripts, documents, configs, data transformations.
- **Researcher** — gathers information: web, docs, context. Prefers citing sources.
- **Evaluator** — the quality gate. Reviews work against spec; outputs a structured verdict (passed / score / issues / recommendation).

Flow: goal → Planner → steps execute in dependency order (each sees its dependencies' outputs) → Evaluator reviews → combined report with plan, per-step outputs, evaluation, and model-routing status.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/aisod/aisod3a-harness.git
cd aisod3a-harness

# 2. Create the Hermes profile + install the Charter identity
bash setup.sh

# 3. Run it — full Hermes capabilities, AISOD 3A identity
hermes -p aisod3a chat

# 4. Pick a working model/provider for the profile
hermes -p aisod3a model
```

The `aisod3a` profile is cloned from Hermes's `default` profile, so it inherits the entire capability set. `setup.sh` only adds the Charter identity (`profile/SOUL.md`).

---

## The Dependency Rule (Charter Article III)

AISOD's own models are the default once they reach proven quality. Third-party models (Qwen, Kimi, DeepSeek, and the like) are an explicit, **logged** fallback only — never the quiet default because switching was never prioritized. Every run reports which path it took: `using_aisod_local` or `using_fallback`. If local weights aren't on disk yet, the bridge path is acceptable — but it must be logged, not silent. An automation agent that depends permanently on someone else's model isn't sovereign, no matter what it's called.

---

## What it automates, in order (Charter Article IV)

The Agent earns its way outward. It does not launch as a general-purpose product before proving itself on work AISOD already owns.

- **FIRST** — our own pipeline: OCR extraction, automated cleaning, language detection, and drafting instruction pairs for the Corpus. A human still makes every certification decision — the harness only drafts.
- **SECOND** — Osona Connect's backend, once proven internally, benchmarked against the DeepSeek/Qwen baseline it replaces before it goes live.
- **THEN** — an offering to others: African businesses and institutions needing automation that understands their languages and context.

## What it is NOT (Charter Article VI)

- Not a public "build anything" platform yet. The plugin-ecosystem ambition (GitHub, AWS, Slack, Stripe) stays parked until the first two proving grounds are real.
- Not a replacement for human judgment in the Corpus. It may suggest a quality-level advance. It never executes one.
- Not deployed customer-facing before proven internally. The order in Article IV is not a suggestion.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│            Hermes Agent (full capability set)         │
│  all tools · all surfaces (CLI/TUI/desktop/dash/gw)  │
│  all providers                                        │
├──────────────────────────────────────────────────────┤
│   AISOD 3A focus layer  (profile: aisod3a)            │
│   Charter identity (SOUL.md) + 4-role pipeline skill │
│   Planner → Coder + Researcher → Evaluator           │
│   (each a delegate_task subagent, full toolset)      │
├──────────────────────────────────────────────────────┤
│   Model layer — Dependency Rule routing               │
│   AISOD LRLM (sovereign default, once proven)        │
│   → Hermes provider pool / any model (logged bridge) │
└──────────────────────────────────────────────────────┘
```

---

## Repository layout

| Path | What it is |
|---|---|
| `setup.sh` | Creates the `aisod3a` Hermes profile and installs the Charter identity |
| `profile/SOUL.md` | The AISOD 3A Charter identity (Articles I–VII), installed into the profile |
| `aisod-3a-harness` skill | The 4-role pipeline operating guide (Planner/Coder/Researcher/Evaluator) |

### Legacy (deprecated)

An earlier build shipped a standalone `aisod3a_harness.py` script plus an API/web package. That approach was **retired**: run outside Hermes it replaced the agent surface and lost every Hermes capability, violating the core directive that 3A is a focus layer ON Hermes. Those files may still exist in git history but are no longer the architecture. Do not rebuild AISOD 3A as a standalone script.

---

## Local languages

The AISOD African Corpus powers language integration. As it grows: more languages become available for detection, translation, and generation; better accuracy on low-resource languages (Oshikwanyama, Rugciriku, Ju/'hoan, etc.); more instruction pairs for fine-tuning. The Corpus pipeline (Charter Article IV, FIRST): OCR extraction → automated cleaning → language detection → instruction-pair drafting. Human still certifies every decision.

---

## License

MIT — same as Hermes Agent.

---

*Built on Hermes Agent. AISOD 3A — AI Automation Agent. Founder's Directive IV.*
