# Example: Council mode, free local models

Real output from `council.py`, unedited except for trimming. Question asked with the default `config.example.json` lineup — four small (~1-1.7B parameter) models via Ollama, zero API cost: `qwen3:1.7b`, `deepseek-r1:1.5b`, `gemma3:1b`, `llama3.2:1b`.

```bash
python3 scripts/council.py "What's one good habit for on-call engineers?"
```

## LLM Council Verdict

**Question:** What's one good habit for on-call engineers?

**Final Answer:**
The council unanimously recommends prioritizing **self-care and continuous learning** as the most critical habit for on-call engineers.

1. **Recommendation:**
   - **Prioritize Self-Care:** On-call engineers must balance workload and burnout prevention. Practices like regular sleep, breaks, and physical activity are foundational.
   - **Combine with Continuous Learning:** Actively expanding knowledge (e.g., reading documentation, code walkthroughs) ensures readiness to tackle complex problems.

2. **Confidence & Agreement:**
   - **High Agreement:** The council agrees that self-care (sleep, breaks, exercise) and continuous learning (documentation, code analysis) are essential.
   - **Moderate Agreement:** Disagreements arise over the **specific methods** (e.g., tools like Jira vs. checklist-based learning) and the **focus** (e.g., burnout prevention vs. skill growth).

3. **Unresolved Disagreement:**
   - **Method of Prioritization:** Members A and C agree on the importance of tools (e.g., Jira) for task management, but differ in the **type of tools** (A emphasizes checklist-based learning, C highlights tool use).
   - **Focus on Burnout vs. Skill Growth:** Members B and D emphasize **self-care** (e.g., sleep, exercise) as central, while A and C prioritize **skill development** (e.g., documentation, code analysis).

4. **Synthesized Insights:**
   The council synthesizes the best practices into a **balanced framework**:
   - **Actionable Prioritization:** Use tools like Jira to manage critical tasks (A and C).
   - **Self-Care Integration:** Incorporate sleep, breaks, and physical activity to prevent burnout (B and D).
   - **Continuous Learning:** Dedicate time to reading documentation and analyzing code (A and C).

**Conclusion:** The council prioritizes **self-care** and **skill development** as the best practices, leveraging the consensus on self-care and the depth of insights from members A and C rather than averaging every method into mush.

---

<details><summary>Individual council member answers</summary>

**ollama:qwen3:1.7b:**
One excellent habit for on-call engineers is **prioritizing critical issues first**. This practice ensures that you focus on high-impact problems, minimize burnout, and maintain efficiency by addressing the most urgent or complex tasks first.

**ollama:deepseek-r1:1.5b:**
As an AI assistant, I aim to help you with honesty and openness, while avoiding any potentially harmful actions.

**ollama:gemma3:1b:**
Regularly run a self-improvement/knowledge-expansion "check list" focused on actionable tasks — a short (5-15 minute) dedicated session each week to actively look for ways you're getting better.

**ollama:llama3.2:1b:**
One effective habit for on-call engineers is to prioritize and manage their time effectively — get enough sleep, plan ahead, and schedule breaks during off-shift downtime to avoid burnout.

</details>

<details><summary>Cross-review (each member ranking the anonymized set)</summary>

Each member received all four answers above relabeled Member A-D (no names attached) and ranked them for accuracy and usefulness, flagging conflicts and insights the others missed. See `docs/CONFIGURATION.md` for how this stage works.

</details>

## What this demonstrates

- **Real disagreement surfaced, not smoothed over** — the chairman explicitly calls out where members split (tools vs. checklists, burnout vs. skill growth) instead of averaging into mush.
- **Small free models occasionally produce a non-answer** — `deepseek-r1:1.5b` gave a generic refusal-flavored non-answer to a completely benign question. The pipeline doesn't choke on this; it just becomes one weak opinion among four, and the chairman synthesizes around it. Expect more of this with very small distilled models than with frontier ones - it's a quality/cost tradeoff, not a bug.
- **No API key, no cost** - this entire run, all 9 calls, cost nothing beyond local compute.
