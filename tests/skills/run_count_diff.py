#!/usr/bin/env python3
"""frontend-code-review の count-diff.sh のテスト。一時的な git リポジトリで数え方を確かめる。

Usage: mise exec -- pnpm run test:skills
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 壊した写しで落ちるかを確かめるときに差し替える
SCRIPT = Path(os.environ.get("COUNT_DIFF_SCRIPT") or ROOT / ".claude" / "skills" / "frontend-code-review" / "scripts" / "count-diff.sh")

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, env=GIT_ENV, check=True, capture_output=True, text=True).stdout


def write(repo: Path, rel: str, content: str | bytes) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        p.write_bytes(content)
    else:
        p.write_text(content)


def lines(n: int, prefix: str = "l") -> str:
    return "".join(f"{prefix}{i}\n" for i in range(n))


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, "src/a.ts", lines(10))
    write(repo, "src/b.ts", lines(5))
    write(repo, "docs/c.md", lines(3))
    write(repo, ".gitignore", "ignored/\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def run(repo: Path, *args: str) -> tuple[int, str, str]:
    if not SCRIPT.exists():
        return 127, "", f"script not found: {SCRIPT}"
    p = subprocess.run(["bash", str(SCRIPT), *args], cwd=repo, env=GIT_ENV, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def parse(out: str) -> dict:
    res: dict = {"untracked": [], "dirstat": []}
    section = None
    for ln in out.splitlines():
        if ln.startswith("files: "):
            res["files"] = int(ln.split(": ", 1)[1])
            section = None
        elif ln.startswith("lines: "):
            # lines: 12 (+10 -2)
            total, rest = ln.split(": ", 1)[1].split(" ", 1)
            add, dele = rest.strip("()").split(" ")
            res["lines"], res["added"], res["deleted"] = int(total), int(add[1:]), int(dele[1:])
            section = None
        elif ln == "untracked:":
            section = "untracked"
        elif ln == "dirstat:":
            section = "dirstat"
        elif section and ln.startswith("  "):
            res[section].append(ln[2:] if section == "untracked" else ln.strip())
    return res


# 各ケースは (id, 説明, 準備, 引数, 期待)。期待の rc 以外のキーは parse の結果と比べる。
def setup_none(repo: Path) -> None:
    pass


def setup_modify(repo: Path) -> None:
    write(repo, "src/a.ts", lines(8) + "new1\nnew2\nnew3\n")  # -2 +3


def setup_untracked_text(repo: Path) -> None:
    setup_modify(repo)
    write(repo, "src/new.ts", lines(4))


def setup_untracked_binary(repo: Path) -> None:
    write(repo, "img/logo.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00binary")


def setup_ignored(repo: Path) -> None:
    write(repo, "ignored/big.ts", lines(100))


def setup_delete(repo: Path) -> None:
    (repo / "src/b.ts").unlink()


def setup_space_name(repo: Path) -> None:
    write(repo, "src/with space.ts", lines(2))


def setup_lead_space(repo: Path) -> None:
    write(repo, " lead.ts", lines(2))


def setup_tracked_binary(repo: Path) -> None:
    write(repo, "img/a.png", b"\x89PNG\x00one")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "bin")
    write(repo, "img/a.png", b"\x89PNG\x00two")
    setup_modify(repo)


def setup_untracked_empty(repo: Path) -> None:
    write(repo, "src/empty.ts", "")


def setup_branch(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, "src/a.ts", lines(10) + "added\n")  # +1
    write(repo, "docs/c.md", lines(2))  # -1
    git(repo, "commit", "-q", "-am", "work")
    # ベースが先に進んでも、merge-base からの差分だけを数える
    git(repo, "checkout", "-q", "main")
    write(repo, "src/b.ts", lines(50))
    git(repo, "commit", "-q", "-am", "main moves")
    git(repo, "checkout", "-q", "feature/x")
    # 未コミットの変更と未追跡は --worktree が無ければ数えない
    write(repo, "src/b.ts", lines(5) + "wt\n")  # +1
    write(repo, "src/new.ts", lines(3))


def setup_paths(repo: Path) -> None:
    setup_untracked_text(repo)
    write(repo, "docs/c.md", lines(3) + "more\n")  # +1
    write(repo, "docs/new.md", lines(2))


CASES = [
    ("CD1", "変更が無い", setup_none, [], {"rc": 0, "files": 0, "lines": 0, "untracked": []}),
    ("CD2", "未コミットの変更は追加と削除を足す", setup_modify, [], {"rc": 0, "files": 1, "lines": 5, "added": 3, "deleted": 2}),
    ("CD3", "未追跡のテキストはファイル数と追加行に足し、一覧に出す", setup_untracked_text, [],
     {"rc": 0, "files": 2, "lines": 9, "added": 7, "deleted": 2, "untracked": ["src/new.ts"]}),
    ("CD4", "未追跡のバイナリはファイル数に足し、行数に入れない", setup_untracked_binary, [],
     {"rc": 0, "files": 1, "lines": 0, "untracked": ["img/logo.png"]}),
    ("CD5", "gitignore したファイルは数えない", setup_ignored, [], {"rc": 0, "files": 0, "lines": 0, "untracked": []}),
    ("CD6", "削除は削除行に数える", setup_delete, [], {"rc": 0, "files": 1, "lines": 5, "added": 0, "deleted": 5}),
    ("CD7", "空白を含む名前の未追跡", setup_space_name, [], {"rc": 0, "files": 1, "lines": 2, "untracked": ["src/with space.ts"]}),
    ("CD8", "空の未追跡ファイルはファイル数にだけ足す", setup_untracked_empty, [], {"rc": 0, "files": 1, "lines": 0, "untracked": ["src/empty.ts"]}),
    ("CD18", "先頭が空白の名前の未追跡", setup_lead_space, [], {"rc": 0, "files": 1, "lines": 2, "untracked": [" lead.ts"]}),
    ("CD19", "追跡済みのバイナリはファイル数に足し、行数に入れない", setup_tracked_binary, [],
     {"rc": 0, "files": 2, "lines": 5, "added": 3, "deleted": 2}),
    ("CD9", "--base は merge-base からのコミット済みだけ", setup_branch, ["--base", "main"],
     {"rc": 0, "files": 2, "lines": 2, "added": 1, "deleted": 1, "untracked": []}),
    ("CD10", "--base --worktree は未コミットと未追跡も足す", setup_branch, ["--base", "main", "--worktree"],
     {"rc": 0, "files": 4, "lines": 6, "added": 5, "deleted": 1, "untracked": ["src/new.ts"]}),
    ("CD11", "パスで絞ると、未追跡も絞る", setup_paths, ["--", "docs"],
     {"rc": 0, "files": 2, "lines": 3, "added": 3, "deleted": 0, "untracked": ["docs/new.md"]}),
    ("CD12", "--base とパスの絞り込み", setup_branch, ["--base", "main", "--", "docs"],
     {"rc": 0, "files": 1, "lines": 1, "untracked": []}),
    ("CD13", "ディレクトリごとの内訳を出す", setup_paths, [], {"rc": 0, "dirstat_has": ["src/", "docs/"]}),
    ("CD14", "存在しないベースは 2", setup_none, ["--base", "nope"], {"rc": 2}),
    ("CD15", "知らない引数は 2", setup_none, ["--bogus"], {"rc": 2}),
    ("CD16", "--worktree だけ（--base 無し）は 2", setup_none, ["--worktree"], {"rc": 2}),
]


def old_procedure(repo: Path, args: list[str]) -> tuple[int, int]:
    """スクリプトに出す前の Step 1 の手順で数えた (ファイル数, 変更行)。"""
    paths = args[args.index("--") + 1:] if "--" in args else []
    if "--base" in args:
        base = args[args.index("--base") + 1]
        if "--worktree" in args:
            rng, untracked = [git(repo, "merge-base", base, "HEAD").strip()], True
        else:
            rng, untracked = [f"{base}...HEAD"], False
    else:
        rng, untracked = ["HEAD"], True
    short = git(repo, "diff", *rng, "--shortstat", "--", *paths)
    nums = [int(w) for w in short.replace(",", " ").split() if w.isdigit()]
    files = nums[0] if nums else 0
    changed = sum(nums[1:]) if nums else 0
    if untracked:
        for f in git(repo, "ls-files", "--others", "--exclude-standard", "--", *paths).splitlines():
            files += 1
            out = subprocess.run(["git", "diff", "--no-index", "--numstat", "/dev/null", f], cwd=repo, env=GIT_ENV,
                                 capture_output=True, text=True).stdout
            add = out.split("\t", 1)[0] if out else "0"
            changed += int(add) if add.isdigit() else 0
    return files, changed


def check(case_id: str, desc: str, setup, args: list[str], expect: dict, tmp: Path) -> str | None:
    repo = make_repo(tmp)
    setup(repo)
    rc, out, err = run(repo, *args)
    if rc != expect["rc"]:
        return f"rc={rc} (want {expect['rc']})\nstdout:\n{out}\nstderr:\n{err}"
    if rc != 0:
        if not err.strip():
            return "失敗したのに stderr に理由が無い"
        return None
    got = parse(out)
    want_files, want_lines = old_procedure(repo, args)
    if (got.get("files"), got.get("lines")) != (want_files, want_lines):
        return f"今の手順と合わない: files={got.get('files')} lines={got.get('lines')} (手順は {want_files}・{want_lines})\nstdout:\n{out}"
    for k, v in expect.items():
        if k == "rc":
            continue
        if k == "dirstat_has":
            joined = " ".join(got["dirstat"])
            missing = [d for d in v if d not in joined]
            if missing:
                return f"dirstat に {missing} が無い\nstdout:\n{out}"
            continue
        if got.get(k) != v:
            return f"{k}={got.get(k)!r} (want {v!r})\nstdout:\n{out}"
    return None


def check_not_repo(tmp: Path) -> str | None:
    d = tmp / "plain"
    d.mkdir()
    rc, out, err = run(d)
    if rc != 2:
        return f"rc={rc} (want 2)\nstdout:\n{out}\nstderr:\n{err}"
    if not err.strip():
        return "失敗したのに stderr に理由が無い"
    return None


def check_git_override(tmp: Path) -> str | None:
    """GIT に渡した git を使う。PATH の先頭の git が動かない環境（評価の sandbox）で呼び直すため。"""
    repo = make_repo(tmp)
    setup_untracked_text(repo)
    real = shutil.which("git")
    log = tmp / "calls.log"
    wrapper = tmp / "mygit"
    wrapper.write_text(f'#!/bin/sh\necho x >> "{log}"\nexec "{real}" "$@"\n')
    wrapper.chmod(0o755)
    broken = tmp / "bin"
    broken.mkdir()
    (broken / "git").write_text("#!/bin/sh\necho broken >&2\nexit 72\n")
    (broken / "git").chmod(0o755)
    env = {**GIT_ENV, "PATH": f"{broken}:{GIT_ENV.get('PATH', '')}", "GIT": str(wrapper)}
    if not SCRIPT.exists():
        return f"script not found: {SCRIPT}"
    p = subprocess.run(["bash", str(SCRIPT)], cwd=repo, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        return f"rc={p.returncode}\nstderr:\n{p.stderr}"
    got = parse(p.stdout)
    if (got.get("files"), got.get("lines")) != (2, 9):
        return f"files={got.get('files')} lines={got.get('lines')} (want 2・9)\nstdout:\n{p.stdout}"
    if not any("src/" in x for x in got["dirstat"]):
        return f"dirstat に src/ が無い\nstdout:\n{p.stdout}"
    if not log.exists():
        return "GIT に渡した git が呼ばれていない"
    # --base と --worktree の経路（ベースの確かめ・merge-base）も GIT の git で通る
    p = subprocess.run(["bash", str(SCRIPT), "--base", "main", "--worktree"], cwd=repo, env=env, capture_output=True, text=True)
    if p.returncode != 0 or (parse(p.stdout).get("files"), parse(p.stdout).get("lines")) != (2, 9):
        return f"--base main --worktree で rc={p.returncode}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}"
    env["GIT"] = str(tmp / "nope")
    p = subprocess.run(["bash", str(SCRIPT)], cwd=repo, env=env, capture_output=True, text=True)
    if p.returncode != 2 or not p.stderr.strip():
        return f"存在しない GIT で rc={p.returncode} (want 2 と理由)\nstderr:\n{p.stderr}"
    return None


def main() -> int:
    failed = 0
    total = 0
    for case_id, desc, setup, args, expect in CASES:
        total += 1
        tmp = Path(tempfile.mkdtemp(prefix="count-diff-"))
        try:
            problem = check(case_id, desc, setup, args, expect, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if problem:
            failed += 1
            print(f"FAIL {case_id}: {desc}\n  " + problem.replace("\n", "\n  "))
        else:
            print(f"PASS {case_id}: {desc}")
    total += 1
    tmp = Path(tempfile.mkdtemp(prefix="count-diff-"))
    try:
        problem = check_not_repo(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if problem:
        failed += 1
        print("FAIL CD17: git 管理下でなければ 2\n  " + problem.replace("\n", "\n  "))
    else:
        print("PASS CD17: git 管理下でなければ 2")
    total += 1
    tmp = Path(tempfile.mkdtemp(prefix="count-diff-"))
    try:
        problem = check_git_override(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if problem:
        failed += 1
        print("FAIL CD20: GIT に渡した git を使う\n  " + problem.replace("\n", "\n  "))
    else:
        print("PASS CD20: GIT に渡した git を使う")
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
