#!/bin/bash
# Stop hook: 終了宣言時に型チェック（tsc --noEmit --incremental）を実行し、
# エラーがあれば exit 2 + stderr で AI に差し戻す（「できました（できてない）」対策）。
# tsconfig.json が無い / tsc が未導入なら素通し（配置先プロジェクトに依存しない）。
# stop_hook_active が true のときは差し戻さず警告のみ（直せないエラーでの無限ループ防止）。
# 実測で 20-30 秒を超えるプロジェクトでは、この hook を外して CI に移すこと。

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0
[ -f "$PROJECT_ROOT/tsconfig.json" ] || exit 0

TSC="$PROJECT_ROOT/node_modules/.bin/tsc"
[ -x "$TSC" ] || exit 0

out=$(cd "$PROJECT_ROOT" && "$TSC" --noEmit --incremental --pretty false 2>&1)
[ $? -eq 0 ] && exit 0

stop_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)
if [ "$stop_active" = "true" ]; then
  {
    echo "typecheck still failing (not blocking again to avoid a loop). Remaining errors:"
    printf '%s\n' "$out" | head -20
  } >&2
  exit 0
fi

{
  echo "typecheck failed (tsc --noEmit). Fix these errors before finishing:"
  printf '%s\n' "$out" | head -50
} >&2
exit 2
