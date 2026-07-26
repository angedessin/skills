#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ を走査し、未処理フラグ
# （.capture-needed / .codify-needed）とアクティブタスク一覧を additionalContext で注入する。
# CLAUDE.md「セッション開始時: find を実行して確認」という説明文ルールの機械保証版。
# 根拠: 「停止・前提条件の契約は説明文では守られない」（skill-design-patterns.md の実証知見）。
# .steering/ が無いプロジェクトでは素通し（配置先自己完結）。
# compact 後（matcher: compact）にも発火するため .steering 再読リマインドを兼ねる。
#
# 外部コマンドに依存しない（find / sed / sort など POSIX 標準ユーティリティのみ）。
# 出力 JSON のエスケープは json_escape() で行う。注入する文字列はこのスクリプトが組み立てた
# 固定文言とタスクのディレクトリ名だけなので、対象は " と \ と改行に限られる。

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

# 固定パスのバックログ。**存在と規模だけを知らせる**（中身は必要になってから読む）。
# なぜ必要か: 着手前のバックログをアーカイブ済みタスクの decisions.md に書くと、上の走査が
# archived/ を除外するため次セッションから構造的に見えない。アクティブタスクとして
# .steering/[task]/ に置くと毎セッションのコンテキスト固定費になるので、その中間として
# 1 枚のファイルを 1 行で知らせる。
# **「未着手 N 件」とは書かない** — 節には「既知の環境問題（タスクではない）」のような
# 非タスク項目も含まれるため、件数として数えると誤報になる。
BACKLOG="$STEERING_DIR/BACKLOG.md"
if [ -f "$BACKLOG" ]; then
  sections=$(grep -c '^## ' "$BACKLOG" 2>/dev/null)
  [ -z "$sections" ] && sections=0
  msg="${msg}【バックログ】.steering/BACKLOG.md（${sections} 節）— 着手前の候補。次のタスクを選ぶときに読んでください。
"
fi

[ -z "$msg" ] && exit 0

# JSON 文字列本体へのエスケープ（囲みの " は付けない）:
# \ と " をエスケープし、タブと改行を \t / \n に畳む。
json_escape() {
  printf '%s' "$1" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g'
}

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$msg")"
exit 0
