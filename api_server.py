"""
AISOD 3A Harness — Model-Agnostic API Server

Wraps the harness in an OpenAI-compatible REST API so any front-end
(web dashboard, CLI, desktop app) can use it.  Model routing is
configurable per-request, so callers can use any model until AISOD 3A
models are ready — and the local-language corpus integration grows
over time as the Charter's data thresholds are met.

Dependencies: fastapi, uvicorn, pydantic, python-multipart, httpx
Install:  pip install fastapi uvicorn pydantic httpx
Run:      uvicorn api_server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the project root so we can import the harness.
PROJECT_ROOT = Path(__file__).resolve().parent
import sys

sys.path.insert(0, str(PROJECT_ROOT))

from aisod3a_harness import AISOD3AHarness, AISODModelProvider  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = int(os.environ.get("AISOD_HARNESS_PORT", "8000"))
HOST = os.environ.get("AISOD_HARNESS_HOST", "0.0.0.0")
WORK_DIR = Path(os.environ.get("AISOD_HARNESS_WORKDIR", tempfile.mkdtemp(prefix="aisod3a-api-")))

# Default model provider — callers can override per-request.
DEFAULT_MODEL_PROVIDER = os.environ.get(
    "AISOD_HARNESS_DEFAULT_MODEL", "hermes"
)  # "hermes" | "openrouter" | "openai" | "local"

# Model-agnostic: every request can name its preferred model.
# When "aisod-local" is requested, the LRLM bridge is used.
# Anything else is passed through to the Hermes provider pool.

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field  # noqa: E402


class ChatRequest(BaseModel):
    model: str = Field(
        default="hermes",
        description="Model identifier. 'hermes' = Hermes provider pool (any model you configure there). "
        "'aisod-local' = AISOD LRLM local models. Any other string is passed through as a custom provider hint.",
    )
    messages: List[Dict[str, str]] = Field(
        ..., description="OpenAI-format chat messages [{role, content}, ...]"
    )
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, gt=0)
    role: Optional[str] = Field(
        default=None,
        description="Harness role to use for this call: planner, coder, researcher, evaluator. "
        "If omitted, treated as a direct chat.",
    )
    goal: Optional[str] = Field(
        default=None,
        description="If set, runs the full harness pipeline (Planner -> Coder/Researcher -> Evaluator) "
        "instead of a single chat call. The 'messages' field is ignored for the planner's context.",
    )
    context: Optional[str] = Field(default="", description="Extra context for the harness run.")
    spec: Optional[str] = Field(default="", description="Spec text for the Evaluator step.")


class ChatResponse(BaseModel):
    id: str = Field(default="cmpl-1")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(__import__("time").time()))
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})


class HarnessRunRequest(BaseModel):
    goal: str = Field(..., description="The goal to run the full harness on.")
    context: Optional[str] = Field(default="", description="Extra context.")
    spec: Optional[str] = Field(default="", description="Spec for the Evaluator.")
    model: str = Field(default="hermes", description="Model provider hint.")


class HarnessRunResponse(BaseModel):
    report: Dict[str, Any] = Field(..., description="Full harness report JSON.")


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    local: bool
    description: str
    supports_languages: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API server
# ---------------------------------------------------------------------------

app = None  # set below


def _build_app():
    from fastapi import FastAPI, HTTPException  # noqa: E402
    from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

    _app = FastAPI(
        title="AISOD 3A Harness API",
        description=(
            "Model-agnostic API for the AISOD 3A AI Automation Agent harness. "
            "Use any AI model until AISOD 3A models are ready. "
            "Local African languages are available as the Corpus grows."
        ),
        version="0.1.0",
    )
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @_app.get("/health")
    def health():
        return {"status": "ok", "service": "aisod3a-harness-api"}

    @_app.get("/v1/models", response_model=List[ModelInfo])
    def list_models():
        """List available models — model-agnostic, grows as AISOD 3A models are added."""
        models = [
            ModelInfo(
                id="hermes",
                name="Hermes Provider Pool",
                provider="hermes",
                local=False,
                description="Any model configured in your Hermes provider pool. "
                "Use OPENAI_API_KEY, OPENROUTER_API_KEY, or any Hermes-supported provider. "
                "Drop-in until AISOD 3A models are ready.",
                supports_languages=["en", "af", "na"],  # grows with the corpus
            ),
            ModelInfo(
                id="aisod-local",
                name="AISOD Local Models (LRLM)",
                provider="aisod",
                local=True,
                description="AISOD's own models via the LRLM model manager (mistral-7b, llama-3.2-3b). "
                "Uses the corpus fine-tuned models when available. "
                "The Sovereign path — per the Dependency Rule (Charter Article III).",
                supports_languages=["en", "na", "oj", "kr", "rs"],  # grows with corpus
            ),
            ModelInfo(
                id="openrouter",
                name="OpenRouter (any model)",
                provider="openrouter",
                local=False,
                description="Any model on OpenRouter. Set AISOD_HARNESS_FALLBACK_MODEL to pick a default. "
                "Model-agnostic by design — swap models without changing your code.",
                supports_languages=["en", "af", "na", "sw", "ha", "yo", "ig"],  # grows with corpus
            ),
        ]
        return models

    @_app.post("/v1/chat/completions", response_model=ChatResponse)
    def chat_completions(req: ChatRequest):
        """OpenAI-compatible chat endpoint — works with any OpenAI SDK client."""
        model = req.model
        role = req.role or "coder"

        if req.goal:
            # Full harness run
            harness = AISOD3AHarness(workdir=WORK_DIR)
            report = harness.run(goal=req.goal, context=req.context, spec=req.spec)
            output = json.dumps(report, indent=2, ensure_ascii=False)
            model_id = model
        else:
            # Single-role chat
            if model == "aisod-local":
                provider = AISODModelProvider(role=role)
                messages = req.messages
                output = provider.chat(messages)
                model_id = f"aisod-local/{role}"
            elif model == "hermes":
                # Hermes provider pool — via the harness in standalone mode
                from aisod3a_harness import _RUNNING_IN_HERMES

                if _RUNNING_IN_HERMES:
                    from hermes_tools import delegate_task

                    system = _system_prompt_for(role)
                    task = (
                        f"Chat completion for role '{role}'.\n\n"
                        + "\n".join(
                            f"{m['role']}: {m['content']}" for m in req.messages
                        )
                    )
                    result = delegate_task(
                        goal=system + "\n\nTASK:\n" + task,
                        context=f"You are the AISOD 3A {role} agent.",
                    )
                    output = result.get("summary", str(result))
                else:
                    output = f"[hermes pool not available in standalone mode — configure AISOD_HARNESS_FALLBACK_MODEL]"
                model_id = "hermes"
            elif model == "openrouter":
                # OpenRouter — direct API call
                openrouter_key = os.environ.get("OPENROUTER_API_KEY")
                if not openrouter_key:
                    output = (
                        "[OpenRouter API key not configured — "
                        "set OPENROUTER_API_KEY in your environment]"
                    )
                    model_id = "openrouter"
                else:
                    try:
                        import httpx  # noqa: E402

                        response = httpx.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {openrouter_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://harness.aisod.tech",
                                "X-Title": "AISOD 3A Harness",
                            },
                            json={
                                "model": "openai/gpt-4o-mini",
                                "messages": req.messages,
                                "temperature": req.temperature or 0.7,
                                "max_tokens": req.max_tokens or 4096,
                            },
                            timeout=30,
                        )
                        response.raise_for_status()
                        data = response.json()
                        output = data["choices"][0]["message"]["content"]
                        model_id = f"openrouter/{data.get('model', 'unknown')}"
                    except Exception as exc:  # noqa: BLE001
                        output = f"[OpenRouter error: {exc}]"
                        model_id = "openrouter"
            else:
                # Any other provider hint — pass-through for future expansion
                output = (
                    f"[model '{model}' requested — "
                    f"configure AISOD_HARNESS_FALLBACK_MODEL or use 'hermes' / 'openrouter' / 'aisod-local']"
                )
                model_id = model

        return ChatResponse(
            model=model_id,
            choices=[{"index": 0, "message": {"role": "assistant", "content": output}, "finish_reason": "stop"}],
        )

    @_app.post("/v1/harness/run", response_model=HarnessRunResponse)
    def harness_run(req: HarnessRunRequest):
        """Run the full AISOD 3A Harness pipeline."""
        harness = AISOD3AHarness(workdir=WORK_DIR)
        report = harness.run(goal=req.goal, context=req.context, spec=req.spec)
        return HarnessRunResponse(report=report)

    @_app.get("/v1/harness/status")
    def harness_status():
        """Model routing status — shows which models are active."""
        harness = AISOD3AHarness(workdir=WORK_DIR)
        return harness.status()

    return _app


def _system_prompt_for(role: str) -> str:
    """Return the system prompt for a harness role."""
    import textwrap

    return textwrap.dedent(
        f"""\
        You are the AISOD 3A {role} agent — part of the AI Automation Agent
        harness (Founder's Directive IV, the AISOD 3A Charter).

        {"Your job: take a user's goal and break it into an ordered list of concrete steps." if role == "planner" else ""}
        {"Your job: take a concrete task and produce the artefact — code, script, document." if role == "coder" else ""}
        {"Your job: gather the information a task needs and return a briefing." if role == "researcher" else ""}
        {"Your job: review completed work against the task and spec. Be candid." if role == "evaluator" else ""}

        AISOD 3A is an AI Automation Agent for African languages and context.
        Local languages are available as the Corpus grows.
        """
    )


# Lazy app creation so we can import this module without starting the server.
app = _build_app()

# Serve the static frontend at / (if the static/ directory exists)
from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse

_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        return FileResponse(str(_STATIC_DIR / "index.html"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn  # noqa: E402

    print(f"AISOD 3A Harness API — starting on http://{HOST}:{PORT}")
    print(f"  Swagger:  http://{HOST}:{PORT}/docs")
    print(f"  Redoc:    http://{HOST}:{PORT}/redoc")
    print(f"  Health:   http://{HOST}:{PORT}/health")
    print()
    print("Model-agnostic: use any model via the 'model' field until AISOD 3A models are ready.")
    print("Local languages available as the Corpus grows.")
    uvicorn.run(app, host=HOST, port=PORT)
