#!/usr/bin/env python3
"""Persona-driven advisor debate mode.

Named advisor personas argue a question across rounds (opening positions, then
rebuttal rounds with early stop on convergence), and a moderator delivers a
structured verdict: summary, consensus points, disagreements, recommendation,
next steps, open questions.

Use this instead of council.py when the question is a real decision with
tradeoffs, risk, strategy, or ethics involved - not for direct factual/creative
answers, where independent-model synthesis (council.py) is a better fit.
"""
import argparse
import datetime
import json
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from providers import call_model_safe, parse_spec  # noqa: E402

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
HISTORY_DIR = SCRIPT_DIR.parent / "history"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def run_persona_turns(personas, build_prompt, model, timeout):
    """All personas share one model spec. If it's ollama-backed, run turns one at
    a time - concurrent generation requests against the same local model still
    contend for the same limited CPU/RAM and time out on small machines."""
    if parse_spec(model)[0] == "ollama":
        return {k: call_model_safe(model, build_prompt(p), timeout) for k, p in personas.items()}

    def ask(key, persona):
        return key, call_model_safe(model, build_prompt(persona), timeout)

    statements = {}
    with ThreadPoolExecutor(max_workers=max(len(personas), 1)) as pool:
        futures = [pool.submit(ask, k, p) for k, p in personas.items()]
        for fut in as_completed(futures):
            key, text = fut.result()
            statements[key] = text
    return statements


def transcript_block(personas, rounds):
    lines = []
    for i, round_statements in enumerate(rounds, start=1):
        lines.append(f"--- Round {i} ---")
        for key, text in round_statements.items():
            lines.append(f"{personas[key]['label']}: {text}")
    return "\n\n".join(lines)


def opening_round(personas, question, model, timeout):
    def build(p):
        return (
            f"{p['system_prompt']}\n\nQuestion under debate: {question}\n\n"
            "State your opening position in under 150 words. Take a clear stance - don't hedge."
        )

    return run_persona_turns(personas, build, model, timeout)


def rebuttal_round(personas, question, rounds, model, timeout):
    history = transcript_block(personas, rounds)

    def build(p):
        return (
            f"{p['system_prompt']}\n\nQuestion under debate: {question}\n\n"
            f"Debate so far:\n{history}\n\n"
            f"As {p['label']}, respond to the others by name where relevant. Hold your "
            "position, concede points if genuinely persuaded, or sharpen your argument. "
            "Under 150 words."
        )

    return run_persona_turns(personas, build, model, timeout)


def check_convergence(question, rounds, personas, model, timeout):
    history = transcript_block(personas, rounds)
    prompt = (
        "You are moderating a structured debate. Based on the transcript below, have "
        "the advisors substantially converged on a shared recommendation (minor caveats "
        "are fine)? Answer YES or NO on the first line, then one sentence why.\n\n"
        f"QUESTION: {question}\n\n{history}"
    )
    result = call_model_safe(model, prompt, timeout)
    return result.strip().upper().startswith("YES"), result


def deliver_verdict(question, rounds, personas, model, timeout):
    history = transcript_block(personas, rounds)
    prompt = (
        "You are the moderator delivering the final verdict for this debate. Using the "
        "full transcript below, produce a markdown report with exactly these sections:\n"
        "## Summary\n(2-3 sentences)\n"
        "## Consensus Points\n(bulleted)\n"
        "## Disagreements\n(markdown table: Advisor | Position)\n"
        "## Verdict\n(a clear, decisive recommendation - don't average opinions into mush)\n"
        "## Next Steps\n(bulleted, concrete)\n"
        "## Open Questions\n(bulleted - what would change the verdict)\n\n"
        f"QUESTION: {question}\n\n{history}"
    )
    return call_model_safe(model, prompt, timeout)


def save_history(question, personas, rounds, verdict):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = HISTORY_DIR / f"{ts}-advisors.json"
    with open(path, "w") as f:
        json.dump(
            {"question": question, "personas": list(personas.keys()), "rounds": rounds, "verdict": verdict, "timestamp": ts},
            f,
            indent=2,
        )
    return path


def main():
    parser = argparse.ArgumentParser(description="Run a persona-driven advisor debate on a question.")
    parser.add_argument("question", help="The question or decision to debate")
    parser.add_argument("--file", help="Path to a file to attach as context", default=None)
    parser.add_argument("--personas", help="Comma-separated persona keys (default: from config.json)", default=None)
    parser.add_argument("--rounds", type=int, help="Max debate rounds (default: from config.json)", default=None)
    parser.add_argument("--config", help="Path to config.json", default=None)
    parser.add_argument("--personas-file", help="Path to personas.json", default=None)
    parser.add_argument("--no-history", action="store_true", help="Don't save a transcript under history/")
    args = parser.parse_args()

    cfg_path = pathlib.Path(args.config) if args.config else SCRIPT_DIR / "config.json"
    if not cfg_path.exists():
        print(
            f"ERROR: {cfg_path} not found.\n"
            f"Run `python3 {SCRIPT_DIR / 'setup.py'}` to create one (or copy "
            "config.example.json to config.json and edit it directly).",
            file=sys.stderr,
        )
        sys.exit(1)
    cfg = load_json(cfg_path)
    all_personas = load_json(args.personas_file or SCRIPT_DIR / "personas.json")

    keys = args.personas.split(",") if args.personas else cfg.get("default_personas", list(all_personas)[:4])
    unknown = [k for k in keys if k not in all_personas]
    if unknown:
        print(f"ERROR: unknown persona(s) {unknown}. Available: {list(all_personas)}", file=sys.stderr)
        sys.exit(1)
    personas = {k: all_personas[k] for k in keys}

    model = cfg.get("debate_model", cfg["chairman_model"])
    timeout = cfg.get("timeout_seconds", 120)
    max_rounds = args.rounds or cfg.get("max_rounds", 3)

    if parse_spec(model)[0] == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
        print(
            f"ERROR: OPENROUTER_API_KEY is not set, but debate_model ({model}) routes "
            "through OpenRouter.\n"
            "Get a key at https://openrouter.ai/ and export it, e.g.:\n"
            "  export OPENROUTER_API_KEY=sk-or-v1-...\n"
            "Or set debate_model in config.json to an 'ollama:<model>' entry to run "
            "entirely on a local model.",
            file=sys.stderr,
        )
        sys.exit(1)

    question = args.question
    if args.file:
        with open(args.file) as f:
            question = f"{question}\n\n---\nATTACHED FILE ({args.file}):\n{f.read()}"

    labels = ", ".join(p["label"] for p in personas.values())
    print(f"Round 1: opening positions from {labels}...", file=sys.stderr)
    rounds = [opening_round(personas, question, model, timeout)]

    for r in range(2, max_rounds + 1):
        if r > 2:
            converged, _ = check_convergence(question, rounds, personas, model, timeout)
            if converged:
                print(f"Converged after round {r - 1}, skipping to verdict.", file=sys.stderr)
                break
        print(f"Round {r}: rebuttals...", file=sys.stderr)
        rounds.append(rebuttal_round(personas, question, rounds, model, timeout))

    print("Moderator delivering verdict...", file=sys.stderr)
    verdict = deliver_verdict(question, rounds, personas, model, timeout)

    print(f"## Advisor Debate: {args.question}\n")
    print(verdict)
    print("\n---\n<details><summary>Full debate transcript</summary>\n")
    print(transcript_block(personas, rounds))
    print("\n</details>")

    if not args.no_history:
        path = save_history(args.question, personas, rounds, verdict)
        print(f"\n(transcript saved to {path})", file=sys.stderr)


if __name__ == "__main__":
    main()
