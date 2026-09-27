"""
Test the OpenRouter API key and the harness before deploying.
Run:  python test_deploy.py

Checks:
1. OpenRouter API key is configured
2. OpenRouter API is reachable
3. The harness can plan and run a simple task
"""

import os
import sys

# Make sure we can import the harness from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["OPENROUTER_API_KEY"] = "Placeholder — set this env var before running"

from aisod3a_harness import AISOD3AHarness


def test_openrouter_direct():
    """Test OpenRouter API directly via httpx."""
    import httpx

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("FAIL: OPENROUTER_API_KEY not set")
        return False

    print(f"Key present: {key[:15]}...")
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://harness.aisod.tech",
                "X-Title": "AISOD 3A Harness Test",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": "Say exactly: OPENROUTER OK"},
                ],
                "temperature": 0.0,
                "max_tokens": 10,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        print(f"OpenRouter response: {content}")
        if "OPENROUTER OK" in content:
            print("PASS: OpenRouter API working")
            return True
        print(f"FAIL: unexpected response: {content}")
        return False
    except Exception as e:
        print(f"FAIL: OpenRouter API error: {e}")
        return False


def test_harness():
    """Test the full harness with a simple goal."""
    print("\n--- Testing full harness ---")
    harness = AISOD3AHarness()
    status = harness.status()
    print(f"Mode: {status['mode']}")
    print(f"Workdir: {status['workdir']}")

    goal = "Write a short greeting message for AISOD 3A"
    print(f"Running: {goal}")

    try:
        report = harness.run(goal)
        print(f"\nPlan: {len(report.get('plan', []))} steps")
        print(f"Pass: {report.get('pass')}")
        print(f"Evaluation: {report.get('evaluation')}")

        for step_num, result in report.get('results', {}).items():
            print(f"\nStep {step_num} [{result['agent']}]:")
            print(result['output'][:300])

        if report.get('pass') is True:
            print("\nPASS: Harness completed successfully")
            return True
        elif report.get('pass') is False:
            print("\nFAIL: Harness evaluation failed")
            return False
        else:
            print("\nOK: Harness ran (no evaluator step)")
            return True
    except Exception as e:
        print(f"FAIL: Harness error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("AISOD 3A Harness — Pre-Deployment Test")
    print("=" * 50)

    ok1 = test_openrouter_direct()
    ok2 = test_harness()

    print("\n" + "=" * 50)
    if ok1 and ok2:
        print("ALL TESTS PASSED — ready to deploy")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED — check output above")
        sys.exit(1)
