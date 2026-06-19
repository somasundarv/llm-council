---
name: llm-council
description: Puts a question, decision, or document to a council of different LLMs (via OpenRouter - e.g. GPT, Gemini, Grok, Claude) and synthesizes a final verdict, adapted from karpathy/llm-council. General-purpose - not tied to any team or domain (works for SRE incident/rollback calls, engineering design/architecture decisions, product or process questions, document/RFC/RCA review, anything where multiple independent takes reduce single-model blind spots). Use on-demand for a "second opinion" or "council review" on a high-stakes call, for cross-checking a draft doc, or wired into a scheduled routine as a recurring digest or pre-flight sanity check for other automations. Trigger on "/llm-council", "ask the council", "get a second opinion from other models", "cross-check this with different LLMs".
---

# LLM Council

Runs the 3-stage deliberation pattern from [karpathy/llm-council](https://github.com/karpathy/llm-council) using real, separate LLMs (not personas of the same model) via [OpenRouter](https://openrouter.ai/), which exposes one API for many vendors:

1. **First opinions** - the question goes to every council model independently, in parallel.
2. **Cross-review** - each model gets the full set of answers, anonymized (Member A/B/C/D), and ranks them for accuracy/insight, flagging conflicts and missed risks.
3. **Chairman synthesis** - one designated model combines everything into a single final answer that states a clear recommendation and explicitly surfaces any unresolved disagreement.

This is domain-agnostic by design - the same flow works for an SRE rollback call, an engineering "should we use Postgres or DynamoDB" debate, a product prioritization question, or a review pass on an RFC/design doc/RCA.

## Setup (one-time)

Requires an OpenRouter API key (one key → access to GPT, Gemini, Grok, Claude, Llama, etc.):

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Get a key at https://openrouter.ai/ and fund it with credits or auto-topup.

Council membership is configured in `scripts/config.json`:

```json
{
  "council_models": [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4"
  ],
  "chairman_model": "google/gemini-3-pro-preview"
}
```

Model slugs are OpenRouter IDs and drift over time - check https://openrouter.ai/models for current ones before relying on the defaults. Edit this file directly to add/remove council members or change the chairman; no code changes needed.

## Running it

Invoke the script via Bash, passing the question as the argument:

```bash
python3 ~/.claude/skills/llm-council/scripts/council.py "Should we use Postgres or DynamoDB for the new event-ingestion service?"
```

To attach a document for review (design doc, RFC, code diff, RCA, postmortem draft, etc.):

```bash
python3 ~/.claude/skills/llm-council/scripts/council.py "Review this RCA for gaps or unsupported conclusions" --file ./incident-482-rca.md
```

The script prints a markdown report to stdout (final verdict up top, individual answers and cross-reviews collapsed below) and saves a JSON transcript to `~/.claude/skills/llm-council/history/`. Relay the stdout report to the user as-is; it's already formatted. If the script exits non-zero (e.g. missing API key, all models failing), surface the stderr message directly rather than retrying silently.

A full run makes `2 x len(council_models) + 1` external API calls (first opinions + cross-reviews + chairman), so expect it to take longer than a normal in-conversation answer - tell the user it's running rather than going silent.

## Usage

**On-demand:** `/llm-council <question, decision, or path to a doc to review>`

**Inside another automation/routine:** any other skill or scheduled agent (RCA generator, design-review bot, on-call triage, release-readiness check) can call this script as a pre-flight sanity check on its own draft output before finalizing - it's just a CLI invocation, no special wiring needed.

**On a recurring schedule:** to get a standing digest rather than only on-demand use, create a cron-triggered Routine (via the `schedule` skill or `CronCreate`) that runs this script on a fixed cadence with either a templated standing question or whatever artifact that routine produces each cycle (e.g. "council-review last night's top alert before it's filed"). Don't create the recurring schedule silently - confirm cadence, the question/artifact source, and where output should land (file, Slack, ticket) with the user first, since it's an unattended job that keeps running and keeps spending API credits.
