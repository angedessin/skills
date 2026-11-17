#!/usr/bin/env python3
"""list-exemptions.sh のテスト。一時的な git リポジトリで、足した免除の拾い方を確かめる。

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
COPIES = [
    ROOT / ".claude" / "skills" / "frontend-code-review" / "scripts" / "list-exemptions.sh",
    ROOT / ".claude" / "skills" / "pr-create" / "scripts" / "list-exemptions.sh",
]
# 壊した写しで落ちるかを確かめるときに差し替える
SCRIPT = Path(os.environ.get("LIST_EXEMPTIONS_SCRIPT") or COPIES[0])

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

TASK = ".steering/20261101-x/test-exemptions.md"
OTHER = ".steering/20261102-y/test-exemptions.md"
BASE_ROW = "- src/old.ts — 前からある免除（20261101）"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, env=GIT_ENV, check=True, capture_output=True, text=True).stdout


def write(repo: Path, rel: str, content: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def ex(none: list[str] = (), fail: list[str] = (), weaken: list[str] = (), extra: str = "") -> str:
    return (
        "# テストの免除\n\n## テスト不要\n\n" + "".join(r + "\n" for r in none)
        + "\n## 失敗を残す\n\n" + "".join(r + "\n" for r in fail)
        + "\n## テストを弱める\n\n" + "".join(r + "\n" for r in weaken)
        + extra
    )


def commit(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, "src/a.ts", "a\n")
    write(repo, TASK, ex(none=[BASE_ROW]))
    commit(repo, "init")
    return repo


def run(cwd: Path, *args: str, env: dict | None = None) -> tuple[int, str, str]:
    if not SCRIPT.exists():
        return 127, "", f"script not found: {SCRIPT}"
    p = subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd, env=env or GIT_ENV, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def setup_none(repo: Path) -> None:
    pass


def setup_add_row(repo: Path) -> None:
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — 文言だけの変更（20261116）"], weaken=["- src/b.test.ts — 仕様の変更で不要になった（20261116）"]))


def setup_untracked(repo: Path) -> None:
    write(repo, OTHER, ex(fail=["- src/c.test.ts — 上流の不具合を待つ（20261116）"]))


def setup_rules(repo: Path) -> None:
    write(repo, TASK, ex(
        none=[BASE_ROW, "- src/nodate.ts — 日付の無い理由", "- src/noreason.ts — ", "- src/noreason2.ts —    ", "- src/nodash.ts 理由",
              "- `./src/tick.ts` — 引用符と ./ を外す（20261116）"],
        extra="\n## メモ\n\n- src/memo.ts — 節の外（20261116）\n",
    ).replace("# テストの免除\n", "# テストの免除\n\n- src/top.ts — 節の前（20261116）\n"))


def setup_reason_changed(repo: Path) -> None:
    write(repo, TASK, ex(none=["- src/old.ts — 理由を書き直した（20261116）"]))


def setup_row_removed(repo: Path) -> None:
    write(repo, TASK, ex())


def setup_root_and_archived(repo: Path) -> None:
    write(repo, ".steering/test-exemptions.md", ex(none=["- src/root.ts — 直下の免除ファイル（20261116）"]))
    write(repo, ".steering/archived/20260101-z/test-exemptions.md", ex(none=["- src/arch.ts — archived は見ない（20261116）"]))
    write(repo, ".steering/archived/test-exemptions.md", ex(none=["- src/arch2.ts — archived の直下も見ない（20261116）"]))
    write(repo, ".steering/20261101-x/sub/test-exemptions.md", ex(none=["- src/deep.ts — 深い場所は見ない（20261116）"]))


def setup_branch(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — ブランチで足した（20261116）"]))
    commit(repo, "work")
    # ベースが先に進んで足した免除は、このブランチの分ではない
    git(repo, "checkout", "-q", "main")
    write(repo, ".steering/20261103-m/test-exemptions.md", ex(none=["- src/m.ts — main の側で足した（20261116）"]))
    commit(repo, "main moves")
    git(repo, "checkout", "-q", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — ブランチで足した（20261116）", "- src/wt.ts — 未コミット（20261116）"]))
    write(repo, OTHER, ex(fail=["- src/ut.test.ts — 未追跡（20261116）"]))


def setup_closed(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, OTHER, ex(weaken=["- src/b.test.ts — 仕様の変更で不要になった（20261116）", "- src/gone.test.ts — 後で解消する（20261116）"]))
    write(repo, ".steering/20261102-y/design.md", "Status: APPROVED\n")
    commit(repo, "add task y")
    # 解消した行は、閉じる前に消してある
    write(repo, OTHER, ex(weaken=["- src/b.test.ts — 仕様の変更で不要になった（20261116）"]))
    commit(repo, "resolve one")
    git(repo, "rm", "-r", "-q", ".steering/20261102-y")
    commit(repo, "close y")
    # 分岐点より前からあるタスクを閉じても、前からある行は載せない
    write(repo, TASK, ex(none=[BASE_ROW, "- src/late.ts — 閉じる前に足した（20261116）"]))
    commit(repo, "add to x")
    git(repo, "rm", "-r", "-q", ".steering/20261101-x")
    commit(repo, "close x")


def setup_resolved(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — 後でテストを書く（20261116）"]))
    commit(repo, "exempt")
    write(repo, TASK, ex(none=[BASE_ROW]))
    commit(repo, "resolved")


def setup_closing(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — ブランチで足した（20261116）"]))
    commit(repo, "work")
    git(repo, "rm", "-r", "-q", ".steering/20261101-x")


def setup_recreated(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — 消す前に足した（20261116）"]))
    commit(repo, "exempt")
    git(repo, "rm", "-r", "-q", ".steering/20261101-x")
    commit(repo, "remove")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/again.ts — 作り直して足した（20261116）"]))
    commit(repo, "recreate")


def setup_section_moved(repo: Path) -> None:
    write(repo, TASK, ex(weaken=[BASE_ROW]))


def setup_closed_with_similar(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, TASK, ex(none=[BASE_ROW, "- src/a.ts — 閉じる前に足した（20261116）"]))
    commit(repo, "work")
    # 中身の似た免除ファイルを同じコミットで足し、git に改名と判定させる
    git(repo, "rm", "-r", "-q", ".steering/20261101-x")
    write(repo, OTHER, ex(none=["- src/a.ts — 閉じる前に足した（20261116）", "- src/c.ts — 別のタスクで足した（20261116）"]))
    commit(repo, "close x, start y")


JA_OPEN = ".steering/20261104-日本語/test-exemptions.md"
JA_CLOSED = ".steering/20261105-閉じた/test-exemptions.md"


def setup_japanese(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    write(repo, JA_OPEN, ex(none=["- src/ja.ts — 日本語のタスク（20261116）"]))
    write(repo, JA_CLOSED, ex(fail=["- src/jc.test.ts — 閉じた日本語のタスク（20261116）"]))
    commit(repo, "add ja tasks")
    git(repo, "rm", "-r", "-q", ".steering/20261105-閉じた")
    commit(repo, "close ja")


def setup_ignored(repo: Path) -> None:
    write(repo, ".gitignore", ".steering/20261102-y/\n")
    commit(repo, "ignore")
    setup_untracked(repo)


def setup_steering_ignored(repo: Path) -> None:
    git(repo, "rm", "-r", "-q", "--cached", ".steering")
    write(repo, ".gitignore", ".steering/\n")
    commit(repo, "ignore steering")


A = "  [テスト不要] src/a.ts — 文言だけの変更（20261116） (%s)" % TASK
B = "  [テストを弱める] src/b.test.ts — 仕様の変更で不要になった（20261116） (%s)" % TASK

# 各ケースは (id, 説明, 準備, 引数, 期待の rc, 期待の stdout の行。None なら見ない)
CASES = [
    ("LE1", "足した免除が無ければ exemptions: 0 だけ", setup_none, [], 0, ["exemptions: 0"]),
    ("LE2", "足した行が、節の名前と免除ファイルのパスつきで出る（前からある行は出ない）", setup_add_row, [], 0, ["exemptions: 2", A, B]),
    ("LE3", "未追跡の免除ファイルの行が出る", setup_untracked, [], 0,
     ["exemptions: 1", f"  [失敗を残す] src/c.test.ts — 上流の不具合を待つ（20261116） ({OTHER})"]),
    ("LE4", "日付の無い行は出る。理由の無い行・節の外の行は出ない。パスの ` と ./ は外す", setup_rules, [], 0,
     ["exemptions: 2", f"  [テスト不要] src/nodate.ts — 日付の無い理由 ({TASK})", f"  [テスト不要] src/tick.ts — 引用符と ./ を外す（20261116） ({TASK})"]),
    ("LE5", "理由だけ変えた行は、新しい理由で出る", setup_reason_changed, [], 0,
     ["exemptions: 1", f"  [テスト不要] src/old.ts — 理由を書き直した（20261116） ({TASK})"]),
    ("LE6", "消しただけの行は出ない", setup_row_removed, [], 0, ["exemptions: 0"]),
    ("LE7", ".steering 直下の免除ファイルは見る。archived と深い場所は見ない", setup_root_and_archived, [], 0,
     ["exemptions: 1", "  [テスト不要] src/root.ts — 直下の免除ファイル（20261116） (.steering/test-exemptions.md)"]),
    ("LE8", "--base は分岐点と HEAD を比べる（未コミット・未追跡・ベースの側の免除は出ない）", setup_branch, ["--base", "main"], 0,
     ["exemptions: 1", f"  [テスト不要] src/a.ts — ブランチで足した（20261116） ({TASK})"]),
    ("LE9", "--base --worktree は未コミットと未追跡も出す", setup_branch, ["--base", "main", "--worktree"], 0,
     ["exemptions: 3", f"  [テスト不要] src/a.ts — ブランチで足した（20261116） ({TASK})", f"  [テスト不要] src/wt.ts — 未コミット（20261116） ({TASK})",
      f"  [失敗を残す] src/ut.test.ts — 未追跡（20261116） ({OTHER})"]),
    ("LE10", "--base で、閉じたタスクの免除が印つきで出る（閉じる前に消した行・分岐点からある行は出ない）", setup_closed, ["--base", "main"], 0,
     ["exemptions: 2", f"  [テスト不要] src/late.ts — 閉じる前に足した（20261116） (閉じたタスク: {TASK})",
      f"  [テストを弱める] src/b.test.ts — 仕様の変更で不要になった（20261116） (閉じたタスク: {OTHER})"]),
    ("LE11", "--base で、ファイルは残っていて行だけ消したものは出ない", setup_resolved, ["--base", "main"], 0, ["exemptions: 0"]),
    ("LE12", "--base --worktree で、閉じる途中（git rm の後、コミットの前）の免除が印つきで出る", setup_closing, ["--base", "main", "--worktree"], 0,
     ["exemptions: 1", f"  [テスト不要] src/a.ts — ブランチで足した（20261116） (閉じたタスク: {TASK})"]),
    ("LE13", "指定なしでは、閉じる途中の免除は出ない（HEAD と比べるので足した行が無い）", setup_closing, [], 0, ["exemptions: 0"]),
    ("LE26", "--base で、消して作り直した免除ファイルは、今ある行だけ出す（閉じたタスクにしない）", setup_recreated, ["--base", "main"], 0,
     ["exemptions: 1", f"  [テスト不要] src/again.ts — 作り直して足した（20261116） ({TASK})"]),
    ("LE27", "同じパス・理由のまま節だけ移した行は、新しい節で出る", setup_section_moved, [], 0,
     ["exemptions: 1", f"  [テストを弱める] src/old.ts — 前からある免除（20261101） ({TASK})"]),
    ("LE28", "--base で、閉じたタスクと同じコミットで似た免除ファイルを足しても、閉じたタスクの免除が出る", setup_closed_with_similar, ["--base", "main"], 0,
     ["exemptions: 3", f"  [テスト不要] src/a.ts — 閉じる前に足した（20261116） ({OTHER})", f"  [テスト不要] src/c.ts — 別のタスクで足した（20261116） ({OTHER})",
      f"  [テスト不要] src/a.ts — 閉じる前に足した（20261116） (閉じたタスク: {TASK})"]),
    ("LE29", "--base で、日本語名のタスクの免除と、日本語名の閉じたタスクの免除が出る", setup_japanese, ["--base", "main"], 0,
     ["exemptions: 2", f"  [テスト不要] src/ja.ts — 日本語のタスク（20261116） ({JA_OPEN})",
      f"  [失敗を残す] src/jc.test.ts — 閉じた日本語のタスク（20261116） (閉じたタスク: {JA_CLOSED})"]),
    ("LE14", "免除ファイルが gitignore で無視されていると unknown で 0", setup_ignored, [], 0, None),
    ("LE15", ".steering ごと無視されていると、免除ファイルが無くても unknown で 0", setup_steering_ignored, ["--base", "main"], 0, None),
    ("LE16", "知らない引数は 2", setup_none, ["--bogus"], 2, None),
    ("LE17", "--worktree だけ（--base 無し）は 2", setup_none, ["--worktree"], 2, None),
    ("LE18", "--base に値が無ければ 2", setup_none, ["--base"], 2, None),
    ("LE19", "存在しないベースは 2", setup_none, ["--base", "nope"], 2, None),
    ("LE20", "パスでの絞り込みは受けず 2", setup_none, ["--", "src"], 2, None),
]
UNKNOWN = {"LE14", "LE15"}


def check(case_id: str, setup, args: list[str], want_rc: int, want_out: list[str] | None, tmp: Path) -> str | None:
    repo = make_repo(tmp)
    setup(repo)
    before = git(repo, "status", "--porcelain", "--ignored")
    rc, out, err = run(repo, *args)
    if rc != want_rc:
        return f"rc={rc} (want {want_rc})\nstdout:\n{out}\nstderr:\n{err}"
    if rc != 0 and not err.strip():
        return "失敗したのに stderr に理由が無い"
    if case_id in UNKNOWN:
        got = out.splitlines()
        if len(got) != 1 or not got[0].startswith("exemptions: unknown (") or "gitignore" not in got[0]:
            return f"exemptions: unknown (… gitignore …) の 1 行でない\nstdout:\n{out}"
    if want_out is not None and out.splitlines() != want_out:
        return "stdout が違う\nwant:\n" + "\n".join(want_out) + f"\ngot:\n{out}"
    if git(repo, "status", "--porcelain", "--ignored") != before:
        return "スクリプトが作業ツリーか index を変えた"
    return None


def check_subdir(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    setup_add_row(repo)
    rc, out, err = run(repo / "src")
    if rc != 0 or out.splitlines() != ["exemptions: 2", A, B]:
        return f"rc={rc}\nstdout:\n{out}\nstderr:\n{err}"
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


def wrapper_env(tmp: Path, body: str) -> tuple[dict, Path]:
    """PATH の先頭の git を壊し、GIT に包みを渡した環境。body は包みの中で実行の前に走る sh。"""
    real = shutil.which("git")
    log = tmp / "calls.log"
    wrapper = tmp / "mygit"
    wrapper.write_text(f'#!/bin/sh\necho x >> "{log}"\n{body}\nexec "{real}" "$@"\n')
    wrapper.chmod(0o755)
    broken = tmp / "bin"
    broken.mkdir()
    (broken / "git").write_text("#!/bin/sh\necho broken >&2\nexit 72\n")
    (broken / "git").chmod(0o755)
    return {**GIT_ENV, "PATH": f"{broken}:{GIT_ENV.get('PATH', '')}", "GIT": str(wrapper)}, log


def check_git_override(tmp: Path) -> str | None:
    repo = make_repo(tmp)
    setup_closed(repo)
    env, log = wrapper_env(tmp, "")
    rc, out, err = run(repo, "--base", "main", env=env)
    if rc != 0 or not out.startswith("exemptions: 2\n"):
        return f"rc={rc} (want 0 と exemptions: 2)\nstdout:\n{out}\nstderr:\n{err}"
    if not log.exists():
        return "GIT に渡した git が呼ばれていない"
    rc, out, err = run(repo, "--base", "main", "--worktree", env=env)
    if rc != 0 or not out.startswith("exemptions: 2\n"):
        return f"--worktree で rc={rc}\nstdout:\n{out}\nstderr:\n{err}"
    env["GIT"] = str(tmp / "nope")
    rc, out, err = run(repo, env=env)
    if rc != 2 or "GIT=" not in err:
        return f"存在しない GIT で rc={rc} (want 2 と GIT=<パス> の案内)\nstderr:\n{err}"
    return None


def check_git_fails_midway(tmp: Path) -> str | None:
    # 免除ファイルの置かれ方で git show を呼ぶ箇所が変わるので、場面ごとに落とす。
    # 続く前の版の show でも unknown になるので、HEAD の版の show だけを落とす
    scenes = [
        ("closed", setup_closed, ["--base", "main"], ("ls-tree", "log", "show", "check-ignore")),
        ("branch", setup_branch, ["--base", "main"], ("HEAD:*",)),
        ("worktree", setup_add_row, [], ("HEAD:*",)),
        ("closing", setup_closing, ["--base", "main", "--worktree"], ("HEAD:*",)),
    ]
    for name, setup, args, pats in scenes:
        (tmp / name).mkdir()
        repo = make_repo(tmp / name)
        setup(repo)
        for i, pat in enumerate(pats):
            d =tmp / name / str(i)
            d.mkdir()
            # -c core.quotepath=false が前に付く呼び出しもあるので、引数のどこにあっても落とす
            env, _ = wrapper_env(d, f'for a in "$@"; do case "$a" in {pat}) exit 128 ;; esac; done')
            rc, out, err = run(repo, *args, env=env)
            got = out.splitlines()
            if rc != 0 or len(got) != 1 or not got[0].startswith("exemptions: unknown ("):
                return f"{name} で git の {pat} の呼び出しが落ちたとき rc={rc} (want 0 と exemptions: unknown の 1 行)\nstdout:\n{out}\nstderr:\n{err}"
    return None


def check_copies(tmp: Path) -> str | None:
    missing = [str(p.relative_to(ROOT)) for p in COPIES if not p.exists()]
    if missing:
        return "無い: " + ", ".join(missing)
    if COPIES[0].read_bytes() != COPIES[1].read_bytes():
        return "2 つの list-exemptions.sh の中身が違う（片方だけ直していないか）"
    return None


EXTRA = [
    ("LE21", "サブディレクトリから呼んでも同じ結果", check_subdir),
    ("LE22", "git 管理下でなければ 2", check_not_repo),
    ("LE23", "GIT に渡した git を使う", check_git_override),
    ("LE24", "git が途中で落ちたら unknown で 0", check_git_fails_midway),
    ("LE25", "2 つのスキルの list-exemptions.sh がバイト単位で一致する", check_copies),
]


def main() -> int:
    failed = 0
    jobs = [(i, d, lambda tmp, i=i, s=s, a=a, r=r, o=o: check(i, s, a, r, o, tmp)) for i, d, s, a, r, o in CASES]
    jobs += [(i, d, f) for i, d, f in EXTRA]
    for case_id, desc, fn in jobs:
        tmp = Path(tempfile.mkdtemp(prefix="list-exemptions-"))
        try:
            problem = fn(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if problem:
            failed += 1
            print(f"FAIL {case_id}: {desc}\n  " + problem.replace("\n", "\n  "))
        else:
            print(f"PASS {case_id}: {desc}")
    print(f"\n{len(jobs) - failed}/{len(jobs)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
