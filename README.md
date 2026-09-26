# aisod3a-harness

AISOD 3A Harness — AI Automation Agent orchestration engine.

Built on top of Hermes Agent.  When run inside Hermes, every role
(Planner, Coder, Researcher, Evaluator) is a delegate_task subagent
with the full Hermes toolset.  When run standalone, roles fall back
to direct model calls.

This is the focus layer on top of Hermes that implements the three-layer
architecture defined in Founder's Directive IV (the AISOD 3A Charter,
September 2026):

  1. Model Family  — AISOD's own models (LRLM) preferred; Hermes pool as bridge
  2. Harness       — this repo: Planner -> Coder + Researcher -> Evaluator
  3. Agent         — the product surface (Android app, API, CLI)

Dependency Rule (Charter Article III):
  AISOD models are the default once they meet the Moat Charter benchmarks.
  Until then, Hermes's provider pool is the explicit bridge — never the
  quiet default.

First proving ground (Charter Article IV, FIRST):
  The Corpus pipeline — OCR, cleaning, language detection, pair drafting.
  Human still certifies every decision.
  Second: Osona Connect backend.
  Then: offering to African businesses and institutions.

## Quick start

```bash
# Inside Hermes (full capability):
python aisod3a_harness.py run "OCR-extract and clean the Oshindonga corpus PDFs"

# Standalone (degraded — needs a model provider):
python aisod3a_harness.py run "Validate an Oshindonga text file"
python aisod3a_harness.py corpus      # Corpus pipeline template
python aisod3a_harness.py status       # Model routing + mode
```

## Structure

```
aisod3a_harness.py   Main harness — Planner, Coder, Researcher, Evaluator
                     + AISODModelProvider (LRLM bridge) + CLI
```

## Design principles (from the Charter)

- **Three layers, one system.** Model, Harness, Agent depend on each other.
- **Dependency Rule.** Our models first; third-party is an explicit fallback.
- **Earn outward.** Corpus pipeline first, then Osona Connect, then others.
- **Human in the loop.** The Harness drafts; humans certify.  Always.
- **No overclaiming.** What we say externally matches what the code does.

## License

MIT — same as Hermes Agent.
