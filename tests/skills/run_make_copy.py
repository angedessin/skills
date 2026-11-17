#!/usr/bin/env python3
"""frontend-code-review の make-copy.sh のテスト。一時的な git リポジトリと、差し替えた TMPDIR で確かめる。

Usage: mise exec -- pnpm run test:skills
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 壊した写しで落ちるかを確かめるときに差し替える
SCRIPT = Path(os.environ.get("MAKE_COPY_SCRIPT") or ROOT / ".claude" / "skills" / "frontend-code-review" / "scripts" / "make-copy.sh")

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}
GIT_ENV.pop("GIT", None)
GIT_ENV.pop("MAKE_COPY_TIMEOUT", None)
DAY_AGO = time.time() - 2 * 86400


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=GIT_ENV)


def write(base: Path, rel: str, content: str = "x\n") -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, ".gitignore", "node_modules/\n")
    write(repo, "src/a.ts", "export const a = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    write(repo, "src/a.ts", "export const a = 2\n")  # 未コミットの変更
    write(repo, "src/new.test.ts", "case\n")  # 未追跡
    write(repo, "node_modules/pkg/index.js", "module.exports = 1\n")  # 無視されたファイルも写す
    return repo


def tmpdir(tmp: Path) -> Path:
    t = tmp / "tmpdir"
    t.mkdir(exist_ok=True)
    return t


def run(cwd: Path, *args: str, env: dict | None = None) -> tuple[int, list[str], str]:
    r = subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env, timeout=60)
    return r.returncode, r.stdout.splitlines(), r.stderr


def env_with(t: Path, **extra: str) -> dict:
    return {**GIT_ENV, "TMPDIR": str(t), **extra}


def files(base: Path) -> dict[str, str]:
    out = {}
    for p in base.rglob("*"):
        rel = p.relative_to(base).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if p.is_file():
            out[rel] = p.read_text(encoding="utf-8")
    return out


def boxes(t: Path) -> list[Path]:
    return sorted(t.glob("review-copy.*"))


def check_copy(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    t = tmpdir(tmp)
    rc, out, err = run(repo / "src", env=env_with(t))  # 根でない場所から呼んでも根を写す
    if rc != 0 or len(out) != 1:
        return f"rc={rc} out={out} err={err}"
    dest = Path(out[0])
    if not dest.is_absolute() or not str(dest.resolve()).startswith(str(t.resolve()) + "/"):
        return f"TMPDIR の下の絶対パスでない: {dest}"
    if (dest / ".git").exists():
        return "写しに .git がある"
    if files(dest) != files(repo):
        return f"中身が違う: {sorted(files(dest))} != {sorted(files(repo))}"
    return None


def check_worktree(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    wt = tmp / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
    write(wt, "src/b.ts", "export const b = 1\n")
    if not (wt / ".git").is_file():
        return "前提の崩れ: worktree の .git がファイルでない"
    rc, out, err = run(wt, env=env_with(tmpdir(tmp)))
    if rc != 0 or len(out) != 1:
        return f"rc={rc} out={out} err={err}"
    dest = Path(out[0])
    if (dest / ".git").exists():
        return "写しに .git がある（worktree の gitdir を指すファイル）"
    if files(dest) != files(wt):
        return f"中身が違う: {sorted(files(dest))} != {sorted(files(wt))}"
    return None


def check_excluded(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    for rel in (".env", "sub/.env.local", "config/prod.env", "certs/dev.pem", "certs/dev.key"):
        write(repo, rel, "secret\n")
    rc, out, err = run(repo, env=env_with(tmpdir(tmp)))
    if rc != 0 or out[1:] != ["excluded: 5"]:
        return f"rc={rc} out={out} err={err}"
    left = [rel for rel in files(Path(out[0])) if "secret" in (Path(out[0]) / rel).read_text()]
    if left:
        return f"除くはずのファイルが写しにある: {left}"
    if "src/a.ts" not in files(Path(out[0])):
        return "ほかのファイルが写っていない"
    return None


def check_git_override(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    log = tmp / "git.log"
    real = shutil.which("git")
    wrapper = bin_dir / "mygit"
    wrapper.write_text(f'#!/bin/sh\necho called >> "{log}"\nexec "{real}" "$@"\n')
    wrapper.chmod(0o755)
    rc, out, err = run(repo, env=env_with(tmpdir(tmp), GIT=str(wrapper)))
    if rc != 0 or not log.exists():
        return f"GIT= の git を使っていない: rc={rc} err={err}"
    return None


def check_no_tmpdir(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    env = dict(GIT_ENV)
    env.pop("TMPDIR", None)
    rc, out, err = run(repo, env=env)
    if rc != 2 or out:
        return f"TMPDIR が無いのに rc={rc} out={out}"
    rc, out, err = run(repo, env=env_with(tmp / "missing"))
    if rc != 2 or out:
        return f"TMPDIR が無いディレクトリなのに rc={rc} out={out}"
    return None


def check_tmpdir_readonly(tmp: Path) -> str | None:
    if os.geteuid() == 0:
        return None  # root は書けてしまう
    repo = make_repo(tmp)
    t = tmpdir(tmp)
    t.chmod(0o500)
    try:
        rc, out, err = run(repo, env=env_with(t))
    finally:
        t.chmod(0o700)
    if rc != 2 or out or boxes(t):
        return f"rc={rc} out={out} 残り={boxes(t)}"
    return None


def check_tmpdir_in_repo(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    t = repo / "node_modules" / ".tmp"
    t.mkdir()
    rc, out, err = run(repo, env=env_with(t))
    if rc != 2 or out or boxes(t):
        return f"rc={rc} out={out} 残り={boxes(t)}"
    return None


def fake_rsync(tmp: Path, body: str) -> dict:
    bin_dir = tmp / "fakebin"
    bin_dir.mkdir()
    f = bin_dir / "rsync"
    f.write_text("#!/bin/sh\n" + body)
    f.chmod(0o755)
    return {"PATH": f"{bin_dir}:{os.environ['PATH']}"}


def check_rsync_fails(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    t = tmpdir(tmp)
    # 途中まで写してから失敗する
    extra = fake_rsync(tmp, 'mkdir -p "$(eval echo \\${$#})/half"; echo boom >&2; exit 23\n')
    rc, out, err = run(repo, env=env_with(t, **extra))
    if rc != 2 or out or boxes(t) or "boom" not in err:
        return f"rc={rc} out={out} 残り={boxes(t)} err={err}"
    return None


def check_timeout(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    t = tmpdir(tmp)
    extra = fake_rsync(tmp, "exec sleep 30\n")
    start = time.time()
    rc, out, err = run(repo, env=env_with(t, MAKE_COPY_TIMEOUT="1", **extra))
    took = time.time() - start
    if rc != 2 or out or boxes(t) or "打ち切った" not in err or took > 10:
        return f"rc={rc} out={out} 残り={boxes(t)} took={took:.1f}s err={err}"
    return None


def check_not_repo(tmp: Path) -> str | None:
    d = tmp / "plain"
    d.mkdir()
    t = tmpdir(tmp)
    rc, out, err = run(d, env=env_with(t, GIT_CEILING_DIRECTORIES=str(tmp)))
    if rc != 2 or out or boxes(t):
        return f"rc={rc} out={out} 残り={boxes(t)}"
    return None


def check_empty(tmp: Path) -> str | None:
    d = tmp / "plain"
    d.mkdir()
    t = tmpdir(tmp)
    rc, out, err = run(d, "--empty", env=env_with(t, GIT_CEILING_DIRECTORIES=str(tmp)))  # git の外でも作れる
    if rc != 0 or len(out) != 1:
        return f"rc={rc} out={out} err={err}"
    dest = Path(out[0])
    if not dest.is_dir() or any(dest.iterdir()) or not str(dest.resolve()).startswith(str(t.resolve()) + "/"):
        return f"空のディレクトリでない: {dest}"
    return None


def check_cleanup(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    t = tmpdir(tmp)
    # 写し元の時刻を古くしておく（rsync -a が引き継ぐ）
    for p in [repo, *repo.rglob("*")]:
        if ".git" not in p.parts:
            os.utime(p, (DAY_AGO, DAY_AGO))
    rc, out, err = run(repo, env=env_with(t))
    if rc != 0:
        return f"1 回目: rc={rc} err={err}"
    first = Path(out[0])
    hour_ago = time.time() - 3600  # 1 日には満たない古さは残す
    os.utime(first.parent / "made", (hour_ago, hour_ago))
    old = t / "review-copy.old111"
    (old / "tree").mkdir(parents=True)
    (old / "made").touch()
    os.utime(old / "made", (DAY_AGO, DAY_AGO))
    unmarked = t / "review-copy.old222"  # 印の無い作りかけは、ディレクトリの時刻で測る
    unmarked.mkdir()
    os.utime(unmarked, (DAY_AGO, DAY_AGO))
    other = t / "keep-me"
    other.mkdir()
    os.utime(other, (DAY_AGO, DAY_AGO))
    rc, out, err = run(repo, env=env_with(t))
    if rc != 0:
        return f"2 回目: rc={rc} err={err}"
    if old.exists() or unmarked.exists():
        return "1 日より古い写しを消していない"
    if not first.exists():
        return "時刻の古い作業ツリーから作った新しい写しを消した"
    if not other.exists():
        return "接頭辞の違うディレクトリを消した"
    return None


def check_bad_args(tmp: Path) -> str | None:
    t = tmpdir(tmp)
    for args, extra in ((["--nope"], {}), (["--empty", "x"], {}), ([], {"MAKE_COPY_TIMEOUT": "abc"})):
        rc, out, err = run(tmp, *args, env=env_with(t, **extra))
        if rc != 2 or out:
            return f"{args} {extra}: rc={rc} out={out}"
    return None


CHECKS = [
    check_copy,
    check_worktree,
    check_excluded,
    check_git_override,
    check_no_tmpdir,
    check_tmpdir_readonly,
    check_tmpdir_in_repo,
    check_rsync_fails,
    check_timeout,
    check_not_repo,
    check_empty,
    check_cleanup,
    check_bad_args,
]


def main() -> int:
    failures = []
    for fn in CHECKS:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d).resolve()
            try:
                msg = fn(tmp)
            except Exception as e:  # noqa: BLE001
                msg = f"例外: {e!r}"
            if msg:
                failures.append(f"{fn.__name__}: {msg}")
    for f in failures:
        print("FAIL", f)
    print(f"make-copy: {len(CHECKS) - len(failures)}/{len(CHECKS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
