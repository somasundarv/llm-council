# llm-council

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-5A32A3.svg)](https://claude.com/claude-code)
[![Zero dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-success.svg)](scripts/)

> Put a question, decision, or document to a council of different LLMs — or a panel of named advisor personas — and get back a synthesized verdict that surfaces disagreement instead of averaging it away.

A [Claude Code](https://claude.com/claude-code) Skill, runnable standalone as plain Python. Adapted from [karpathy/llm-council](https://github.com/karpathy/llm-council) (the original 3-stage deliberation pattern) and the dual Council/Advisors split popularized by [jacob-bd/the-ai-counsel](https://github.com/jacob-bd/the-ai-counsel) — reimplemented from scratch as a ~600-line, zero-dependency tool rather than a FastAPI/React app, so it installs in seconds and runs anywhere `python3` does.


> **Privacy note:** any model configured through a cloud provider (OpenRouter) sends your question text to that provider. For confidential material — incident details, unreleased designs — use local `ollama:` models only.
General-purpose, not tied to any team or domain: an SRE rollback call, an engineering architecture decision, a product prioritization question, or a review pass on an RFC/design doc/RCA all fit the same pattern — multiple independent takes catch what one model misses.

## Two modes

| | Council (`council.py`) | Advisors (`advisors.py`) |
|---|---|---|
| **What happens** | Different LLMs independently answer, anonymously peer-review each other, a chairman synthesizes | Named personas (Skeptic, Strategist, Risk Assessor, ...) debate across rounds and a moderator delivers a verdict |
| **Best for** | Direct answers, factual questions, "give me the best response" | Real tradeoffs, risk, strategy, ethics — something worth arguing about |
| **Pick it when** | One defensible answer exists | Reasonable people (or models) could disagree |

Full guide: [docs/MODES.md](docs/MODES.md).

## Quickstart

```bash
git clone https://github.com/somasundarv/llm-council.git
cd llm-council
python3 scripts/setup.py        # pick your models interactively
python3 scripts/council.py "What's one good habit for on-call engineers?"
```

`setup.py` writes `scripts/config.json` from the tracked template (`config.example.json`) — your personal model choices, gitignored, never committed. Free by default: the template ships with four small (~1-1.7B parameter) models across four vendors via local [Ollama](https://ollama.com/), so the quickstart above costs nothing beyond local compute. See a [real example run](examples/council-on-call-habit.md) before installing anything.

Want stronger answers or paid frontier models (GPT, Gemini, Grok, Claude via OpenRouter) instead? Full setup, sizing guidance, and the `provider:model` config format: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Usage

**Inside Claude Code**, install this directory under `~/.claude/skills/llm-council/` (personal) or `<project>/.claude/skills/llm-council/` (project-scoped), then:

```
/llm-council <question, decision, or path to a doc to review>
```

**Standalone**, run either script directly:

```bash
# Council mode
python3 scripts/council.py "Should we use Postgres or DynamoDB for the new event-ingestion service?"
python3 scripts/council.py "Review this RCA for gaps or unsupported conclusions" --file ./incident-482-rca.md

# Advisor mode
python3 scripts/advisors.py "Should we sunset the legacy API or keep maintaining it for one more year?"
python3 scripts/advisors.py "Is this rollback decision sound?" --personas skeptic,risk_assessor,customer_advocate --rounds 2
```

Output is a markdown report (verdict up top, full transcript collapsed below); a JSON transcript is saved under `history/` (gitignored).

**As a step in other automation**: any other tool, skill, or scheduled agent can shell out to either script as a pre-flight sanity check on its own draft output before finalizing — no special wiring, it's just a CLI call.

**On a recurring schedule**: wire either script into cron (or a Claude Code Routine) to get a standing digest rather than only on-demand use.

## Repo layout

```
llm-council/
├── scripts/
│   ├── setup.py              interactive config wizard
│   ├── council.py            mode 1: independent answers -> peer review -> chairman
│   ├── advisors.py           mode 2: persona debate -> moderator verdict
│   ├── providers.py           shared OpenRouter/Ollama dispatch
│   ├── personas.json         8 editable advisor personas
│   ├── config.example.json   tracked template
│   └── config.json           your personal config (gitignored, made by setup.py)
├── docs/
│   ├── CONFIGURATION.md      providers, model sizing, the provider:model format
│   └── MODES.md              Council vs. Advisors decision guide
├── examples/
│   └── council-on-call-habit.md   real sample output
├── history/                  saved run transcripts (gitignored)
├── SKILL.md                  Claude Code skill definition
└── LICENSE
```

## Why no FastAPI/React app

The-ai-counsel and the original llm-council are both full local apps with a UI, settings persistence, conversation history with search, and (for the-ai-counsel) web search and an MCP server. This project deliberately stays a script: no server to start, no frontend to build, nothing to keep running. The tradeoff is no UI and no built-in web grounding — if you want those, the projects above are the better fit. If you want something you can `git clone` and run in one line, or wire directly into an agent's automation, this is the smaller tool for that.

## License

MIT — see [LICENSE](LICENSE).

## Credits

Built on [karpathy/llm-council](https://github.com/karpathy/llm-council) by Andrej Karpathy (the original 3-stage deliberation pattern) and inspired by the dual Council/Advisors mode split in [jacob-bd/the-ai-counsel](https://github.com/jacob-bd/the-ai-counsel). Both are full local apps worth a look if you want a UI and more provider/integration breadth than this lighter, script-only tool aims for.
