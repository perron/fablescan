# AGENTS.md

This repository is fablescan, a small MIT-licensed Python CLI that audits
prompts and skill files for patterns that fight Claude Fable 5.2 prompting
guidance.

## Layout

- `fablescan/cli.py` — rules, scanner, CLI
- `tests/test_fablescan.py` — behavior tests, including a guard against
  pasting official prompt blocks into suggestions
- `README.md` — install, a real quick-start example, limits

## How to work here

1. `pip install -e ".[dev]"` and `python3 -m pytest -q`.
2. New checks belong in `RULES` with original wording and a short suggestion.
3. Do not copy text from https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2.
   Paraphrase the idea and link to the guide.
4. Default exit codes: `0` clean, `1` warnings, `2` errors (`dump-reasoning`).
5. `--suggest-missing` (default) only adds info findings on instruction
   filenames such as `AGENTS.md` and `CLAUDE.md`, not on every short skill.

## Do not

- Do not publish, force-push, or change repository visibility.
- Do not add workflow-file commits unless the operator's token has the
  `workflow` scope.
- Do not claim the tool is official Anthropic software.

## Checks before you finish

```bash
python3 -m pytest -q
fablescan --version
```
