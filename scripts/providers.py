"""Shared LLM provider dispatch for council.py and advisors.py.

Model specs are either:
  - "provider:model"  e.g. "ollama:llama3.1"
  - a bare slug       e.g. "openai/gpt-5.1"  -> treated as an OpenRouter model id
    (kept bare for backward compatibility with existing config files)

Supported providers:
  - openrouter (cloud, needs OPENROUTER_API_KEY) - https://openrouter.ai/
  - ollama (local, free, needs `ollama serve` running) - https://ollama.com/
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import error, request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KNOWN_PROVIDERS = ("openrouter", "ollama")


def _post(url, headers, payload, timeout):
    body = json.dumps(payload).encode()
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def call_openrouter(model, content, timeout):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set - get one at https://openrouter.ai/")
    data = _post(
        OPENROUTER_URL,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://claude.ai/code",
            "X-Title": "llm-council-skill",
        },
        {"model": model, "messages": [{"role": "user", "content": content}]},
        timeout,
    )
    return data["choices"][0]["message"]["content"]


def call_ollama(model, content, timeout):
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    data = _post(
        f"{host}/v1/chat/completions",
        {"Content-Type": "application/json"},
        {"model": model, "messages": [{"role": "user", "content": content}], "stream": False},
        timeout,
    )
    return data["choices"][0]["message"]["content"]


def parse_spec(spec):
    if ":" in spec and spec.split(":", 1)[0] in KNOWN_PROVIDERS:
        provider, model = spec.split(":", 1)
        return provider, model
    return "openrouter", spec


def call_model(spec, content, timeout):
    provider, model = parse_spec(spec)
    if provider == "ollama":
        return call_ollama(model, content, timeout)
    return call_openrouter(model, content, timeout)


def call_model_safe(spec, content, timeout):
    """Never raises - returns a generic (model-name-free) error string on failure
    so a failed call can't deanonymize itself when embedded in an anonymized review."""
    try:
        return call_model(spec, content, timeout)
    except error.HTTPError as e:
        return f"[ERROR: request failed - HTTP {e.code}]"
    except Exception as e:
        return f"[ERROR: request failed or timed out - {type(e).__name__}]"


def run_parallel(specs, content, timeout):
    """Run model calls concurrently, except ollama-backed ones, which are run
    one at a time. Multiple local models loading into RAM simultaneously is what
    causes timeouts on memory-constrained machines; cloud (openrouter) calls have
    no such shared-resource bottleneck and stay fully parallel."""
    ollama_specs = [s for s in specs if parse_spec(s)[0] == "ollama"]
    other_specs = [s for s in specs if parse_spec(s)[0] != "ollama"]

    results = {}
    with ThreadPoolExecutor(max_workers=max(len(other_specs), 1)) as pool:
        futures = {pool.submit(call_model_safe, s, content, timeout): s for s in other_specs}
        for s in ollama_specs:
            results[s] = call_model_safe(s, content, timeout)
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()
    return results
