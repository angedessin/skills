#!/bin/bash
# PostToolUse(Edit|Write) hook【マスター専用】: 編集対象に応じた検証を実行し、
# 違反を exit 2 + stderr で AI に差し戻す。
#
# モード:
#   skill    .claude/skills/**/SKILL.md      → validate_skills.py --skill
#   template templates/SKILL.template.md     → validate_skills.py --template
#            （テンプレは name がプレースホルダのため専用モードで検証する）
#   assets   .claude/hooks/*.sh / README.md / docs/starter-kit.md /
#            scripts/deploy_skills.py        → check_asset_consistency.py
#
# 狙い: アストラル面絵文字（lone surrogate による API 400 クラッシュの実績あり）や
# frontmatter 違反、および**資産どうしの片側修正**を「書いた瞬間」に機械検出する。
# assets モードを足した理由は、hook を 1 本追加して分類を忘れる / README や配置手順が
# 実体から遅れる、という型が繰り返し起きたため（うち 1 度は、まさにその漏れをルール化した
# コミット自身が同じ漏れを再発させた）。人の注意ではなく機械で支える。
#
# **対象は「リポジトリルート基準の厳密なパス」で判定する。** `*/README.md` のような
# 広いグロブにすると templates/README.md や references/README.md の編集でも起動し、
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
  "$PROJECT_ROOT"/.claude/hooks/*.sh) MODE=assets ;;
  "$PROJECT_ROOT/.claude/settings.json") MODE=assets ;;
  "$PROJECT_ROOT/README.md") MODE=assets ;;
  "$PROJECT_ROOT/docs/starter-kit.md") MODE=assets ;;
  "$PROJECT_ROOT/scripts/deploy_skills.py") MODE=assets ;;
  "$PROJECT_ROOT/scripts/check_asset_consistency.py") MODE=assets ;;
  *) exit 0 ;;
esac

if [ "$MODE" = assets ]; then
  CHECKER="$PROJECT_ROOT/scripts/check_asset_consistency.py"
  # 配置先（マスター外）にはスクリプトが無い -> 素通し
  [ -f "$CHECKER" ] || exit 0
  out=$(python3 "$CHECKER" 2>&1)
  rc=$?
  [ "$rc" -eq 0 ] && exit 0
  if [ "$rc" -eq 1 ]; then
    {
      echo "Asset consistency check failed (scripts/check_asset_consistency.py)."
      echo "同じ情報を持つ別の箇所が追随していません。片側だけ直して終わらせないでください:"
      printf '%s\n' "$out"
    } >&2
    exit 2
  fi
  # rc=2 は走査の前提そのものが崩れている（settings.json が壊れている等）。
  # **無言で捨てない** — 持ち出しセット不在はスクリプト側で SKIP に降格したので、
  # ここに来るのは本当の異常だけ。以前は「1 以外は素通し」にしていたため、
  # 対象不在の exit 2 が他の契約の FAIL を握りつぶして hook が恒久的に無音になっていた。
  {
    echo "Asset consistency check could not run (scripts/check_asset_consistency.py, exit $rc)."
    echo "契約違反ではなく、走査の前提が崩れています。先にこれを直してください:"
    printf '%s\n' "$out"
  } >&2
  exit 2
fi

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
