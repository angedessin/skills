#!/bin/bash
# PostToolUse(Edit|Write) hook【マスター専用】: SKILL.md と雛形を書いた瞬間に validate_skills.py で検証し、
# 違反を exit 2 + stderr で差し戻す（絵文字の lone surrogate は API の 400 クラッシュの原因）。
# 対象はルート基準の厳密なパスで見る（広いと無関係な編集が差し戻される）。
# jq・python3・スクリプトが無ければ素通し。

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

FILE=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0

case "$FILE" in
  "$PROJECT_ROOT"/.claude/skills/*/SKILL.md) MODE=skill ;;
  "$PROJECT_ROOT/templates/SKILL.template.md") MODE=template ;;
  *) exit 0 ;;
esac

VALIDATOR="$PROJECT_ROOT/scripts/validate_skills.py"
# 配置先（マスター外）にはスクリプトが無い -> 素通し
[ -f "$VALIDATOR" ] || exit 0

if [ "$MODE" = template ]; then
  out=$(python3 "$VALIDATOR" --template "$FILE" 2>&1)
else
  out=$(python3 "$VALIDATOR" --skill "$(dirname "$FILE")" 2>&1)
fi
[ $? -eq 0 ] && exit 0

{
  echo "Skill validation failed (scripts/validate_skills.py). Fix these before finishing:"
  printf '%s\n' "$out"
} >&2
exit 2
