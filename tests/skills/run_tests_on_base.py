#!/usr/bin/env python3
"""frontend-code-review の run-tests-on-base.sh のテスト。一時的な git リポジトリと偽の vitest で確かめる。

偽の vitest はテストファイルの中の宣言を読む（ファイルの中身で振る舞いが決まるので、ベースの版と今の版で結果が変わる）:
  case <名前> needs <パス>:<文字列>   <パス> に <文字列> があれば通る
  import <パス>                       <パス> が無ければファイルごと落ちる（import のエラーのまね）

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
SCRIPT = Path(os.environ.get("RUN_TESTS_ON_BASE_SCRIPT") or ROOT / ".claude" / "skills" / "frontend-code-review" / "scripts" / "run-tests-on-base.sh")

FAKE_VITEST = r'''#!/usr/bin/env python3
import json, os, sys, time
here = os.path.dirname(os.path.realpath(__file__))
fake = os.path.join(here, "..", ".fake")
with open(os.path.join(fake, "calls"), "a") as f:
    f.write(os.getcwd() + " " + " ".join(sys.argv[1:]) + "\n")
if os.path.exists(os.path.join(fake, "sleep")):
    with open(os.path.join(fake, "pid"), "w") as f:
        f.write(str(os.getpid()))
    time.sleep(float(open(os.path.join(fake, "sleep")).read()))
if os.path.exists(os.path.join(fake, "exit")):
    print("fake vitest: failed to load config", file=sys.stderr)
    sys.exit(int(open(os.path.join(fake, "exit")).read()))
out, files = None, []
# 本物の vitest run のフィルタは部分一致で、渡していない似た名前のファイルも流れる
extra = os.path.join(fake, "extra")
extra_files = open(extra).read().split() if os.path.exists(extra) else []
for a in sys.argv[1:]:
    if a.startswith("--outputFile="):
        out = a.split("=", 1)[1]
    elif a.startswith("-") or a == "run":
        continue
    else:
        files.append(a)
cwd = os.getcwd()
files += [f for f in extra_files if f not in files]
results, nfail = [], 0
for t in files:
    path = os.path.join(cwd, t)
    if not os.path.exists(path):
        continue
    asserts, broken = [], None
    for ln in open(path).read().splitlines():
        w = ln.split()
        if len(w) >= 2 and w[0] == "import" and not os.path.exists(os.path.join(cwd, w[1])):
            broken = "Failed to resolve import " + w[1]
        if len(w) >= 4 and w[0] == "case" and w[2] == "needs":
            rel, _, s = w[3].partition(":")
            p = os.path.join(cwd, rel)
            ok = os.path.exists(p) and s in open(p).read()
            asserts.append({"fullName": w[1], "status": "passed" if ok else "failed",
                            "failureMessages": [] if ok else ["AssertionError: " + w[1]]})
    if broken:
        results.append({"name": path, "status": "failed", "message": broken, "assertionResults": []})
        nfail += 1
        continue
    failed = any(a["status"] == "failed" for a in asserts)
    nfail += failed
    results.append({"name": path, "status": "failed" if failed else "passed", "message": "", "assertionResults": asserts})
json.dump({"numTotalTestSuites": len(results), "numFailedTestSuites": nfail, "success": nfail == 0, "testResults": results}, open(out, "w"))
sys.exit(1 if nfail else 0)
'''

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


def write(repo: Path, rel: str, content: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def make_repo(tmp: Path, vitest: bool = True) -> Path:
    """main に実装（src/sort.ts）と既存のテストをコミットした状態。"""
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, ".gitignore", "node_modules/\n")
    write(repo, "src/sort.ts", "export const sortByPrice = list => list // OLD\n")
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\n")
    write(repo, "src/other.ts", "export const x = 1\n")
    if vitest:
        bin_ = repo / "node_modules" / ".bin" / "vitest"
        bin_.parent.mkdir(parents=True)
        bin_.write_text(FAKE_VITEST)
        bin_.chmod(0o755)
        (repo / "node_modules" / ".fake").mkdir()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def change_impl(repo: Path) -> None:
    write(repo, "src/sort.ts", "export const sortByPrice = list => [...list].sort() // NEW\n")


def run(repo: Path, *args: str, env: dict | None = None, timeout: int = 60) -> tuple[int, str, str]:
    if not SCRIPT.exists():
        return 127, "", f"script not found: {SCRIPT}"
    p = subprocess.run(["bash", str(SCRIPT), *args], cwd=repo, env=env or GIT_ENV, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def parse(out: str) -> dict:
    res: dict = {"passed_list": []}
    section = None
    for ln in out.splitlines():
        if ln.startswith("tests: "):
            res["tests"] = int(ln.split(": ", 1)[1])
            section = None
        elif ln.startswith("passed-on-base: "):
            res["passed"] = int(ln.split(": ", 1)[1])
            section = "passed"
        elif ln.startswith("failed-on-base: "):
            res["failed"] = int(ln.split(": ", 1)[1])
            section = None
        elif section == "passed" and ln.startswith("  "):
            res["passed_list"].append(ln[2:])
    return res


def calls(repo: Path) -> list[str]:
    f = repo / "node_modules" / ".fake" / "calls"
    return f.read_text().splitlines() if f.exists() else []


# 各ケースは (id, 説明, 準備, 引数, 期待)。期待のキー: rc・tests・passed・failed・passed_list・err_has・no_vitest_call
def s_none(repo: Path) -> None:
    write(repo, "src/other.ts", "export const x = 2\n")  # 実装だけ


def s_new_file_real(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/sort.new.test.ts", "case sorts needs src/sort.ts:NEW\n")


def s_new_file_shallow(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/sort.new.test.ts", "case sorts needs src/sort.ts:sortByPrice\n")


def s_modified_shallow(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\ncase sorts needs src/sort.ts:list\n")


def s_modified_real(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\ncase sorts needs src/sort.ts:NEW\n")


def s_new_helper(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/test/helper.ts", "export {}\n")
    write(repo, "src/sort.new.test.ts", "import src/test/helper.ts\ncase sorts needs src/sort.ts:sortByPrice\n")


def s_ignored_kinds(repo: Path) -> None:
    change_impl(repo)
    write(repo, "e2e/sort.spec.ts", "case e2e needs src/sort.ts:sortByPrice\n")
    write(repo, "src/sort.stories.tsx", "export {}\n")


def s_branch(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    change_impl(repo)
    write(repo, "src/sort.new.test.ts", "case committed-shallow needs src/sort.ts:sortByPrice\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "work")
    # 未コミットのテストは --worktree が無ければ対象にしない（未追跡と、HEAD にある既存のテストの変更）
    write(repo, "src/wt.test.ts", "case wt-shallow needs src/sort.ts:sortByPrice\n")
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\ncase wt-mod needs src/sort.ts:sortByPrice\n")
    # コミット済みのテストの未コミットの書き換えも、--worktree が無ければ流さない（HEAD の版を流す）
    write(repo, "src/sort.new.test.ts", "case committed-shallow needs src/sort.ts:sortByPrice\ncase wt-extra needs src/sort.ts:sortByPrice\n")


def s_branch_base_moves(repo: Path) -> None:
    s_branch(repo)
    # ベースが先に進んでも、merge-base を変える前のコードにする
    git(repo, "stash", "-u", "-q")
    git(repo, "checkout", "-q", "main")
    write(repo, "src/sort.ts", "export const renamedOnMain = list => list\n")
    git(repo, "commit", "-q", "-am", "main moves")
    git(repo, "checkout", "-q", "feature/x")
    git(repo, "stash", "pop", "-q")
    write(repo, "src/sort.new.test.ts", "case committed-shallow needs src/sort.ts:sortByPrice\n")


def s_failed_on_base_same_name(repo: Path) -> None:
    # ベースの版では落ちていた同名のテストを、変える前でも通る形に書き換える
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\ncase sorts needs src/sort.ts:NOPE\n")
    git(repo, "commit", "-q", "-am", "broken test on base")
    change_impl(repo)
    write(repo, "src/sort.test.ts", "case keeps-items needs src/sort.ts:sortByPrice\ncase sorts needs src/sort.ts:list\n")


def s_japanese_names(repo: Path) -> None:
    write(repo, "src/sort.test.ts", "case 件数を表示する needs src/sort.ts:sortByPrice\n")
    git(repo, "commit", "-q", "-am", "japanese")
    change_impl(repo)
    write(repo, "src/sort.test.ts", "case 件数を表示する needs src/sort.ts:sortByPrice\ncase 安い順に並べる needs src/sort.ts:list\n")


def s_extra_run(repo: Path) -> None:
    s_new_file_shallow(repo)
    # 渡していない既存のテストも流れる（部分一致のまね）。数えない
    (repo / "node_modules" / ".fake" / "extra").write_text("src/sort.test.ts\n")


def s_rename(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature/x")
    git(repo, "mv", "src/sort.test.ts", "src/sorting.test.ts")
    git(repo, "commit", "-q", "-m", "rename")


def s_newline_name(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/nl\nname.test.ts", "case newline needs src/sort.ts:sortByPrice\n")


def s_space_name(repo: Path) -> None:
    change_impl(repo)
    write(repo, "src/with space.test.ts", "case spaced needs src/sort.ts:sortByPrice\n")


CASES = [
    ("RB1", "テストが変わっていなければ vitest を呼ばない", s_none, [], {"rc": 0, "tests": 0, "no_vitest_call": True}),
    ("RB2", "新しいテストファイルが変える前に落ちれば報告しない", s_new_file_real, [], {"rc": 0, "tests": 1, "passed": 0, "failed": 1}),
    ("RB3", "新しいテストファイルが変える前でも通れば報告する", s_new_file_shallow, [],
     {"rc": 0, "tests": 1, "passed": 1, "failed": 0, "passed_list": ["src/sort.new.test.ts > sorts"]}),
    ("RB4", "変えたテストファイルは、前から通っていたテストを除いて報告する", s_modified_shallow, [],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/sort.test.ts > sorts"]}),
    ("RB5", "変えたテストファイルの新しいテストが変える前に落ちれば報告しない", s_modified_real, [], {"rc": 0, "tests": 1, "passed": 0, "failed": 1}),
    ("RB6", "ベースに無いファイルを import するテストは落ちたと数える", s_new_helper, [], {"rc": 0, "tests": 1, "passed": 0, "failed": 1}),
    ("RB7", "e2e/ の下とテスト以外のファイルは対象にしない", s_ignored_kinds, [], {"rc": 0, "tests": 0, "no_vitest_call": True}),
    ("RB8", "--base はコミット済みのテストだけ", s_branch, ["--base", "main"],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/sort.new.test.ts > committed-shallow"]}),
    ("RB9", "--base --worktree は未コミットと未追跡のテストも足す", s_branch, ["--base", "main", "--worktree"],
     {"rc": 0, "tests": 3, "passed": 4,
      "passed_list": ["src/sort.new.test.ts > committed-shallow", "src/sort.new.test.ts > wt-extra", "src/sort.test.ts > wt-mod",
                      "src/wt.test.ts > wt-shallow"]}),
    ("RB10", "ベースが先に進んでも merge-base のコードで流す", s_branch_base_moves, ["--base", "main"],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/sort.new.test.ts > committed-shallow"]}),
    ("RB11", "改名しただけのテストは、前から通っていたので報告しない", s_rename, ["--base", "main"], {"rc": 0, "tests": 1, "passed": 0, "failed": 0}),
    ("RB12", "空白を含む名前のテストファイル", s_space_name, [],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/with space.test.ts > spaced"]}),
    ("RB20", "改行を含む名前のテストファイルも数える", s_newline_name, [], {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["$'src/nl\\nname.test.ts' > newline"]}),
    ("RB21", "ベースで落ちていた同じ名前のテストは、前から通っていたとしない", s_failed_on_base_same_name, [],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/sort.test.ts > sorts"]}),
    ("RB23", "日本語の名前のテストも、前から通っていたものを除く", s_japanese_names, [],
     {"rc": 0, "tests": 1, "passed": 1, "passed_list": ["src/sort.test.ts > 安い順に並べる"]}),
    ("RB22", "渡していないのに流れたテストファイルは数えない", s_extra_run, [],
     {"rc": 0, "tests": 1, "passed": 1, "failed": 0, "passed_list": ["src/sort.new.test.ts > sorts"]}),
    ("RB13", "存在しないベースは 2", s_none, ["--base", "nope"], {"rc": 2, "err_has": "ベースが見つからない"}),
    ("RB14", "--worktree だけ（--base 無し）は 2", s_none, ["--worktree"], {"rc": 2}),
    ("RB15", "知らない引数は 2", s_none, ["--bogus"], {"rc": 2}),
]


def check(case_id: str, setup, args: list[str], expect: dict, tmp: Path) -> str | None:
    repo = make_repo(tmp)
    setup(repo)
    before = git(repo, "status", "--porcelain", "--untracked-files=all")
    head = git(repo, "rev-parse", "HEAD")
    tdir = tmp / "t"
    tdir.mkdir()
    rc, out, err = run(repo, *args, env={**GIT_ENV, "TMPDIR": str(tdir)})
    if rc != expect["rc"]:
        return f"rc={rc} (want {expect['rc']})\nstdout:\n{out}\nstderr:\n{err}"
    # 作業ツリーと HEAD を変えない・写しを残さない
    if git(repo, "status", "--porcelain", "--untracked-files=all") != before or git(repo, "rev-parse", "HEAD") != head:
        return f"作業ツリーか HEAD が変わった\nstatus:\n{git(repo, 'status', '--porcelain')}"
    if any(tdir.iterdir()):
        return f"一時ディレクトリが残った: {[p.name for p in tdir.iterdir()]}"
    if rc != 0:
        if not err.strip():
            return "失敗したのに stderr に理由が無い"
        if expect.get("err_has") and expect["err_has"] not in err:
            return f"stderr に {expect['err_has']!r} が無い\nstderr:\n{err}"
        return None
    if expect.get("no_vitest_call") and calls(repo):
        return f"vitest を呼んだ: {calls(repo)}"
    got = parse(out)
    for k, v in expect.items():
        if k in ("rc", "err_has", "no_vitest_call"):
            continue
        key = {"passed_list": "passed_list"}.get(k, k)
        if got.get(key) != v:
            return f"{k}={got.get(key)!r} (want {v!r})\nstdout:\n{out}\nstderr:\n{err}"
    # vitest はベースの写しの中で流す（作業ツリーでは流さない）
    for c in calls(repo):
        if c.split(" ", 1)[0] == str(repo) or c.split(" ", 1)[0] == os.path.realpath(repo):
            return f"作業ツリーで vitest を流した: {c}"
    return None


def check_special(tmp: Path) -> list[tuple[str, str, str | None]]:
    res = []

    # RB16: vitest が無ければ 2
    d = tmp / "rb16"
    d.mkdir()
    repo = make_repo(d, vitest=False)
    s_new_file_shallow(repo)
    rc, out, err = run(repo, env={**GIT_ENV, "TMPDIR": str(d)})
    res.append(("RB16", "vitest が無ければ 2", None if rc == 2 and "vitest" in err else f"rc={rc}\nstdout:\n{out}\nstderr:\n{err}"))

    # RB17: vitest が結果を返さなければ（設定のエラー）2
    d = tmp / "rb17"
    d.mkdir()
    repo = make_repo(d)
    s_new_file_shallow(repo)
    (repo / "node_modules" / ".fake" / "exit").write_text("1")
    tdir = d / "t"
    tdir.mkdir()
    rc, out, err = run(repo, env={**GIT_ENV, "TMPDIR": str(tdir)})
    problem = None
    if rc != 2 or "結果を返さなかった" not in err:
        problem = f"rc={rc}\nstdout:\n{out}\nstderr:\n{err}"
    elif "failed to load config" not in err:
        problem = f"vitest の出力の末尾が stderr に無い\nstderr:\n{err}"
    elif any(tdir.iterdir()):
        problem = "一時ディレクトリが残った"
    res.append(("RB17", "vitest が結果を返さなければ 2 で、出力の末尾を添える", problem))

    # RB18: 打ち切り。時間内に 2 で終わり、vitest を止める
    d = tmp / "rb18"
    d.mkdir()
    repo = make_repo(d)
    s_new_file_shallow(repo)
    (repo / "node_modules" / ".fake" / "sleep").write_text("30")
    tdir = d / "t"
    tdir.mkdir()
    t0 = time.monotonic()
    rc, out, err = run(repo, env={**GIT_ENV, "TMPDIR": str(tdir), "RUN_TESTS_ON_BASE_TIMEOUT": "2"}, timeout=40)
    took = time.monotonic() - t0
    problem = None
    if rc != 2 or "打ち切った" not in err:
        problem = f"rc={rc}\nstdout:\n{out}\nstderr:\n{err}"
    elif took > 15:
        problem = f"打ち切りに {took:.1f} 秒かかった"
    else:
        pid_f = repo / "node_modules" / ".fake" / "pid"
        if pid_f.exists():
            pid = int(pid_f.read_text())
            try:
                os.kill(pid, 0)
                problem = f"vitest（pid {pid}）が動いたまま"
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
        if not problem and any(tdir.iterdir()):
            problem = "一時ディレクトリが残った"
    res.append(("RB18", "打ち切ったら 2 で、vitest を止め、写しを消す", problem))

    # RB19: GIT に渡した git を使う（PATH の先頭の git が動かない環境）
    d = tmp / "rb19"
    d.mkdir()
    repo = make_repo(d)
    s_new_file_shallow(repo)
    real = shutil.which("git")
    log = d / "calls.log"
    wrapper = d / "mygit"
    wrapper.write_text(f'#!/bin/sh\necho x >> "{log}"\nexec "{real}" "$@"\n')
    wrapper.chmod(0o755)
    broken = d / "bin"
    broken.mkdir()
    (broken / "git").write_text("#!/bin/sh\necho broken >&2\nexit 72\n")
    (broken / "git").chmod(0o755)
    tdir = d / "t"
    tdir.mkdir()
    env = {**GIT_ENV, "PATH": f"{broken}:{GIT_ENV.get('PATH', '')}", "GIT": str(wrapper), "TMPDIR": str(tdir)}
    rc, out, err = run(repo, env=env)
    problem = None
    if rc != 0 or parse(out).get("passed") != 1:
        problem = f"rc={rc}\nstdout:\n{out}\nstderr:\n{err}"
    elif not log.exists():
        problem = "GIT に渡した git が呼ばれていない"
    else:
        env["GIT"] = str(d / "nope")
        rc, out, err = run(repo, env=env)
        if rc != 2 or "GIT=" not in err:
            problem = f"存在しない GIT で rc={rc} (want 2 と GIT=<パス> の案内)\nstderr:\n{err}"
    res.append(("RB19", "GIT に渡した git を使う", problem))
    return res


def main() -> int:
    failed = 0
    total = 0
    for case_id, desc, setup, args, expect in CASES:
        total += 1
        tmp = Path(tempfile.mkdtemp(prefix="run-tests-on-base-"))
        try:
            problem = check(case_id, setup, args, expect, tmp)
        except subprocess.TimeoutExpired:
            problem = "時間切れ"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if problem:
            failed += 1
            print(f"FAIL {case_id}: {desc}\n  " + problem.replace("\n", "\n  "))
        else:
            print(f"PASS {case_id}: {desc}")
    tmp = Path(tempfile.mkdtemp(prefix="run-tests-on-base-"))
    try:
        for case_id, desc, problem in check_special(tmp):
            total += 1
            if problem:
                failed += 1
                print(f"FAIL {case_id}: {desc}\n  " + problem.replace("\n", "\n  "))
            else:
                print(f"PASS {case_id}: {desc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
