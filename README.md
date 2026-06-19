# llm-council

A [Claude Code](https://claude.com/claude-code) Skill that puts a question, decision, or document to a council of different LLMs and synthesizes a final verdict — adapted from [karpathy/llm-council](https://github.com/karpathy/llm-council).

General-purpose: not tied to any team or domain. Works equally for an SRE rollback call, an engineering architecture decision, a product question, or a review pass on an RFC/design doc/RCA — anywhere multiple independent takes reduce single-model blind spots.

## How it works

1. **First opinions** — the question goes to every council model independently, in parallel.
2. **Cross-review** — each model gets the full set of answers, anonymized (Member A/B/C/D), and ranks them for accuracy/insight, flagging conflicts and missed risks.
3. **Chairman synthesis** — one designated model combines everything into a final answer that states a clear recommendation and explicitly surfaces any unresolved disagreement.

Unlike persona-based "council" approaches that reuse one model with different prompts, this calls genuinely different vendors (GPT, Gemini, Grok, Claude, etc.) through [OpenRouter](https://openrouter.ai/)'s single API, so the diversity of opinion is real.

## Setup

Requires an OpenRouter API key:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Get one at https://openrouter.ai/.

Install as a Claude Code skill by placing (or symlinking) this directory under `~/.claude/skills/llm-council/` (personal) or `<project>/.claude/skills/llm-council/` (project-scoped).

Council membership lives in `scripts/config.json`:

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

Model slugs are OpenRouter IDs and drift over time — check https://openrouter.ai/models for current ones. Edit this file to add/remove members or change the chairman; no code changes needed.

## Usage

**On-demand**, inside Claude Code:

```
/llm-council <question, decision, or path to a doc to review>
```

Or run the script directly:

```bash
python3 scripts/council.py "Should we use Postgres or DynamoDB for the new event-ingestion service?"
python3 scripts/council.py "Review this RCA for gaps or unsupported conclusions" --file ./incident-482-rca.md
```

Output is a markdown report (final verdict up top, individual answers and cross-reviews collapsed below), and a JSON transcript is saved under `history/` (gitignored).

**As a step in other automation**: any other skill or scheduled agent can shell out to `scripts/council.py` as a pre-flight sanity check on its own draft output before finalizing.

**On a recurring schedule**: wire it into a cron-triggered Routine to get a standing digest rather than only on-demand use.

No third-party Python dependencies — stdlib only.

## License

Not yet specified — pick one (MIT/Apache-2.0/etc.) before treating this as reusable by others.
