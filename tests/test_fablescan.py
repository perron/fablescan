from __future__ import annotations

import json
from pathlib import Path

import pytest

import fablescan.cli as fs


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_help_and_version():
    with pytest.raises(SystemExit) as exc:
        fs.main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        fs.main(["--version"])
    assert exc.value.code == 0


def test_clean_skill(tmp_path, capsys):
    skill = write(
        tmp_path / "tidy-notes" / "SKILL.md",
        "---\nname: tidy-notes\ndescription: Tidy a notes folder when the user asks to clean notes.\n---\n\n"
        "Sort the notes by date and write a short summary.\n",
    )
    assert fs.main([str(skill.parent), "--no-suggest-missing"]) == 0
    out = capsys.readouterr().out
    assert "ok:" in out
    assert fs.GUIDE_URL in out


def test_always_delegate(tmp_path, capsys):
    path = write(tmp_path / "AGENTS.md", "Always delegate every task to a subagent.\n")
    assert fs.main([str(path), "--no-suggest-missing"]) == 1
    out = capsys.readouterr().out
    assert "always-delegate" in out
    assert "excerpt:" in out
    assert "Always delegate" in out


def test_no_deliberation(tmp_path, capsys):
    path = write(tmp_path / "prompt.md", "Answer without deliberating. Be brief.\n")
    assert fs.main([str(path)]) == 1
    assert "no-deliberation" in capsys.readouterr().out


def test_token_budget(tmp_path, capsys):
    path = write(tmp_path / "prompt.md", "Token budget: you have 8000 tokens remaining.\n")
    assert fs.main([str(path)]) == 1
    assert "token-budget-in-prompt" in capsys.readouterr().out


def test_absolute_caution(tmp_path, capsys):
    path = write(tmp_path / "rules.md", "- Never retry\n- Always ask for approval before any tool call.\n")
    assert fs.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "absolute-caution" in out


def test_treat_answer_done(tmp_path, capsys):
    path = write(tmp_path / "chat.md", "Treat the earlier answer as done and focus your thinking on the new message.\n")
    assert fs.main([str(path)]) == 1
    assert "treat-answer-done" in capsys.readouterr().out


def test_rigid_style(tmp_path, capsys):
    path = write(tmp_path / "style.md", "One instruction per sentence, in 20 words or fewer.\n")
    assert fs.main([str(path)]) == 1
    assert "rigid-style" in capsys.readouterr().out


def test_dump_reasoning_is_error(tmp_path, capsys):
    path = write(tmp_path / "prompt.md", "Write your hidden reasoning in the response so I can audit it.\n")
    assert fs.main([str(path)]) == 2
    out = capsys.readouterr().out
    assert "dump-reasoning" in out
    assert "error:" in out


def test_micromanage_steps(tmp_path, capsys):
    path = write(tmp_path / "SKILL.md", "You must follow these steps exactly. Do not deviate from these steps.\n")
    assert fs.main([str(path)]) == 1
    assert "micromanage-steps" in capsys.readouterr().out


def test_short_workflow_is_not_micromanagement(tmp_path, capsys):
    path = write(
        tmp_path / "SKILL.md",
        "Use this three-step workflow: search, then open a template, then read the component docs.\n",
    )
    assert fs.main([str(path), "--no-suggest-missing"]) == 0
    assert "micromanage-steps" not in capsys.readouterr().out


def test_json_and_missing_hints(tmp_path, capsys):
    path = write(tmp_path / "AGENTS.md", "You are a coding agent for this repository.\n")
    assert fs.main([str(path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    codes = {f["code"] for f in data["findings"]}
    assert "missing-finish-task" in codes
    assert "missing-ownership" in codes
    assert data["guide"] == fs.GUIDE_URL
    assert data["infos"] >= 1


def test_missing_path(tmp_path, capsys):
    assert fs.main([str(tmp_path / "nope.md")]) == 1
    assert "path not found" in capsys.readouterr().err


def test_skips_node_modules(tmp_path, capsys):
    write(tmp_path / "node_modules" / "pkg" / "AGENTS.md", "Always delegate all work to a subagent.\n")
    write(tmp_path / "AGENTS.md", "Build the feature and report what you changed.\n")
    # AGENTS.md may get missing-* info only
    code = fs.main([str(tmp_path), "--no-suggest-missing"])
    out = capsys.readouterr().out
    assert code == 0
    assert "always-delegate" not in out


def test_dont_think_unrelated_is_clean(tmp_path, capsys):
    path = write(tmp_path / "note.md", "I don't think that's the right folder.\nNever mind the earlier draft.\n")
    assert fs.main([str(path)]) == 0
    assert "no-deliberation" not in capsys.readouterr().out


def test_unicode(tmp_path, capsys):
    path = write(tmp_path / "prompt.md", "Token budget: 残り 4000 tokens left.\n漢字\n")
    assert fs.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "token-budget-in-prompt" in out


def test_suggestions_are_short_and_original():
    # Guard against pasting long official prompt blocks into redistributed text.
    for rule in fs.RULES:
        assert len(rule["suggest"]) < 400
        assert "Please avoid stopping while you still owe work" not in rule["suggest"]
        assert "This codebase is yours: what it's for and how it's built" not in rule["suggest"]
        assert "Write for an intelligent but low-context reader" not in rule["suggest"]
        assert "ASD-STE100" not in rule["suggest"]
        assert "anthropic" not in rule["suggest"].lower()
