#!/usr/bin/env python3
"""Hook fixture runner — stdin JSON → hook → assert permissionDecision.

Usage: mise exec -- pnpm run test:hooks
       python3 tests/hooks/run_fixtures.py --hooks-dir <dir>   # 持ち出し先の hook 実体に同じケースを流す
Exit 0 = all pass. Exit 1 = failure (prints details).

hook の JSON 出力を手で確かめるときは `echo "$out"` を使わず `printf '%s' "$out"` を使う。
sh と zsh の echo は `\n` を展開するので、正しい JSON が壊れて見える（20261103 に macOS の sh・zsh で確認。bash は展開しない）。
検証が失敗したら、まず検証側を疑う。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"

# guard-gated-write.sh のヘッダにある対象パスの正本（1 行）。runner はここからケースを自動生成し、
# permissions.ask との一致は tests/sandbox/check_settings.py で検査する。
GATED_MARKER_RE = re.compile(r"^# GATED_PATHS:[ \t]*(.+)$", re.MULTILINE)
SKIP = "SKIP"  # 直接の検査が確かめられなかったときの印（problem の位置に置く）

# expect: "deny" | "ask" | "silence"
CASES: list[dict] = [
    # A — delete hook deny
    {"id": "A1", "hook": "guard-gated-delete.sh", "command": "rm -f docs/knowledge/x.md", "expect": "deny"},
    {"id": "A2", "hook": "guard-gated-delete.sh", "command": "rm ./CLAUDE.md", "expect": "deny"},
    {"id": "A3", "hook": "guard-gated-delete.sh", "command": "rm docs/knowledge/y.md", "expect": "deny"},
    {"id": "A4", "hook": "guard-gated-delete.sh", "command": "rm -R docs/knowledge/x", "expect": "deny"},
    {"id": "A5", "hook": "guard-gated-delete.sh", "command": "rm --recursive docs/knowledge/x", "expect": "deny"},
    {"id": "A6", "hook": "guard-gated-delete.sh", "command": "rm -f -r docs/knowledge/x", "expect": "deny"},
    {"id": "A7", "hook": "guard-gated-delete.sh", "command": "mv docs/knowledge/x.md /tmp/", "expect": "deny"},
    {"id": "A8", "hook": "guard-gated-delete.sh", "command": "mv a.md docs/knowledge/a.md", "expect": "deny"},
    # B — delete hook silence
    {"id": "B9", "hook": "guard-gated-delete.sh", "command": "rm /tmp/foo", "expect": "silence"},
    {"id": "B10", "hook": "guard-gated-delete.sh", "command": "rm README.md", "expect": "silence"},
    {"id": "B12", "hook": "guard-gated-delete.sh", "command": "bash -c 'rm docs/knowledge/x.md'", "expect": "silence"},
    {"id": "B13", "hook": "guard-gated-delete.sh", "command": "git rm docs/knowledge/x.md", "expect": "silence"},
    {"id": "A20", "hook": "guard-gated-delete.sh", "command": "cd docs/knowledge && rm x.md", "expect": "deny"},
    {"id": "A21", "hook": "guard-gated-delete.sh", "command": "/bin/rm docs/knowledge/x.md", "expect": "deny"},
    # 連鎖・代入前置・ラッパー・大文字小文字・docs/ の全体
    {"id": "A22", "hook": "guard-gated-delete.sh", "command": "FOO=1 rm docs/knowledge/x.md", "expect": "deny"},
    {"id": "A23", "hook": "guard-gated-delete.sh", "command": "env rm docs/knowledge/x.md", "expect": "deny"},
    {"id": "A24", "hook": "guard-gated-delete.sh", "command": "rm CLAUDE.MD", "expect": "deny"},
    {"id": "A25", "hook": "guard-gated-delete.sh", "command": "rm docs/decisions/y.md", "expect": "deny"},
    {"id": "A26", "hook": "guard-gated-delete.sh", "command": "true && rm CLAUDE.md", "expect": "deny"},
    {"id": "A27", "hook": "guard-gated-delete.sh", "command": "rm x; rm CLAUDE.md", "expect": "deny"},
    {"id": "A28", "hook": "guard-gated-delete.sh", "command": "mv docs/user-guide.md /tmp/x", "expect": "deny"},
    {"id": "A29", "hook": "guard-gated-delete.sh", "command": f"rm {shlex.quote(f'{ROOT}/docs/x.md')}", "expect": "deny"},
    {"id": "A30", "hook": "guard-gated-delete.sh", "command": "rm sub/CLAUDE.md", "expect": "deny"},
    {"id": "A31", "hook": "guard-gated-delete.sh", "command": "rm -- docs/x.md", "expect": "deny"},
    {"id": "A32", "hook": "guard-gated-delete.sh", "command": "cat <<'EOF' > /tmp/a\nit's\nEOF\nrm CLAUDE.md", "expect": "deny"},
    # プロジェクトの外のパスは止めない・cd を解決する
    {"id": "B34", "hook": "guard-gated-delete.sh", "command": "rm /tmp/x/docs/y.md", "expect": "silence"},
    {"id": "B35", "hook": "guard-gated-delete.sh", "command": "rm /tmp/x/docs/knowledge/y", "expect": "silence"},
    {"id": "B36", "hook": "guard-gated-delete.sh", "command": "rm /tmp/x/CLAUDE.md", "expect": "silence"},
    {"id": "B37", "hook": "guard-gated-delete.sh", "command": "cd /tmp/x && rm CLAUDE.md", "expect": "silence"},
    {"id": "B38", "hook": "guard-gated-delete.sh", "command": "rm docsy/x.md", "expect": "silence"},
    {"id": "B39", "hook": "guard-gated-delete.sh", "command": "rm ../docs/x.md", "expect": "silence"},
    # docs/ そのもの
    {"id": "A33", "hook": "guard-gated-delete.sh", "command": "rm -rf docs", "expect": "deny"},
    {"id": "A34", "hook": "guard-gated-delete.sh", "command": "rm -rf docs/", "expect": "deny"},
    {"id": "A35", "hook": "guard-gated-delete.sh", "command": "mv docs docs.bak", "expect": "deny"},
    {"id": "A36", "hook": "guard-gated-delete.sh", "command": "rm -rf docs/*", "expect": "deny"},
    {"id": "A37", "hook": "guard-gated-delete.sh", "command": "rm -rf docs*", "expect": "deny"},
    # コメントの後ろの行を見失わない（語の途中の # はコメントではない）
    {"id": "A38", "hook": "guard-gated-delete.sh", "command": "# 古いファイルを消す\nrm CLAUDE.md", "expect": "deny"},
    {"id": "A39", "hook": "guard-gated-delete.sh", "command": "ls # 確認\nrm -f docs/knowledge/x.md", "expect": "deny"},
    {"id": "A40", "hook": "guard-gated-delete.sh", "command": "[ $# -gt 0 ] && rm CLAUDE.md", "expect": "deny"},
    {"id": "A41", "hook": "guard-gated-delete.sh", "command": "curl https://x/#a && rm CLAUDE.md", "expect": "deny"},
    {"id": "A42", "hook": "guard-gated-delete.sh", "command": 'echo "#x" && rm CLAUDE.md', "expect": "deny"},
    {"id": "A59", "hook": "guard-gated-delete.sh", "command": 'echo "a #b" && rm CLAUDE.md', "expect": "deny"},
    {"id": "B44", "hook": "guard-gated-delete.sh", "command": "ls # rm CLAUDE.md", "expect": "silence"},
    # 記号の連なり・制御構文
    {"id": "A43", "hook": "guard-gated-delete.sh", "command": "x=$(pwd); rm CLAUDE.md", "expect": "deny"},
    {"id": "A44", "hook": "guard-gated-delete.sh", "command": "(make); rm docs/x.md", "expect": "deny"},
    {"id": "A45", "hook": "guard-gated-delete.sh", "command": "(true)&&rm CLAUDE.md", "expect": "deny"},
    {"id": "A46", "hook": "guard-gated-delete.sh", "command": "true &&(rm CLAUDE.md)", "expect": "deny"},
    {"id": "A47", "hook": "guard-gated-delete.sh", "command": "if [ -f CLAUDE.md ]; then rm CLAUDE.md; fi", "expect": "deny"},
    {"id": "A48", "hook": "guard-gated-delete.sh", "command": "for f in a; do rm docs/x.md; done", "expect": "deny"},
    {"id": "B45", "hook": "guard-gated-delete.sh", "command": "if cd /tmp/x; then\n  rm CLAUDE.md\nfi", "expect": "silence"},
    # 手前のグロブ・変数
    {"id": "A49", "hook": "guard-gated-delete.sh", "command": "rm -f */CLAUDE.md", "expect": "deny"},
    {"id": "A50", "hook": "guard-gated-delete.sh", "command": "rm -f packages/*/CLAUDE.md", "expect": "deny"},
    {"id": "A51", "hook": "guard-gated-delete.sh", "command": "rm {a,b}/CLAUDE.md", "expect": "deny"},
    {"id": "A52", "hook": "guard-gated-delete.sh", "command": "rm docs/knowledge/$name.md", "expect": "deny"},
    {"id": "A53", "hook": "guard-gated-delete.sh", "command": "rm docs/x-$(date +%F).md", "expect": "deny"},
    {"id": "A54", "hook": "guard-gated-delete.sh", "command": "rm docs/$f", "expect": "deny"},
    {"id": "B46", "hook": "guard-gated-delete.sh", "command": "rm /tmp/*/CLAUDE.md", "expect": "silence"},
    {"id": "B47", "hook": "guard-gated-delete.sh", "command": "rm -f docs-old*", "expect": "silence"},
    # サブシェルの cd は外に残らない
    {"id": "B48", "hook": "guard-gated-delete.sh", "command": "(cd docs && pnpm build) && rm -f out.txt", "expect": "silence"},
    {"id": "B49", "hook": "guard-gated-delete.sh", "command": "X=$(cd docs && pwd)\nrm out.txt", "expect": "silence"},
    {"id": "A55", "hook": "guard-gated-delete.sh", "command": "(cd /tmp/x && ls); rm CLAUDE.md", "expect": "deny"},
    {"id": "A56", "hook": "guard-gated-delete.sh", "command": "cd docs && cd knowledge && rm x.md", "expect": "deny"},
    {"id": "B50", "hook": "guard-gated-delete.sh", "command": "rm x < CLAUDE.md", "expect": "silence"},
    # ルートごと消す形（再帰のときだけ）
    {"id": "A60", "hook": "guard-gated-delete.sh", "command": "rm -rf .", "expect": "deny"},
    {"id": "A61", "hook": "guard-gated-delete.sh", "command": "rm -rf ./", "expect": "deny"},
    {"id": "A62", "hook": "guard-gated-delete.sh", "command": "rm -rf *", "expect": "deny"},
    {"id": "A63", "hook": "guard-gated-delete.sh", "command": "rm -rf ./*", "expect": "deny"},
    {"id": "A64", "hook": "guard-gated-delete.sh", "command": f"rm -r {shlex.quote(f'../{ROOT.name}')}", "expect": "deny"},
    {"id": "A65", "hook": "guard-gated-delete.sh", "command": "rm -rf ..", "expect": "deny"},
    {"id": "A66", "hook": "guard-gated-delete.sh", "command": "rm -R .", "expect": "deny"},
    {"id": "A67", "hook": "guard-gated-delete.sh", "command": "rm --recursive .", "expect": "deny"},
    {"id": "A68", "hook": "guard-gated-delete.sh", "command": "rm -rf ../*", "cwd": "tests", "expect": "deny"},
    {"id": "A70", "hook": "guard-gated-delete.sh", "command": "rm -rf */", "expect": "deny"},
    {"id": "A71", "hook": "guard-gated-delete.sh", "command": "rm -rf ./*/", "expect": "deny"},
    {"id": "A72", "hook": "guard-gated-delete.sh", "command": "rm -rf **", "expect": "deny"},
    {"id": "A73", "hook": "guard-gated-delete.sh", "command": "rm -rf ./**", "expect": "deny"},
    {"id": "B67", "hook": "guard-gated-delete.sh", "command": "rm -rf */", "cwd": "tests", "expect": "silence"},
        {"id": "B54", "hook": "guard-gated-delete.sh", "command": "rm -f *.log", "expect": "silence"},
    {"id": "B55", "hook": "guard-gated-delete.sh", "command": "rm -rf *.log", "expect": "silence"},
        {"id": "B57", "hook": "guard-gated-delete.sh", "command": "rm -rf *", "cwd": "tests", "expect": "silence"},
    {"id": "B58", "hook": "guard-gated-delete.sh", "command": "cd /tmp/x && rm -rf .", "expect": "silence"},
    {"id": "B59", "hook": "guard-gated-delete.sh", "command": "mv . /tmp/x", "expect": "silence"},
    {"id": "B60", "hook": "guard-gated-delete.sh", "command": "rm -rf sub", "expect": "silence", "note": "途中のディレクトリの下の CLAUDE.md は見ない（守らない形）"},
    {"id": "B61", "hook": "guard-gated-delete.sh", "command": "rm -rf $X", "expect": "silence"},
    # root と cwd（Claude Code の Bash は cwd が呼び出しをまたいで残る）
    {"id": "A57", "hook": "guard-gated-delete.sh", "command": "rm x.md", "cwd": "docs", "expect": "deny"},
    {"id": "A58", "hook": "guard-gated-delete.sh", "command": "rm ../CLAUDE.md", "cwd": "docs", "expect": "deny"},
    {"id": "A69", "hook": "guard-gated-delete.sh", "command": "rm x.md", "cwd": "docs", "project": None, "expect": "deny", "note": "CLAUDE_PROJECT_DIR が無ければ cwd の git のルートも見る"},
    {"id": "B51", "hook": "guard-gated-delete.sh", "command": "rm CLAUDE.md", "cwd": "/tmp", "project": None, "expect": "deny", "note": "git の外で CLAUDE_PROJECT_DIR も無ければ cwd をルートと見る"},
    # 守らない形（判定を増やさず、沈黙することをここで固定する。正本はこの一覧）
    {"id": "B40", "hook": "guard-gated-delete.sh", "command": "rm $X/CLAUDE.md", "expect": "silence"},
    {"id": "B42", "hook": "guard-gated-delete.sh", "command": "cd - && rm CLAUDE.md", "home": True, "expect": "silence", "note": "HOME がルートでも cd - の行き先は見ない"},
    {"id": "B43", "hook": "guard-gated-delete.sh", "command": "cat <<'EOF'\nrm CLAUDE.md\nEOF", "expect": "silence"},
    {"id": "B52", "hook": "guard-gated-delete.sh", "command": "cd $X && rm CLAUDE.md", "expect": "silence"},
    {"id": "B53", "hook": "guard-gated-delete.sh", "command": 'rm CLAUDE.md "', "expect": "silence", "note": "解析の失敗（シェルでも構文エラーになる形）"},
    {"id": "B62", "hook": "guard-gated-delete.sh", "command": 'rm -rf "$PWD"', "expect": "silence"},
    {"id": "B63", "hook": "guard-gated-delete.sh", "command": "rm -rf $PWD/*", "expect": "silence"},
    {"id": "B64", "hook": "guard-gated-delete.sh", "command": 'rm -rf "$(pwd)"', "expect": "silence"},
    {"id": "B65", "hook": "guard-gated-delete.sh", "command": "rm --recur .", "expect": "silence"},
    {"id": "B66", "hook": "guard-gated-delete.sh", "command": f"mv {shlex.quote(f'../{ROOT.name}')} /tmp/x", "expect": "silence"},
    # グロブとブレースは今あるファイルに対して展開する
    {"id": "A74", "hook": "guard-gated-delete.sh", "command": 'rm -f *', "expect": "deny"},
    {"id": "A75", "hook": "guard-gated-delete.sh", "command": 'rm -f */', "expect": "deny"},
    {"id": "A76", "hook": "guard-gated-delete.sh", "command": 'rm CLAUD*', "expect": "deny"},
    {"id": "A77", "hook": "guard-gated-delete.sh", "command": 'rm *.md', "expect": "deny"},
    {"id": "A78", "hook": "guard-gated-delete.sh", "command": 'mv *.md archive/', "expect": "deny"},
    {"id": "A79", "hook": "guard-gated-delete.sh", "command": 'mv * /tmp/x', "expect": "deny"},
    {"id": "A80", "hook": "guard-gated-delete.sh", "command": 'rm -rf */*', "expect": "deny"},
    {"id": "A81", "hook": "guard-gated-delete.sh", "command": 'rm -f {CLAUDE.md,README.md}', "expect": "deny"},
    {"id": "A82", "hook": "guard-gated-delete.sh", "command": 'rm {CLAUDE,README}.md', "expect": "deny"},
    {"id": "A83", "hook": "guard-gated-delete.sh", "command": 'rm {docs,src}/a.md', "expect": "deny"},
    {"id": "A84", "hook": "guard-gated-delete.sh", "command": 'rm -rf {docs,src}', "expect": "deny"},
    # 当たる候補が後ろにある形と 2 組の形（先頭だけ・1 組だけの展開では当たらない）
    {"id": "A112", "hook": "guard-gated-delete.sh", "command": 'rm {README.md,CLAUDE.md}', "expect": "deny"},
    {"id": "A113", "hook": "guard-gated-delete.sh", "command": 'rm {src,docs}/a.md', "expect": "deny"},
    {"id": "A114", "hook": "guard-gated-delete.sh", "command": 'rm {x,y}/{a,CLAUDE.md}', "expect": "deny"},
    # 連鎖の演算子
    {"id": "A85", "hook": "guard-gated-delete.sh", "command": 'false || rm CLAUDE.md', "expect": "deny"},
    {"id": "A86", "hook": "guard-gated-delete.sh", "command": 'ls |& rm CLAUDE.md', "expect": "deny"},
    {"id": "A87", "hook": "guard-gated-delete.sh", "command": 'sleep 1 & rm CLAUDE.md', "expect": "deny"},
    {"id": "A88", "hook": "guard-gated-delete.sh", "command": 'true ;; rm CLAUDE.md', "expect": "deny"},
    {"id": "A89", "hook": "guard-gated-delete.sh", "command": 'ls | rm CLAUDE.md', "expect": "deny"},
    # ラッパー
    {"id": "A90", "hook": "guard-gated-delete.sh", "command": 'timeout 5 rm CLAUDE.md', "expect": "deny"},
    {"id": "A91", "hook": "guard-gated-delete.sh", "command": 'time rm CLAUDE.md', "expect": "deny"},
    {"id": "A92", "hook": "guard-gated-delete.sh", "command": 'nice -n 5 rm CLAUDE.md', "expect": "deny"},
    {"id": "A93", "hook": "guard-gated-delete.sh", "command": 'nohup rm CLAUDE.md', "expect": "deny"},
    {"id": "A94", "hook": "guard-gated-delete.sh", "command": 'stdbuf -o0 rm CLAUDE.md', "expect": "deny"},
    {"id": "A95", "hook": "guard-gated-delete.sh", "command": 'command rm CLAUDE.md', "expect": "deny"},
    {"id": "A96", "hook": "guard-gated-delete.sh", "command": 'builtin rm CLAUDE.md', "expect": "deny"},
    {"id": "A97", "hook": "guard-gated-delete.sh", "command": 'noglob rm CLAUDE.md', "expect": "deny"},
    {"id": "A98", "hook": "guard-gated-delete.sh", "command": 'xargs rm CLAUDE.md', "expect": "deny"},
    {"id": "A99", "hook": "guard-gated-delete.sh", "command": 'exec rm CLAUDE.md', "expect": "deny"},
    {"id": "A100", "hook": "guard-gated-delete.sh", "command": 'sudo rm CLAUDE.md', "expect": "deny"},
    {"id": "A101", "hook": "guard-gated-delete.sh", "command": '{ rm CLAUDE.md; }', "expect": "deny"},
    {"id": "A102", "hook": "guard-gated-delete.sh", "command": '! rm CLAUDE.md', "expect": "deny"},
    # 制御語
    {"id": "A103", "hook": "guard-gated-delete.sh", "command": 'if rm CLAUDE.md; then ls; fi', "expect": "deny"},
    {"id": "A104", "hook": "guard-gated-delete.sh", "command": 'if ls; then ls; elif rm CLAUDE.md; then ls; fi', "expect": "deny"},
    {"id": "A105", "hook": "guard-gated-delete.sh", "command": 'if ls; then ls; else rm CLAUDE.md; fi', "expect": "deny"},
    {"id": "A106", "hook": "guard-gated-delete.sh", "command": 'while rm CLAUDE.md; do ls; done', "expect": "deny"},
    {"id": "A107", "hook": "guard-gated-delete.sh", "command": 'until rm CLAUDE.md; do ls; done', "expect": "deny"},
    # ヒアドキュメント
    {"id": "A108", "hook": "guard-gated-delete.sh", "command": "cat <<-END\nit's\n\tEND\nrm CLAUDE.md", "expect": "deny"},
    {"id": "A109", "hook": "guard-gated-delete.sh", "command": "cat <<A >/tmp/a; cat <<B >/tmp/b\nit's\nA\nit's\nB\nrm CLAUDE.md", "expect": "deny"},
    {"id": "B69", "hook": "guard-gated-delete.sh", "command": 'cat <<END\n  END\nrm CLAUDE.md\nEND', "expect": "silence"},
    {"id": "B81", "hook": "guard-gated-delete.sh", "command": 'cat <<END\n\tEND\nrm CLAUDE.md\nEND', "expect": "silence", "note": "タブを除くのは <<- だけ"},
    {"id": "A115", "hook": "guard-gated-delete.sh", "command": 'cat <<"EOF" > /tmp/a\nit\'s\nEOF\nrm CLAUDE.md', "expect": "deny"},
    # 入力のリダイレクトの先は消す対象ではない・ラッパーの値を取るオプション
    {"id": "B82", "hook": "guard-gated-delete.sh", "command": 'rm x <<< CLAUDE.md', "expect": "silence"},
    {"id": "B83", "hook": "guard-gated-delete.sh", "command": 'rm x <& CLAUDE.md', "expect": "silence"},
    {"id": "A116", "hook": "guard-gated-delete.sh", "command": 'sudo -g staff rm CLAUDE.md', "expect": "deny"},
    # 守らない形（レビューで見つけて、判定を増やさないと決めたもの）
    {"id": "B70", "hook": "guard-gated-delete.sh", "command": 'pushd docs && rm x.md', "expect": "silence"},
    {"id": "B71", "hook": "guard-gated-delete.sh", "command": 'xargs -I {} rm docs/{}', "expect": "silence"},
    {"id": "B72", "hook": "guard-gated-delete.sh", "command": 'timeout -s KILL 5 rm docs/a.md', "expect": "silence"},
    {"id": "B73", "hook": "guard-gated-delete.sh", "command": 'mv --target-directory=docs a.md', "expect": "silence"},
    {"id": "B74", "hook": "guard-gated-delete.sh", "command": "find docs -name '*.md' -delete", "expect": "silence"},
    {"id": "B75", "hook": "guard-gated-delete.sh", "command": 'unlink CLAUDE.md', "expect": "silence"},
    {"id": "B76", "hook": "guard-gated-delete.sh", "command": 'rmdir docs/x', "expect": "silence"},
    {"id": "B77", "hook": "guard-gated-delete.sh", "command": 'rm .claude/hooks/x', "expect": "silence"},
    {"id": "B78", "hook": "guard-gated-delete.sh", "command": 'mv .claude/a b', "expect": "silence"},
    # 誤検知として許容する形
    {"id": "A110", "hook": "guard-gated-delete.sh", "command": "pushd /tmp && rm docs/a.md", "expect": "deny", "note": "pushd を追わない"},
    # ルートの綴りの大文字小文字が違うと外と見る
    {"id": "B79", "hook": "guard-gated-delete.sh", "command": f"cd ../{shlex.quote(ROOT.name.upper())} && rm docs/a.md", "expect": "silence"},
    {"id": "B80", "hook": "guard-gated-delete.sh", "command": f"rm ../{shlex.quote(ROOT.name.upper())}/CLAUDE.md", "expect": "silence"},
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
    {"id": "B22", "hook": "guard-gated-delete.sh", "command": "rm -f docsy-archive*", "expect": "silence"},
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
    # cp の書き込み先・sed -i の対象（acceptEdits では通常の確認が出ないことがある）
    {"id": "W50", "hook": "guard-gated-write.sh", "command": 'cp /tmp/x CLAUDE.md', "expect": "ask"},
    {"id": "W51", "hook": "guard-gated-write.sh", "command": 'cp -f /tmp/x docs/', "expect": "ask"},
    {"id": "W52", "hook": "guard-gated-write.sh", "command": 'cp -t docs a.md', "expect": "ask"},
    {"id": "W53", "hook": "guard-gated-write.sh", "command": 'cp --target-directory=.claude/hooks a', "expect": "ask"},
    {"id": "W54", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ docs/x.md", "expect": "ask"},
    {"id": "W55", "hook": "guard-gated-write.sh", "command": 'sed -i.bak s/a/b/ CLAUDE.md', "expect": "ask"},
    {"id": "W56", "hook": "guard-gated-write.sh", "command": 'sed -Ei s/a/b/ .claude/settings.json', "expect": "ask"},
    {"id": "W57", "hook": "guard-gated-write.sh", "command": 'sed --in-place s/a/b/ CLAUDE.md', "expect": "ask"},
    {"id": "W58", "hook": "guard-gated-write.sh", "command": 'cp CLAUDE.md /tmp/x', "expect": "silence"},
    {"id": "W59", "hook": "guard-gated-write.sh", "command": 'cp docs/a.md /tmp/', "expect": "silence"},
    {"id": "W60", "hook": "guard-gated-write.sh", "command": 'sed -n 1p docs/x.md', "expect": "silence"},
    {"id": "W61", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ src/a.ts", "expect": "silence"},
    # リダイレクトの番号（`2>`）を書き込み先と取り違えない
    {"id": "W71", "hook": "guard-gated-write.sh", "command": 'cp /tmp/x CLAUDE.md 2>/dev/null', "expect": "ask"},
    {"id": "W72", "hook": "guard-gated-write.sh", "command": 'cp /tmp/x docs/a.md 2>&1', "expect": "ask"},
    {"id": "W73", "hook": "guard-gated-write.sh", "command": 'cp a CLAUDE.md 1>&2', "expect": "ask"},
    {"id": "W74", "hook": "guard-gated-write.sh", "command": 'cp a .claude/settings.json >/dev/null 2>&1', "expect": "ask"},
    {"id": "W75", "hook": "guard-gated-write.sh", "command": 'cp a /tmp/x 2>/dev/null', "expect": "silence"},
    # cp・sed -i の対象のグロブとブレースは、今あるファイルに対して展開する
    {"id": "W76", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ *.md", "expect": "ask"},
    {"id": "W77", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ CLAUD*", "expect": "ask"},
    {"id": "W78", "hook": "guard-gated-write.sh", "command": 'sed -i s/a/b/ {README,CLAUDE}.md', "expect": "ask"},
    {"id": "W79", "hook": "guard-gated-write.sh", "command": 'cp CLAUDE.md{.bak,}', "expect": "ask"},
    {"id": "W80", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ src/*.ts", "expect": "silence"},
    {"id": "W81", "hook": "guard-gated-write.sh", "command": 'cp {CLAUDE.md,/tmp/x}', "expect": "silence"},
    # sed と cp の別の書き方
    {"id": "W82", "hook": "guard-gated-write.sh", "command": "sed -I '' s/a/b/ CLAUDE.md", "expect": "ask"},
    {"id": "W83", "hook": "guard-gated-write.sh", "command": 'sed --in-place=.bak s/a/b/ CLAUDE.md', "expect": "ask"},
    {"id": "W84", "hook": "guard-gated-write.sh", "command": 'cp -tdocs a.md', "expect": "ask"},
    {"id": "W85", "hook": "guard-gated-write.sh", "command": 'cp -rt docs a.md', "expect": "ask"},
    {"id": "W86", "hook": "guard-gated-write.sh", "command": 'cp --target-directory docs a.md', "expect": "ask"},
    # リダイレクトと tee の先のグロブも展開する
    {"id": "W88", "hook": "guard-gated-write.sh", "command": 'echo x > CLAUD*', "expect": "ask"},
    {"id": "W89", "hook": "guard-gated-write.sh", "command": 'echo x > [C]LAUDE.md', "expect": "ask"},
    {"id": "W90", "hook": "guard-gated-write.sh", "command": 'echo x >> doc?/user-guide.md', "expect": "ask"},
    {"id": "W91", "hook": "guard-gated-write.sh", "command": 'echo x | tee *.md', "expect": "ask"},
    {"id": "W92", "hook": "guard-gated-write.sh", "command": 'echo x | tee CLAUD*', "expect": "ask"},
    {"id": "W93", "hook": "guard-gated-write.sh", "command": 'echo x | tee READM*', "expect": "silence"},
    {"id": "W94", "hook": "guard-gated-write.sh", "command": 'echo x > src/*.ts', "expect": "silence"},
    # 入力の cwd から、プロジェクトのルートからのパスに直して見る
    {"id": "W95", "hook": "guard-gated-write.sh", "command": 'cp a user-guide.md', "cwd": "docs", "expect": "ask"},
    {"id": "W96", "hook": "guard-gated-write.sh", "command": 'sed -i s/a/b/ *.md', "cwd": "docs", "expect": "ask"},
    {"id": "W97", "hook": "guard-gated-write.sh", "command": 'echo x > user-guide.md', "cwd": "docs", "expect": "ask"},
    {"id": "W98", "hook": "guard-gated-write.sh", "command": 'echo x > a', "cwd": ".claude/hooks", "expect": "ask"},
    {"id": "W99", "hook": "guard-gated-write.sh", "command": 'echo x > a.txt', "cwd": "tests", "expect": "silence"},
    {"id": "W100", "hook": "guard-gated-write.sh", "command": 'ls > ../README.md', "cwd": "docs", "expect": "silence"},
    # sed のスクリプトと -e・-f の値はファイルとして見ない（cwd が docs/ でも docs/1d と読まない）
    {"id": "W101", "hook": "guard-gated-write.sh", "command": 'sed -i 1d /tmp/x', "cwd": "docs", "expect": "silence"},
    {"id": "W102", "hook": "guard-gated-write.sh", "command": 'sed -i s/a/b/ /tmp/x', "cwd": "docs", "expect": "silence"},
    {"id": "W103", "hook": "guard-gated-write.sh", "command": 'sed -i s/a/b/ ../src/a.ts', "cwd": "docs", "expect": "silence"},
    {"id": "W104", "hook": "guard-gated-write.sh", "command": 'sed -i -e 1d -- /tmp/x', "cwd": "docs", "expect": "silence"},
    {"id": "W105", "hook": "guard-gated-write.sh", "command": "sed -i '' -e 1d -f x.sed /tmp/x", "cwd": "docs", "expect": "silence"},
    {"id": "W106", "hook": "guard-gated-write.sh", "command": 'sed -ni -e1d --expression=2d /tmp/x', "cwd": "docs", "expect": "silence"},
    {"id": "W113", "hook": "guard-gated-write.sh", "command": 'sed -i --expression 1d /tmp/x', "cwd": "docs", "expect": "silence"},
    {"id": "W114", "hook": "guard-gated-write.sh", "command": 'sed -i.bef 1d /tmp/x', "cwd": "docs", "expect": "silence", "note": "-i の後ろの e・f は拡張子"},
    {"id": "W115", "hook": "guard-gated-write.sh", "command": "sed -i '' 1d /tmp/x", "cwd": "docs", "expect": "silence", "note": "BSD の -i '' の空の拡張子"},
    # スクリプトを外しても、対象のファイルは見る
    {"id": "W107", "hook": "guard-gated-write.sh", "command": 'sed -i -e 1d CLAUDE.md', "expect": "ask"},
    {"id": "W108", "hook": "guard-gated-write.sh", "command": 'sed -i -f x.sed docs/x.md', "expect": "ask"},
    {"id": "W109", "hook": "guard-gated-write.sh", "command": 'sed -i -ne 1d -- CLAUDE.md', "expect": "ask"},
    {"id": "W110", "hook": "guard-gated-write.sh", "command": 'sed --expression 1d -i docs/x.md', "expect": "ask"},
    {"id": "W111", "hook": "guard-gated-write.sh", "command": 'sed -i.bef 1d CLAUDE.md', "expect": "ask", "note": "-i の後ろの e・f は拡張子"},
    {"id": "W112", "hook": "guard-gated-write.sh", "command": 'sed -i 1d a.md', "cwd": "docs", "expect": "ask"},
    # 展開が上限を超えたら判定せずに倒す
    {"id": "W87", "hook": "guard-gated-write.sh", "command": "cp a " + "{a,b}" * 20, "expect": "ask"},
    {"id": "A111", "hook": "guard-gated-delete.sh", "command": "rm " + "{a,b}" * 20, "expect": "deny"},
    # リダイレクトの種類
    {"id": "W62", "hook": "guard-gated-write.sh", "command": 'ls >& CLAUDE.md', "expect": "ask"},
    {"id": "W63", "hook": "guard-gated-write.sh", "command": 'ls >| CLAUDE.md', "expect": "ask"},
    {"id": "W64", "hook": "guard-gated-write.sh", "command": 'ls &>> CLAUDE.md', "expect": "ask"},
    # 誤検知として許容する形（代償は確認 1 回）
    {"id": "W65", "hook": "guard-gated-write.sh", "command": 'grep ">" docs/guide.md', "expect": "ask"},
    {"id": "W66", "hook": "guard-gated-write.sh", "command": 'echo x > .claude/worktrees/x/src/a.txt', "expect": "ask"},
    # 守らない形（default モードでは通常の確認に落ちる。acceptEdits では作業ディレクトリの中の cp・sed・リダイレクトが
    # 確認なしで通りうる（README の「hook と設定」）。cd と連鎖した形の実機の挙動は確かめていない）
    # 入力の cwd は解決する（W95〜W100）が、同じ呼び出しの中の cd は追わない
    {"id": "W67", "hook": "guard-gated-write.sh", "command": 'cd docs && echo x > a.md', "expect": "silence"},
    {"id": "W68", "hook": "guard-gated-write.sh", "command": 'echo x > $F', "expect": "silence"},
    {"id": "W69", "hook": "guard-gated-write.sh", "command": "bash -c 'echo x > CLAUDE.md'", "expect": "silence"},
    {"id": "W70", "hook": "guard-gated-write.sh", "command": 'python3 -c \'open("CLAUDE.md", "w")\'', "expect": "silence"},
    # W41-W44 — ヒアドキュメントの本文は見ない（アポストロフィがあっても shlex が失敗して縮退しない）
    {"id": "W41", "hook": "guard-gated-write.sh", "command": "cat <<'EOF' > /tmp/out.txt\nit's in docs/readme\nEOF", "expect": "silence"},
    {"id": "W42", "hook": "guard-gated-write.sh", "command": "cat <<EOF\necho x > CLAUDE.md\nEOF", "expect": "silence"},
    {"id": "W43", "hook": "guard-gated-write.sh", "command": "cat <<'EOF' > CLAUDE.md\nit's\nEOF", "expect": "ask"},
    {"id": "W44", "hook": "guard-gated-write.sh", "command": 'echo "a << b"\necho x > CLAUDE.md', "expect": "ask"},
    {"id": "W45", "hook": "guard-gated-write.sh", "command": "# c\necho x > CLAUDE.md", "expect": "ask"},
    {"id": "W46", "hook": "guard-gated-write.sh", "command": 'git commit -m "#1" > CLAUDE.md', "expect": "ask"},
    {"id": "W49", "hook": "guard-gated-write.sh", "command": 'git commit -m "a #1" > CLAUDE.md', "expect": "ask"},
    {"id": "W47", "hook": "guard-gated-write.sh", "command": "x=$(pwd); echo y > CLAUDE.md", "expect": "ask"},
    {"id": "W48", "hook": "guard-gated-write.sh", "command": "if true; then echo y | tee CLAUDE.md; fi", "expect": "ask"},
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
    # WP — python3 が無い環境では全文 grep（CLAUDE.md と docs/）に縮退する。完全な沈黙にはしない
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
    {"id": "WP7", "hook": "guard-gated-write.sh", "command": "cp /tmp/x CLAUDE.md", "expect": "silence", "no_python": True, "note": "縮退経路は cp を見ない（W50 と対）"},
    {"id": "WP8", "hook": "guard-gated-write.sh", "command": "sed -i '' s/a/b/ docs/x.md", "expect": "silence", "no_python": True, "note": "縮退経路は sed -i を見ない（W54 と対）"},
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


def base_payload(command: str | None, cwd: Path = ROOT) -> dict:
    p: dict = {
        "session_id": "fixture",
        "transcript_path": "/tmp/claude/transcripts/fixture.jsonl",
        "cwd": str(cwd),
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


def link_cases(tmp: Path) -> list[dict]:
    """シンボリックリンクはリンク自体の場所で判定する。tmp の中に小さなプロジェクトを作って確かめる。"""
    project = tmp / "links"
    outside = tmp / "outside-link"
    (project / "docs").mkdir(parents=True)
    (project / "node_modules" / "@acme").mkdir(parents=True)
    (project / "AGENTS.md").write_text("x")
    (project / "CLAUDE.md").symlink_to("AGENTS.md")
    (project / "docs" / "x.md").write_text("x")
    (project / "sub").mkdir()
    (project / "sub" / "CLAUDE.md").write_text("x")
    (project / "docs" / "link.md").symlink_to("/tmp/foo")
    (project / "node_modules" / "@acme" / "docs").symlink_to("../../docs")
    (project / "guide.md").symlink_to("CLAUDE.md")
    (project / "node_modules" / "@acme" / "self").symlink_to("../..")
    (project / "current").symlink_to(".")
    outside.symlink_to(project / "docs" / "x.md")
    outside_root = tmp / "outside-root"
    outside_root.symlink_to(project)
    # docs/ そのものがリンクのプロジェクト（リンク自体も、たどった先の中身も docs/ として止める）
    linked = tmp / "linked-docs"
    linked.mkdir()
    (tmp / "docs-real").mkdir()
    (linked / "docs").symlink_to(tmp / "docs-real")
    base = {"hook": "guard-gated-delete.sh", "cwd": str(project), "project": str(project)}
    linked_base = {"hook": "guard-gated-delete.sh", "cwd": str(linked), "project": str(linked)}
    return [
        {**base, "id": "L1", "command": "rm CLAUDE.md", "expect": "deny"},
        {**base, "id": "L2", "command": "rm docs/link.md", "expect": "deny"},
        {**base, "id": "L3", "command": "rm node_modules/@acme/docs", "expect": "silence"},
        {**base, "id": "L4", "command": "rm guide.md", "expect": "silence"},
        {**base, "id": "L5", "command": f"rm {shlex.quote(str(outside))}", "expect": "silence"},
        # ルートを指すリンクは、リンク自体を消すだけなら止めない
        {**base, "id": "L6", "command": "rm -rf node_modules/@acme/self", "expect": "silence"},
        {**base, "id": "L7", "command": "rm -r current", "expect": "silence"},
        {**base, "id": "L8", "command": f"rm -r {shlex.quote(str(outside_root))}", "expect": "silence"},
        # 末尾の / はリンクをたどる（リンクを残してリンク先の中身を消す）
        {**base, "id": "L9", "command": "rm -rf current/", "expect": "deny"},
        {**base, "id": "L10", "command": "rm -rf current/*", "expect": "deny"},
        {**base, "id": "L11", "command": "rm -rf node_modules/@acme/docs/", "expect": "deny"},
        {**base, "id": "L12", "command": "rm -rf node_modules/@acme/docs/*", "expect": "deny"},
        {**linked_base, "id": "L13", "command": "rm docs", "expect": "deny"},
        {**linked_base, "id": "L14", "command": "rm -rf docs/", "expect": "deny"},
        {**base, "id": "L15", "command": "rm sub/*", "expect": "deny"},
        {**base, "id": "L16", "command": "rm sub/*.log", "expect": "silence"},
    ]


def glob_cases(tmp: Path) -> list[dict]:
    """グロブの展開を、中身を決めた tmp のプロジェクトで確かめる（実リポジトリのファイルの有無に左右されない）。"""
    deep = tmp / "glob-deep"
    for f in ("CLAUDE.md", "docs/guide/a.md", "sub/a/b/CLAUDE.md", "src/x.md"):
        (deep / f).parent.mkdir(parents=True, exist_ok=True)
        (deep / f).write_text("x")
    many = deep / "many"
    many.mkdir()
    for i in range(5001):
        (many / f"{i}.log").write_text("")
    base = {"hook": "guard-gated-delete.sh", "cwd": str(deep), "project": str(deep)}
    # CLAUDE.md も docs/ も無いプロジェクト（ルートごと消す形は、展開の当たりでなく形で止める）
    bare = tmp / "glob-bare"
    (bare / "src").mkdir(parents=True)
    (bare / "src" / "a.ts").write_text("x")
    bare_base = {"hook": "guard-gated-delete.sh", "cwd": str(bare), "project": str(bare)}
    # パスにグロブの記号を含むプロジェクト
    bracket = tmp / "glob[1]"
    bracket.mkdir()
    (bracket / "CLAUDE.md").write_text("x")
    bracket_base = {"hook": "guard-gated-delete.sh", "cwd": str(bracket), "project": str(bracket)}
    # cp の最後の引数のグロブは、シェルの並び順に頼らず当たりのすべてを見る（zsh は a.md CLAUDE.md の順）
    order = tmp / "glob-order"
    for f in ("a.md", "CLAUDE.md", "src/a.ts", "src/b.ts"):
        (order / f).parent.mkdir(parents=True, exist_ok=True)
        (order / f).write_text("x")
    order_base = {"hook": "guard-gated-write.sh", "cwd": str(order), "project": str(order)}
    # 承認制のパスがどの並び順でも先頭に来る構成（最後の当たりだけを見る実装は当たらない）
    first = tmp / "glob-first"
    first.mkdir()
    for f in ("CLAUDE.md", "n99.md"):  # n99 は APFS の走査でも CLAUDE.md の後ろに来る
        (first / f).write_text("x")
    first_base = {"hook": "guard-gated-write.sh", "cwd": str(first), "project": str(first)}
    return [
        {**order_base, "id": "GL12", "command": "cp *.md", "expect": "ask"},
        {**first_base, "id": "GL14", "command": "cp *.md", "expect": "ask"},
        {**order_base, "id": "GL13", "command": "cp src/*.ts", "expect": "silence"},
        {**bare_base, "id": "GL6", "command": "rm -rf *", "expect": "deny"},
        {**bare_base, "id": "GL7", "command": "rm -rf ./*", "expect": "deny"},
        {**bare_base, "id": "GL8", "command": "rm -rf */", "expect": "deny"},
        {**bare_base, "id": "GL9", "command": "rm -rf **", "expect": "deny"},
        {**bare_base, "id": "GL10", "command": "rm -rf src/*", "expect": "silence"},
        {**bracket_base, "id": "GL11", "command": "rm *.md", "expect": "deny"},
        # `**` は zsh と同じく再帰する
        {**base, "id": "GL1", "command": "rm -f **/*.md", "expect": "deny"},
        {**base, "id": "GL2", "command": "rm sub/**/*.md", "expect": "deny"},
        {**base, "id": "GL3", "command": "rm src/**/*.md", "expect": "silence"},
        # 当たりが上限を超えたら判定せずに deny
        {**base, "id": "GL4", "command": "rm many/*.log", "expect": "deny"},
        {**base, "id": "GL5", "command": "rm many/1*.log", "expect": "silence"},
    ]


def worktree_cases(tmp: Path) -> list[dict]:
    """worktree に入っても CLAUDE_PROJECT_DIR は開始時の場所のまま。本物の worktree を作って確かめる。"""

    def git(*args: str, cwd: Path) -> None:
        subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.com", "-c", "commit.gpgsign=false", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
        )

    main = tmp / "wt-main"
    other = tmp / "wt-other"
    for repo in (main, other):
        (repo / "docs").mkdir(parents=True)
        (repo / "docs" / "a.md").write_text("x")
        git("init", "-q", cwd=repo)
        git("add", ".", cwd=repo)
        git("commit", "-qm", "x", cwd=repo)
    inner = main / ".claude" / "worktrees" / "x"
    outer = tmp / "wt-outer"
    git("worktree", "add", "-q", str(inner), "-b", "inner", cwd=main)
    git("worktree", "add", "-q", str(outer), "-b", "outer", cwd=main)
    app = main / "packages" / "app"
    app.mkdir(parents=True)
    site = main / "docs" / "site"
    site.mkdir()
    site_base = {"hook": "guard-gated-delete.sh", "project": str(site), "cwd": str(site)}
    quoted_main, quoted_outer, quoted_other, quoted_tmp = (shlex.quote(str(p)) for p in (main, outer, other, tmp))
    base = {"hook": "guard-gated-delete.sh", "project": str(main)}
    app_base = {"hook": "guard-gated-delete.sh", "project": str(app), "cwd": str(app)}
    return [
        # 同じ呼び出しの cd で worktree に移る
        {**base, "id": "T11", "cwd": str(main), "command": "cd .claude/worktrees/x && rm docs/a.md", "expect": "deny"},
        {**base, "id": "T12", "cwd": str(main), "command": f"cd {quoted_outer} && rm docs/a.md", "expect": "deny"},
        {**base, "id": "T13", "cwd": str(main), "command": f"cd {quoted_outer} && rm CLAUDE.md", "expect": "deny"},
        {**base, "id": "T14", "cwd": str(main), "command": f"cd {quoted_outer} && rm -rf .", "expect": "deny"},
        {**base, "id": "T15", "cwd": str(main), "command": f"cd {quoted_other} && rm docs/a.md", "expect": "silence"},
        {**base, "id": "T16", "cwd": str(outer), "command": f"cd {quoted_tmp} && rm {quoted_outer}/docs/a.md", "expect": "deny"},
        # 守らない形: 本体にいて、別の worktree をパスで直接指す
        {**base, "id": "T17", "cwd": str(main), "command": f"rm {quoted_outer}/docs/a.md", "expect": "silence"},
        {**base, "id": "T18", "cwd": str(main), "command": f"rm {quoted_outer}/CLAUDE.md", "expect": "silence"},
        {**base, "id": "T19", "cwd": str(main), "command": "rm .claude/worktrees/x/docs/a.md", "expect": "silence"},
        # プロジェクトがリポジトリの一部なら、同じリポジトリの中は止める
        {**app_base, "id": "M1", "command": "rm ../../docs/a.md", "expect": "deny"},
        {**app_base, "id": "M2", "command": "rm ../../CLAUDE.md", "expect": "deny"},
        {**app_base, "id": "M3", "command": "rm ../other/CLAUDE.md", "expect": "deny"},
        {**app_base, "id": "M4", "command": "rm -rf ../..", "expect": "deny"},
        {**app_base, "id": "M5", "command": "rm ../other/x.md", "expect": "silence"},
        {**app_base, "id": "M6", "command": "rm /tmp/x/CLAUDE.md", "expect": "silence"},
        # プロジェクトが親リポジトリの docs/ の下にあっても、プロジェクトの中は自分のルートから見る
        {**site_base, "id": "S1", "command": "rm tmp.txt", "expect": "silence"},
        {**site_base, "id": "S2", "command": "rm dist/a.js", "expect": "silence"},
        {**site_base, "id": "S3", "command": "rm docs/x.md", "expect": "deny"},
        {**site_base, "id": "S4", "command": "rm ../x.md", "expect": "deny"},
        {**base, "id": "T1", "cwd": str(inner), "command": "rm docs/a.md", "expect": "deny"},
        {**base, "id": "T2", "cwd": str(inner), "command": "rm CLAUDE.md", "expect": "deny"},
        {**base, "id": "T3", "cwd": str(outer), "command": "rm docs/a.md", "expect": "deny"},
        {**base, "id": "T4", "cwd": str(outer), "command": "rm CLAUDE.md", "expect": "deny"},
        {**base, "id": "T5", "cwd": str(inner / "docs"), "command": "rm a.md", "expect": "deny"},
        {**base, "id": "T6", "cwd": str(outer), "command": f"rm {quoted_main}/docs/a.md", "expect": "deny"},
        {**base, "id": "T7", "cwd": str(outer), "command": "rm -rf .", "expect": "deny"},
        {**base, "id": "T8", "cwd": str(outer), "command": "rm src/a.md", "expect": "silence"},
        # 別のリポジトリにいるときは止めない
        {**base, "id": "T9", "cwd": str(other), "command": "rm docs/a.md", "expect": "silence"},
        {**base, "id": "T10", "cwd": str(tmp), "command": "rm docs/a.md", "expect": "silence"},
    ]


def run_hook(hook: Path, raw: str, project: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    return subprocess.run(["bash", str(hook)], input=raw, capture_output=True, text=True, cwd=str(project), env=env, check=False)


def check_gated_direct(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    """guard_gated.py を直接呼ぶ。hook を通すと、解析の失敗と縮退の grep の答えを区別できない。"""
    script, hook = hooks_dir / "guard_gated.py", hooks_dir / "guard-gated-write.sh"
    cases = [
        ("write", "echo x > CLAUDE.md", 0, "ASK"),
        ("write", "ls", 0, "SILENT"),
        ("write", 'echo x > CLAUDE.md "', 3, ""),
        ("write", "echo $'a\\'b' > CLAUDE.md", 3, ""),
        ("delete", "rm CLAUDE.md", 0, "DENY"),
        ("delete", 'rm CLAUDE.md "', 3, ""),
    ]
    out = []
    for i, (mode, command, code, want) in enumerate(cases, 1):
        args = ["python3", str(script), mode] + ([str(hook)] if mode == "write" else [])
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}  # run_case と同じく継承しない
        p = subprocess.run(args, input=json.dumps(base_payload(command)), capture_output=True, text=True, cwd=str(ROOT), env=env, check=False)
        ok = p.returncode == code and p.stdout.strip() == want
        out.append((f"P{i}", f"guard_gated.py {mode}: {command}", None if ok else f"exit {p.returncode}; stdout={p.stdout!r}; 期待 exit {code} {want!r}"))
    return out


def check_session_start(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    hook = hooks_dir / "session-start-check.sh"
    project = tmp / "session-start"
    out = []

    def expect_empty(cid: str, label: str) -> None:
        p = run_hook(hook, "", project)
        out.append((cid, label, None if p.returncode == 0 and not p.stdout else f"exit {p.returncode}; stdout={p.stdout!r}"))

    project.mkdir()
    expect_empty("SS1", ".steering/ が無ければ何も出さない")
    (project / ".steering" / "archived" / "old").mkdir(parents=True)
    expect_empty("SS2", "archived だけなら何も出さない")
    names = ['2026-a"b', "2026-c\\x", "2026-d"]
    for name in names:
        (project / ".steering" / name).mkdir()
    p = run_hook(hook, "", project)
    try:
        context = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
        bad = None if all(n in context for n in names) and "archived" not in context else f"context={context!r}"
    except (json.JSONDecodeError, KeyError) as e:
        bad = f"{type(e).__name__}; stdout={p.stdout!r}"
    out.append(("SS3", "タスク名の引用符と \\ でも JSON が壊れず、archived を含まない", bad))
    return out


def check_validate_skill_edit(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    hook = hooks_dir / "validate-skill-edit.sh"
    if not hook.is_file():  # マスター専用
        return [("VS", "validate-skill-edit.sh が無い", SKIP)]
    if not shutil.which("jq"):  # jq が無ければ hook は素通しするので、確かめられない
        return [("VS", "jq が無い", SKIP)]
    project = tmp / "skill-edit"
    skill = project / ".claude" / "skills" / "x" / "SKILL.md"
    other = project / "src" / "a.md"
    for f in (skill, other, project / "templates" / "SKILL.template.md"):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
    validator = project / "scripts" / "validate_skills.py"
    validator.parent.mkdir()
    out = []
    template = project / "templates" / "SKILL.template.md"
    cases = [
        ("VS1", "SKILL.md は --skill でディレクトリを渡し、違反は exit 2 で差し戻す", skill, "sys.exit(1)", 2, f"--skill {skill.parent}"),
        ("VS2", "雛形は --template でファイルを渡し、違反は exit 2 で差し戻す", template, "sys.exit(1)", 2, f"--template {template}"),
        ("VS3", "違反が無ければ exit 0", skill, "sys.exit(0)", 0, ""),
        ("VS4", "対象外のファイルは検証しない", other, "sys.exit(1)", 0, ""),
    ]
    for cid, label, path, body, code, args in cases:
        # スタブは受け取った引数を出す
        validator.write_text(f"import sys\nprint('violation', ' '.join(sys.argv[1:]))\n{body}\n")
        p = run_hook(hook, json.dumps({"tool_input": {"file_path": str(path)}}), project)
        ok = p.returncode == code and (code == 0 or f"violation {args}" in p.stderr)
        out.append((cid, label, None if ok else f"exit {p.returncode}; stderr={p.stderr!r}"))
    return out


def check_typecheck(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    """stop-typecheck.sh を偽の tsc で流す。状態はケースの間で持ち越す（順番に意味がある）。"""
    hook = hooks_dir / "stop-typecheck.sh"
    if not shutil.which("jq"):  # jq が無ければ hook は素通しするので、確かめられない
        return [("TC", "jq が無い", SKIP)]
    project = tmp / "typecheck"
    tsc = project / "node_modules" / ".bin" / "tsc"
    tsc.parent.mkdir(parents=True)
    (project / "tsconfig.json").write_text("{}")
    errors = project / "errors.txt"  # 偽の tsc は、このファイルの中身を出して失敗する。無ければ成功する
    tsc.write_text(f'#!/bin/bash\n[ -f "{errors}" ] || exit 0\ncat "{errors}"\nexit 2\n')
    tsc.chmod(0o755)
    state = tmp / "typecheck-tmpdir"
    state.mkdir()
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "TMPDIR": str(state)}

    def stop(active: bool, session: str = "s1") -> subprocess.CompletedProcess[str]:
        raw = json.dumps({"session_id": session, "stop_hook_active": active, "cwd": str(project)})
        return subprocess.run(["bash", str(hook)], input=raw, capture_output=True, text=True, cwd=str(project), env=env, check=False)

    def write_errors(text: str | None) -> None:
        if text is None:
            errors.unlink(missing_ok=True)
        else:
            errors.write_text(text)

    cases = [
        # (id, 説明, tsc のエラー, stop_hook_active, session_id, 期待の終了コード)
        ("TC1", "ほかの hook の差し戻しの後（stop_hook_active）でも、初めての型エラーなら 2", "a.ts(1,1): error TS1\n", True, "s1", 2),
        ("TC2", "同じエラーの 2 回目は 0 で警告", "a.ts(1,1): error TS1\n", True, "s1", 0),
        ("TC3", "ターンが変われば（stop_hook_active が false）、同じエラーでもまた 2", "a.ts(1,1): error TS1\n", False, "s1", 2),
        ("TC3b", "ターンの中で同じエラーが続けば 0 のまま（交互に差し戻さない）", "a.ts(1,1): error TS1\n", True, "s1", 0),
        ("TC4", "エラーが変われば 2", "a.ts(2,1): error TS2\n", True, "s1", 2),
        ("TC5", "型エラーが無ければ 0", None, True, "s1", 0),
        ("TC6", "ターンの中で直った後に同じエラーが戻れば、また 2（直ったら状態を消す）", "a.ts(2,1): error TS2\n", True, "s1", 2),
        ("TC7", "別のセッションの状態は使わない（s1 に同じエラーの記録があっても 2）", "a.ts(2,1): error TS2\n", True, "s2", 2),
    ]
    out = []
    for cid, label, text, active, session, code in cases:
        write_errors(text)
        p = stop(active, session)
        ok = p.returncode == code and (code == 0 or (text or "") in p.stderr) and (text is None or code == 2 or "still failing" in p.stderr)
        out.append((cid, label, None if ok else f"exit {p.returncode}（期待 {code}）; stderr={p.stderr!r}"))
    return out


# 偽の vitest。本物と同じ形の json を書く（20261112 に vitest 5.1.0 で確かめた形: 落ちたら numFailedTestSuites と
# testResults[].status=="failed"。一回限りの突き合わせで、本物の形が変わっても test:hooks は気づけない）。
# - `related <file> --run --reporter=json --outputFile=<path>`: node_modules/.fake/related の「<パス> <件数> [札...]」の行から作る。
#   札: <テストのパス>（assertion で落ちる）・msg:<テストのパス>（import のエラーなど、message だけで落ちる）・ok:<テストのパス>（流れて通る）・
#   exit=<N>（json を書かずに N で終える）・rc=<N>（落ちたファイルの無い json を書いて N で終える。Unhandled Errors のまね）
# - `run <テストのパス>... --reporter=json --outputFile=<path>`: 渡したファイルを流したことにする。.fake/failing に載ったパスは落ちる。
#   .fake/run-extra に載ったパスも落ちたとして足す（本物のフィルタは部分一致なので、渡していない似た名前のファイルも流れる）
# -- で始まる引数（--run・--reporter・--coverage.enabled など）はファイルとして扱わない
# 呼ばれるたびに .fake/calls に引数を 1 行足す。.fake/sleep があればその秒数だけ眠る（眠るプロセスの pid を .fake/sleep-pid に残す）。
# .fake/exit があれば、どの呼び出しも json を書かずにその終了コードで終える（道具の故障・設定のエラーのまね）。
FAKE_VITEST = r"""#!/bin/bash
here=$(cd "$(dirname "$0")/.." && pwd)
echo "$*" >> "$here/.fake/calls"
mode=""; out=""; files=()
for a in "$@"; do
  case "$a" in
    --outputFile=*) out="${a#--outputFile=}" ;;
    related|run) [ -z "$mode" ] && mode="$a" || files+=("$a") ;;
    --*) ;;
    *) files+=("$a") ;;
  esac
