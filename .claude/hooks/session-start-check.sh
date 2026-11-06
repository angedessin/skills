#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ のアクティブタスク一覧を additionalContext で注入する。
# 配置先に依存を増やさないよう、POSIX 標準のコマンドだけを使う。

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

# `$!{N;ba}` を使う。よくある `:a;N;$!ba;...` は BSD sed で 1 行の入力に何も出力しない。
json_escape() {
  printf '%s' "$1" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | sed -e ':a' -e '$!{N;ba' -e '}' -e 's/\n/\\n/g'
}

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$msg")"
exit 0
