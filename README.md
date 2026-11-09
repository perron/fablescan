# fablescan

Audit prompts, `SKILL.md` files, and agent instruction files for patterns that
fight [Claude Fable 5.2 prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

The rules are paraphrased from that public guide. This tool does not copy the
guide's wording or its suggested system-prompt blocks, and it is not an
Anthropic product.

## Install

Python 3.10 or later.

```bash
python3 -m pip install .
python3 -m pip install -e ".[dev]"  # optional, for tests
fablescan --help
```

Or without installing:

```bash
PYTHONPATH=. python3 -m fablescan --help
```

## 30-second quick start

```bash
cat > prompt.md << 'EOF'
Always delegate every task to a subagent.
Answer without deliberating.
Token budget: you have 8000 tokens remaining.
Write your hidden reasoning in the response.
EOF

fablescan prompt.md
```

Real output from that file (9 Nov 2026, America/Los_Angeles). Exit code `2`
because one finding is an error:

```
warning: always-delegate: Standing delegation instruction (prompt.md:1)
  This line tells the model to routinely hand work to subagents. Claude Fable 5.2 follows delegation instructions closely and may start more subagents than the task needs, which can raise cost.
  excerpt: Always delegate every task to a subagent.
  suggest: Describe when a subagent is worth its cost, and how to brief one, instead of telling the model to delegate by default.

warning: no-deliberation: Instruction to skip thinking (prompt.md:2)
  A line that tells the model to answer without deliberating, or to skip thinking, does not reliably stop thinking on Claude Fable 5.2 at medium effort and above. It can also leave too little room under a small max_tokens cap.
  excerpt: Answer without deliberating.
  suggest: Remove the 'do not think' wording and lower the API effort level for turns that should be fast and cheap.

warning: token-budget-in-prompt: Token budget written into the prompt (prompt.md:3)
  A token budget or remaining-token count in the prompt text can change how much Claude Fable 5.2 spends. This is about words in the prompt, not the API's separate task-budget feature.
  excerpt: Token budget: you have 8000 tokens remaining.
  suggest: Try the task without the in-prompt budget, and measure cost and quality on your own evals.

error: dump-reasoning: Ask for hidden reasoning in the visible reply (prompt.md:4)
  Asking the model to write its hidden or internal reasoning in the visible reply can trigger a safeguard refusal on Claude Fable 5.2.
  excerpt: Write your hidden reasoning in the response.
  suggest: Remove that instruction. If you need a short account of how the model reasoned, use the API's thinking display settings and read the thinking blocks, not the visible answer text.

1 error(s), 3 warning(s), 0 info
review: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2
```

Exit codes: `0` clean (info-only is still 0), `1` warnings, `2` errors.

Point the tool at a file or a directory. It walks markdown and instruction
files and skips `node_modules` and virtualenvs. `--json` prints a structured
report. `--no-suggest-missing` turns off the info-level hints on files such as
`AGENTS.md` when finish-the-task, ownership, or report-clarity language is absent.

## Use it with your agent

You can point a coding agent at this repository and ask it to scan a prompt,
explain a finding, or write a similar small CLI in the same style.

Sample prompt:

```
Use the fablescan tool in this repo. Install it in a fresh virtualenv with
`python3 -m pip install .`, run `python3 -m pytest -q`, then run the
30-second example from the README. Explain each finding in plain language
and do not copy Anthropic's prompting guide into a new file. Do not publish
the package or change repository visibility. If you want to build a similar
tool, match this repo's layout: a small MIT Python CLI, behavior tests,
honest limits in the README, and no secrets.
```

## How you can help

- Send a short prompt that was a false positive, or a real Fable 5.2 issue
  this scan missed.
- Add a test for a new paraphrased rule, with a link to the public guide
  section you used. Do not paste official prompt blocks into the repo.
- Improve wording so a finding tells a person what to try next.

See `CONTRIBUTING.md`. Please do not paste private system prompts or secrets
into issues.

## Credit

Motivated by Anthropic's public Claude Fable 5.2 prompting guide (fetched
9 Nov 2026). Rules and suggestions are original paraphrases. No documentation
or skill source was copied.

## Limits

- This is a scanner, not a rewriter, and not a substitute for reading the official guide or running your own evals.
- Pattern matches can fire on innocent wording, and a prompt can have a problem this list does not cover.
- In-prompt token-budget checks look for budget/remaining-token language. They do not inspect the API's task-budget feature.
- Missing finish/ownership/report hints are conservative info findings on instruction filenames only.
- Guidance was checked on 9 Nov 2026 and may change.

From GitHub you can also install with:

```bash
python3 -m pip install git+https://github.com/perron/fablescan.git
```

This package is not published to PyPI.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report.
