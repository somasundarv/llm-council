---
name: llm-council
description: Puts a question, decision, or document to a council of different LLMs (GPT, Gemini, Grok, Claude, or free local Ollama models) that peer-review each other, or a panel of advisor personas that debate in rounds to a verdict. General-purpose - any domain where independent takes reduce single-model blind spots. Trigger on "/llm-council", "ask the council", "get a second opinion from other models", "debate this with advisors", "cross-check this with different LLMs".
permissions:
  network: true          # calls out to OpenAI/Gemini/Grok/OpenRouter/Ollama HTTP APIs
  subprocess: true        # shells out to the `claude` CLI for the claude: provider
  env: [OPENROUTER_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, XAI_API_KEY]  # read only, used solely to authenticate outbound API calls, never logged or transmitted elsewhere
  filesystem: [scripts/config.json, history/]  # local config read + debate/council history write
---

# LLM Council

Two deliberation modes, both adapted from [karpathy/llm-council](https://github.com/karpathy/llm-council) (and the dual-mode split popularized by [jacob-bd/the-ai-counsel](https://github.com/jacob-bd/the-ai-counsel)):

- **`council.py`** - real, separate LLMs (not personas of the same model) independently answer, anonymously peer-review each other, then a chairman synthesizes. Best for direct answers, factual questions, or "give me the best response" synthesis.
- **`advisors.py`** - named personas (same or different underlying model) debate across rounds and a moderator delivers a structured verdict. Best when there's a real tradeoff, risk, strategy, ethics question, or decision to make - something worth arguing about, not just answering.

**Picking a mode:** if the question has one defensible answer, use Council. If reasonable people (or models) could disagree, use Advisors. When in doubt, default to Council - it's cheaper (no multi-round debate) and the chairman still flags disagreement if the independent answers conflict.

## Setup (one-time)

`scripts/config.json` is gitignored - it's the user's personal model choice, never committed. If it doesn't exist yet (fresh clone, or this is the first run in a new environment), run the interactive wizard:

```bash
python3 ~/.claude/skills/llm-council/scripts/setup.py
```

It walks through council members, chairman model, debate model, rounds, and timeout, then writes `config.json` from the tracked `config.example.json` template. If a user asks to "configure the models" or "set up llm-council," run this script rather than hand-editing JSON for them - it's built for exactly that.

Two providers, mixed freely in the same config:

- **OpenRouter** (cloud, one key → GPT, Gemini, Grok, Claude, Llama, etc.): `export OPENROUTER_API_KEY=sk-or-v1-...` (get one at https://openrouter.ai/, fund with credits or auto-topup). Billed per-token regardless of any chat-product subscription the user already has to that vendor.
- **Ollama** (local, free, no key): install from https://ollama.com/, run `ollama serve`, then `ollama pull <model>` for whatever's configured. Pick model sizes that fit the machine's RAM - see `docs/CONFIGURATION.md` for a sizing table; on 8GB or less, stick to ~1-2B parameter tags.

Model entries are either `provider:model` (e.g. `ollama:qwen3:1.7b`) or a bare slug (e.g. `openai/gpt-5.1`), treated as OpenRouter for backward compatibility. Full reference, including why concurrent Ollama calls are serialized internally to avoid timeouts on small machines: `docs/CONFIGURATION.md`.

Personas live in `scripts/personas.json` (8 defined: skeptic, pragmatist, strategist, risk_assessor, ethicist, data_analyst, innovator, customer_advocate) - each is just a label + system prompt, fully editable, and you can add more. Unlike `config.json`, this file is tracked in git.

## Running it

**Council mode** - pass the question as the argument:

```bash
python3 ~/.claude/skills/llm-council/scripts/council.py "Should we use Postgres or DynamoDB for the new event-ingestion service?"
python3 ~/.claude/skills/llm-council/scripts/council.py "Review this RCA for gaps or unsupported conclusions" --file ./incident-482-rca.md
```

Makes `2 x len(council_models) + 1` external calls (first opinions + cross-reviews + chairman).

**Advisor mode** - same shape, plus optional persona/round overrides:

```bash
python3 ~/.claude/skills/llm-council/scripts/advisors.py "Should we sunset the legacy API or keep maintaining it for one more year?"
python3 ~/.claude/skills/llm-council/scripts/advisors.py "Is this rollback decision sound?" --personas skeptic,risk_assessor,customer_advocate --rounds 2
```

Runs an opening round, then up to `max_rounds` rebuttal rounds with an early stop once a convergence check says the advisors agree, then a moderator verdict (Summary / Consensus Points / Disagreements table / Verdict / Next Steps / Open Questions).

Both scripts print a markdown report to stdout (verdict up top, full transcript collapsed below) and save a JSON transcript to `~/.claude/skills/llm-council/history/` (gitignored). Relay the stdout report to the user as-is; it's already formatted. If a script exits non-zero (missing API key, unknown persona), surface the stderr message directly rather than retrying silently. Both take longer than a normal in-conversation answer - tell the user it's running rather than going silent.

## Usage

**On-demand:** `/llm-council <question, decision, or path to a doc to review>` - decide between council.py and advisors.py using the heuristic above, or follow an explicit mode the user names ("debate this" → advisors, "ask the council" → council).

**Inside another automation/routine:** any other skill or scheduled agent (RCA generator, design-review bot, on-call triage, release-readiness check) can call either script as a pre-flight sanity check on its own draft output before finalizing - it's just a CLI invocation, no special wiring needed.

**On a recurring schedule:** to get a standing digest rather than only on-demand use, create a cron-triggered Routine (via the `schedule` skill or `CronCreate`) that runs one of these scripts on a fixed cadence with either a templated standing question or whatever artifact that routine produces each cycle (e.g. "council-review last night's top alert before it's filed"). Don't create the recurring schedule silently - confirm cadence, the question/artifact source, and where output should land (file, Slack, ticket) with the user first, since it's an unattended job that keeps running and keeps spending API credits (or none, if running entirely on Ollama).
