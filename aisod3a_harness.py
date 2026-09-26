"""
AISOD 3A Harness — AI Automation Agent orchestration engine.

Built ON TOP of Hermes Agent: when run inside Hermes, every role (Planner,
Coder, Researcher, Evaluator) maps to a delegate_task subagent that keeps
Hermes's full toolset (read_file, write_file, terminal, web_search, etc.).
When run standalone (no delegate_task available), it falls back to the
model's chat interface directly.

This is NOT a replacement for Hermes — it is a focus layer on top of it.
Hermes remains fully capable; the 3A layer adds structure and the
Corpus-first mission from the AISOD 3A Charter (Founder's Directive IV).

Three layers (Charter Article II):
  1. Model Family   — AISOD's own models (LRLM) preferred; Hermes pool as bridge
  2. Harness        — this file: Planner -> Coder + Researcher -> Evaluator
  3. Agent          — the product surface (Android app, API, CLI)

Dependency Rule (Article III):
  AISOD models are the default once they meet the Moat Charter benchmarks.
  Until then, Hermes's provider pool is the explicit bridge — never the
  quiet default.

First proving ground (Article IV, FIRST):
  The Corpus pipeline — OCR, cleaning, language detection, pair drafting.
  Human still certifies every decision.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

AISOD_HOME = Path(os.environ.get(
    "AISOD_HOME",
    Path.home() / "Desktop/Initiate/ALL/AISOD Inc",
))
LRLM_DIR = AISOD_HOME / "2026/AISOD AI LRLM"
CORPUS_DIR = AISOD_HOME / "2026/AISOD Data"

# Detect whether we're inside Hermes (has delegate_task) or standalone.
_RUNNING_IN_HERMES = False
try:
    from hermes_tools import delegate_task  # type: ignore[import-untyped]

    _RUNNING_IN_HERMES = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Model tier assignment (Charter Article V)
# ---------------------------------------------------------------------------

MODEL_TIERS: Dict[str, str] = {
    "planner": "mistral-7b",
    "coder": "mistral-7b",
    "researcher": "mistral-7b",
    "evaluator": "llama-3.2-3b",
}

# ---------------------------------------------------------------------------
# System prompts per role — the AISOD 3A identity
# ---------------------------------------------------------------------------

SYSTEM_PLANNER = textwrap.dedent("""\
    You are the AISOD 3A Planner agent — part of the AI Automation Agent
    harness (Founder's Directive IV, the AISOD 3A Charter).

    Your job: take a user's goal and break it into an ordered list of
    concrete, assignable steps.  Each step must be doable by one of the
    other harness roles: Coder, Researcher, or Evaluator.

    Use the full toolset available to you.  If context would help, read
    relevant files.  If a web search would clarify requirements, do it.

    Output strictly as a JSON array.  Each object has:
      - "step":      integer, starting at 1
      - "agent":     "coder" | "researcher" | "evaluator"
      - "task":      a clear, actionable instruction (one or two sentences)
      - "depends_on": list of prior step numbers this step needs (may be [])

    AISOD 3A is an AI Automation Agent for African languages and context.
    The work you plan should respect that.  Do not add commentary outside
    the JSON array.
""")

SYSTEM_CODER = textwrap.dedent("""\
    You are the AISOD 3A Coder agent — part of the AI Automation Agent
    harness (Founder's Directive IV, the AISOD 3A Charter).

    Your job: take a concrete task and produce the artefact — code, a
    script, a document, a config file, a data transformation, etc.

    Be precise.  When writing files, name the path and write the full
    contents.  When running commands, state what you ran and what it
    produced.  Return a short structured report at the end: what you
    did, what files were created or modified, and anything that needs
    follow-up.

    You have access to the full Hermes toolset — read files, write
    files, run terminal commands, search the web.  Use them.
""")

SYSTEM_RESEARCHER = textwrap.dedent("""\
    You are the AISOD 3A Researcher agent — part of the AI Automation
    Agent harness (Founder's Directive IV, the AISOD 3A Charter).

    Your job: gather the information a task needs.  Return a concise but
    complete briefing: what you found, what sources you used (or would
    use), and what's still missing.

    You have access to web_search and file reading.  Prefer citing
    sources.  If web access isn't available, say so plainly and work
    from the context provided.

    AISOD 3A is focused on African languages and context — when
    researching, prioritise sources that reflect that reality.
""")

SYSTEM_EVALUATOR = textwrap.dedent("""\
    You are the AISOD 3A Evaluator agent — part of the AI Automation
    Agent harness (Founder's Directive IV, the AISOD 3A Charter).

    Your job: review completed work against the original task and any
    spec provided.  Be candid — a pass with no issues noted is
    suspicious, especially in the Corpus pipeline where the Harness
    may only draft and a human always certifies (Charter Article VI).

    AISOD 3A may suggest a quality-level advance.  It never executes
    one.  Enforcement rule from the Corpus Platform specification does
    not bend for automation speed.

    Output strictly as a JSON object:
      - "passed":        boolean
      - "score":         float 0.0-1.0
      - "issues":        list of issue strings (empty if none)
      - "strengths":     list of strength strings
      - "recommendation": "approve" | "revise" | "reject"
      - "note":          short human-readable summary

    Do not add commentary outside the JSON object.
""")


def _system_for(role: str) -> str:
    return {
        "planner": SYSTEM_PLANNER,
        "coder": SYSTEM_CODER,
        "researcher": SYSTEM_RESEARCHER,
        "evaluator": SYSTEM_EVALUATOR,
    }.get(role, SYSTEM_CODER)


# ---------------------------------------------------------------------------
# Model layer — AISOD LRLM bridge (standalone mode only)
# ---------------------------------------------------------------------------

class AISODModelProvider:
    def __init__(self, role: str = "coder"):
        self.role = role
        self.preferred_tier = MODEL_TIERS.get(role, "llama-3.2-3b")
        self._aisod_client = None
        self._using_fallback = False
        self._fallback_reason = ""

    def _try_load_aisod(self) -> bool:
        try:
            sys.path.insert(0, str(LRLM_DIR))
            from inference.model_manager import ModelManager  # noqa: E402

            mm = ModelManager(
                config_path=str(LRLM_DIR / "config/models.yaml")
            )
            available = mm.get_available_models()
            if self.preferred_tier not in available:
                for candidate in available:
                    if candidate in MODEL_TIERS.values():
                        self.preferred_tier = candidate
                        break
                else:
                    return False
            model = mm.load_model(self.preferred_tier)
            self._aisod_client = model
            return True
        except Exception as exc:  # noqa: BLE001
            self._fallback_reason = f"LRLM load failed: {exc}"
            return False

    def _chat_fallback(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Standalone fallback: direct model call via Hermes's provider."""
        try:
            from hermes_tools import chat as _chat_fn  # noqa: E402

            prompt = "\n".join(
                f"{m['role']}: {m['content']}" for m in messages
            )
            return _chat_fn(prompt)  # type: ignore[return-value]
        except ImportError:
            return (
                "[harness error: standalone mode needs a model provider — "
                "run inside Hermes, or configure AISOD_HARNESS_FALLBACK]"
            )

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if self._aisod_client is None:
            if not self._try_load_aisod():
                self._using_fallback = True
                self._fallback_reason = (
                    self._fallback_reason or "no AISOD model available"
                )

        if self._aisod_client is not None:
            try:
                return self._aisod_client.chat(messages, **kwargs)
            except Exception as exc:  # noqa: BLE001
                self._using_fallback = True
                self._fallback_reason = str(exc)
                return self._chat_fallback(messages, **kwargs)
        return self._chat_fallback(messages, **kwargs)

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "preferred_tier": self.preferred_tier,
            "using_aisod_local": self._aisod_client is not None,
            "using_fallback": self._using_fallback,
            "fallback_reason": self._fallback_reason,
        }


# ---------------------------------------------------------------------------
# Agent roles
# ---------------------------------------------------------------------------

def _run_as_delegate(
    role: str,
    task: str,
    context: str = "",
    system: str = "",
) -> str:
    """Run an agent role via Hermes delegate_task — full toolset preserved."""
    result = delegate_task(
        goal=f"{system}\n\nTASK:\n{task}\n\nCONTEXT:\n{context}",
        context=(
            f"You are operating as the AISOD 3A {role} agent. "
            f"Everything you do contributes to the AI Automation Agent.\n\n"
            f"Your task:\n{task}"
        ),
    )
    return result.get("summary", str(result))


def _run_as_chat(
    model: AISODModelProvider,
    role: str,
    task: str,
    context: str = "",
) -> str:
    """Standalone fallback: single chat call to the model."""
    system = _system_for(role)
    user = f"TASK:\n{task}\n\nCONTEXT:\n{context}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return model.chat(messages)


class PlannerAgent:
    def __init__(self, model: Optional[AISODModelProvider] = None):
        self.model = model

    def plan(self, goal: str, context: str = "") -> List[Dict[str, Any]]:
        if _RUNNING_IN_HERMES:
            raw = _run_as_delegate(
                "planner", goal, context, system=_system_for("planner")
            )
        else:
            raw = _run_as_chat(self.model, "planner", goal, context)
        return _parse_json_array(
            raw,
            default=[{
                "step": 1, "agent": "coder",
                "task": goal, "depends_on": [],
            }],
        )


class CoderAgent:
    def __init__(self, model: Optional[AISODModelProvider] = None):
        self.model = model

    def execute(
        self,
        task: str,
        context: str = "",
        workdir: Optional[Path] = None,
    ) -> str:
        if _RUNNING_IN_HERMES:
            return _run_as_delegate(
                "coder", task, context, system=_system_for("coder")
            )
        return _run_as_chat(self.model, "coder", task, context)


class ResearcherAgent:
    def __init__(self, model: Optional[AISODModelProvider] = None):
        self.model = model

    def research(self, query: str, context: str = "") -> str:
        if _RUNNING_IN_HERMES:
            return _run_as_delegate(
                "researcher", query, context,
                system=_system_for("researcher"),
            )
        return _run_as_chat(self.model, "researcher", query, context)


class EvaluatorAgent:
    def __init__(self, model: Optional[AISODModelProvider] = None):
        self.model = model

    def evaluate(
        self, task: str, work: str, spec: str = ""
    ) -> Dict[str, Any]:
        context = (
            f"ORIGINAL TASK:\n{task}\n\nSPEC:\n{spec}\n\nWORK PRODUCED:\n{work}"
        )
        if _RUNNING_IN_HERMES:
            raw = _run_as_delegate(
                "evaluator",
                "Evaluate the work below against the task and spec.",
                context,
                system=_system_for("evaluator"),
            )
        else:
            raw = _run_as_chat(self.model, "evaluator", "", context)
        return _parse_json_object(
            raw,
            default={
                "passed": False, "score": 0.0,
                "issues": [raw], "strengths": [],
                "recommendation": "revise",
                "note": "evaluator parse failed",
            },
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class AISOD3AHarness:
    """
    The AISOD 3A Harness.

    Inside Hermes: every role is a delegate_task subagent with full
    Hermes toolset.  Standalone: roles fall back to direct model calls.
    """

    def __init__(self, workdir: Optional[Path] = None):
        self.workdir = workdir or Path(
            tempfile.mkdtemp(prefix="aisod3a-")
        )
        self.workdir.mkdir(parents=True, exist_ok=True)

        self._pm = (
            AISODModelProvider(role="planner")
            if not _RUNNING_IN_HERMES else None
        )
        self._cm = (
            AISODModelProvider(role="coder")
            if not _RUNNING_IN_HERMES else None
        )
        self._rm = (
            AISODModelProvider(role="researcher")
            if not _RUNNING_IN_HERMES else None
        )
        self._em = (
            AISODModelProvider(role="evaluator")
            if not _RUNNING_IN_HERMES else None
        )

        self.planner = PlannerAgent(self._pm)
        self.coder = CoderAgent(self._cm)
        self.researcher = ResearcherAgent(self._rm)
        self.evaluator = EvaluatorAgent(self._em)

        self.plan: List[Dict[str, Any]] = []
        self.log: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        if _RUNNING_IN_HERMES:
            models = {
                "planner": {"mode": "hermes_delegate"},
                "coder": {"mode": "hermes_delegate"},
                "researcher": {"mode": "hermes_delegate"},
                "evaluator": {"mode": "hermes_delegate"},
            }
        else:
            models = {
                "planner": self._pm.status,
                "coder": self._cm.status,
                "researcher": self._rm.status,
                "evaluator": self._em.status,
            }
        return {
            "workdir": str(self.workdir),
            "mode": "hermes_delegate" if _RUNNING_IN_HERMES else "standalone",
            "models": models,
        }

    def run(
        self,
        goal: str,
        context: str = "",
        spec: str = "",
    ) -> Dict[str, Any]:
        self.log = []
        self._log("harness_start", {"goal": goal, "mode": self.status()["mode"]})

        self.plan = self.planner.plan(goal, context)
        self._log("plan", self.plan)

        results: Dict[int, Dict[str, Any]] = {}
        for step in self.plan:
            n = step["step"]
            agent_name = step["agent"]
            task = step["task"]
            deps = step.get("depends_on", [])

            dep_parts = []
            for d in deps:
                if d in results:
                    dep_parts.append(
                        f"Step {d} result:\n"
                        f"{results[d].get('output', '')[:800]}"
                    )
            dep_context = "\n\n".join(dep_parts)

            self._log(
                "step_start",
                {"step": n, "agent": agent_name, "task": task[:200]},
            )

            if agent_name == "coder":
                output = self.coder.execute(task, dep_context, self.workdir)
            elif agent_name == "researcher":
                output = self.researcher.research(task, dep_context)
            elif agent_name == "evaluator":
                target = deps[0] if deps else (n - 1)
                target_output = results.get(target, {}).get("output", "")
                output = self.evaluator.evaluate(
                    task=task, work=target_output, spec=spec,
                )
                output = json.dumps(output, indent=2)
            else:
                output = f"[unknown agent: {agent_name}]"

            results[n] = {"agent": agent_name, "task": task, "output": output}
            self._log(
                "step_done",
                {"step": n, "agent": agent_name, "output_preview": output[:200]},
            )

        final_eval: Optional[Dict[str, Any]] = None
        eval_step = next(
            (s for s in self.plan if s["agent"] == "evaluator"), None
        )
        if eval_step:
            final_eval = json.loads(results[eval_step["step"]]["output"])

        report = {
            "goal": goal,
            "plan": self.plan,
            "results": {str(k): v for k, v in results.items()},
            "evaluation": final_eval,
            "model_status": self.status(),
            "log": self.log,
            "pass": final_eval.get("passed", False) if final_eval else None,
        }
        self._log("harness_done", {"pass": report["pass"]})
        return report

    def _log(self, event: str, payload: Any) -> None:
        self.log.append({"event": event, "payload": payload})


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _parse_json_array(text: str, default: List[Any]) -> List[Any]:
    try:
        data = json.loads(text.strip())
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    s = text.find("[")
    e = text.rfind("]")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    return default


def _parse_json_object(text: str, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    return default


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_USAGE = """
AISOD 3A Harness — AI Automation Agent
=======================================

Usage:
  python aisod3a_harness.py run "<goal>"        Run the full harness
  python aisod3a_harness.py status              Model routing + mode
  python aisod3a_harness.py corpus              Corpus pipeline template

Run inside Hermes for full capability (delegate_task + all tools).
Standalone mode degrades to direct model calls.

Examples:
  python aisod3a_harness.py run "Validate an Oshindonga text file"
  python aisod3a_harness.py corpus
"""


def _cli() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(_USAGE)
        return

    harness = AISOD3AHarness()

    if args[0] == "status":
        print(json.dumps(harness.status(), indent=2))
        return

    if args[0] == "corpus":
        goal = (
            "Run the AISOD Corpus pipeline on the Oshindonga corpus directory. "
            "For each PDF/TXT file: (1) extract text via OCR if needed, "
            "(2) clean the text — remove headers, footers, page numbers, "
            "recognise line-break artefacts, (3) detect the language, "
            "(4) draft an instruction-response pair a fine-tuning run could use. "
            "The human still makes every certification decision — the harness only "
            "drafts.  Workdir: the Corpus pipeline output folder."
        )
        context = (
            f"CORPUS_DIR: {CORPUS_DIR}/New corpus data/Oshindonga_Corpus_Organized"
        )
        spec = (
            "Charter Article IV FIRST: OCR extraction, automated cleaning, language "
            "detection, and drafting instruction pairs for the Corpus. Human role still "
            "required for every certification decision. This is where the Agent proves it "
            "can be trusted with real, valuable work."
        )
        report = harness.run(goal, context=context, spec=spec)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args[0] == "run":
        goal = " ".join(args[1:]).strip()
        if not goal:
            print("Error: goal required.")
            print(_USAGE)
            return
        report = harness.run(goal)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print(f"Unknown command: {args[0]}")
    print(_USAGE)


if __name__ == "__main__":
    _cli()
