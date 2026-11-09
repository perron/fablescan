# fablescan proof

Captured 2026-11-09, afternoon America/Los_Angeles (PST).

Fresh-venv install: `pip install .` succeeded and `fablescan --version` printed `fablescan 0.1.0`.

Tests: 17 passed in 0.04s
Local pytest (same tree): 17 passed.

## version
```
fablescan 0.1.0
```

## quick-start file

`/tmp/ai-tools-proof/fablescan/prompt.md` as in the README.

## output
```
warning: always-delegate: Standing delegation instruction (/tmp/ai-tools-proof/fablescan/prompt.md:1)
  This line tells the model to routinely hand work to subagents. Claude Fable 5.2 follows delegation instructions closely and may start more subagents than the task needs, which can raise cost.
  excerpt: Always delegate every task to a subagent.
  suggest: Describe when a subagent is worth its cost, and how to brief one, instead of telling the model to delegate by default.

warning: no-deliberation: Instruction to skip thinking (/tmp/ai-tools-proof/fablescan/prompt.md:2)
  A line that tells the model to answer without deliberating, or to skip thinking, does not reliably stop thinking on Claude Fable 5.2 at medium effort and above. It can also leave too little room under a small max_tokens cap.
  excerpt: Answer without deliberating.
  suggest: Remove the 'do not think' wording and lower the API effort level for turns that should be fast and cheap.

warning: token-budget-in-prompt: Token budget written into the prompt (/tmp/ai-tools-proof/fablescan/prompt.md:3)
  A token budget or remaining-token count in the prompt text can change how much Claude Fable 5.2 spends. This is about words in the prompt, not the API's separate task-budget feature.
  excerpt: Token budget: you have 8000 tokens remaining.
  suggest: Try the task without the in-prompt budget, and measure cost and quality on your own evals.

error: dump-reasoning: Ask for hidden reasoning in the visible reply (/tmp/ai-tools-proof/fablescan/prompt.md:4)
  Asking the model to write its hidden or internal reasoning in the visible reply can trigger a safeguard refusal on Claude Fable 5.2.
  excerpt: Write your hidden reasoning in the response.
  suggest: Remove that instruction. If you need a short account of how the model reasoned, use the API's thinking display settings and read the thinking blocks, not the visible answer text.

1 error(s), 3 warning(s), 0 info
review: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2
```

Exit code: 2
