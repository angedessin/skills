#!/usr/bin/env python3
"""Hook fixture runner — stdin JSON → hook → assert permissionDecision.

Usage: mise exec -- pnpm run test:hooks
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"

# expect: "deny" | "ask" | "silence"
CASES: list[dict] = [
    # A — delete hook deny
    {"id": "A1", "hook": "guard-gated-delete.sh", "command": "rm -f docs/knowledge/x.md", "expect": "deny"},
    {"id": "A2", "hook": "guard-gated-delete.sh", "command": "rm ./CLAUDE.md", "expect": "deny"},
    {"id": "A3", "hook": "guard-gated-delete.sh", "command": "rm docs/decisions/y.md", "expect": "deny"},
    {"id": "A4", "hook": "guard-gated-delete.sh", "command": "rm -R docs/knowledge/x", "expect": "deny"},
    {"id": "A5", "hook": "guard-gated-delete.sh", "command": "rm --recursive docs/knowledge/x", "expect": "deny"},
    {"id": "A6", "hook": "guard-gated-delete.sh", "command": "rm -f -r docs/knowledge/x", "expect": "deny"},
    {"id": "A7", "hook": "guard-gated-delete.sh", "command": "mv docs/knowledge/x.md /tmp/", "expect": "deny"},
    {"id": "A8", "hook": "guard-gated-delete.sh", "command": "mv a.md docs/knowledge/a.md", "expect": "deny"},
    # B — delete hook silence
    {"id": "B9", "hook": "guard-gated-delete.sh", "command": "rm /tmp/foo", "expect": "silence"},
    {"id": "B10", "hook": "guard-gated-delete.sh", "command": "rm README.md", "expect": "silence"},
    {"id": "B11", "hook": "guard-gated-delete.sh", "command": "cd docs/knowledge && rm x.md", "expect": "silence"},
    {"id": "B12", "hook": "guard-gated-delete.sh", "command": "bash -c 'rm docs/knowledge/x.md'", "expect": "silence"},
    {"id": "B13", "hook": "guard-gated-delete.sh", "command": "git rm docs/knowledge/x.md", "expect": "silence"},
    {"id": "B14", "hook": "guard-gated-delete.sh", "command": "/bin/rm docs/knowledge/x.md", "expect": "silence"},
    {
        "id": "B15",
        "hook": "guard-gated-delete.sh",
        "note": "empty payload",
        "payload": "",
        "expect": "silence",
    },
    {
        "id": "B16",
        "hook": "guard-gated-delete.sh",
        "note": "transcript_path contains docs/knowledge; command=ls",
        "payload": {
            "session_id": "fixture",
            "transcript_path": "/tmp/project/docs/knowledge/transcript.jsonl",
            "cwd": str(ROOT),
            "permission_mode": "default",
            "tool_input": {"command": "ls"},
        },
        "expect": "silence",
    },
    {
        "id": "B17",
        "hook": "guard-gated-delete.sh",
        "note": "missing tool_input.command",
        "payload": {
            "session_id": "fixture",
            "transcript_path": "/tmp/t.jsonl",
            "cwd": str(ROOT),
            "tool_input": {},
        },
        "expect": "silence",
    },
    {"id": "B18", "hook": "guard-gated-delete.sh", "command": "echo docs/knowledge/x.md", "expect": "silence"},
    # D — write hook regression (same runner)
    {"id": "D21", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.md", "expect": "ask"},
    {"id": "D22", "hook": "guard-gated-write.sh", "command": "git log", "expect": "silence"},
]


def base_payload(command: str | None) -> dict:
    p: dict = {
        "session_id": "fixture",
        "transcript_path": "/tmp/claude/transcripts/fixture.jsonl",
        "cwd": str(ROOT),
        "permission_mode": "default",
        "tool_input": {},
    }
    if command is not None:
        p["tool_input"]["command"] = command
    return p


def decision_from_stdout(stdout: str) -> str | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        compact = text.replace(" ", "")
        if '"permissionDecision":"deny"' in compact:
            return "deny"
        if '"permissionDecision":"ask"' in compact:
            return "ask"
        return f"unparseable:{text[:80]!r}"
    hook_out = data.get("hookSpecificOutput") or {}
    return hook_out.get("permissionDecision")


def run_case(case: dict) -> tuple[bool, str]:
    hook_path = HOOKS / case["hook"]
    if not hook_path.is_file():
        return False, f"hook missing: {hook_path}"

    if "payload" in case:
        payload = case["payload"]
        raw = payload if isinstance(payload, str) else json.dumps(payload)
    else:
        raw = json.dumps(base_payload(case.get("command")))

    proc = subprocess.run(
        ["bash", str(hook_path)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    if proc.returncode != 0:
        return False, f"exit {proc.returncode}; stderr={proc.stderr!r}"

    got = decision_from_stdout(proc.stdout)
    expect = case["expect"]
    if expect == "silence":
        ok = got is None
        detail = f"expected silence, got {got!r}; stdout={proc.stdout!r}"
    else:
        ok = got == expect
        detail = f"expected {expect!r}, got {got!r}; stdout={proc.stdout!r}"
    return ok, detail


def main() -> int:
    failed = 0
    for case in CASES:
        ok, detail = run_case(case)
        status = "PASS" if ok else "FAIL"
        label = case.get("command") or case.get("note", "")
        print(f"{status} {case['id']}: {label}")
        if not ok:
            print(f"  {detail}")
            failed += 1
    total = len(CASES)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
