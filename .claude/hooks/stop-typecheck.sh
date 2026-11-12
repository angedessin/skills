#!/bin/bash
# Stop hook: 終了宣言時に型チェック（tsc --noEmit --incremental）を実行し、
# エラーがあれば exit 2 + stderr で AI に差し戻す（「できました（できてない）」対策）。
# tsconfig.json が無い / tsc が未導入なら素通し（配置先プロジェクトに依存しない）。
# 無限ループの防止は自分の状態で判定する: 差し戻した tsc の出力のハッシュを残し、同じエラーが続くときだけ警告で通す。
# エラーが変われば再び差し戻す。stop_hook_active は見ない（どの Stop hook の差し戻しでも立つので、
# ほかの Stop hook と並べると型検査が素通りになる）。状態はプロジェクトの外（TMPDIR の下に session_id ごと）に置く。
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
