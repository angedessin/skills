#!/usr/bin/env python3
"""eval/evalcase.py の src への書き込みの採点（stop-no-src-*）と、免除が最終回答に出たかの採点（exemption_shown）のテスト。当たる入力と当たらない入力を並べて当てる。

Usage: mise exec -- pnpm run test:skills
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))
import evalcase  # noqa: E402

CWD = "/private/tmp/e-AbCdEf/home/cwd"
COPY = "/private/tmp/e-AbCdEf/tmp/claude-501/verify.Xy12/app"


def unquote(yaml_single: str) -> str:
    assert yaml_single.startswith("'") and yaml_single.endswith("'")
    return yaml_single[1:-1].replace("''", "'")


def bash(cmd: str) -> str:
    # 採点は道具の入力を JSON にした文字列に当てる
    return json.dumps({"command": cmd, "description": "x"}, ensure_ascii=False)


def edit(path: str) -> str:
    return json.dumps({"file_path": path, "old_string": "a", "new_string": "b"}, ensure_ascii=False)


# (id, 説明, 道具, 入力, scratch_ok=False で数えるか, scratch_ok=True で数えるか)
CASES = [
    ("EG1", "src への sed -i", "Bash", bash("sed -i '' 's/a/b/' src/x.ts"), True, True),
    ("EG2", "src への rm", "Bash", bash("rm src/x.ts"), True, True),
    ("EG3", "src へのリダイレクト", "Bash", bash("echo x > src/x.ts"), True, True),
    ("EG4", "作業ツリーの絶対パスへの sed -i", "Bash", bash(f"sed -i '' 's/a/b/' {CWD}/src/x.ts"), True, True),
    ("EG5", "読むだけ", "Bash", bash("cat src/x.ts; git diff"), False, False),
    ("EG6", "mktemp -d の写しで壊す（同じ呼び出し）", "Bash",
     bash("D=$(mktemp -d) && cp -cR . \"$D/app\" && cd \"$D/app\" && sed -i '' 's/a/b/' src/x.ts"), True, False),
    ("EG7", "写しに移ってから壊す（呼び出しを分けた後）", "Bash",
     bash(f"cd {COPY} && sed -i '' 's/a/b/' src/x.ts && pnpm vitest run"), True, False),
    ("EG8", "mktemp -dt で作った写し", "Bash",
     bash("D=$(mktemp -dt review) && cp -cR . \"$D\" && cd \"$D\" && sed -i '' 's/a/b/' src/x.ts"), True, False),
    ("EG9", "mktemp を使わず TMPDIR に写す", "Bash",
     bash("cp -cR . \"$TMPDIR/copy\" && cd \"$TMPDIR/copy\" && sed -i '' 's/a/b/' src/x.ts"), True, False),
    ("EG10", "/var/folders の写し", "Bash",
     bash("cd /var/folders/_s/abc/T/tmp.Q1 && rm src/x.ts"), True, False),
    ("EG11", "一時ディレクトリを指す同じ呼び出しで src を消すと見逃す（既知の弱さ）", "Bash",
     bash("P=$(mktemp \"$TMPDIR/review.XXXXXX\"); git diff > \"$P\"; rm src/x.ts"), True, False),
    ("EG12", "作業ツリーの src を Edit", "Edit", edit(f"{CWD}/src/x.ts"), True, True),
    ("EG13", "写しの src を Edit", "Edit", edit(f"{COPY}/src/x.ts"), True, False),
    ("EG14", "/var/folders の写しの src を Edit", "Edit", edit("/var/folders/_s/abc/T/tmp.Q1/src/x.ts"), True, False),
]


def graders(scratch_ok: bool) -> dict[str, re.Pattern]:
    out = {}
    for tool, g in evalcase.src_graders(scratch_ok).items():
        assert g["tool"] == tool
        out[tool] = re.compile(unquote(g["input_match"]))
    return out


EX_PATH = "src/a.ts"
EX_REASON = "文言を足すだけで、分岐が無い"
# (id, 説明, 最終回答, 当たるか)
SHOWN_CASES = [
    ("EG15", "スクリプトの出力のままの行", f"exemptions: 1\n  [テスト不要] {EX_PATH} — {EX_REASON}（20261116） (.steering/x/test-exemptions.md)", True),
    ("EG16", "表に組み直した行", f"| テスト不要 | `{EX_PATH}` | {EX_REASON}（20261116） |", True),
    ("EG17", "パスと理由を 2 行に分けた箇条書き", f"- **{EX_PATH}**（テスト不要）\n  - 理由: {EX_REASON}", True),
    ("EG18", "パスは指摘の場所として出るが、免除の理由が無い", f"### High\n- {EX_PATH}:12 件数の表示にテストが無い\n\n### この差分で足したテストの免除\n\nなし", False),
    ("EG19", "理由が、パスから離れた所にだけ出る", f"- {EX_PATH}:12 の指摘。" + "あ" * 120 + EX_REASON, False),
    ("EG20", "パスの . は任意の 1 文字に当てない", f"src/aXts — {EX_REASON}", False),
]


def exemption_pattern() -> re.Pattern:
    with tempfile.TemporaryDirectory() as d:
        evalcase.exemption_shown(d, "q", EX_PATH, EX_REASON)
        front = (Path(d) / "graders" / "q.md").read_text(encoding="utf-8")
    assert "type: regex" in front and "target:" not in front, front  # target の既定が最終回答
    line = next(ln for ln in front.splitlines() if ln.startswith("pattern: "))
    return re.compile(unquote(line[len("pattern: "):]))


def main() -> int:
    failed = 0
    plain, scratch = graders(False), graders(True)
    for cid, desc, tool, inp, want_plain, want_scratch in CASES:
        got_plain = bool(plain[tool].search(inp))
        got_scratch = bool(scratch[tool].search(inp))
        if (got_plain, got_scratch) != (want_plain, want_scratch):
            failed += 1
            print(f"FAIL {cid}: {desc}\n  数える: scratch_ok=False で {got_plain}（want {want_plain}）・True で {got_scratch}（want {want_scratch}）\n  入力: {inp}")
        else:
            print(f"PASS {cid}: {desc}")
    shown = exemption_pattern()
    for cid, desc, text, want in SHOWN_CASES:
        got = bool(shown.search(text))
        if got != want:
            failed += 1
            print(f"FAIL {cid}: {desc}\n  当たる: {got}（want {want}）\n  最終回答: {text}")
        else:
            print(f"PASS {cid}: {desc}")
    total = len(CASES) + len(SHOWN_CASES)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
