---
name: llm-council
description: Puts a question, decision, or document to either a council of different LLMs (GPT, Gemini, Grok, Claude, or free local Ollama models) that peer-review each other, or a panel of named advisor personas (Skeptic, Strategist, Risk Assessor, etc.) that debate in rounds to a verdict - adapted from karpathy/llm-council and jacob-bd/the-ai-counsel. General-purpose - not tied to any team or domain (works for SRE incident/rollback calls, engineering design/architecture decisions, product or process questions, document/RFC/RCA review, anything where multiple independent takes reduce single-model blind spots). Use on-demand for a "second opinion," "council review," or "advisor debate" on a high-stakes call, for cross-checking a draft doc, or wired into a scheduled routine as a recurring digest or pre-flight sanity check for other automations. Trigger on "/llm-council", "ask the council", "get a second opinion from other models", "debate this with advisors", "cross-check this with different LLMs".
---

# LLM Council

Two deliberation modes, both adapted from [karpathy/llm-council](https://github.com/karpathy/llm-council) (and the dual-mode split popularized by [jacob-bd/the-ai-counsel](https://github.com/jacob-bd/the-ai-counsel)):

- **`council.py`** - real, separate LLMs (not personas of the same model) independently answer, anonymously peer-review each other, then a chairman synthesizes. Best for direct answers, factual questions, or "give me the best response" synthesis.
- **`advisors.py`** - named personas (same or different underlying model) debate across rounds and a moderator delivers a structured verdict. Best when there's a real tradeoff, risk, strategy, ethics question, or decision to make - something worth arguing about, not just answering.

**Picking a mode:** if the question has one defensible answer, use Council. If reasonable people (or models) could disagree, use Advisors. When in doubt, default to Council - it's cheaper (no multi-round debate) and the chairman still flags disagreement if the independent answers conflict.

## Setup (one-time)

Pick a provider per model - mix and match freely:

- **OpenRouter** (cloud, one key → GPT, Gemini, Grok, Claude, Llama, etc.): `export OPENROUTER_API_KEY=sk-or-v1-...` (get one at https://openrouter.ai/, fund with credits or auto-topup).
- **Ollama** (local, free, no key): install from https://ollama.com/, run `ollama serve`, then `ollama pull <model>` for whatever you want to use (e.g. `ollama pull llama3.1`).

Model entries throughout `scripts/config.json` are either `provider:model` (e.g. `ollama:llama3.1`) or a bare slug (e.g. `openai/gpt-5.1`), which is treated as OpenRouter for backward compatibility:

```json
{
  "council_models": [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "ollama:llama3.1"
  ],
  "chairman_model": "google/gemini-3-pro-preview",
  "debate_model": "anthropic/claude-sonnet-4.5",
  "default_personas": ["skeptic", "pragmatist", "strategist", "risk_assessor"],
  "max_rounds": 3
}
```

Model slugs are OpenRouter IDs and drift over time - check https://openrouter.ai/models before relying on the defaults. Edit `config.json` directly to add/remove council members, change the chairman/debate model, swap in Ollama models to cut API spend, or pick which personas debate by default. No code changes needed. Running entirely on `ollama:` entries needs no API key at all.

Personas live in `scripts/personas.json` (8 defined: skeptic, pragmatist, strategist, risk_assessor, ethicist, data_analyst, innovator, customer_advocate) - each is just a label + system prompt, fully editable, and you can add more.

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
