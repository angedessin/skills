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
import socket
import subprocess
import sys
import time
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
    except PermissionError:
        return None
    except OSError as e:
        return f"作れない理由が権限でない: {path}（{type(e).__name__}）"
    path.unlink(missing_ok=True)
    return f"作れてしまう: {path}"


def blocked_rename(path: Path) -> str | None:
    """実際に動かそうとする。実在しないファイルや同じ名前への rename は sandbox の中でも権限エラーにならないので、確かめにならない。
    通ってしまったらすぐ戻す。unlink は戻せないので確かめない（Seatbelt では同じ書き込みの制限）。"""
    if not path.exists():
        return f"確かめる対象が無い: {path}"
    moved = path.with_name(path.name + ".sandbox-probe")
    try:
        os.rename(path, moved)
    except PermissionError:
        return None
    except OSError as e:
        return f"動かせない理由が権限でない: {path}（{type(e).__name__}）"
    os.rename(moved, path)
    return f"動かせてしまう: {path}"


def unreadable_by_cat(path: Path) -> str | None:
    """出力の中身ではなく終了コードで見る。空のファイルが残っていても、読めれば落ちる。"""
    p = run(["cat", str(path)])
    return f"cat で読めてしまう: {path.name}" if p.returncode == 0 else None


def unreadable_by_grep(directory: Path, denied: list[Path], plain: Path) -> str | None:
    """対照の plain だけが当たり、denied は全部エラーになること。"""
    p = run(["grep", "-rl", SENTINEL, str(directory)])
    found = p.stdout.splitlines()
    if found != [str(plain)]:
        return f"grep -r の結果が対照だけでない: {found}"
    silent = [f.name for f in denied if f.name not in p.stderr]
    return f"grep -r で読めてしまう（エラーにならない）: {silent}" if silent else None


def unreadable_by_python(path: Path) -> str | None:
    try:
        path.read_text()
    except PermissionError:
        return None
    except OSError as e:
        return f"読めない理由が権限でない: {path.name}（{type(e).__name__}）"
    return f"python で読めてしまう: {path.name}"


def readable_control(path: Path) -> str | None:
    """同じ方法で、denyRead の対象外のファイルは読める（読めない検査が別の理由で通らないための対照）。"""
    p = run(["cat", str(path)])
    if p.returncode != 0 or SENTINEL not in p.stdout:
        return f"cat で対照が読めない: {path.name}"
    return None if SENTINEL in path.read_text() else f"python で対照が読めない: {path.name}"


def git_writes_object(work: Path) -> str | None:
    """毎回違う中身にする（git write-tree は cache-tree が有効だと何も書かない）。"""
    source = work / "object-probe.txt"
    source.write_text(f"{time.time_ns()}\n")
    return succeeds(["git", "hash-object", "-w", str(source)])


def unreadable_secret_dir(path: Path) -> str | None:
    """~/.ssh・~/.aws は一覧が取れないことだけを見る。無ければ確かめられないので通す。"""
    if not os.path.lexists(path):
        return None
    try:
        os.listdir(path)
    except OSError:
        return None
    return f"一覧が取れてしまう: {path}"


def secret_label(home: Path, name: str) -> str:
    return f"読めない: ~/{name}" + ("" if os.path.lexists(home / name) else "（無いので確かめていない）")


def succeeds(cmd: list[str]) -> str | None:
    try:
        p = run(cmd)
    except subprocess.TimeoutExpired:
        return f"時間切れ: {' '.join(cmd)}"
    if p.returncode == 0:
        return None
    tail = (p.stderr or p.stdout).strip().splitlines()[-3:]
    return f"exit {p.returncode}: {' '.join(cmd)}\n  " + "\n  ".join(tail)


def can_listen_on_localhost() -> str | None:
    """E2E の開発サーバーが動く条件（allowLocalBinding）。"""
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
        except OSError as e:
            return f"ローカルのポートを listen できない: {e}"
    return None


