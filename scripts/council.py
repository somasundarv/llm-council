#!/usr/bin/env python3
"""Multi-LLM council deliberation, adapted from github.com/karpathy/llm-council.

Stage 1: ask N different LLMs (via OpenRouter) the same question independently.
Stage 2: anonymize the answers and have each model cross-review/rank the set.
Stage 3: a chairman model synthesizes a final answer, flagging disagreement.

No third-party dependencies - stdlib only, so it runs anywhere python3 runs.
"""
import argparse
import datetime
import json
import os
import pathlib
import random
import string
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from providers import call_model_safe, parse_spec, run_parallel  # noqa: E402

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
HISTORY_DIR = SCRIPT_DIR.parent / "history"


def load_config(path=None):
    cfg_path = pathlib.Path(path) if path else SCRIPT_DIR / "config.json"
    if not cfg_path.exists():
        print(
            f"ERROR: {cfg_path} not found.\n"
            f"Run `python3 {SCRIPT_DIR / 'setup.py'}` to create one (or copy "
            "config.example.json to config.json and edit it directly).",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(cfg_path) as f:
        return json.load(f)


def stage1_first_opinions(models, question, timeout):
    return run_parallel(models, question, timeout)


def stage2_cross_review(models, question, opinions, timeout):
    member_ids = list(string.ascii_uppercase[: len(opinions)])
    shuffled = list(opinions.items())
    random.shuffle(shuffled)
    anonymized_block = "\n\n".join(
        f"MEMBER {label}: {text}" for label, (_, text) in zip(member_ids, shuffled)
    )
    review_prompt = (
        "You are an impartial reviewer on a multi-LLM council. Below are anonymized "
        "responses (Member labels) from different council members to the same question. "
        "Rank them by accuracy and usefulness, and call out: (a) any factual or claim "
        "conflicts between members, (b) any insight one member caught that the others "
        "missed. Be terse and specific.\n\n"
        f"QUESTION: {question}\n\n{anonymized_block}"
    )
    return run_parallel(models, review_prompt, timeout)


def stage3_chairman(chairman_model, question, opinions, reviews, timeout):
    opinions_block = "\n\n".join(f"--- {m} ---\n{text}" for m, text in opinions.items())
    reviews_block = "\n\n".join(f"--- review by {m} ---\n{text}" for m, text in reviews.items())
    chairman_prompt = (
        "You are the Chairman of an LLM council. You are given a question, the "
        "independent first-opinion answers from each council member (attributed by "
        "model name), and each member's cross-review of the anonymized answer set. "
        "Produce a single final answer that:\n"
        "1. States a clear recommendation/answer\n"
        "2. Notes confidence and how much the council agreed\n"
        "3. Explicitly flags any unresolved disagreement between members and why it matters\n"
        "4. Synthesizes the best insights across all members rather than just picking one\n"
        "Be decisive - don't just average everything into mush.\n\n"
        f"QUESTION: {question}\n\nFIRST OPINIONS:\n{opinions_block}\n\nCROSS-REVIEWS:\n{reviews_block}"
    )
    return call_model_safe(chairman_model, chairman_prompt, timeout)


def render_report(question, opinions, reviews, verdict):
    lines = [
        "## LLM Council Verdict\n",
        f"**Question:** {question}\n",
        verdict,
        "\n---\n",
        "<details><summary>Individual council member answers</summary>\n",
    ]
    for m, text in opinions.items():
        lines.append(f"\n**{m}:**\n{text}\n")
    lines.append("\n</details>\n\n<details><summary>Cross-review (each member ranking the anonymized set)</summary>\n")
    for m, text in reviews.items():
        lines.append(f"\n**Review by {m}:**\n{text}\n")
    lines.append("\n</details>")
    return "\n".join(lines)


def save_history(question, opinions, reviews, verdict):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = HISTORY_DIR / f"{ts}.json"
    with open(path, "w") as f:
        json.dump(
            {"question": question, "opinions": opinions, "reviews": reviews, "verdict": verdict, "timestamp": ts},
            f,
            indent=2,
        )
    return path


def main():
    parser = argparse.ArgumentParser(description="Run a question/task through a council of different LLMs.")
    parser.add_argument("question", help="The question, decision, or task to put to the council")
    parser.add_argument("--file", help="Path to a file (doc, RFC, diff, RCA, etc.) to attach as context", default=None)
    parser.add_argument("--config", help="Path to config.json", default=None)
    parser.add_argument("--no-history", action="store_true", help="Don't save a transcript under history/")
    args = parser.parse_args()

    cfg = load_config(args.config)
    council_models = cfg["council_models"]
    chairman_model = cfg["chairman_model"]
    timeout = cfg.get("timeout_seconds", 120)

    needs_openrouter = any(parse_spec(m)[0] == "openrouter" for m in council_models + [chairman_model])
    if needs_openrouter and not os.environ.get("OPENROUTER_API_KEY"):
        print(
            "ERROR: OPENROUTER_API_KEY is not set, but at least one configured model "
            "routes through OpenRouter.\n"
            "Get a key at https://openrouter.ai/ and export it, e.g.:\n"
            "  export OPENROUTER_API_KEY=sk-or-v1-...\n"
            "Or switch council_models/chairman_model in config.json to 'ollama:<model>' "
            "entries to run entirely on local models.",
            file=sys.stderr,
        )
        sys.exit(1)

    full_question = args.question
    if args.file:
        with open(args.file) as f:
            attached = f.read()
        full_question = f"{args.question}\n\n---\nATTACHED FILE ({args.file}):\n{attached}"

    print(f"Stage 1: asking {len(council_models)} models independently...", file=sys.stderr)
    opinions = stage1_first_opinions(council_models, full_question, timeout)

    print("Stage 2: cross-reviewing anonymized answers...", file=sys.stderr)
    reviews = stage2_cross_review(council_models, full_question, opinions, timeout)

    print(f"Stage 3: chairman ({chairman_model}) synthesizing...", file=sys.stderr)
    verdict = stage3_chairman(chairman_model, full_question, opinions, reviews, timeout)

    report = render_report(args.question, opinions, reviews, verdict)
    print(report)

    if not args.no_history:
        path = save_history(args.question, opinions, reviews, verdict)
        print(f"\n(transcript saved to {path})", file=sys.stderr)


if __name__ == "__main__":
    main()
