# Configuration

Every model the council/advisors use is controlled by one file: `scripts/config.json`. It's gitignored — it's your personal setup, never committed, never clobbered by `git pull`. `scripts/config.example.json` is the tracked template.

## Getting your own config

```bash
python3 scripts/setup.py
```

Walks you through council members, chairman model, debate model, round count, and timeout, then writes `scripts/config.json`. Re-run it anytime to reconfigure. Or skip the wizard entirely:

```bash
cp scripts/config.example.json scripts/config.json
# then edit scripts/config.json by hand
```

## The model spec format

Every model field (`council_models`, `chairman_model`, `debate_model`) takes either:

- **`provider:model`** — e.g. `ollama:qwen3:1.7b`, `openrouter:anthropic/claude-sonnet-4.5`
- **a bare slug** — e.g. `openai/gpt-5.1` — treated as OpenRouter for backward compatibility with configs from before the `provider:` prefix existed

Mix providers freely in the same `council_models` list — there's no requirement that every member use the same provider.

## Provider 1: OpenRouter (cloud, paid)

One API key, 100+ models across vendors (GPT, Gemini, Grok, Claude, Llama, etc.):

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Get a key and add credits at https://openrouter.ai/. Model slugs drift over time — check https://openrouter.ai/models before relying on any slug in `config.example.json`. A handful of OpenRouter models are free (suffixed `:free`, e.g. `meta-llama/llama-3.1-8b-instruct:free`) but carry tight rate limits.

Every model that resolves to OpenRouter is billed per-token by its vendor's rate, regardless of any subscription you have to that vendor's chat product — a ChatGPT Plus or Claude subscription does **not** cover raw API calls made this way.

## Provider 2: Ollama (local, free)

No API key, no per-call cost — runs on your own machine:

```bash
brew install ollama          # or see https://ollama.com/ for other platforms
brew services start ollama   # keeps it running; or `ollama serve` for a foreground process
ollama pull qwen3:1.7b        # repeat for each model you reference in config.json
```

### Sizing models to your hardware

Ollama will happily try to download and load a model too big for your machine, then fail or thrash. As a rule of thumb, you want total RAM to comfortably exceed the model's file size (inference overhead - KV cache, context buffers - adds 20-50%+ on top of the raw weights):

| Your RAM | Reasonable model sizes | Example tags |
|---|---|---|
| 8GB or less | ~1-2B parameter models | `qwen3:1.7b`, `deepseek-r1:1.5b`, `gemma3:1b`, `llama3.2:1b` |
| 16GB | ~7-8B | `qwen3:8b`, `llama3.1:8b`, `phi4-mini` |
| 32GB+ | ~14-32B | `phi4`, `qwen3:32b` |
| 64GB+ / dedicated GPU | 70B+ or full-size flagship tags | `llama3.3:70b`, `gpt-oss:120b` |

`config.example.json` ships with the 8GB-or-less row so it works out of the box on modest hardware. If you have more RAM, swap in bigger tags for meaningfully better answers.

### Concurrency note

`council.py` asks every council member the same question in parallel - that's fine for cloud APIs, but multiple different local models loading into RAM **simultaneously** is what causes timeouts on constrained machines (confirmed firsthand while building this: 8/9 calls timed out running 4 models concurrently on an 8GB machine; serializing the Ollama calls fixed it). `providers.py` already handles this for you - Ollama-backed calls run one at a time regardless of how many you configure, while any OpenRouter calls in the same list still run fully in parallel. You don't need to do anything for this, just be aware council runs are not actually fully concurrent when Ollama is involved, so they take longer than the call count alone suggests.

If you still see timeouts, raise `timeout_seconds` in config.json (the chairman call in particular bundles every opinion and review into one long prompt, and needs more time than an individual turn).

## Other config fields

| Field | Used by | Meaning |
|---|---|---|
| `council_models` | `council.py` | List of models that independently answer, then cross-review each other |
| `chairman_model` | `council.py` | Synthesizes the final verdict from all opinions + reviews |
| `debate_model` | `advisors.py` | Single model every persona's turn runs on |
| `default_personas` | `advisors.py` | Which keys from `personas.json` debate when `--personas` isn't passed |
| `max_rounds` | `advisors.py` | Debate rounds before forcing a verdict (early-stops on convergence) |
| `timeout_seconds` | both | Per-call HTTP timeout |

## Personas

`scripts/personas.json` defines the named advisors used by `advisors.py` - 8 ship by default (skeptic, pragmatist, strategist, risk_assessor, ethicist, data_analyst, innovator, customer_advocate). Each is just:

```json
"skeptic": {
  "label": "The Skeptic",
  "system_prompt": "You are the Skeptic in a structured debate. ..."
}
```

Add your own by adding a new key, or edit any `system_prompt` to retune a persona's stance. This file is tracked in git (it's not a secret/personal-preference file the way `config.json` is) — feel free to commit improvements.
