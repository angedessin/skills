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
        direct = [r for check in (check_gated_direct, check_session_start, check_validate_skill_edit) for r in check(hooks_dir, tmp)]
        skipped = [r for r in direct if r[2] is SKIP]
        direct = [r for r in direct if r[2] is not SKIP]
        for cid, label in ((c, l) for c, l, _ in skipped):
            print(f"SKIP {cid}: {label}")
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
