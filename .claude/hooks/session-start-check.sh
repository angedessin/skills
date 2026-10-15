#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ のアクティブタスク一覧を
# additionalContext で注入する。compact 後にも発火するため .steering 再読のリマインドを兼ねる。
# .steering/ が無いプロジェクトでは素通し。
#
# 外部コマンドは find / sed / sort など POSIX 標準ユーティリティだけを使う。
# 出力 JSON のエスケープは json_escape() で行う。注入する文字列はこのスクリプトが組み立てた
# 固定文言とタスクのディレクトリ名だけなので、対象は " と \ と改行に限られる。

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0

STEERING_DIR="$PROJECT_ROOT/.steering"
[ -d "$STEERING_DIR" ] || exit 0

# アクティブタスク一覧（archived を除く直下ディレクトリ）
tasks=$(find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name archived 2>/dev/null \
  | sort | while read -r d; do echo "  - $(basename "$d")"; done)

msg=""
if [ -n "$tasks" ]; then
  msg="${msg}【アクティブタスク】作業開始前にすべて読み、複数ある場合はどれを再開するかユーザーに確認してください:
$tasks
"
fi

[ -z "$msg" ] && exit 0

# JSON 文字列本体へのエスケープ（囲みの " は付けない）:
# \ と " をエスケープし、タブと改行を \t / \n に畳む。
# **改行の畳み込みは移植形の `$!{N;ba}` を使う。** よくある `:a;N;$!ba;s/\n/\\n/g` は
# **BSD sed（macOS）で入力が 1 行のとき何も出力しない**（N が EOF で打ち切る）。
# 従来は msg が「見出し + 項目」で必ず 2 行以上だったため到達しなかったが、1 行だけの
# 通知を足した瞬間に空の additionalContext を注入する（= 静かに何も伝えない）状態になる。
json_escape() {
  printf '%s' "$1" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | sed -e ':a' -e '$!{N;ba' -e '}' -e 's/\n/\\n/g'
}

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$msg")"
exit 0