def network(url: str, expect_ok: bool) -> str | None:
    """拒否は proxy の CONNECT の 403 で見分ける（名前解決の失敗やオフラインを拒否と数えない）。"""
    p = run(["curl", "-sS", "-o", "/dev/null", "--max-time", "10", "-w", "%{http_connect}", url], timeout=20)
    if expect_ok:
        return None if p.returncode == 0 else f"許可した通信先に届かない: {url}（{p.stderr.strip()}）"
    if p.returncode == 0:
        return f"許可していない通信先に届く: {url}"
    return None if p.stdout.strip() == "403" else f"proxy の拒否ではない失敗: {url}（{p.stderr.strip()}）"


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

    plain = work / "plain.txt"
    plain.write_text(f"{SENTINEL}=dummy\n")

    home = Path.home()
    checks = [
        ("読める（対照）: denyRead の対象外", lambda: readable_control(plain)),
        ("読めない: ルートの .env* を cat", lambda: unreadable_by_cat(root_env)),
        ("読めない: 深い階層の .env* を cat", lambda: unreadable_by_cat(nested_env)),
        ("読めない: *.env を cat", lambda: unreadable_by_cat(nested_named)),
        ("読めない: grep -r", lambda: unreadable_by_grep(work, [nested_env, nested_named], plain)),
        ("読めない: python", lambda: unreadable_by_python(nested_env)),
        (secret_label(home, ".ssh"), lambda: unreadable_secret_dir(home / ".ssh")),
        (secret_label(home, ".aws"), lambda: unreadable_secret_dir(home / ".aws")),
        ("書けない: .claude/settings.json", lambda: blocked_write(settings)),
        ("書けない: .claude/hooks", lambda: blocked_write(ROOT / ".claude/hooks/guard-gated-write.sh")),
        ("書けない: .claude/skills", lambda: blocked_write(ROOT / ".claude/skills/steering/SKILL.md")),
        ("書けない: .claude/agents", lambda: blocked_write(ROOT / ".claude/agents/review-bug.md")),
        ("作れない: .claude/hooks の新しいファイル", lambda: blocked_new_file(ROOT / ".claude/hooks/.sandbox-probe-new")),
        ("作れない: .claude/skills の新しいファイル", lambda: blocked_new_file(ROOT / ".claude/skills/.sandbox-probe-new")),
        ("作れない: .claude/agents の新しいファイル", lambda: blocked_new_file(ROOT / ".claude/agents/.sandbox-probe-new")),
        ("動かせない: .claude/hooks", lambda: blocked_rename(ROOT / ".claude/hooks/guard-gated-write.sh")),
        ("動かせない: .claude/skills", lambda: blocked_rename(ROOT / ".claude/skills/steering/SKILL.md")),
        ("動かせない: .claude/agents", lambda: blocked_rename(ROOT / ".claude/agents/review-bug.md")),
        ("書けない: 作業ディレクトリの外", lambda: blocked_new_file(home / ".sandbox-probe-write")),
        ("通信: 許可した registry.npmjs.org", lambda: network("https://registry.npmjs.org/", True)),
        ("通信: 許可していない www.iana.org", lambda: network("https://www.iana.org/", False)),
        ("動く: ローカルのポートの listen", can_listen_on_localhost),
        ("動く: mise 経由の pnpm", lambda: succeeds([*MISE, "pnpm", "-v"])),
        ("動く: validate", lambda: succeeds([*MISE, "pnpm", "run", "-s", "validate"])),
        ("動く: test:hooks", lambda: succeeds([*MISE, "pnpm", "run", "-s", "test:hooks"])),
        ("動く: lint", lambda: succeeds([*MISE, "pnpm", "run", "-s", "lint"])),
        ("動く: test:sandbox", lambda: succeeds([*MISE, "pnpm", "run", "-s", "test:sandbox"])),
        ("動く: git status", lambda: succeeds(["git", "status", "--short"])),
        ("動く: git の object の書き込み", lambda: git_writes_object(work)),
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
