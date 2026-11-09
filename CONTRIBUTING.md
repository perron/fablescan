# Contributing to fablescan

Thanks for helping. This is a small, original scanner. The useful work is
better tests, fewer false positives, and clearer wording — not a copy of
Anthropic's prompting guide.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
fablescan --help
```

Add a behavior test for each new rule or each false-positive you fix. Put a
minimal markdown fixture in the test, not a production prompt that contains
secrets.

## Rules

- Paraphrase public guidance. Do not paste Anthropic's documentation or its
  suggested system-prompt blocks into the tool, the README, or a skill.
- Keep suggestions short and original. The tests fail if a suggestion contains
  well-known official prompt sentences.
- Link out to the official guide. Do not claim endorsement.

## What not to do

- Do not add network calls, telemetry, or API keys.
- Do not commit private prompts or credentials.
- Do not change repository visibility or publish to PyPI unless the maintainer
  asks for that exact action.

## Pull requests

Keep the diff small, name the public source you used (with a date), and
mention remaining uncertainty.
