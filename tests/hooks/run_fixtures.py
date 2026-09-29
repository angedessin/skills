#!/usr/bin/env python3
"""Hook fixture runner — stdin JSON → hook → assert permissionDecision.

Usage: mise exec -- pnpm run test:hooks
       python3 tests/hooks/run_fixtures.py --hooks-dir <dir>   # 持ち出し先の hook 実体に同じケースを流す
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"

# guard-gated-write.sh のヘッダにある対象パスの正本（1 行）。runner はここからケースを自動生成し、
# check_asset_consistency.py の契約 (s) は permissions.ask と突合する。
GATED_MARKER_RE = re.compile(r"^# GATED_PATHS:[ \t]*(.+)$", re.MULTILINE)

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
    # H1/H2/M1/M2 回帰
    {"id": "A9", "hook": "guard-gated-delete.sh", "command": 'rm "docs/knowledge/x.md"', "expect": "deny"},
    {"id": "A10", "hook": "guard-gated-delete.sh", "command": "rm -rf docs/knowledge", "expect": "deny"},
    {"id": "A11", "hook": "guard-gated-delete.sh", "command": "mv docs/knowledge /tmp/", "expect": "deny"},
    {"id": "B19", "hook": "guard-gated-delete.sh", "command": "rm /tmp/a && ls docs/knowledge/", "expect": "silence"},
    {"id": "B20", "hook": "guard-gated-delete.sh", "command": "rm CLAUDE.md.bak", "expect": "silence"},
    # M1 — newline / line-continuation / leading newline
    {"id": "A12", "hook": "guard-gated-delete.sh", "command": "rm -f docs/knowledge/x.md\nls", "expect": "deny"},
    {"id": "A13", "hook": "guard-gated-delete.sh", "command": "rm -f \\\n  docs/knowledge/x.md", "expect": "deny"},
    {"id": "A14", "hook": "guard-gated-delete.sh", "command": "\nrm -f docs/knowledge/x.md", "expect": "deny"},
    {"id": "A15", "hook": "guard-gated-delete.sh", "command": "ls\nrm -f docs/knowledge/x.md", "expect": "deny"},
    {"id": "A16", "hook": "guard-gated-delete.sh", "command": "rm CLAUDE.md\nrm docs/knowledge/x.md", "expect": "deny"},
    {"id": "B21", "hook": "guard-gated-delete.sh", "command": "ls\necho hi", "expect": "silence"},
    # M2 — glob / brace adjacent
    {"id": "A17", "hook": "guard-gated-delete.sh", "command": "rm -f CLAUDE.md*", "expect": "deny"},
    {"id": "A18", "hook": "guard-gated-delete.sh", "command": "rm -rf docs/knowledge*", "expect": "deny"},
    {"id": "A19", "hook": "guard-gated-delete.sh", "command": "mv docs/knowledge{,.bak}", "expect": "deny"},
    {"id": "B22", "hook": "guard-gated-delete.sh", "command": "rm -f docs/knowledge-archive-old*", "expect": "silence"},
    {
        "id": "BP1",
        "hook": "guard-gated-delete.sh",
        "note": "python3 が無ければ抽出できず沈黙（フェイルオープン契約。A1 と対）",
        "command": "rm -f docs/knowledge/x.md",
        "expect": "silence",
        "no_python": True,
    },
    # D — write hook regression (same runner)
    {"id": "D21", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.md", "expect": "ask"},
    {"id": "D22", "hook": "guard-gated-write.sh", "command": "git log", "expect": "silence"},
    # W — write hook（構造抽出・連鎖の全部分・git mv）。対象パスごとの基本形は gated_cases() が自動生成する
    {"id": "W1", "hook": "guard-gated-write.sh", "command": "ls && echo x > CLAUDE.md", "expect": "ask"},
    {"id": "W2", "hook": "guard-gated-write.sh", "command": "git show HEAD:a >> docs/knowledge/x.md", "expect": "ask"},
    {"id": "W3", "hook": "guard-gated-write.sh", "command": "git log -1 | tee -a .claude/hooks/x", "expect": "ask"},
    {"id": "W4", "hook": "guard-gated-write.sh", "command": "git mv -f x .claude/hooks/y", "expect": "ask"},
    {"id": "W5", "hook": "guard-gated-write.sh", "command": "echo x >CLAUDE.md", "expect": "ask"},
    {"id": "W6", "hook": "guard-gated-write.sh", "command": "echo x > ./CLAUDE.md", "expect": "ask"},
    {"id": "W7", "hook": "guard-gated-write.sh", "command": "echo x 2> CLAUDE.md", "expect": "ask"},
    {"id": "W8", "hook": "guard-gated-write.sh", "command": "echo x &> .claude/settings.json", "expect": "ask"},
    {"id": "W9", "hook": "guard-gated-write.sh", "command": "{ echo a; echo b; } > docs/decisions/x.md", "expect": "ask"},
    {"id": "W10", "hook": "guard-gated-write.sh", "command": "echo x | tee /tmp/a CLAUDE.md", "expect": "ask"},
    {"id": "W11", "hook": "guard-gated-write.sh", "command": "git -C . mv x CLAUDE.md", "expect": "ask"},
    {"id": "W12", "hook": "guard-gated-write.sh", "command": "git mv docs/knowledge/a.md /tmp/a.md", "expect": "ask"},
    {"id": "W13", "hook": "guard-gated-write.sh", "command": "cat <<'EOF' > CLAUDE.md\nx\nEOF", "expect": "ask"},
    {"id": "W14", "hook": "guard-gated-write.sh", "command": "ls\necho x > .claude/settings.local.json", "expect": "ask"},
    {
        "id": "W15",
        "hook": "guard-gated-write.sh",
        "note": "two gated writes in one command -> exactly one JSON",
        "command": "echo a > CLAUDE.md; echo b | tee docs/knowledge/x.md; git mv x .claude/hooks/y",
        "expect": "ask",
    },
    # W26-W27 — 空白なしの `;` 連鎖で、後続に別の対象パスが無い形（W15 は tee 側でも ask になり単独で固定できない）
    {"id": "W26", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.md;ls", "expect": "ask"},
    {"id": "W27", "hook": "guard-gated-write.sh", "command": "git mv x CLAUDE.md; ls", "expect": "ask"},
    # W28-W40 — 20260929 レビュー（正当性）: git -C の合成・env / exec / sudo 前置・大文字小文字
    {"id": "W28", "hook": "guard-gated-write.sh", "command": "git -C .claude/hooks mv old.sh new.sh", "expect": "ask"},
    {"id": "W29", "hook": "guard-gated-write.sh", "command": "git -C docs/knowledge mv x.md y.md", "expect": "ask"},
    {"id": "W30", "hook": "guard-gated-write.sh", "command": "git -C docs mv a.md knowledge/b.md", "expect": "ask"},
    {"id": "W31", "hook": "guard-gated-write.sh", "command": "env FOO=bar tee CLAUDE.md", "expect": "ask"},
    {"id": "W32", "hook": "guard-gated-write.sh", "command": "echo x | env -u HOME A=1 tee CLAUDE.md", "expect": "ask"},
    {"id": "W33", "hook": "guard-gated-write.sh", "command": "exec git mv a docs/knowledge/x.md", "expect": "ask"},
    {"id": "W34", "hook": "guard-gated-write.sh", "command": "echo x | sudo tee .claude/settings.json", "expect": "ask"},
    {"id": "W35", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.MD", "expect": "ask"},
    {"id": "W36", "hook": "guard-gated-write.sh", "command": "echo x >> DOCS/Knowledge/y.md", "expect": "ask"},
    {"id": "W37", "hook": "guard-gated-write.sh", "command": "git -C /tmp/repo mv a b", "expect": "silence"},
    {"id": "W38", "hook": "guard-gated-write.sh", "command": "git -C .claude/hooks status", "expect": "silence"},
    {"id": "W39", "hook": "guard-gated-write.sh", "command": "env FOO=bar ls > /tmp/x", "expect": "silence"},
    {"id": "W40", "hook": "guard-gated-write.sh", "command": "echo x > claude.md.bak", "expect": "silence"},
    {"id": "W16", "hook": "guard-gated-write.sh", "command": "cat .claude/settings.json > /tmp/x", "expect": "silence"},
    {"id": "W17", "hook": "guard-gated-write.sh", "command": "git mv a b", "expect": "silence"},
    {"id": "W18", "hook": "guard-gated-write.sh", "command": 'echo "> CLAUDE.md"', "expect": "silence"},
    {"id": "W19", "hook": "guard-gated-write.sh", "command": 'git commit -m "echo x > CLAUDE.md"', "expect": "silence"},
    {"id": "W20", "hook": "guard-gated-write.sh", "command": "sed -n 1p CLAUDE.md > /tmp/x", "expect": "silence"},
    {"id": "W21", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.md.bak", "expect": "silence"},
    {"id": "W22", "hook": "guard-gated-write.sh", "command": "git diff 2>&1 | head", "expect": "silence"},
    {"id": "W23", "hook": "guard-gated-write.sh", "command": "ls # > CLAUDE.md", "expect": "silence"},
    {
        "id": "W24",
        "hook": "guard-gated-write.sh",
        "note": "transcript_path / cwd contain .claude/ but command does not write there",
        "payload": {
            "session_id": "fixture",
            "transcript_path": "/Users/u/.claude/projects/p/.claude/hooks/t.jsonl",
            "cwd": "/Users/u/.claude/hooks",
            "permission_mode": "default",
            "tool_input": {"command": "echo x > /tmp/out.txt", "description": "write to .claude/settings.json"},
        },
        "expect": "silence",
    },
    {"id": "W25", "hook": "guard-gated-write.sh", "note": "empty payload", "payload": "", "expect": "silence"},
    # WP — python3 が無い環境では全文 grep（元の 3 系統）に縮退する。完全な沈黙にはしない
    {"id": "WP1", "hook": "guard-gated-write.sh", "command": "echo x > CLAUDE.md", "expect": "ask", "no_python": True},
    {"id": "WP2", "hook": "guard-gated-write.sh", "command": "git log", "expect": "silence", "no_python": True},
    {"id": "WP3", "hook": "guard-gated-write.sh", "command": "ls | tee docs/knowledge/x.md", "expect": "ask", "no_python": True},
    {
        "id": "WP4",
        "hook": "guard-gated-write.sh",
        "note": "縮退経路を通った証拠: .claude/ は全文 grep では見ない（構造判定なら ask。G*r と対）",
        "command": "echo x > .claude/hooks/x",
        "expect": "silence",
        "no_python": True,
    },
    {"id": "WP6", "hook": "guard-gated-write.sh", "command": "echo x > Docs/Knowledge/x.md", "expect": "ask", "no_python": True},
    {
        "id": "WP5",
        "hook": "guard-gated-write.sh",
        "note": "縮退経路は git mv を見ない（構造判定にのみある機能。G*m と対）",
        "command": "git mv x CLAUDE.md",
        "expect": "silence",
        "no_python": True,
    },
]


def gated_paths(hooks_dir: Path) -> list[str] | None:
    """guard-gated-write.sh のマーカー行から対象パスを読む。無ければ None。"""
    hook = hooks_dir / "guard-gated-write.sh"
    if not hook.is_file():
        return None
    m = GATED_MARKER_RE.search(hook.read_text(encoding="utf-8"))
    return m.group(1).split() if m else None


def gated_cases(paths: list[str]) -> list[dict]:
    """対象パスごとにリダイレクト / tee / git mv の ask ケースを生成する（マーカーとロジックの乖離を検出）。"""
    cases: list[dict] = []
    for i, path in enumerate(paths, 1):
        target = f"{path}x.md" if path.endswith("/") else path
        cases += [
            {"id": f"G{i}r", "hook": "guard-gated-write.sh", "command": f"git show HEAD:a > {target}", "expect": "ask"},
            {"id": f"G{i}t", "hook": "guard-gated-write.sh", "command": f"git log -1 | tee {target}", "expect": "ask"},
            {"id": f"G{i}m", "hook": "guard-gated-write.sh", "command": f"git mv tmp.txt {target}", "expect": "ask"},
        ]
    return cases


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
        return f"unparseable:{text[:80]!r}"
    hook_out = data.get("hookSpecificOutput") or {}
    return hook_out.get("permissionDecision")


def _self_test_decision_from_stdout() -> None:
    """M3: broken JSON must not be treated as deny/ask via substring match."""
    broken = [
        '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"said "hi""}}',
        'noise\n{"hookSpecificOutput":{"permissionDecision":"deny"}}',
        '{"hookSpecificOutput":{"permissionDecision":"deny"',
    ]
    for s in broken:
        got = decision_from_stdout(s)
        if not (isinstance(got, str) and got.startswith("unparseable:")):
            raise AssertionError(f"expected unparseable sentinel, got {got!r} for {s!r}")
    ok = decision_from_stdout('{"hookSpecificOutput":{"permissionDecision":"deny"}}')
    if ok != "deny":
        raise AssertionError(f"valid deny JSON regressed: {ok!r}")


def path_without_python(tmp: Path) -> str:
    """python3 を含まない PATH を作る（hook が使う外部コマンドだけを置く）。"""
    bindir = tmp / "bin"
    bindir.mkdir(exist_ok=True)
    for tool in ("cat", "grep", "sed", "awk"):
        found = shutil.which(tool)
        if found and not (bindir / tool).exists():
            (bindir / tool).symlink_to(found)
    return str(bindir)


def run_case(case: dict, hooks_dir: Path, tmp: Path) -> tuple[bool, str]:
    hook_path = hooks_dir / case["hook"]
    if not hook_path.is_file():
        return False, f"hook missing: {hook_path}"

    if "payload" in case:
        payload = case["payload"]
        raw = payload if isinstance(payload, str) else json.dumps(payload)
    else:
        raw = json.dumps(base_payload(case.get("command")))

    env = None
    if case.get("no_python"):
        env = dict(os.environ, PATH=path_without_python(tmp))
    proc = subprocess.run(
        [shutil.which("bash") or "/bin/bash", str(hook_path)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--hooks-dir", type=Path, default=HOOKS, help="検査する hook 実体のディレクトリ")
    args = parser.parse_args()
    hooks_dir: Path = args.hooks_dir.resolve()

    try:
        _self_test_decision_from_stdout()
        print("PASS self: decision_from_stdout unparseable")
    except AssertionError as e:
        print(f"FAIL self: decision_from_stdout unparseable\n  {e}")
        return 1

    failed = 0
    paths = gated_paths(hooks_dir)
    if paths is None:
        print(f"FAIL marker: {hooks_dir / 'guard-gated-write.sh'} に '# GATED_PATHS:' 行が無い")
        failed += 1
        paths = []
    cases = CASES + gated_cases(paths)
    tmp = Path(tempfile.mkdtemp(prefix="hook-fixtures-"))
    try:
        for case in cases:
            ok, detail = run_case(case, hooks_dir, tmp)
            status = "PASS" if ok else "FAIL"
            label = case.get("command") or case.get("note", "")
            print(f"{status} {case['id']}: {label!r}" if "\n" in label else f"{status} {case['id']}: {label}")
            if not ok:
                print(f"  {detail}")
                failed += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases) + (1 if not gated_paths(hooks_dir) else 0)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
