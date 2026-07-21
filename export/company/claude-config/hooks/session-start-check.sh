#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ を走査し、未処理フラグ
# （.capture-needed / .codify-needed）とアクティブタスク一覧を additionalContext で注入する。
# CLAUDE.md「セッション開始時: find を実行して確認」という説明文ルールの機械保証版。
# 根拠: 「停止・前提条件の契約は説明文では守られない」（skill-design-patterns.md の実証知見）。
# .steering/ が無いプロジェクトでは素通し（配置先自己完結）。jq 不在時もフェイルオープン。
# compact 後（matcher: compact）にも発火するため .steering 再読リマインドを兼ねる。

command -v jq >/dev/null 2>&1 || exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0

STEERING_DIR="$PROJECT_ROOT/.steering"
[ -d "$STEERING_DIR" ] || exit 0

# フラグ検出 -> 該当タスク名（archived/ を除外）
capture_tasks=$(find "$STEERING_DIR" -name '.capture-needed' -not -path '*/archived/*' 2>/dev/null \
  | while read -r f; do basename "$(dirname "$f")"; done | sort)
codify_tasks=$(find "$STEERING_DIR" -name '.codify-needed' -not -path '*/archived/*' 2>/dev/null \
  | while read -r f; do basename "$(dirname "$f")"; done | sort)

# アクティブタスク一覧（archived を除く直下ディレクトリ）
tasks=$(find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name archived 2>/dev/null \
  | sort | while read -r d; do echo "  - $(basename "$d")"; done)

msg=""
if [ -n "$capture_tasks" ]; then
  msg="${msg}【未保存ナレッジ】.capture-needed を検出。ユーザーに「knowledge-capture を実行しますか？」と確認してください。対象タスク:
$(printf '%s\n' "$capture_tasks" | sed 's/^/  - /')

"
fi
if [ -n "$codify_tasks" ]; then
  msg="${msg}【未 codify の学び】.codify-needed を検出。ユーザーに「compound を実行しますか？」と確認してください。対象タスク:
$(printf '%s\n' "$codify_tasks" | sed 's/^/  - /')

"
fi
if [ -n "$tasks" ]; then
  msg="${msg}【アクティブタスク】作業開始前にすべて読み、複数ある場合はどれを再開するかユーザーに確認してください:
$tasks
"
fi

[ -z "$msg" ] && exit 0

jq -cn --arg msg "$msg" \
  '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$msg}}'
exit 0