done
if [ -f "$here/.fake/sleep" ]; then
  sleep "$(cat "$here/.fake/sleep")" &
  echo $! > "$here/.fake/sleep-pid"
  wait
fi
if [ -f "$here/.fake/exit" ]; then
  echo "fake vitest: failed to load config" >&2
  exit "$(cat "$here/.fake/exit")"
fi
cwd=$(pwd -P)
entry() { # $1 = テストのパス, $2 = assert|msg
  if [ "$2" = msg ]; then
    printf '{"name":"%s/%s","status":"failed","message":"Failed to resolve import in %s","assertionResults":[]}' "$cwd" "$1" "$1"
  else
    printf '{"name":"%s/%s","status":"failed","message":"","assertionResults":[{"fullName":"case in %s","status":"failed","failureMessages":["AssertionError: boom in %s"]}]}' "$cwd" "$1" "$1" "$1"
  fi
}
tr=""; nf=0; rc=0
if [ "$mode" = run ]; then
  n=${#files[@]}
  for t in "${files[@]}"; do
    if grep -qxF -- "$t" "$here/.fake/failing" 2>/dev/null; then
      tr="$tr${tr:+,}$(entry "$t" assert)"; nf=$((nf + 1))
    else
      tr="$tr${tr:+,}{\"name\":\"$cwd/$t\",\"status\":\"passed\",\"message\":\"\",\"assertionResults\":[]}"
    fi
  done
  while IFS= read -r t; do
    [ -n "$t" ] && tr="$tr${tr:+,}$(entry "$t" assert)" && nf=$((nf + 1))
  done < <(cat "$here/.fake/run-extra" 2>/dev/null)
else
  line=$(awk -v f="${files[0]}" '$1==f' "$here/.fake/related" 2>/dev/null)
  set -- $line
  n=${2:-0}
  shift 2 2>/dev/null || set --
  for t in "$@"; do
    case "$t" in
      exit=*) echo "fake vitest: crashed" >&2; exit "${t#exit=}" ;;
      rc=*) rc=${t#rc=} ;;
      msg:*) tr="$tr${tr:+,}$(entry "${t#msg:}" msg)"; nf=$((nf + 1)) ;;
      ok:*) tr="$tr${tr:+,}{\"name\":\"$cwd/${t#ok:}\",\"status\":\"passed\",\"message\":\"\",\"assertionResults\":[]}" ;;
      *) tr="$tr${tr:+,}$(entry "$t" assert)"; nf=$((nf + 1)) ;;
    esac
  done
