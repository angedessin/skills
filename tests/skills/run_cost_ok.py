#!/usr/bin/env python3
"""frontend-code-review の費用の停止を通す印（--cost-ok）が、スキルの本文と評価の依頼文で食い違っていないかを確かめる。
費用の目安が本文でなく references/cost.md にあることも確かめる。

gen_review_cases.py を一時ディレクトリに向けて流し、生成した prompt.md を見る。
大きい差分をレビューさせるケースには印があり、止まることを見るケースには無いこと。

Usage: mise exec -- pnpm run test:skills
Exit 0 = all pass. Exit 1 = failure.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARK = "--cost-ok"
SKILL = ROOT / ".claude" / "skills" / "frontend-code-review" / "SKILL.md"
COST = SKILL.parent / "references" / "cost.md"
GEN = ROOT / "eval" / "gen_review_cases.py"
WITH_MARK = ("r-a-hardening", "r-b-deploy-integrity", "f1-semicolon")
WITHOUT_MARK = ("l1-large-diff", "l2-phrase-not-enough")


def main() -> int:
    failures = []
    body = SKILL.read_text(encoding="utf-8")
    if MARK not in body:
        failures.append(f"SKILL.md に {MARK} が無い")
    if not COST.exists():
        failures.append("references/cost.md が無い（費用の目安の置き場）")
    if re.search(r"\d\s*ドル", body):
        failures.append("SKILL.md に金額がある（目安は references/cost.md に置く）")
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, "-I", str(GEN), tmp], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAIL gen_review_cases.py が失敗した: {r.stderr.strip()[-300:]}")
            return 1
        for cid, want in [(c, True) for c in WITH_MARK] + [(c, False) for c in WITHOUT_MARK]:
            prompt = Path(tmp) / "evals" / "review" / cid / "prompt.md"
            if not prompt.exists():
                failures.append(f"{cid}: prompt.md が生成されない")
            elif (MARK in prompt.read_text(encoding="utf-8")) != want:
                failures.append(f"{cid}: 印が{'無い' if want else 'ある'}")
    for f in failures:
        print(f"FAIL {f}")
    print("OK: 0 failed" if not failures else f"NG: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
