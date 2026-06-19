# llm-council

A [Claude Code](https://claude.com/claude-code) Skill that puts a question, decision, or document to a council of different LLMs, or a panel of named advisor personas, and synthesizes a final verdict — adapted from [karpathy/llm-council](https://github.com/karpathy/llm-council) and the dual-mode split popularized by [jacob-bd/the-ai-counsel](https://github.com/jacob-bd/the-ai-counsel).

General-purpose: not tied to any team or domain. Works equally for an SRE rollback call, an engineering architecture decision, a product question, or a review pass on an RFC/design doc/RCA — anywhere multiple independent takes reduce single-model blind spots.

## Two modes

- **Council** (`scripts/council.py`) — real, separate LLMs independently answer, anonymously peer-review each other (Member A/B/C/D), then a chairman synthesizes. Best for direct answers, factual questions, or "give me the best response."
- **Advisors** (`scripts/advisors.py`) — named personas (Skeptic, Pragmatist, Strategist, Risk Assessor, etc.) debate across rounds, with early stop on convergence, and a moderator delivers a structured verdict. Best when there's a real tradeoff, risk, strategy, or ethics question worth arguing about.

Pick Council when one defensible answer exists; pick Advisors when reasonable people (or models) could disagree.

## Setup

Pick a provider per model — mix and match freely:

- **OpenRouter** (cloud, one key → GPT, Gemini, Grok, Claude, Llama, etc.):
  ```bash
  export OPENROUTER_API_KEY=sk-or-v1-...
  ```
  Get a key at https://openrouter.ai/.
- **Ollama** (local, free, no key): install from https://ollama.com/, then:
  ```bash
  ollama serve
  ollama pull llama3.1
  ```

Install as a Claude Code skill by placing (or symlinking) this directory under `~/.claude/skills/llm-council/` (personal) or `<project>/.claude/skills/llm-council/` (project-scoped).

Council/advisor membership lives in `scripts/config.json`. Each model entry is `provider:model` (e.g. `ollama:llama3.1`) or a bare OpenRouter slug (e.g. `openai/gpt-5.1`, kept bare for backward compatibility):

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

OpenRouter model slugs drift over time — check https://openrouter.ai/models for current ones. Running entirely on `ollama:` entries needs no API key.

Personas live in `scripts/personas.json` — 8 defined (skeptic, pragmatist, strategist, risk_assessor, ethicist, data_analyst, innovator, customer_advocate), each just a label + system prompt, fully editable/extendable.

## Usage

**Inside Claude Code:**

```
/llm-council <question, decision, or path to a doc to review>
```

**Or run directly:**

```bash
# Council mode
python3 scripts/council.py "Should we use Postgres or DynamoDB for the new event-ingestion service?"
python3 scripts/council.py "Review this RCA for gaps or unsupported conclusions" --file ./incident-482-rca.md

# Advisor mode
python3 scripts/advisors.py "Should we sunset the legacy API or keep maintaining it for one more year?"
python3 scripts/advisors.py "Is this rollback decision sound?" --personas skeptic,risk_assessor,customer_advocate --rounds 2
```

Output is a markdown report (verdict up top, full transcript collapsed below), and a JSON transcript is saved under `history/` (gitignored).

**As a step in other automation**: any other skill or scheduled agent can shell out to either script as a pre-flight sanity check on its own draft output before finalizing.

**On a recurring schedule**: wire either script into a cron-triggered Routine to get a standing digest rather than only on-demand use.

No third-party Python dependencies — stdlib only.

## License

Not yet specified — pick one (MIT/Apache-2.0/etc.) before treating this as reusable by others.
