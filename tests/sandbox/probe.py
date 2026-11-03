#!/usr/bin/env python3
"""sandbox の中で実際にコマンドを流して確かめる（課金なし）。

Usage: sandbox を有効にした Claude Code の Bash ツールから流す:
       mise exec -- pnpm run test:sandbox:probe

通常のターミナルや sandbox の外では、最初の確認で止まる（exit 2）。
sandbox の外に出すコマンド（excludedCommands）は Claude Code が呼び出しの文字列で判定するので、
このスクリプトの子プロセスとしては確かめられない。tests/sandbox/README.md の手順で確かめる。

秘密を出力しない: 読めるかどうかだけを見て、中身は表示しない。
Exit 0 = all pass. Exit 1 = failure. Exit 2 = sandbox の外で動いている。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "SANDBOX_PROBE_" + "SENTINEL"  # このファイル自体が grep に当たらないよう分けて書く
MISE = ["mise", "exec", "--"]
TIMEOUT = 180


def run(cmd: list[str], timeout: int = TIMEOUT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def can_open_for_append(path: Path) -> bool:
    """書かずに開くだけ。ファイルの中身は変わらない。"""
    try:
        with path.open("a"):
            return True
    except OSError:
        return False


def blocked_write(path: Path) -> str | None:
    if not path.exists():
        return f"確かめる対象が無い: {path}"
    return f"書き込めてしまう: {path}" if can_open_for_append(path) else None


def blocked_new_file(path: Path) -> str | None:
    try:
        with path.open("x"):
            pass
    except FileExistsError:
        return f"確かめる対象が既にある: {path}"
    except OSError:
        return None
    path.unlink(missing_ok=True)
    return f"作れてしまう: {path}"


def unreadable_by_cat(path: Path) -> str | None:
    p = run(["cat", str(path)])
    return f"cat で読めてしまう: {path.name}" if SENTINEL in p.stdout else None


def unreadable_by_grep(directory: Path) -> str | None:
    p = run(["grep", "-rl", SENTINEL, str(directory)])
    return f"grep -r で読めてしまう: {p.stdout.strip()}" if p.stdout.strip() else None


def unreadable_by_python(path: Path) -> str | None:
    try:
        return f"python で読めてしまう: {path.name}" if SENTINEL in path.read_text() else None
    except OSError:
        return None


def unreadable_secret_dir(path: Path) -> str | None:
    """~/.ssh・~/.aws は一覧が取れないことだけを見る。無ければ確かめられないので通す。"""
    if not os.path.lexists(path):
        return None
    try:
        os.listdir(path)
    except OSError:
        return None
    return f"一覧が取れてしまう: {path}"


def succeeds(cmd: list[str]) -> str | None:
    try:
        p = run(cmd)
    except subprocess.TimeoutExpired:
        return f"時間切れ: {' '.join(cmd)}"
    if p.returncode == 0:
        return None
    tail = (p.stderr or p.stdout).strip().splitlines()[-3:]
    return f"exit {p.returncode}: {' '.join(cmd)}\n  " + "\n  ".join(tail)


def network(url: str, expect_ok: bool) -> str | None:
    p = run(["curl", "-sS", "-o", "/dev/null", "--max-time", "10", url], timeout=20)
    if expect_ok and p.returncode != 0:
        return f"許可した通信先に届かない: {url}（{p.stderr.strip()}）"
    if not expect_ok and p.returncode == 0:
        return f"許可していない通信先に届く: {url}"
    return None


def main() -> int:
    settings = ROOT / ".claude" / "settings.json"
    if can_open_for_append(settings):
        print("sandbox の外で動いています（.claude/settings.json に書き込める）。")
        print("sandbox を有効にした Claude Code の Bash ツールから流してください。")
        return 2

    # denyRead のファイルは sandbox の中で作れるが消せない（Seatbelt の unlink も止まる）。
    # 消さずに決まった場所で使い回す。どちらも .gitignore 済みで、中身はダミー。
    work = ROOT / ".tmp" / "sandbox-probe"
    work.mkdir(parents=True, exist_ok=True)
    root_env = ROOT / ".env.sandbox-probe"
    nested_env = work / ".env.probe"
    nested_named = work / "prod.env"
    for f in (root_env, nested_env, nested_named):
        if not os.path.lexists(f):
            f.write_text(f"{SENTINEL}=dummy\n")

    home = Path.home()
    checks = [
        ("読めない: ルートの .env* を cat", lambda: unreadable_by_cat(root_env)),
        ("読めない: 深い階層の .env* を cat", lambda: unreadable_by_cat(nested_env)),
        ("読めない: *.env を cat", lambda: unreadable_by_cat(nested_named)),
        ("読めない: grep -r", lambda: unreadable_by_grep(work)),
        ("読めない: python", lambda: unreadable_by_python(nested_env)),
        ("読めない: ~/.ssh", lambda: unreadable_secret_dir(home / ".ssh")),
        ("読めない: ~/.aws", lambda: unreadable_secret_dir(home / ".aws")),
        ("書けない: .claude/settings.json", lambda: blocked_write(settings)),
        ("書けない: .claude/hooks", lambda: blocked_write(ROOT / ".claude/hooks/guard-gated-write.sh")),
        ("書けない: .claude/skills", lambda: blocked_write(ROOT / ".claude/skills/steering/SKILL.md")),
        ("書けない: .claude/agents", lambda: blocked_write(ROOT / ".claude/agents/review-bug.md")),
        ("書けない: 作業ディレクトリの外", lambda: blocked_new_file(home / ".sandbox-probe-write")),
        ("通信: 許可した registry.npmjs.org", lambda: network("https://registry.npmjs.org/", True)),
        ("通信: 許可していない www.iana.org", lambda: network("https://www.iana.org/", False)),
        ("動く: mise 経由の pnpm", lambda: succeeds([*MISE, "pnpm", "-v"])),
        ("動く: validate", lambda: succeeds([*MISE, "pnpm", "run", "-s", "validate"])),
        ("動く: test:hooks", lambda: succeeds([*MISE, "pnpm", "run", "-s", "test:hooks"])),
        ("動く: lint", lambda: succeeds([*MISE, "pnpm", "run", "-s", "lint"])),
        ("動く: test:sandbox", lambda: succeeds([*MISE, "pnpm", "run", "-s", "test:sandbox"])),
        ("動く: git status", lambda: succeeds(["git", "status", "--short"])),
        ("動く: git の object の書き込み", lambda: succeeds(["git", "write-tree"])),
    ]

    failed = 0
    for label, check in checks:
        try:
            problem = check()
        except subprocess.TimeoutExpired:
            problem = "時間切れ"
        print(f"{'FAIL' if problem else 'PASS'} {label}")
        if problem:
            print(f"  {problem}")
            failed += 1

    print(f"\n{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
