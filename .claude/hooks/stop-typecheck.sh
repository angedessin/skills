#!/bin/bash
# Stop hook: tsc --noEmit で型エラーがあれば exit 2 で差し戻す。ターンの中で同じエラーが続けば警告で通す（ループ防止）。
# stop_hook_active が true でも緩めない: ほかの Stop hook の差し戻しでも立つので、並べると型検査が素通りになる。
# false（ターンの最初の Stop）では状態を消し、ユーザーの新しい依頼のたびに残った型エラーを 1 回は差し戻す。
# 実測で 20-30 秒を超えるプロジェクトでは、この hook を外して CI に移すこと。

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0
[ -f "$PROJECT_ROOT/tsconfig.json" ] || exit 0

TSC="$PROJECT_ROOT/node_modules/.bin/tsc"
[ -x "$TSC" ] || exit 0

session=$(printf '%s' "$input" | jq -r '.session_id // "nosession"' 2>/dev/null | tr -c 'A-Za-z0-9_-' '_')
STATE_DIR="${TMPDIR:-/tmp}/claude-stop-typecheck"
STATE="$STATE_DIR/${session:-nosession}"
active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)
[ "$active" = "true" ] || rm -f "$STATE"

out=$(cd "$PROJECT_ROOT" && "$TSC" --noEmit --incremental --pretty false 2>&1)
if [ $? -eq 0 ]; then
  rm -f "$STATE"
  exit 0
fi

hash=$(printf '%s' "$out" | cksum)
if [ -f "$STATE" ] && [ "$(cat "$STATE")" = "$hash" ]; then
  {
    echo "typecheck still failing with the same errors (not blocking again to avoid a loop). Remaining errors:"
    printf '%s\n' "$out" | head -20
  } >&2
  exit 0
fi

mkdir -p "$STATE_DIR" && printf '%s' "$hash" > "$STATE"
{
  echo "typecheck failed (tsc --noEmit). Fix these errors before finishing:"
  printf '%s\n' "$out" | head -50
} >&2
exit 2
