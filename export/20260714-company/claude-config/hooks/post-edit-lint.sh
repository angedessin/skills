#!/bin/bash
# PostToolUse(Edit|Write) hook: 編集されたファイルだけを format + lint し、
# 自動修正で解消しない違反を exit 2 + stderr で AI に差し戻す（検証ループの心臓部）。
# 配置先プロジェクトの設定を実行時に検出する（あれば使う、無ければ素通し）:
#   biome.json(c)      -> biome check --write   (ts/tsx/js/jsx/json/jsonc/css)
#   eslint.config.*    -> eslint --fix          (ts/tsx/js/jsx。Biome 設定が無い場合のみ)
#   stylelint 設定     -> stylelint --fix       (scss/css)
# 出力は AI が消費する前提: 簡潔形式・カラー無効。
# 自動修正でファイルが書き換わった場合は additionalContext で 1 行通知する
# （無音の書き換えは AI のファイル状態を古くし、次の Edit 失敗を招くため）。
# 品質ゲートでありセキュリティゲートではないため、jq / ツール不在時はフェイルオープン（素通し）。

command -v jq >/dev/null 2>&1 || exit 0

FILE=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0
BIN="$PROJECT_ROOT/node_modules/.bin"

ext="${FILE##*.}"

# 拡張子と設定ファイルの存在で実行ツールを決める
run_biome=""
run_eslint=""
run_stylelint=""
case "$ext" in
  ts|tsx|js|jsx|json|jsonc|css)
    if [ -f "$PROJECT_ROOT/biome.json" ] || [ -f "$PROJECT_ROOT/biome.jsonc" ]; then
      run_biome=1
    fi
    ;;
esac
if [ -z "$run_biome" ]; then
  case "$ext" in
    ts|tsx|js|jsx)
      if ls "$PROJECT_ROOT"/eslint.config.* >/dev/null 2>&1; then
        run_eslint=1
      fi
      ;;
  esac
fi
case "$ext" in
  scss|css)
    if ls "$PROJECT_ROOT"/.stylelintrc* "$PROJECT_ROOT"/stylelint.config.* >/dev/null 2>&1; then
      run_stylelint=1
    fi
    ;;
esac
[ -z "$run_biome$run_eslint$run_stylelint" ] && exit 0

hash_of() { cksum "$1" 2>/dev/null; }
before=$(hash_of "$FILE")

errors=""

if [ -n "$run_biome" ] && [ -x "$BIN/biome" ]; then
  # --no-errors-on-unmatched: ignore 対象ファイル（.gitignore 等）を明示パスで渡してもエラーにしない
  out=$("$BIN/biome" check --write --reporter=github --colors=off --no-errors-on-unmatched "$FILE" 2>&1)
  if [ $? -ne 0 ]; then
    # AI 向けに診断行（::error / ::warning）だけ残す。診断行ゼロの失敗（設定エラー等）は生出力を返す
    diag=$(printf '%s\n' "$out" | grep -E '^::(error|warning)' )
    [ -z "$diag" ] && diag="$out"
    errors="${errors}${diag}
"
  fi
fi

if [ -n "$run_eslint" ] && [ -x "$BIN/eslint" ]; then
  out=$("$BIN/eslint" --fix --format unix --no-color "$FILE" 2>&1)
  [ $? -ne 0 ] && errors="${errors}${out}
"
fi

if [ -n "$run_stylelint" ] && [ -x "$BIN/stylelint" ]; then
  out=$(NO_COLOR=1 "$BIN/stylelint" --fix --formatter unix "$FILE" 2>&1)
  [ $? -ne 0 ] && errors="${errors}${out}
"
fi

after=$(hash_of "$FILE")

if [ -n "$errors" ]; then
  if [ "$before" != "$after" ]; then
    echo "note: $FILE was partially auto-fixed by the lint hook. Re-read it before further edits." >&2
  fi
  echo "lint violations remain after auto-fix. Fix them:" >&2
  printf '%s\n' "$errors" | head -50 >&2
  exit 2
fi

if [ "$before" != "$after" ]; then
  # 違反ゼロだが自動修正で書き換えあり -> AI のファイル状態同期のため 1 行通知
  jq -cn --arg msg "reformatted by lint hook: $FILE (re-read this file before further edits to it)" \
    '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$msg}}'
fi

exit 0