fi
[ "$nf" -gt 0 ] && rc=1
ok=true; [ "$rc" -ne 0 ] && ok=false
printf '{"numTotalTestSuites":%s,"numFailedTestSuites":%s,"numFailedTests":%s,"success":%s,"testResults":[%s]}' "$n" "$nf" "$nf" "$ok" "$tr" > "$out"
exit "$rc"
"""


def check_test_gate(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    """stop-test-gate.sh の骨格（判定 1〜4・免除のファイル）。ケースごとに一時的な git リポジトリを作る。"""
    hook = hooks_dir / "stop-test-gate.sh"
    if not hook.is_file():
        return [("GT", "stop-test-gate.sh が無い", "hook missing")]
    if not shutil.which("jq"):  # jq が無ければ hook は素通しするので、確かめられない
        return [("GT", "jq が無い", SKIP)]
    gate_tmp = tmp / "gate-tmpdir"
    gate_tmp.mkdir()
    root = tmp / "gate"
    root.mkdir()

    def git(*args: str, cwd: Path) -> None:
        subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.com", "-c", "commit.gpgsign=false", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
        )

    def install_vitest(repo: Path, related: dict[str, int | str]) -> None:
        vitest = repo / "node_modules" / ".bin" / "vitest"
        vitest.parent.mkdir(parents=True, exist_ok=True)
        vitest.write_text(FAKE_VITEST)
        vitest.chmod(0o755)
        fake = repo / "node_modules" / ".fake"
        fake.mkdir(exist_ok=True)
        (fake / "related").write_text("".join(f"{p} {n}\n" for p, n in related.items()))

    def write(repo: Path, rel: str, text: str = "export {}\n") -> None:
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)

    def make_repo(name: str, related: dict[str, int | str] | None = None, vitest: bool = True, base_files: dict[str, str] | None = None) -> Path:
        """main に src/base.ts（と base_files）をコミットし、feature ブランチに移った状態のリポジトリ。"""
        repo = root / name
        repo.mkdir()
        write(repo, ".gitignore", "node_modules/\n")
        write(repo, "src/base.ts")
        for rel, text in (base_files or {}).items():
            write(repo, rel, text)
        git("init", "-q", "-b", "main", cwd=repo)
        git("add", ".", cwd=repo)
        git("commit", "-qm", "init", cwd=repo)
        git("checkout", "-qb", "feature", cwd=repo)
        if vitest:
            install_vitest(repo, related or {})
        return repo

    def commit(repo: Path, msg: str = "x") -> None:
        git("add", "-A", cwd=repo)
        git("commit", "-qm", msg, cwd=repo)

    def stop(repo: Path, cwd: Path | None = None, session: str = "gate", timeout: int | None = None) -> subprocess.CompletedProcess[str]:
        raw = json.dumps({"session_id": session, "stop_hook_active": False, "cwd": str(cwd or repo)})
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(repo), "TMPDIR": str(gate_tmp), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        if timeout is not None:
            env["STOP_TEST_GATE_TIMEOUT"] = str(timeout)
        try:
            return subprocess.run(["bash", str(hook)], input=raw, capture_output=True, text=True, errors="replace", cwd=str(repo), env=env, check=False, timeout=60)
        except subprocess.TimeoutExpired:  # hook が固まっても runner 全体を止めず、そのケースを落とす
            return subprocess.CompletedProcess(["bash", str(hook)], -1, "", "fixture: hook が 60 秒で終わらなかった")

    def calls(repo: Path) -> int:
        f = repo / "node_modules" / ".fake" / "calls"
        return len(f.read_text().splitlines()) if f.is_file() else 0

    out: list[tuple[str, str, str | None]] = []
    NO_TEST = "関係するテストがありません"

    def expect(
        cid: str,
        label: str,
        p: subprocess.CompletedProcess[str],
        code: int,
        *,
        says: str | tuple[str, ...] | None = None,
        absent: str | tuple[str, ...] = (),
        quiet: bool = False,
        called: int | None = None,
        repo: Path | None = None,
    ) -> None:
        problems = []
        if p.returncode != code:
            problems.append(f"exit {p.returncode}（期待 {code}）")
        if "\ufffd" in p.stderr:
            problems.append("stderr に UTF-8 として読めないバイトがある")
        for want in (says,) if isinstance(says, str) else (says or ()):
            if want not in p.stderr:
                problems.append(f"stderr に {want!r} が無い")
        for bad in (absent,) if isinstance(absent, str) else absent:
            if bad in p.stderr:
                problems.append(f"stderr に {bad!r} がある")
        if quiet and p.stderr.strip():
            problems.append("stderr が空でない")
        if called is not None and repo is not None and calls(repo) != called:
            problems.append(f"vitest の呼び出し {calls(repo)} 回（期待 {called}）")
        out.append((cid, label, f"{'; '.join(problems)}; stderr={p.stderr!r}" if problems else None))

    def exemption(repo: Path, rel: str, lines: str) -> None:
        write(repo, rel, f"# テストの免除\n\n## テスト不要\n{lines}\n## 失敗を残す\n")

    # 1. 素通し
    plain = root / "plain"
    write(plain, "src/a.ts")
    install_vitest(plain, {})
    expect("GT1", "git の管理下でなければ素通し", stop(plain), 0, called=0, repo=plain)
    r = make_repo("no-vitest", vitest=False)
    write(r, "src/a.ts")
    expect("GT2", "vitest が無ければ素通し（警告も出さない）", stop(r), 0, quiet=True)

    # 4. 関係するテストの有無
    r = make_repo("untested")
    write(r, "src/a.ts")
    expect("GT3", "未追跡の実装ファイルに関係するテストが無いと 2（ファイル名を出す）", stop(r), 2, says=("src/a.ts", NO_TEST), repo=r)
    r = make_repo("tested", {"src/a.ts": 1})
    write(r, "src/a.ts")
    expect("GT4", "関係するテストがあれば 0", stop(r), 0, quiet=True, called=1, repo=r)
    r = make_repo("modified")
    write(r, "src/base.ts", "export const x = 1\n")
    expect("GT5", "コミット前の変更（追跡済み）にテストが無いと 2", stop(r), 2, says=("src/base.ts", NO_TEST))
    r = make_repo("mixed", {"src/a.ts": 1})
    write(r, "src/a.ts")
    write(r, "src/b.ts")
    p = stop(r)
    expect("GT6", "テストのあるファイルと無いファイルを混ぜると、無い方だけを挙げて 2", p, 2, says="src/b.ts")
    if p.returncode == 2 and "src/a.ts" in p.stderr:
        out[-1] = ("GT6", out[-1][1], f"テストのある src/a.ts まで挙げた; stderr={p.stderr!r}")

    # 3. 対象の実装ファイル
    r = make_repo("committed")
    write(r, "src/a.ts")
    commit(r)
    expect("GT7", "コミット済みでも、ベースとの分岐点からの差分にテストが無いと 2", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("on-main")
    git("checkout", "-q", "main", cwd=r)
    write(r, "src/a.ts")
    commit(r)
    expect("GT8", "ベースそのもの（main）の上では、コミット済みの分は見ない", stop(r), 0, called=0, repo=r)
    write(r, "src/b.ts")
    expect("GT9", "ベースの上でも、未コミットの変更は見る", stop(r), 2, says=("src/b.ts", NO_TEST))
    r = make_repo("origin-head")
    git("checkout", "-q", "main", cwd=r)
    git("branch", "-q", "-m", "main", "trunk", cwd=r)
    git("update-ref", "refs/remotes/origin/trunk", "trunk", cwd=r)
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk", cwd=r)
    git("checkout", "-q", "feature", cwd=r)
    write(r, "src/a.ts")
    commit(r)
    expect("GT10", "ベースは origin/HEAD を先に見る（main が無くても分岐点を取る）", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("excluded")
    for rel in ("src/types.d.ts", "vite.config.ts", "src/Button.stories.tsx", "src/a.test.ts", "src/b.spec.tsx", "src/__tests__/c.ts", "tests/d.ts", "e2e/e.ts", "README.md", ".eslintrc.cjs", ".prettierrc.mjs", "src/.hidden.ts"):
        write(r, rel)
    expect("GT11", "実装ファイルでないもの（d.ts・config・stories・テスト・md・名前が . で始まる設定）だけなら related は呼ばず、変えたテストを 1 回流して 0", stop(r), 0, called=1, repo=r)
    calls_file = r / "node_modules" / ".fake" / "calls"
    line = calls_file.read_text() if calls_file.is_file() else ""
    if not line.startswith("run ") or "e2e/e.ts" in line:
        out[-1] = ("GT11", out[-1][1], f"related を呼んだか、e2e を流した: {line!r}")
    r = make_repo("deleted")
    (r / "src" / "base.ts").unlink()
    expect("GT12", "削除だけの変更は判定しない", stop(r), 0, called=0, repo=r)
    r = make_repo("added-then-deleted")
    write(r, "src/a.ts")
    commit(r)
    (r / "src" / "a.ts").unlink()
    expect("GT13", "ブランチで足して作業ツリーで消したファイルは判定しない", stop(r), 0, called=0, repo=r)

    # 2. 根は入力の cwd から決める
    r = make_repo("wt-main")
    wt = root / "wt-linked"
    git("worktree", "add", "-q", str(wt), "-b", "wt", cwd=r)
    install_vitest(wt, {})
    write(wt, "src/a.ts")
    expect("GT14", "worktree の中の変更を判定する（CLAUDE_PROJECT_DIR は本体のまま）", stop(r, cwd=wt), 2, says=("src/a.ts", NO_TEST))
    (wt / "src" / "a.ts").unlink()
    write(r, "src/b.ts")
    expect("GT15", "cwd が worktree なら、本体の変更は見ない", stop(r, cwd=wt), 0)

    # 免除のファイル
    task = ".steering/20261111-x/test-exemptions.md"
    r = make_repo("exempt-task")
    write(r, "src/a.ts")
    exemption(r, task, "- src/a.ts — 文言の変更だけ（20261111）\n")
    expect("GT16", "アクティブなタスクの「テスト不要」に載っていれば 0", stop(r), 0, quiet=True)
    r = make_repo("exempt-no-reason")
    write(r, "src/a.ts")
    exemption(r, task, "- src/a.ts\n- src/a.ts — \n")
    expect("GT17", "理由の無い行では免除しない", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("exempt-other-section")
    write(r, "src/a.ts")
    write(r, task, "# テストの免除\n\n## テスト不要\n\n## テストを弱める\n- src/a.ts — 別の節（20261111）\n")
    expect("GT18", "「テスト不要」以外の節の行では免除しない", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("exempt-two-tasks")
    write(r, "src/a.ts")
    write(r, "src/b.ts")
    exemption(r, ".steering/20261111-x/test-exemptions.md", "- src/a.ts — 理由（20261111）\n")
    exemption(r, ".steering/20261111-y/test-exemptions.md", "- src/b.ts — 理由（20261111）\n")
    expect("GT19", "アクティブなタスクが複数なら、全タスクの免除を合わせて見る", stop(r), 0)
    r = make_repo("exempt-archived")
    write(r, "src/a.ts")
    write(r, ".steering/20261111-x/design.md", "x\n")
    exemption(r, ".steering/archived/old/test-exemptions.md", "- src/a.ts — 理由（20261111）\n")
    expect("GT20", "archived の下の免除は見ない", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("exempt-global")
    write(r, "src/a.ts")
    exemption(r, ".steering/test-exemptions.md", "- src/a.ts — 理由（20261111）\n")
    expect("GT21", "タスクが無ければ .steering/test-exemptions.md を見る", stop(r), 0, says="免除したまま変わりました")
    r = make_repo("exempt-global-with-task")
    write(r, "src/a.ts")
    write(r, ".steering/20261111-x/design.md", "x\n")
    exemption(r, ".steering/test-exemptions.md", "- src/a.ts — 理由（20261111）\n")
    expect("GT22", "タスクがあれば、差し戻しの文はタスクの免除のファイルを案内し、タスクの外の免除では警告しない", stop(r), 2, says=(".steering/20261111-x/test-exemptions.md", NO_TEST), absent="免除したまま変わりました")

    def exemption_fail(repo: Path, lines: str) -> None:
        write(repo, ".steering/test-exemptions.md", f"# テストの免除\n\n## テスト不要\n\n## 失敗を残す\n{lines}\n")

    # 5. テストの成否
    r = make_repo("fail", {"src/a.ts": "1 src/a.test.ts"})
    write(r, "src/a.ts")
    expect("GT23", "関係するテストが落ちると 2（落ちたテストと失敗の文を出す）", stop(r), 2, says="AssertionError: boom in src/a.test.ts")
    r = make_repo("fail-exempt", {"src/a.ts": "1 src/a.test.ts"})
    write(r, "src/a.ts")
    exemption_fail(r, "- src/a.test.ts — 外部 API の仕様変更待ち（20261112）\n")
    expect("GT24", "落ちたテストが「失敗を残す」に載っていれば 0", stop(r), 0, quiet=True)
    r = make_repo("fail-partly-exempt", {"src/a.ts": "2 src/a.test.ts src/b.test.ts"})
    write(r, "src/a.ts")
    exemption_fail(r, "- src/a.test.ts — 理由（20261112）\n")
    p = stop(r)
    expect("GT25", "落ちたテストの一部だけが載っていれば、載っていない方を挙げて 2", p, 2, says="src/b.test.ts")
    if p.returncode == 2 and "boom in src/a.test.ts" in p.stderr:
        out[-1] = ("GT25", out[-1][1], f"免除したテストまで挙げた; stderr={p.stderr!r}")
    r = make_repo("fail-impl-exempt", {"src/a.ts": "1 src/a.test.ts"})
    write(r, "src/a.ts")
    exemption_fail(r, "- src/a.ts — 理由（20261112）\n")
    expect("GT26", "実装ファイルが「失敗を残す」に載っていれば vitest を呼ばずに 0", stop(r), 0, called=0, repo=r)

    # 6. 時間切れ
    r = make_repo("slow", {"src/a.ts": 1})
    write(r, "src/a.ts")
    (r / "node_modules" / ".fake" / "sleep").write_text("20")
    t0 = time.monotonic()
    p = stop(r, timeout=1)
    took = time.monotonic() - t0
    expect("GT27", "打ち切り時間を超えると 2（流しきれなかった）", p, 2, says="流しきれなかった")
    if took > 10:
        out[-1] = ("GT27", out[-1][1], f"打ち切らずに {took:.1f} 秒かかった; stderr={p.stderr!r}")
    sleep_pid = int((r / "node_modules" / ".fake" / "sleep-pid").read_text())
    for _ in range(30):  # 止めた後、親が消えて回収されるまで少し待つ
        try:
            os.kill(sleep_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        out.append(("GT27b", "打ち切ったら、vitest が起こした子のプロセスまで止める", f"pid {sleep_pid} が残っている"))
    r = make_repo("slow-two", {"src/a.ts": 1, "src/b.ts": 1})
    write(r, "src/a.ts")
    write(r, "src/b.ts")
    (r / "node_modules" / ".fake" / "sleep").write_text("20")
    p = stop(r, timeout=1)
    expect("GT28", "打ち切ったら、判定していない残りのファイルも挙げる", p, 2, says="src/b.ts", called=1, repo=r)

    # 7. 道具の故障
    for cid, code, label in (("GT29", "127", "道具の故障（127）は 0 で警告"), ("GT30", "1", "json の無い失敗（設定のエラー）は 0 で警告")):
        r = make_repo(f"broken-{code}", {"src/a.ts": 1})
        write(r, "src/a.ts")
        (r / "node_modules" / ".fake" / "exit").write_text(code)
        expect(cid, label, stop(r), 0, says="failed to load config")

    # 9. 同じ差分で何度も流さない
    r = make_repo("cache", {"src/a.ts": 1})
    write(r, "src/a.ts")
    stop(r, session="c1")
    expect("GT31", "同じ差分で通った後は vitest を呼ばない", stop(r, session="c1"), 0, called=1, repo=r)
    write(r, "src/a.ts", "export const a = 1\n")
    expect("GT32", "差分が変われば、また流す", stop(r, session="c1"), 0, called=2, repo=r)
    expect("GT33", "別のセッションでは、また流す", stop(r, session="c2"), 0, called=3, repo=r)
    r = make_repo("cache-fail", {"src/a.ts": "1 src/a.test.ts"})
    write(r, "src/a.ts")
    stop(r, session="c1")
    expect("GT34", "落ちた差分は残さない（同じ差分でも、また流して 2）", stop(r, session="c1"), 2, called=2, repo=r)
    r = make_repo("cache-broken", {"src/a.ts": 1})
    write(r, "src/a.ts")
    (r / "node_modules" / ".fake" / "exit").write_text("127")
    stop(r, session="c1")
    expect("GT35", "道具の故障で通した差分も残さない", stop(r, session="c1"), 0, called=2, repo=r)
    r = make_repo("cache-exemption")
    write(r, "src/a.ts")
    write(r, ".gitignore", "node_modules/\n.steering/\n")  # 免除のファイルが git の差分に出ないプロジェクト
    exemption(r, ".steering/test-exemptions.md", "- src/a.ts — 理由（20261112）\n")
    stop(r, session="c1")
    exemption(r, ".steering/test-exemptions.md", "")
    expect("GT36", "免除のファイルを変えれば、同じコードの差分でも判定し直す（.steering/ を無視していても）", stop(r, session="c1"), 2, says=("src/a.ts", NO_TEST))
    a = make_repo("cache-same-a", {"src/a.ts": 1})
    b = make_repo("cache-same-b")
    for repo in (a, b):
        write(repo, "src/a.ts")
    stop(a, session="c1")
    expect("GT37", "同じ差分でも、別のリポジトリの記録は使わない", stop(b, session="c1"), 2, says=("src/a.ts", NO_TEST))

    # 8. テストを弱めた
    spec = "src/a.test.ts"
    two = "import { it, expect } from 'vitest'\nit('a', () => {\n  expect.assertions(2)\n  expect(1).toBe(1)\n  expect.soft(2).toBe(2)\n})\n"

    def weak_repo(name: str) -> Path:
        return make_repo(name, base_files={spec: two})

    r = weak_repo("weak-expect")
    write(r, spec, two.replace("  expect(1).toBe(1)\n", ""))
    expect("GT38", "テストファイルの expect が減ると 2（実装ファイルが変わっていなくても）", stop(r), 2, says=spec)
    r = weak_repo("weak-soft")
    write(r, spec, two.replace("  expect.soft(2).toBe(2)\n", ""))
    expect("GT39", "expect.soft も expect として数える", stop(r), 2, says=spec)
    r = weak_repo("weak-same")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)").replace("  expect.assertions(2)\n", ""))
    expect("GT40", "expect の数が同じなら 0（expect.assertions は数えない）", stop(r), 0, quiet=True)
    for cid, label, line in (
        ("GT41", "it.skip が増えると 2", "it.skip('b', () => {})\n"),
        ("GT42", "test.only が増えると 2", "test.only('b', () => {})\n"),
        ("GT43", "describe.todo が増えると 2", "describe.todo('b')\n"),
        ("GT44", "it.skipIf が増えると 2", "it.skipIf(true)('b', () => {})\n"),
        ("GT45", "xit が増えると 2", "xit('b', () => {})\n"),
    ):
        r = weak_repo(f"weak-{cid}")
        write(r, spec, two + line)
        expect(cid, label, stop(r), 2, says=spec)
    r = weak_repo("weak-not-skip")
    write(r, spec, two + "it('c', () => { ctx.skip(); expect(skipped).toBe(1); expect(latest.only).toBe(1) })\n")
    expect("GT46", "テストの外の skip・only という語（ctx.skip・skipped・latest.only）は数えない", stop(r), 0)
    r = weak_repo("weak-deleted")
    (r / spec).unlink()
    expect("GT47", "テストファイルを消すと 2", stop(r), 2, says=spec)
    r = make_repo("weak-new-file")
    write(r, "src/b.test.ts", "it.todo('later')\n")
    expect("GT48", "新しいテストファイルでも todo を足すと 2", stop(r), 2, says="src/b.test.ts")
    r = weak_repo("weak-exempt")
    write(r, spec, two.replace("  expect(1).toBe(1)\n", ""))
    write(r, task, f"# テストの免除\n\n## テストを弱める\n- {spec} — 重複したテストの整理（20261112）\n")
    expect("GT49", "「テストを弱める」に載っていれば 0", stop(r), 0, quiet=True)
    r = weak_repo("weak-exempt-wrong-section")
    write(r, spec, two.replace("  expect(1).toBe(1)\n", ""))
    write(r, ".steering/test-exemptions.md", f"# テストの免除\n\n## 失敗を残す\n- {spec} — 別の節（20261112）\n")
    expect("GT50", "「テストを弱める」以外の節では弱めた判定を免除しない", stop(r), 2, says=spec)

    # 10. タスクの外の免除に載ったファイルが変わった
    global_ex = "# テストの免除\n\n## テスト不要\n- src/base.ts — 文言だけのファイル（20261101）\n"
    r = make_repo("global-warn", base_files={".steering/test-exemptions.md": global_ex})
    write(r, "src/base.ts", "export const changed = 1\n")
    expect("GT51", "タスクの外の免除に載ったファイルが変わると、0 で警告（理由を添える）", stop(r), 0, says="文言だけのファイル")
    r = make_repo("global-quiet", base_files={".steering/test-exemptions.md": global_ex}, related={"src/a.ts": 1})
    write(r, "src/a.ts")
    p = stop(r)
    expect("GT52", "載っていないファイルの変更では警告しない", p, 0)
    if p.returncode == 0 and p.stderr.strip():
        out[-1] = ("GT52", out[-1][1], f"警告が出た; stderr={p.stderr!r}")

    r = make_repo("cache-tracked", {"src/a.ts": 1})
    write(r, "src/a.ts")
    commit(r)
    stop(r, session="c1")
    write(r, "src/a.ts", "export const a = 2\n")
    expect("GT53", "通った後に追跡済みの実装ファイルを変えれば、また流す", stop(r, session="c1"), 0, called=2, repo=r)
    r = make_repo("japanese-impl")
    write(r, "src/商品一覧.ts")
    expect("GT54", "日本語名の実装ファイルも判定する", stop(r), 2, says=("src/商品一覧.ts", NO_TEST))
    r = make_repo("japanese-test", base_files={"src/商品一覧.test.ts": two})
    write(r, "src/商品一覧.test.ts", two.replace("  expect(1).toBe(1)\n", ""))
    expect("GT55", "日本語名のテストファイルで expect が減ると 2", stop(r), 2, says="src/商品一覧.test.ts")
    r = make_repo("origin-head-on-main")
    git("checkout", "-q", "main", cwd=r)
    git("update-ref", "refs/remotes/origin/main", "main", cwd=r)
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main", cwd=r)
    write(r, "src/a.ts")
    commit(r)
    expect("GT56", "origin/HEAD の指すブランチ（main）の上では、コミット済みの分は見ない", stop(r), 0, called=0, repo=r)
    r = make_repo("fail-message", {"src/a.ts": "1 msg:src/a.test.ts"})
    write(r, "src/a.ts")
    expect("GT57", "message だけで落ちたテストは、その文を添えて 2", stop(r), 2, says="Failed to resolve import in src/a.test.ts")
    exts = ("src/b.tsx", "src/c.js", "src/d.jsx", "src/e.mts", "src/f.cts", "src/g.mjs", "src/h.cjs", "src/i.vue", "src/j.svelte")
    r = make_repo("impl-exts")
    for rel in exts:
        write(r, rel)
    write(r, "src/types.d.mts")
    expect("GT58", "ts 以外の実装ファイル（tsx・js・jsx・mts・cts・mjs・cjs・vue・svelte）も判定し、d.mts は除く", stop(r), 2, says=(*exts, NO_TEST), absent="src/types.d.mts")
    places = ("src/a.spec.tsx", "src/__tests__/b.ts", "tests/c.ts", "e2e/d.spec.ts", "src/e.test.mts")
    r = make_repo("weak-places", base_files={rel: two for rel in places})
    for rel in places:
        write(r, rel, two.replace("  expect(1).toBe(1)\n", ""))
    expect("GT59", "spec・__tests__・tests・e2e・.test.mts でも expect が減ると 2", stop(r), 2, says=places)
    for cid, label, line in (
        ("GT60", "fit が増えると 2", "fit('b', () => {})\n"),
        ("GT61", "xtest が増えると 2", "xtest('b', () => {})\n"),
        ("GT62", "xdescribe が増えると 2", "xdescribe('b', () => {})\n"),
        ("GT63", "fdescribe が増えると 2", "fdescribe('b', () => {})\n"),
        ("GT64", "bench.skip が増えると 2", "bench.skip('b', () => {})\n"),
        ("GT65", "suite.skip が増えると 2", "suite.skip('b', () => {})\n"),
        ("GT66", "間に修飾のある skip（it.concurrent.skip）が増えると 2", "it.concurrent.skip('b', () => {})\n"),
    ):
        r = weak_repo(f"weak-{cid}")
        write(r, spec, two + line)
        expect(cid, label, stop(r), 2, says=spec)
    r = make_repo("weak-poll", base_files={spec: two + "it('p', async () => { await expect.poll(() => 1).toBe(1) })\n"})
    write(r, spec, two + "it('p', async () => {})\n")
    expect("GT67", "expect.poll も expect として数える", stop(r), 2, says=spec)
    r = make_repo("args", {"src/a.ts": 1})
    write(r, "src/a.ts")
    stop(r)
    calls_file = r / "node_modules" / ".fake" / "calls"
    line = (calls_file.read_text().splitlines() or [""])[0] if calls_file.is_file() else ""
    m = re.fullmatch(r"related src/a\.ts --run --coverage\.enabled=false --reporter=json --outputFile=(\S+)", line)
    out.append(("GT68", "vitest に related <file> --run とカバレッジを切る指定を渡し、json はプロジェクトの外に書く",
                None if m and not Path(m.group(1)).resolve().is_relative_to(r.resolve()) else f"引数: {line!r}"))
    r = make_repo("json-reset", {"src/a.ts": 1, "src/b.ts": "1 exit=127"})
    write(r, "src/a.ts")
    write(r, "src/b.ts")
    expect("GT69", "2 つ目のファイルだけが道具の故障なら、そのファイルを挙げて 0 で警告", stop(r, session="j1"), 0, says=("src/b.ts", "crashed"), called=2, repo=r)
    expect("GT70", "道具の故障があった差分は残さない（もう一度流す）", stop(r, session="j1"), 0, called=4, repo=r)
    r = weak_repo("rename-weak")
    git("mv", spec, "src/a.spec.ts", cwd=r)
    write(r, "src/a.spec.ts", two.replace("  expect(1).toBe(1)\n", ""))
    commit(r)
    expect("GT71", "テストファイルを改名して expect を減らすと 2（古いパスの版と比べ、旧 → 新 と出す）", stop(r), 2, says="src/a.test.ts → src/a.spec.ts")
    r = make_repo("rename-only", base_files={"src/b.test.ts": two + "it.skip('x', () => {})\n"})
    git("mv", "src/b.test.ts", "src/b.spec.ts", cwd=r)
    commit(r)
    expect("GT72", "skip を含むテストファイルを改名しただけなら 0", stop(r), 0, quiet=True)
    r = weak_repo("run-changed-fail")
    write(r, spec, two.replace("toBe(1)", "toBe(2)"))
    (r / "node_modules" / ".fake" / "failing").write_text(f"{spec}\n")
    expect("GT73", "実装を変えずにテストだけを変えて落ちると 2", stop(r), 2, says=f"AssertionError: boom in {spec}")
    r = weak_repo("run-changed-pass")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    expect("GT74", "変えたテストが通れば 0（まとめて 1 回流す）", stop(r), 0, quiet=True, called=1, repo=r)
    r = make_repo("run-changed-e2e", base_files={"e2e/x.spec.ts": two})
    write(r, "e2e/x.spec.ts", two.replace("toBe(1)", "toEqual(1)"))
    expect("GT75", "e2e/ の下のテストは vitest で流さない", stop(r), 0, called=0, repo=r)
    r = make_repo("rc-only", {"src/a.ts": "1 rc=1"})
    write(r, "src/a.ts")
    expect("GT76", "落ちたテストファイルが無くても、vitest が 0 以外で終われば 2", stop(r), 2, says=("src/a.ts", "失敗で終わりました"))
    r = make_repo("master-base")
    git("branch", "-q", "-m", "main", "master", cwd=r)
    write(r, "src/a.ts")
    commit(r)
    expect("GT77", "origin/HEAD も main も無ければ master を分岐点に使う", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("exempt-loose")
    write(r, "src/a.ts")
    write(r, "src/b.ts")
    exemption(r, task, "- `src/a.ts` — 文言だけ（20261114）\n- ./src/b.ts — 文言だけ（20261114）\n")
    expect("GT78", "免除のパスはバッククォートで囲んでも、./ を付けても効く", stop(r), 0, quiet=True)

    r = weak_repo("run-deleted-exempt")
    (r / spec).unlink()
    write(r, task, f"# テストの免除\n\n## テストを弱める\n- {spec} — 重複したテストの整理（20261114）\n")
    expect("GT79", "消したテストは流さない（「テストを弱める」に載せれば vitest を呼ばずに 0）", stop(r), 0, quiet=True, called=0, repo=r)
    r = weak_repo("run-fail-exempt")
    write(r, spec, two.replace("toBe(1)", "toBe(2)"))
    (r / "node_modules" / ".fake" / "failing").write_text(f"{spec}\n")
    write(r, task, f"# テストの免除\n\n## 失敗を残す\n- {spec} — 仕様の確認待ち（20261114）\n")
    expect("GT80", "「失敗を残す」に載った変えたテストは流さずに 0", stop(r), 0, quiet=True, called=0, repo=r)
    r = weak_repo("run-timeout")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    (r / "node_modules" / ".fake" / "sleep").write_text("20")
    expect("GT81", "変えたテストを流しきれなければ 2（そのテストを挙げる）", stop(r, timeout=1), 2, says=("流しきれなかった", spec))
    r = weak_repo("run-broken")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    (r / "node_modules" / ".fake" / "exit").write_text("127")
    expect("GT82", "変えたテストを流して道具が故障したら 0 で警告", stop(r, session="rb"), 0, says="failed to load config", called=1, repo=r)
    expect("GT83", "変えたテストで道具が故障した差分は残さない（もう一度流す）", stop(r, session="rb"), 0, called=2, repo=r)
    r = make_repo("run-args", {"src/a.ts": 1}, base_files={spec: two, "src/b.test.ts": two})
    write(r, "src/a.ts")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    write(r, "src/b.test.ts", two.replace("toBe(1)", "toEqual(1)"))
    write(r, ".steering/20261111-x/test-exemptions.md", "# テストの免除\n\n## 失敗を残す\n- src/b.test.ts — 理由（20261114）\n")
    stop(r)
    lines = (r / "node_modules" / ".fake" / "calls").read_text().splitlines()
    ok = len(lines) == 2 and re.fullmatch(rf"run {re.escape(spec)} --coverage\.enabled=false --reporter=json --outputFile=\S+", lines[1])
    out.append(("GT84", "変えたテストの run には、流すテストのパスだけ（実装ファイル・免除したテストを除く）とカバレッジを切る指定を渡す",
                None if ok else f"呼び出し: {lines!r}"))
    r = make_repo("ran-dedupe", {"src/a.ts": f"1 ok:{spec}"}, base_files={spec: two})
    write(r, "src/a.ts")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    expect("GT85", "変えたテストが関係するテストとして流れて通れば、run で流し直さない", stop(r), 0, quiet=True, called=1, repo=r)
    r = make_repo("ran-dedupe-fail", {"src/a.ts": f"1 {spec}"}, base_files={spec: two})
    write(r, "src/a.ts")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    p = stop(r)
    expect("GT86", "変えたテストが関係するテストとして落ちれば、run で流し直さず 1 回だけ挙げる", p, 2, says=f"boom in {spec}", called=1, repo=r)
    if p.stderr.count(f"AssertionError: boom in {spec}") != 1:
        out[-1] = ("GT86", out[-1][1], f"失敗の文が {p.stderr.count(f'AssertionError: boom in {spec}')} 回出た; stderr={p.stderr!r}")
    r = weak_repo("run-partial-match")
    write(r, spec, two.replace("toBe(1)", "toEqual(1)"))
    (r / "node_modules" / ".fake" / "run-extra").write_text("src/a.test.tsx\n")
    expect("GT87", "run で渡していない似た名前のテストが落ちても、差し戻さない", stop(r), 0, quiet=True)
    r = make_repo("default-branch")
    git("branch", "-q", "-m", "main", "trunk", cwd=r)
    git("config", "init.defaultBranch", "trunk", cwd=r)
    write(r, "src/a.ts")
    commit(r)
    expect("GT88", "origin/HEAD が無ければ init.defaultBranch を分岐点に使う", stop(r), 2, says=("src/a.ts", NO_TEST))
    r = make_repo("global-warn-loose", base_files={".steering/test-exemptions.md": "# テストの免除\n\n## テスト不要\n- `src/base.ts` — 文言だけのファイル（20261101）\n"})
    write(r, "src/base.ts", "export const changed = 1\n")
    expect("GT89", "タスクの外の免除の警告は、バッククォートで囲んだパスにも出す", stop(r), 0, says="文言だけのファイル")
    r = weak_repo("rename-to-impl")
    git("mv", spec, "src/a.ts", cwd=r)
    commit(r)
    expect("GT90", "テストでない名前への改名は、テストを消したとして 2", stop(r), 2, says=(spec, "ファイルを消した"))
    r = weak_repo("rename-unstaged")
    (r / spec).rename(r / "src" / "a.spec.ts")
    expect("GT91", "ステージしない mv は組にできないので、古いパスを消したとして 2", stop(r), 2, says=(spec, "ファイルを消した"))
    return out


def check_tree_guard(hooks_dir: Path, tmp: Path) -> list[tuple[str, str, str | None]]:
    """subagent-tree-guard.sh の start と stop。ケースごとに一時的な git リポジトリを作る。"""
    hook = hooks_dir / "subagent-tree-guard.sh"
    if not hook.is_file():
        return [("TG", "subagent-tree-guard.sh が無い", "hook missing")]
    if not shutil.which("jq"):
        return [("TG", "jq が無い", SKIP)]
    root = tmp / "tree-guard"
    root.mkdir()
    guard_tmp = tmp / "tree-guard-tmpdir"  # リポジトリの外に置く（中に置くと記録が未追跡のファイルに出る）
    guard_tmp.mkdir()
    genv = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    def git(repo: Path, *args: str) -> None:
        subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@example.com", "-c", "commit.gpgsign=false", *args], cwd=repo, check=True, capture_output=True, env=genv)

    def write(repo: Path, rel: str, text: str) -> None:
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)

    def make_repo(name: str) -> Path:
        """main に 2 ファイルをコミットし、tracked.ts を変えたまま・dirty.ts を変えた・未追跡の u/x.ts がある状態。"""
        repo = root / name
        repo.mkdir()
        write(repo, ".gitignore", "node_modules/\n")
        write(repo, "src/clean.ts", "export const a = 1\n")
        write(repo, "src/dirty.ts", "export const b = 1\n")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "init")
        write(repo, "src/dirty.ts", "export const b = 2\n")  # 既に変更のあるファイル
        write(repo, "u/x.ts", "export const x = 1\n")  # 未追跡のディレクトリの下のファイル
        write(repo, "node_modules/.cache/x", "1\n")  # 無視されたファイル（見ない）
        return repo

    def run(mode: str, cwd: Path, agent: str = "a1", session: str = "s1", extra_env: dict | None = None) -> subprocess.CompletedProcess[str]:
        payload = {"session_id": session, "agent_id": agent, "agent_type": "review-verify", "cwd": str(cwd)}
        if mode == "stop":
            payload["stop_hook_active"] = False
        env = {**genv, "TMPDIR": str(guard_tmp), **(extra_env or {})}
        return subprocess.run(["bash", str(hook), mode], input=json.dumps(payload), capture_output=True, text=True, cwd=str(cwd), env=env, check=False, timeout=60)

    def rec(session: str = "s1", agent: str = "a1") -> Path:
        return guard_tmp / "claude-tree-guard" / session / agent

    def result(session: str = "s1", agent: str = "a1") -> str:
        f = rec(session, agent) / "result"
        return f.read_text().strip() if f.is_file() else ""

    out: list[tuple[str, str, str | None]] = []
    n = 0

    def case(label: str, change, want_rc: int, want_result: str, want_err: str | None = None) -> None:
        """start → change(repo) → stop を 1 回流し、終了コード・記録・stderr を見る。"""
        nonlocal n
        n += 1
        repo = make_repo(f"r{n}")
        session = f"s{n}"
        p = run("start", repo, session=session)
        problem = None if p.returncode == 0 else f"start exit {p.returncode}: {p.stderr}"
        if not problem:
            change(repo)
            p = run("stop", repo, session=session)
            got = result(session)
            if p.returncode != want_rc or got != want_result or (want_err and want_err not in p.stderr):
                problem = f"exit {p.returncode}（期待 {want_rc}）; result={got!r}（期待 {want_result!r}）; stderr={p.stderr[:400]!r}"
        out.append((f"TG{n}", label, problem))

    def commit_one(repo: Path) -> None:
        write(repo, "src/new.ts", "export {}\n")
        git(repo, "add", "src/new.ts")
        git(repo, "commit", "-qm", "by verifier")

    def remote_only(repo: Path) -> None:
        git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    case("違いが無ければ 0 で、same と記録する", lambda r: None, 0, "same")
    case("コミットが増えたら 2 で差し戻し、増えたコミットを出す", commit_one, 2, "differs", "by verifier")
    case("ブランチが増えたら 2", lambda r: git(r, "branch", "tmp-branch"), 2, "differs", "refs/heads/tmp-branch")
    case("きれいな追跡ファイルを変えたら 2", lambda r: write(r, "src/clean.ts", "export const a = 9\n"), 2, "differs", "src/clean.ts")
    case("既に変更のあるファイルをさらに変えたら 2", lambda r: write(r, "src/dirty.ts", "export const b = 3\n"), 2, "differs", "src/dirty.ts")
    case("未追跡のファイルの中身を変えたら 2", lambda r: write(r, "u/x.ts", "export const x = 2\n"), 2, "differs", "u/x.ts")
    case("未追跡のディレクトリの下にファイルを足したら 2", lambda r: write(r, "u/y.ts", "export {}\n"), 2, "differs", "u/y.ts")
    case("ステージしたら 2", lambda r: git(r, "add", "src/dirty.ts"), 2, "differs", "ステージ")
    case("追跡ファイルを消したら 2", lambda r: (r / "src/clean.ts").unlink(), 2, "differs", "src/clean.ts")
    case("リモートの ref だけが変わっても 0", remote_only, 0, "same")
    case("無視されたファイルだけが変わっても 0", lambda r: write(r, "node_modules/.cache/y", "1\n"), 0, "same")

    def seq(label: str, steps: list) -> None:
        """start の後に、(動き, 引数) の列を順に流す。動きは change（repo を変える）・stop（期待の終了コードと記録）・start。"""
        nonlocal n
        n += 1
        repo = make_repo(f"r{n}")
        session = f"s{n}"
        problem = None
        p = run("start", repo, session=session)
        if p.returncode != 0:
            problem = f"start exit {p.returncode}"
        for i, (kind, arg) in enumerate(steps):
            if problem:
                break
            if kind == "change":
                arg(repo)
            elif kind == "start":
                run("start", repo, session=session)
            elif kind == "stop":
                want_rc, want_result, cwd = (*arg, None)[:3]
                p = run("stop", cwd(tmp) if cwd else repo, session=session)
                got = result(session)
                if p.returncode != want_rc or got != want_result:
                    problem = f"{i + 1} 手目の stop: exit {p.returncode}（期待 {want_rc}）; result={got!r}（期待 {want_result!r}）; stderr={p.stderr[:300]!r}"
        out.append((f"TG{n}", label, problem))

    other = tmp / "tree-guard-other"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    write(other, "o.ts", "export {}\n")  # こちらで比べると「未追跡が増えた」とは出ない（控えは本体）
    seq("stop の cwd が別のリポジトリでも、控えた根と比べる",
        [("change", lambda r: write(r, "src/clean.ts", "export const a = 9\n")), ("stop", (2, "differs", lambda t: other))])
    seq("違いが無いとき、stop の cwd が別のリポジトリでも 0（別のリポジトリを比べない）",
        [("stop", (0, "same", lambda t: other))])
    seq("差し戻しは 1 回だけ: 2 回目は違いが同じなら 0 で not-returned",
        [("change", commit_one), ("stop", (2, "differs")), ("stop", (0, "not-returned"))])
    seq("差し戻しは 1 回だけ: 2 回目は違いが変わっていても 0 で not-returned",
        [("change", commit_one), ("stop", (2, "differs")), ("change", lambda r: write(r, "u/z.ts", "1\n")), ("stop", (0, "not-returned"))])
    seq("1 回目の後に戻っていれば、2 回目は returned",
        [("change", lambda r: write(r, "u/y.ts", "1\n")), ("stop", (2, "differs")), ("change", lambda r: (r / "u/y.ts").unlink()), ("stop", (0, "returned"))])
    seq("start が 2 回走っても、控えは最初のまま（再開で汚れた状態を控え直さない）",
        [("change", commit_one), ("start", None), ("stop", (2, "differs"))])

    # 控えが無い（start が動かなかった）
    n += 1
    repo = make_repo(f"r{n}")
    p = run("stop", repo, session=f"s{n}")
    got = result(f"s{n}")
    ok = p.returncode == 0 and got == "unchecked" and "比べていない" in p.stderr
    out.append((f"TG{n}", "控えが無ければ 0 で、unchecked と記録し、stderr に 1 行出す", None if ok else f"exit {p.returncode}; result={got!r}; stderr={p.stderr!r}"))

    # git・jq が無ければ素通し（記録も残さない）
    jq_only = tmp / "tree-guard-bin-jq"
    jq_only.mkdir()
    (jq_only / "jq").symlink_to(shutil.which("jq"))
    bash = shutil.which("bash")
    for label, path in (("jq が無ければ素通し", str(tmp / "tree-guard-empty-bin")), ("git が無ければ素通し", str(jq_only))):
        n += 1
        repo = make_repo(f"r{n}")
        payload = json.dumps({"session_id": f"s{n}", "agent_id": "a1", "cwd": str(repo)})
        env = {**genv, "TMPDIR": str(guard_tmp), "PATH": path}
        problems = []
        for mode in ("start", "stop"):
            p = subprocess.run([bash, str(hook), mode], input=payload, capture_output=True, text=True, cwd=str(repo), env=env, check=False, timeout=60)
            if p.returncode != 0 or p.stdout or p.stderr:
                problems.append(f"{mode}: exit {p.returncode}; stdout={p.stdout!r}; stderr={p.stderr!r}")
        if rec(f"s{n}").exists():
            problems.append("記録を残した")
        out.append((f"TG{n}", label, "; ".join(problems) or None))

    # report — 入力の形は評価の試し実行（20261117）で取った実物に合わせる
    def report(session: str, event: str = "PostToolUse", status: str = "completed") -> subprocess.CompletedProcess[str]:
        if event == "Stop":
            payload = {"session_id": session, "hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(root)}
        else:
            payload = {"session_id": session, "hook_event_name": "PostToolUse", "tool_name": "Agent", "cwd": str(root),
                       "tool_response": {"status": status, "agentId": "a1"}}
        env = {**genv, "TMPDIR": str(guard_tmp)}
        return subprocess.run(["bash", str(hook), "report"], input=json.dumps(payload), capture_output=True, text=True, cwd=str(root), env=env, check=False, timeout=60)

    def context(p: subprocess.CompletedProcess[str]) -> str:
        try:
            return json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"] if p.stdout.strip() else ""
        except (json.JSONDecodeError, KeyError):
            return f"<壊れた JSON: {p.stdout!r}>"

    def session_with(name: str, agents: dict[str, list]) -> None:
        """agents = {agent_id: [動き...]}。動きは "start"・"stop"・関数（repo を変える）。"""
        for agent, steps in agents.items():
            repo = root / f"{name}-{agent}"
            if not repo.exists():  # 同じ session と agent を続けて流すときは、前の repo を使う
                make_repo(repo.name)
            for step in steps:
                if step == "start":
                    run("start", repo, agent=agent, session=name)
                elif step == "stop":
                    run("stop", repo, agent=agent, session=name)
                else:
                    step(repo)

    def add_file(repo: Path) -> None:
        write(repo, "u/leftover.ts", "1\n")

    def drop_file(repo: Path) -> None:
        (repo / "u/leftover.ts").unlink()

    rp = 0

    def rcase(label: str, ok: bool, detail: str) -> None:
        nonlocal rp
        rp += 1
        out.append((f"RP{rp}", label, None if ok else detail))

    p = report("none")
    rcase("記録が無ければ何も出さない", p.returncode == 0 and not p.stdout and not p.stderr, f"exit {p.returncode}; {p.stdout!r} {p.stderr!r}")

    session_with("rp-left", {"a1": ["start", add_file, "stop", "stop"]})  # 差し戻しの後も残った
    p1, p2 = report("rp-left"), report("rp-left")
    c1 = context(p1)
    rcase("違いが残った記録を、違いの一覧と「自分では戻さず」つきで知らせる",
          p1.returncode == 0 and "u/leftover.ts" in c1 and "残っている" in c1 and "自分では戻さず" in c1, f"exit {p1.returncode}; context={c1!r}")
    rcase("同じ記録を 2 回知らせない", p2.returncode == 0 and not p2.stdout, f"2 回目: {p2.stdout!r}")

    session_with("rp-back", {"a1": ["start", add_file, "stop", drop_file, "stop"]})
    c = context(report("rp-back"))
    rcase("戻った記録は「元に戻った」と戻る前の違いを知らせる", "元に戻った" in c and "u/leftover.ts" in c, f"context={c!r}")

    session_with("rp-same", {"a1": ["start", "stop"]})
    p = report("rp-same")
    rcase("違いの無い記録は知らせない", p.returncode == 0 and not p.stdout, f"{p.stdout!r}")

    session_with("rp-pending", {"a1": ["start", add_file, "stop"]})  # 差し戻した直後（検証役はまだ動いている）
    p = report("rp-pending")
    session_with("rp-pending", {"a1": ["stop"]})  # 検証役が戻さずに終わった
    c = context(report("rp-pending"))
    rcase("差し戻した直後の記録は知らせず、検証役が終わった後に知らせる", p.returncode == 0 and not p.stdout and "u/leftover.ts" in c, f"直後={p.stdout!r} 後={c!r}")

    session_with("rp-unchecked", {"a1": ["stop"], "a2": ["stop"]})
    p1, p2 = report("rp-unchecked"), report("rp-unchecked")
    c1 = context(p1)
    session_with("rp-unchecked", {"a3": ["stop"]})
    p3 = report("rp-unchecked")
    rcase("確かめていない記録は session ごとに 1 回だけ知らせる",
          "確かめていない" in c1 and c1.count("確かめていない") == 1 and not p2.stdout and not p3.stdout, f"1={c1!r} 2={p2.stdout!r} 3={p3.stdout!r}")

    session_with("rp-async", {"a1": ["start", add_file, "stop", "stop"]})
    pa = report("rp-async", status="async_launched")
    pb = report("rp-async")
    rcase("背景の agent の起動直後（async_launched）は読まず、印も付けない",
          not pa.stdout and "u/leftover.ts" in context(pb), f"async={pa.stdout!r} 後={pb.stdout!r}")

    session_with("rp-stop", {"a1": ["start", add_file, "stop", "stop"]})
    s1, s2 = report("rp-stop", event="Stop"), report("rp-stop", event="Stop")
    rcase("親の Stop では exit 2 と stderr で 1 回だけ知らせる",
          s1.returncode == 2 and "u/leftover.ts" in s1.stderr and not s1.stdout and s2.returncode == 0 and not s2.stderr,
          f"1: exit {s1.returncode} {s1.stderr!r}; 2: exit {s2.returncode} {s2.stderr!r}")

    session_with("rp-mine", {"a1": ["start", "stop"]})
    session_with("rp-other", {"a1": ["start", add_file, "stop", "stop"]})
    p = report("rp-mine")
    rcase("別の session の記録は知らせない", not p.stdout, f"{p.stdout!r}")

    old = guard_tmp / "claude-tree-guard" / "rp-old"
    (old / "a1").mkdir(parents=True)
    ago = time.time() - 2 * 86400
    os.utime(old, (ago, ago))
    session_with("rp-new", {"a1": ["start"]})
    rcase("start が 1 日より古い session の記録を消す", not old.exists() and rec("rp-new").is_dir(), f"old={old.exists()} new={rec('rp-new').is_dir()}")
    return out


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
        raw = json.dumps(base_payload(case.get("command"), ROOT / case.get("cwd", "")))

    # 実行環境の CLAUDE_PROJECT_DIR を継承しない（別のセッションから流しても結果を変えない）
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    project = case.get("project", str(ROOT))
    if project is not None:
        env["CLAUDE_PROJECT_DIR"] = project
    if case.get("home"):
        env["HOME"] = str(ROOT)
    if case.get("no_python"):
        env["PATH"] = path_without_python(tmp)
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
    tmp = Path(tempfile.mkdtemp(prefix="hook-fixtures-")).resolve()
    try:
        cases = CASES + gated_cases(paths) + link_cases(tmp) + glob_cases(tmp) + worktree_cases(tmp)
        for case in cases:
            ok, detail = run_case(case, hooks_dir, tmp)
            status = "PASS" if ok else "FAIL"
            label = case.get("command") or case.get("note", "")
            print(f"{status} {case['id']}: {label!r}" if "\n" in label else f"{status} {case['id']}: {label}")
            if not ok:
                print(f"  {detail}")
                failed += 1
        direct = [r for check in (check_gated_direct, check_session_start, check_validate_skill_edit, check_typecheck, check_test_gate, check_tree_guard) for r in check(hooks_dir, tmp)]
        skipped = [r for r in direct if r[2] is SKIP]
        direct = [r for r in direct if r[2] is not SKIP]
        for cid, label in ((c, l) for c, l, _ in skipped):
            print(f"SKIP {cid}: {label}")
        # 型検査とゲートの SKIP は失敗にする（完了条件「SKIP が 0 件」を機械で保証する）。jq の無い環境で
        # わざと流すときだけ HOOK_FIXTURES_ALLOW_SKIP=1 で通す
        hard = [c for c, _, _ in skipped if c in ("TC", "GT")]
        if hard and os.environ.get("HOOK_FIXTURES_ALLOW_SKIP") != "1":
            # 下の結果の一覧に FAIL として足す（合計の数にも入る）
            direct.append(("SKIP", "型検査とゲートを確かめられた", f"{hard} を SKIP した（jq を入れるか、HOOK_FIXTURES_ALLOW_SKIP=1）"))
        for cid, label, problem in direct:
            print(f"{'FAIL' if problem else 'PASS'} {cid}: {label}")
            if problem:
                print(f"  {problem}")
                failed += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases) + len(direct) + (1 if not gated_paths(hooks_dir) else 0)
    print(f"\n{total - failed}/{total} passed" + (f"（{len(skipped)} 件を SKIP）" if skipped else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
