"""Audit prompts and skills against Claude Fable 5.2 prompting guidance.

Rules are paraphrased from Anthropic's public prompting guide. This tool does
not copy the guide's wording or its suggested prompt blocks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

__version__ = "0.1.0"

GUIDE_URL = (
    "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/"
    "prompting-claude-fable-5-2"
)

INSTRUCTION_NAMES = {
    "AGENTS.md",
    "AGENT.md",
    "CLAUDE.md",
    "GEMINI.md",
    "HERMES.md",
    ".hermes.md",
    ".cursorrules",
    "SKILL.md",
}
INSTRUCTION_SUFFIXES = {".md", ".mdc", ".txt", ".prompt"}
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".tox",
    "vendor",
    ".mypy_cache",
    ".pytest_cache",
    ".eggs",
}

# Each pattern is original. Suggestions are short paraphrases, not a copy of
# Anthropic's sample system-prompt text.
RULES: list[dict] = [
    {
        "code": "always-delegate",
        "severity": "warning",
        "title": "Standing delegation instruction",
        "message": (
            "This line tells the model to routinely hand work to subagents. "
            "Claude Fable 5.2 follows delegation instructions closely and may "
            "start more subagents than the task needs, which can raise cost."
        ),
        "suggest": (
            "Describe when a subagent is worth its cost, and how to brief one, "
            "instead of telling the model to delegate by default."
        ),
        "patterns": [
            r"\balways\s+(delegate|hand\s+off|spawn\s+a\s+sub-?agent|use\s+sub-?agents?)\b",
            r"\bdelegate\s+(everything|all\s+tasks?|all\s+work|every\s+task)\b",
            r"\b(must|should)\s+always\s+delegate\b",
            r"\buse\s+sub-?agents?\s+for\s+(every|all|each)\b",
            r"\bfor\s+every\s+task,?\s+delegate\b",
        ],
    },
    {
        "code": "no-deliberation",
        "severity": "warning",
        "title": "Instruction to skip thinking",
        "message": (
            "A line that tells the model to answer without deliberating, or to "
            "skip thinking, does not reliably stop thinking on Claude Fable 5.2 "
            "at medium effort and above. It can also leave too little room under "
            "a small max_tokens cap."
        ),
        "suggest": (
            "Remove the 'do not think' wording and lower the API effort level "
            "for turns that should be fast and cheap."
        ),
        "patterns": [
            r"\banswer\s+(directly\s+)?without\s+(deliberating|thinking|reasoning)\b",
            r"\bwithout\s+(any\s+)?(deliberation|reasoning)\b",
            r"\bdo\s+not\s+(deliberate|reason\s+out\s+loud)\b",
            r"\bdon't\s+deliberate\b",
            r"\bskip\s+(your\s+)?(thinking|deliberation|reasoning)\b",
            r"\bdisable\s+thinking\b",
            r"\bthink\s+less\b",
            r"\bno\s+chain-?of-?thought\b",
        ],
    },
    {
        "code": "token-budget-in-prompt",
        "severity": "warning",
        "title": "Token budget written into the prompt",
        "message": (
            "A token budget or remaining-token count in the prompt text can "
            "change how much Claude Fable 5.2 spends. This is about words in "
            "the prompt, not the API's separate task-budget feature."
        ),
        "suggest": (
            "Try the task without the in-prompt budget, and measure cost and "
            "quality on your own evals."
        ),
        "patterns": [
            r"\btoken\s+budget\b",
            r"\bbudget\s+of\s+\d[\d,]*\s+tokens?\b",
            r"\b(?:you\s+have|remaining|tokens?\s+left[:\s]+)\s*\d[\d,]*\s+tokens?\b",
            r"\b\d[\d,]*\s+tokens?\s+(remaining|left)\b",
            r"\byou\s+may\s+use\s+(at\s+most\s+)?\d[\d,]*\s+tokens?\b",
        ],
    },
    {
        "code": "absolute-caution",
        "severity": "warning",
        "title": "Absolute caution without a stated scope",
        "message": (
            "Absolute 'never' or 'always ask first' rules can pile up in "
            "skills, notes, and agent files. Claude Fable 5.2 follows them "
            "closely and may ask for approvals it does not need, or hold back "
            "routine work such as a safe retry."
        ),
        "suggest": (
            "Scope the rule (what it covers and why). Name the actions that "
            "need approval, and the routine actions that do not. Keep a human "
            "confirmation step for risky or irreversible work."
        ),
        "patterns": [
            r"(?im)^(?:\s*[-*]\s*|\s*\d+\.\s*)?never\s+(?:retry|continue|proceed|guess|fix|edit|commit|push|delete|run|call|use|ask|do|write|change)\b",
            r"(?im)^(?:\s*[-*]\s*|\s*\d+\.\s*)?always\s+ask\s+(for\s+)?(approval|permission|the\s+user)\b",
            r"\bask\s+(for\s+approval|permission)\s+before\s+(any|every|all|each)\b",
            r"\bdo\s+not\s+ever\s+(retry|continue|proceed|guess)\b",
            r"\bstop\s+at\s+the\s+first\s+error\b",
        ],
    },
    {
        "code": "treat-answer-done",
        "severity": "warning",
        "title": "Treat an earlier answer as finished",
        "message": (
            "Lines that tell the model to treat an earlier answer as done, or "
            "not to re-examine it, can make Claude Fable 5.2 less likely to "
            "notice mistakes in its previous replies."
        ),
        "suggest": (
            "Keep this wording only if you have tested that the model still "
            "catches its own earlier mistakes when you want it to."
        ),
        "patterns": [
            r"\btreat\s+(that|the|an|any)\s+(earlier\s+)?(answer|response|reply)\s+as\s+(done|final|finished|complete)\b",
            r"\bdo\s+not\s+re-?examin(?:e|ing)\s+(your\s+)?(earlier|previous)\b",
            r"\bdon't\s+re-?examin(?:e|ing)\s+(your\s+)?(earlier|previous)\b",
            r"\bfocus\s+(your\s+)?thinking\s+on\s+the\s+new\s+message\b",
        ],
    },
    {
        "code": "rigid-style",
        "severity": "warning",
        "title": "Rigid style cap",
        "message": (
            "Claude Fable 5.2 follows style rules closely, so a hard cap such "
            "as a very low word limit per sentence can make the prose choppy."
        ),
        "suggest": (
            "Drop style caps you no longer need. If you want clearer reports, "
            "ask for a self-contained summary in plain language instead of a "
            "strict word limit."
        ),
        "patterns": [
            r"\bone\s+instruction\s+per\s+sentence\b",
            r"\bin\s+\d+\s+words?\s+or\s+fewer\b",
            r"\bno\s+more\s+than\s+\d+\s+words?\s+per\s+sentence\b",
            r"\bsentences?\s+must\s+(be\s+)?(under|at\s+most|no\s+more\s+than)\s+\d+\s+words?\b",
            r"\beach\s+sentence\s+(must|may)\s+(be\s+)?(under|at\s+most)\s+\d+\s+words?\b",
        ],
    },
    {
        "code": "dump-reasoning",
        "severity": "error",
        "title": "Ask for hidden reasoning in the visible reply",
        "message": (
            "Asking the model to write its hidden or internal reasoning in the "
            "visible reply can trigger a safeguard refusal on Claude Fable 5.2."
        ),
        "suggest": (
            "Remove that instruction. If you need a short account of how the "
            "model reasoned, use the API's thinking display settings and read "
            "the thinking blocks, not the visible answer text."
        ),
        "patterns": [
            r"\b(write|print|show|dump|reveal|include|reproduce)\s+(your\s+)?(hidden\s+|internal\s+|full\s+)?(chain[- ]of[- ]thought|reasoning|thinking)\s+in\s+the\s+(response|reply|answer|output|visible)\b",
            r"\b(internal\s+reasoning|hidden\s+reasoning|chain[- ]of[- ]thought)\s+in\s+the\s+(response|reply|answer|output)\b",
            r"\breproduce\s+(your\s+)?(internal\s+)?reasoning\b",
            r"\bput\s+(your\s+)?(full\s+)?thinking\s+in\s+the\s+(user[- ]facing\s+)?(reply|response|answer)\b",
        ],
    },
    {
        "code": "micromanage-steps",
        "severity": "warning",
        "title": "Mandatory step list that leaves no room to finish the work",
        "message": (
            "A long mandatory step list, or a rule not to deviate from the "
            "steps, can fight Claude Fable 5.2's tendency to own the work and "
            "finish it. Short workflows that describe a real order are fine."
        ),
        "suggest": (
            "State the outcome, who owns the work, and what 'done' looks like. "
            "Keep a step list only where the order is a real constraint."
        ),
        "patterns": [
            r"\byou\s+must\s+follow\s+these\s+steps\s+exactly\b",
            r"\bmandatory\s+step[- ]by[- ]step\b",
            r"\bdo\s+not\s+deviate\s+from\s+these\s+steps\b",
            r"\bdon't\s+deviate\s+from\s+these\s+steps\b",
            r"\bfollow\s+these\s+\d+\s+steps\s+in\s+order(?:\s+exactly)?\b",
            r"\bdo\s+not\s+skip\s+(any|a)\s+step\b",
        ],
    },
]

COMPILED = [
    {
        **rule,
        "regexes": [re.compile(p, re.IGNORECASE) for p in rule["patterns"]],
    }
    for rule in RULES
]

# Hint language for instruction files (info only). These are rough presence
# checks, not a requirement that every skill copy Anthropic's advice.
MISSING_HINTS = [
    {
        "code": "missing-finish-task",
        "needle": re.compile(
            r"\b(finish\s+(the\s+)?(whole\s+)?task|do\s+not\s+stop\s+early|don't\s+stop\s+early|be\s+persistent|carry\s+on\s+with\s+work|avoid\s+stopping)\b",
            re.I,
        ),
        "message": (
            "This instruction file does not obviously tell the model to finish "
            "the work it still owes. On long tasks at lower effort, Claude "
            "Fable 5.2 sometimes stops early with leftover work."
        ),
        "suggest": (
            "If you see early stops, add a short line that the model should "
            "keep going through ordinary errors, and only stop on a real, "
            "deliberate blocker or when it needs the user."
        ),
    },
    {
        "code": "missing-ownership",
        "needle": re.compile(
            r"\b(this\s+codebase\s+is\s+yours|you\s+own\s+(this\s+)?(code|codebase)|the\s+code\s+is\s+yours|take\s+ownership)\b",
            re.I,
        ),
        "message": (
            "This instruction file does not obviously say who owns the code. "
            "When the prompt is silent, Claude Fable 5.2 may add to existing "
            "structure or report nearby problems instead of fixing them."
        ),
        "suggest": (
            "If you want the model to merge repeated code and fix related "
            "issues, say that the codebase is its to keep building. Leave that "
            "out when the user wants the smallest possible change."
        ),
    },
    {
        "code": "missing-report-clarity",
        "needle": re.compile(
            r"\b(self-contained|low-context\s+reader|stands?\s+on\s+its\s+own|key\s+points\s+in\s+the\s+first|plain\s+language|closing\s+recap)\b",
            re.I,
        ),
        "message": (
            "This instruction file does not obviously ask for a self-contained "
            "final report. Readers of a long agent run often have not seen the "
            "tool calls behind it."
        ),
        "suggest": (
            "If the model writes handoffs or final reports, ask it to put the "
            "key points first and to write so a reader without the tool log "
            "can still follow along."
        ),
    },
]

MISSING_FILE_HINTS = {
    "AGENTS.md",
    "AGENT.md",
    "CLAUDE.md",
    "GEMINI.md",
    "HERMES.md",
    ".hermes.md",
    ".cursorrules",
}


@dataclass
class Finding:
    severity: str
    code: str
    title: str
    message: str
    suggest: str
    path: str
    line: int
    excerpt: str


def is_instruction_file(path: Path) -> bool:
    if path.name in INSTRUCTION_NAMES or path.name.upper() == "SKILL.MD":
        return True
    if path.suffix.lower() in INSTRUCTION_SUFFIXES:
        return True
    return False


def iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if is_instruction_file(path):
            files.append(path)
    return sorted(files)


def scan_text(text: str, path: Path, *, suggest_missing: bool) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines() or [""]
    seen: set[tuple[str, int]] = set()
    for i, line in enumerate(lines, 1):
        for rule in COMPILED:
            for regex in rule["regexes"]:
                if regex.search(line):
                    key = (rule["code"], i)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(
                        Finding(
                            severity=rule["severity"],
                            code=rule["code"],
                            title=rule["title"],
                            message=rule["message"],
                            suggest=rule["suggest"],
                            path=str(path),
                            line=i,
                            excerpt=line.strip()[:240],
                        )
                    )
                    break
    # Multi-line patterns: join with spaces for a second pass, but only add a
    # finding if that code has not already been recorded for this file.
    compact = re.sub(r"\s+", " ", text)
    already = {f.code for f in findings}
    for rule in COMPILED:
        if rule["code"] in already:
            continue
        for regex in rule["regexes"]:
            if regex.search(compact):
                findings.append(
                    Finding(
                        severity=rule["severity"],
                        code=rule["code"],
                        title=rule["title"],
                        message=rule["message"],
                        suggest=rule["suggest"],
                        path=str(path),
                        line=0,
                        excerpt=compact[:240],
                    )
                )
                break
    if suggest_missing and path.name in MISSING_FILE_HINTS:
        already = {f.code for f in findings}
        for hint in MISSING_HINTS:
            if hint["code"] in already:
                continue
            if not hint["needle"].search(text):
                findings.append(
                    Finding(
                        severity="info",
                        code=hint["code"],
                        title="Possible missing guidance",
                        message=hint["message"],
                        suggest=hint["suggest"],
                        path=str(path),
                        line=0,
                        excerpt="",
                    )
                )
    return findings


def scan_path(path: Path, *, suggest_missing: bool) -> list[Finding]:
    findings: list[Finding] = []
    for file in iter_files(path):
        text = file.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text(text, file, suggest_missing=suggest_missing))
    return findings


def format_finding(f: Finding) -> str:
    loc = f"{f.path}:{f.line}" if f.line else f.path
    parts = [f"{f.severity}: {f.code}: {f.title} ({loc})"]
    parts.append(f"  {f.message}")
    if f.excerpt:
        parts.append(f"  excerpt: {f.excerpt}")
    parts.append(f"  suggest: {f.suggest}")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fablescan",
        description=(
            "Audit prompts and SKILL.md / AGENTS.md files for patterns that "
            "fight Claude Fable 5.2 prompting guidance. Rules are paraphrased; "
            "this tool does not copy the official guide."
        ),
    )
    parser.add_argument("path", help="file or directory to scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--suggest-missing",
        action="store_true",
        default=True,
        help="add info findings when instruction files lack finish/ownership/report hints (default)",
    )
    parser.add_argument(
        "--no-suggest-missing",
        action="store_false",
        dest="suggest_missing",
        help="do not add info findings for missing finish/ownership/report language",
    )
    parser.add_argument("--version", action="version", version=f"fablescan {__version__}")
    args = parser.parse_args(argv)
    target = Path(args.path)
    if not target.exists():
        print(f"error: path not found: {target}", file=sys.stderr)
        return 1
    findings = scan_path(target, suggest_missing=args.suggest_missing)
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos = sum(1 for f in findings if f.severity == "info")
    if args.json:
        print(
            json.dumps(
                {
                    "findings": [asdict(f) for f in findings],
                    "errors": errors,
                    "warnings": warnings,
                    "infos": infos,
                    "guide": GUIDE_URL,
                },
                indent=2,
            )
        )
    else:
        if not findings:
            print(f"ok: no Fable 5.2 prompting issues found in {target}")
        else:
            for f in findings:
                print(format_finding(f))
                print()
            print(f"{errors} error(s), {warnings} warning(s), {infos} info")
        print(f"review: {GUIDE_URL}")
    if errors:
        return 2
    if warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
