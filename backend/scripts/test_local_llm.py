#!/usr/bin/env python3
"""Test and routing script to direct all Ichnoscope LLM requests through a local Ollama model (e.g., qwen3:8b).

This script:
1. Connects to the local Ollama instance (default: http://localhost:11434).
2. Verifies model availability (qwen3:8b, or auto-detects installed models).
3. Intercepts and routes all LLM provider requests (Gemini, Groq, OpenRouter, Ollama)
   to the local Ollama model via OpenAI-compatible endpoints.
4. Executes structured JSON extraction and incident triage explanation.
5. Runs the end-to-end replay pipeline offline with real telemetry.
6. Optionally writes these settings to backend/.env for persistent local testing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path so ichnoscope package can be imported
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import httpx
    from ichnoscope.config import Settings, load_settings
    from ichnoscope.explain import explain
    from ichnoscope.llm import complete_structured
    from ichnoscope.models import Explanation, Incident, Culprit
    from ichnoscope.pipeline import run_pipeline
except ImportError as err:
    print(f"Error importing Ichnoscope modules: {err}")
    print("Ensure you run this script using the virtualenv python: .venv/Scripts/python.exe")
    sys.exit(1)


def get_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Fetch installed model names from local Ollama service."""
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Could not reach Ollama at {base_url}: {exc}")
    return []


def build_ollama_env_overrides(model_name: str, base_url: str = "http://localhost:11434") -> dict[str, str]:
    """Construct environment dictionary routing every provider to local Ollama."""
    v1_url = f"{base_url.rstrip('/')}/v1"
    return {
        # Active provider chain prioritizes Ollama
        "LLM_CHAIN": "ollama,gemini,groq,openrouter",
        "USE_STUB_LLM": "false",
        "DRY_RUN": "true",
        "USE_STUB_GITHUB": "true",
        # Ollama native configuration
        "OLLAMA_MODEL": model_name,
        "OLLAMA_BASE_URL": v1_url,
        # Gemini routed to Ollama
        "GEMINI_MODEL": model_name,
        "GEMINI_BASE_URL": v1_url,
        "GEMINI_API_KEY": "local-ollama-token",
        # Groq routed to Ollama
        "GROQ_MODEL": model_name,
        "GROQ_BASE_URL": v1_url,
        "GROQ_API_KEY": "local-ollama-token",
        # OpenRouter routed to Ollama
        "OPENROUTER_MODEL": model_name,
        "OPENROUTER_BASE_URL": v1_url,
        "OPENROUTER_API_KEY": "local-ollama-token",
    }


def write_persistent_env(env_vars: dict[str, str], target_file: Path) -> None:
    """Write or update key-value pairs in target .env file."""
    lines = []
    if target_file.is_file():
        lines = target_file.read_text(encoding="utf-8").splitlines()

    existing_keys = set()
    updated_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in env_vars:
                updated_lines.append(f"{k}={env_vars[k]}")
                existing_keys.add(k)
                continue
        updated_lines.append(line)

    # Append any remaining new keys
    for k, v in env_vars.items():
        if k not in existing_keys:
            updated_lines.append(f"{k}={v}")

    target_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    print(f"[OK] Saved local Ollama routing configuration to: {target_file}")


def run_model_direct(settings: Settings, prompt: str) -> None:
    """Test direct structured completion through the configured provider."""
    print("\n--- Test 1: Direct Structured Completion ---")
    start = time.perf_counter()
    providers = settings.llm_providers()
    if not providers:
        print("[FAIL] No usable LLM providers configured in settings!")
        return

    provider = providers[0]
    print(f"Targeting provider: {provider.name} | Model: {provider.model} | Endpoint: {provider.base_url}")

    try:
        result = complete_structured(
            Explanation,
            system="You are an expert software triage assistant. You must respond in valid JSON conforming to the requested schema.",
            user=f"Analyze this incident scenario and respond in JSON with domain ('backend', 'frontend', 'database', or 'infra'), root_cause_hypothesis, and exactly 3 checklist steps:\n{prompt}",
            settings=settings,
            timeout_s=45.0,
        )
        duration = time.perf_counter() - start

        exp: Explanation = result.value
        print(f"[PASS] Successfully received structured explanation in {duration:.2f}s!")
        print(f"  • Provider: {result.provider} (Model: {result.model})")
        print(f"  • Domain: {exp.domain}")
        print(f"  • Root Cause Hypothesis: {exp.root_cause_hypothesis}")
        print("  • Verification Checklist:")
        for idx, step in enumerate(exp.checklist, 1):
            print(f"      {idx}. {step}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Structured extraction failed: {exc}")


