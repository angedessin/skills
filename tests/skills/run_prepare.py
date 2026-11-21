"""eval/prepare.sh が、実行中の評価を見つけたら何も消さずに止まることを確かめる。

prepare.sh を一時ディレクトリに写し、偽の pgrep を PATH の先頭に置いて流す。gen_*_cases.py は写さないので、
止まらなかった場合は evals/ を消した後の python で失敗する（消したかどうかで、止まったかを見分ける）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPARE = ROOT / "eval" / "prepare.sh"
STOP_MSG = "実行中の claude plugin eval がある"


def setup(tmp: Path, pgrep_out: str | None) -> tuple[Path, dict]:
    work = tmp / "eval"
    (work / "evals" / "design").mkdir(parents=True)
    (work / "evals" / "design" / "keep").write_text("x")
    (work / "skills").mkdir()
    (work / "skills" / "keep").write_text("x")
    shutil.copy(PREPARE, work / "prepare.sh")
    env = {k: v for k, v in os.environ.items() if k != "PREPARE_FORCE"}
    if pgrep_out is not None:
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        body = f"printf '%s' '{pgrep_out}'\n" + ("exit 0\n" if pgrep_out else "exit 1\n")
        (bin_dir / "pgrep").write_text("#!/bin/sh\n" + body)
        (bin_dir / "pgrep").chmod(0o755)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return work, env


def run(work: Path, env: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(work / "prepare.sh"), "c", "design"], capture_output=True, text=True, env=env, check=False)


def kept(work: Path) -> bool:
    return (work / "evals" / "design" / "keep").exists() and (work / "skills" / "keep").exists()


def check_stops(tmp: Path) -> str | None:
    work, env = setup(tmp, "4242\n4343\n")
    p = run(work, env)
    if p.returncode != 1 or STOP_MSG not in p.stderr or "4242 4343" not in p.stderr:
        return f"exit {p.returncode}; stderr={p.stderr!r}"
    return None if kept(work) else "evals/ か skills/ を消した"


def check_force(tmp: Path) -> str | None:
    work, env = setup(tmp, "4242\n")
    env["PREPARE_FORCE"] = "1"
    p = run(work, env)
    if STOP_MSG in p.stderr:
        return f"PREPARE_FORCE=1 でも止まった; stderr={p.stderr!r}"
    return None if not (work / "evals" / "design" / "keep").exists() else "止まらずに進んでいない（evals/ が残った）"


def check_none_running(tmp: Path) -> str | None:
    work, env = setup(tmp, "")
    p = run(work, env)
    if STOP_MSG in p.stderr:
        return f"実行中の評価が無いのに止まった; stderr={p.stderr!r}"
    return None if not (work / "evals" / "design" / "keep").exists() else "止まらずに進んでいない（evals/ が残った）"


def main() -> int:
    checks = [
        ("PR1", "実行中の評価があれば、exit 1 で pid を出し、evals/ と skills/ に触らない", check_stops),
        ("PR2", "PREPARE_FORCE=1 なら止まらない", check_force),
        ("PR3", "実行中の評価が無ければ止まらない", check_none_running),
    ]
    failed = 0
    for cid, label, fn in checks:
        with tempfile.TemporaryDirectory(prefix="prepare-") as t:
            problem = fn(Path(t).resolve())
        print(f"{'FAIL' if problem else 'PASS'} {cid}: {label}")
        if problem:
            print(f"  {problem}")
            failed += 1
    print(f"prepare: {len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
