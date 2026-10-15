#!/bin/bash
# PostToolUse(Edit|Write) hook【マスター専用】: 編集対象に応じた検証を実行し、
# 違反を exit 2 + stderr で AI に差し戻す。
#
# モード:
#   skill    .claude/skills/**/SKILL.md      → validate_skills.py --skill
#   template templates/SKILL.template.md     → validate_skills.py --template
#            （テンプレは name がプレースホルダのため専用モードで検証する）
#
# 狙い: アストラル面絵文字（lone surrogate による API 400 クラッシュの実績あり）や
# frontmatter 違反を「書いた瞬間」に機械検出する。
#
# **対象は「リポジトリルート基準の厳密なパス」で判定する。** 広いグロブにすると
# 無関係な編集が差し戻される（警報疲れを招き、検査を黙らせる修正を誘発する）。
#
# scripts/ 配下のスクリプトに依存するため配置先には同送しない。
# jq / python3 / スクリプト不在時はフェイルオープン（配置先で誤爆させない）。

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