def run_pipeline_replay(settings: Settings, fixture_path: Path) -> None:
    """Test full end-to-end incident pipeline replay with the local model."""
    print("\n--- Test 2: Full End-to-End Pipeline Replay ---")
    if not fixture_path.is_file():
        print(f"[FAIL] Fixture not found at {fixture_path}")
        return

    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Error reading fixture: {exc}")
        return

    # Use a unique timestamp or memory DB so replay tests fresh triage
    import tempfile
    temp_db = tempfile.mktemp(suffix=".db")

    print(f"Running pipeline for fixture: {fixture_path.name}")
    start = time.perf_counter()
    state = run_pipeline(
        payload=payload,
        auto_publish=True,
        db_path=temp_db,
        settings=settings,
    )
    duration = time.perf_counter() - start

    print(f"\n[PIPELINE RESULT] Status: {state.status.upper()} (Triage Duration: {duration:.2f}s)")
    if state.incident:
        print(f"  • Incident: {state.incident.exception_type}: {state.incident.error_message}")
        print(f"  • Location: {state.incident.file_path}:{state.incident.line_number}")
        print(f"  • Severity: {state.severity}")
    if state.culprit:
        print(f"  • Suspect Commit: {state.culprit.sha[:7]} by @{state.culprit.author_login}")
    if state.explanation:
        print(f"  • LLM Domain: {state.explanation.domain}")
        print(f"  • LLM Hypothesis: {state.explanation.root_cause_hypothesis}")
        print("  • LLM Checklist:")
        for idx, item in enumerate(state.explanation.checklist, 1):
            print(f"      {idx}. {item}")
    if state.issue_url:
        print(f"  • Published Mock GitHub Issue: {state.issue_url}")

    print("\nPipeline Logs Excerpt:")
    for log in state.logs[-6:]:
        print(f"  {log}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Route Ichnoscope LLM requests through a local Ollama model (e.g. qwen3:8b)."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3:8b",
        help="Ollama model tag to use (default: qwen3:8b).",
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama service base URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default="backend/fixtures/bug1_keyerror_payment.json",
        help="Path to Sentry JSON fixture to test with.",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Save these Ollama settings permanently into backend/.env for dashboard & backend use.",
    )
    parser.add_argument(
        "--pull-if-missing",
        action="store_true",
        help="Attempt to run 'ollama pull <model>' if the requested model is not found.",
    )

    args = parser.parse_args()

    print("==================================================================")
    print("       Ichnoscope Local Ollama Model Testing & Router Suite       ")
    print("==================================================================")

    # 1. Inspect Ollama status
    installed_models = get_ollama_models(args.ollama_url)
    print(f"Ollama Endpoint: {args.ollama_url}")
    print(f"Installed Models in Ollama: {installed_models if installed_models else 'None / Ollama unreachable'}")

    model_to_use = args.model
    if model_to_use not in installed_models:
        # Check if model has a variant or default tag
        matched = [m for m in installed_models if model_to_use.split(":")[0] in m]
        if matched:
            model_to_use = matched[0]
            print(f"[INFO] Using closely matched installed model: {model_to_use}")
        elif installed_models:
            print(f"[WARN] Requested model '{model_to_use}' is not currently in Ollama.")
            print(f"       Available installed models: {', '.join(installed_models)}")
            if args.pull_if_missing:
                print(f"[INFO] Pulling model '{model_to_use}'...")
                os.system(f"ollama pull {model_to_use}")
            else:
                fallback = installed_models[0]
                print(f"       Defaulting to installed model: {fallback} for this test run.")
                print("       (Tip: run 'ollama pull qwen3:8b' or pass --model <name>)")
                model_to_use = fallback
        else:
            print(f"[WARN] No models found or Ollama is offline. Will attempt request with {model_to_use}.")

    # 2. Build environment overrides
    env_overrides = build_ollama_env_overrides(model_to_use, args.ollama_url)
    os.environ.update(env_overrides)

    print(f"\n[ROUTING ACTIVE] All LLM requests (Ollama, Gemini, Groq, OpenRouter) -> Local {model_to_use}")

    # 3. Load Ichnoscope settings
    settings = load_settings(os.environ)

    # 4. Optional: Write to backend/.env
    if args.write_env:
        env_file = BACKEND_DIR / ".env"
        write_persistent_env(env_overrides, env_file)

    # 5. Run direct structured completion test
    sample_prompt = (
        "Exception: KeyError: 'stripe_customer_id' in services/payment.py:84.\n"
        "Suspect commit diff: + customer_id = user_account['stripe_customer_id']\n"
        "Stack trace: KeyError in process_checkout."
    )
    run_model_direct(settings, sample_prompt)

    # 6. Run pipeline replay test
    fixture_path = ROOT_DIR / args.fixture if not Path(args.fixture).is_absolute() else Path(args.fixture)
    run_pipeline_replay(settings, fixture_path)

    print("\n==================================================================")
    print("Testing complete! To run any CLI command or server with this local model:")
    print("  $env:LLM_CHAIN='ollama'")
    print(f"  $env:OLLAMA_MODEL='{model_to_use}'")
    print("  $env:OLLAMA_BASE_URL='http://localhost:11434/v1'")
    print("  $env:USE_STUB_LLM='false'")
    print("==================================================================")


if __name__ == "__main__":
    main()
