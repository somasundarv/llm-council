#!/usr/bin/env python3
"""Interactive setup - pick which LLMs power your council/advisors.

Run once after cloning:  python3 scripts/setup.py
Writes scripts/config.json (gitignored - your personal choice, never committed,
never overwritten by `git pull`). Re-run anytime to reconfigure.

Non-interactive use: just edit config.json directly, or copy
config.example.json to config.json yourself - this wizard is a convenience,
not a requirement.
"""
import json
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
EXAMPLE = SCRIPT_DIR / "config.example.json"
TARGET = SCRIPT_DIR / "config.json"


def prompt(label, default):
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def prompt_model_list(label, defaults):
    print(f"\n{label}")
    print("Enter each model as 'provider:model' (e.g. ollama:qwen3:1.7b) or a bare")
    print("OpenRouter slug (e.g. openai/gpt-5.1). Blank line to stop.")
    print(f"Current default ({len(defaults)}): {', '.join(defaults)}")
    models = []
    i = 1
    while True:
        raw = input(f"  model {i} (blank to stop, or to keep defaults if list is empty): ").strip()
        if not raw:
            break
        models.append(raw)
        i += 1
    return models or defaults


def main():
    if not EXAMPLE.exists():
        raise SystemExit(f"ERROR: {EXAMPLE} is missing - re-clone the repo.")

    cfg = json.loads(EXAMPLE.read_text())
    cfg.pop("_note", None)

    print("=== llm-council setup ===\n")
    print("Two provider options, mix freely:")
    print("  ollama:<model>      free, local - needs `ollama serve` + `ollama pull <model>`")
    print("  <openrouter-slug>   paid, cloud  - needs OPENROUTER_API_KEY (e.g. openai/gpt-5.1)")
    print("See docs/CONFIGURATION.md for the full reference and model-size guidance.\n")

    cfg["council_models"] = prompt_model_list(
        "Council members (council.py - independent first opinions):", cfg["council_models"]
    )
    cfg["chairman_model"] = prompt(
        "\nChairman model (synthesizes the final council.py verdict)", cfg["chairman_model"]
    )
    cfg["debate_model"] = prompt(
        "Debate model (drives every advisors.py persona turn)", cfg["debate_model"]
    )
    cfg["max_rounds"] = int(prompt("Max advisor debate rounds", cfg["max_rounds"]))
    cfg["timeout_seconds"] = int(prompt("Per-call timeout in seconds", cfg["timeout_seconds"]))

    TARGET.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"\nWrote {TARGET}")

    all_models = cfg["council_models"] + [cfg["chairman_model"], cfg["debate_model"]]
    uses_openrouter = any(":" not in m or m.split(":", 1)[0] != "ollama" for m in all_models)
    uses_ollama = any(m.startswith("ollama:") for m in all_models)

    if uses_openrouter:
        print("\nReminder: at least one model routes through OpenRouter.")
        print("  export OPENROUTER_API_KEY=sk-or-v1-...   (get one at https://openrouter.ai/)")
    if uses_ollama:
        print("\nReminder: at least one model runs on local Ollama.")
        print("  ollama serve   (or `brew services start ollama` to keep it running)")
        pulled = [m.split(":", 1)[1] for m in all_models if m.startswith("ollama:")]
        for model in dict.fromkeys(pulled):
            print(f"  ollama pull {model}")


if __name__ == "__main__":
    main()
