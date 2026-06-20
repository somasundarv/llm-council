# Council vs. Advisors

Two deliberation modes, one tool. Picking the right one matters more than picking the right models.

## Council (`council.py`)

Real, separate LLMs independently answer the same question, anonymously peer-review each other's answers, then a chairman model synthesizes a final verdict. No personas, no debate - just diverse models converging (or visibly failing to converge) on an answer.

**Use it for:**
- Direct factual questions with one defensible answer
- "Give me the best response" synthesis across models
- Cross-checking a draft document, RCA, or design doc for gaps a single model might miss
- Anything where you want diversity of *model*, not diversity of *viewpoint*

**Examples:**
- "What's causing this stack trace?"
- "Review this RCA for unsupported conclusions."
- "Summarize this RFC's key tradeoffs."

## Advisors (`advisors.py`)

Named personas (Skeptic, Pragmatist, Strategist, Risk Assessor, etc.) argue the question across rounds, rebutting each other by name, until they converge or hit `max_rounds`. A moderator then delivers a structured verdict: summary, consensus points, a disagreements table, a decisive recommendation, next steps, and open questions.

**Use it for:**
- Real tradeoffs, strategic choices, or prioritization calls
- Risk reviews where you want worst-case thinking surfaced explicitly
- Ethical or fairness questions
- Anything where reasonable people could land in different places

**Examples:**
- "Should we sunset the legacy API or keep maintaining it?"
- "Is this rollback decision sound given the blast radius?"
- "Build vs. buy for the new notification system?"

## The simple heuristic

> If the question has one defensible answer, use **Council**.
> If reasonable people (or models) could disagree, use **Advisors**.

When genuinely unsure, default to Council — it's cheaper (single pass, no multi-round debate) and the chairman still explicitly flags disagreement if the independent answers conflict. You lose the named-persona framing and the structured verdict table, but you keep the core "don't trust one model's blind spots" value.

## Cost/time shape of each

| | Council | Advisors |
|---|---|---|
| Calls per run | `2 × len(council_models) + 1` | `len(personas) × rounds_run` (+1 convergence check per round after the 2nd) `+ 1` verdict |
| Models involved | Up to `len(council_models)` distinct models | 1 model (`debate_model`), multiple personas via prompting |
| Best diversity source | Different vendors/models | Different argued positions |

Advisors generally costs more calls for a given `max_rounds`, since every persona speaks every round, not just once.
