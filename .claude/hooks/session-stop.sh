#!/bin/bash
# Stop hook: knowledge-capture 未実行のアクティブタスクに .capture-needed フラグを立てる
# （セッション記録は git が持っているため、ログ追記はしない）
# Claude Code が Stop hook を実行する際のカレントディレクトリに依存しないよう
# git からプロジェクトルートを明示的に取得する

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
  exit 0
fi

STEERING_DIR="$PROJECT_ROOT/.steering"
if [ ! -d "$STEERING_DIR" ]; then
  exit 0
fi

# アクティブタスクをすべて処理（archived/ を除外）
find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name "archived" | while read -r ACTIVE; do
  TASK_NAME=$(basename "$ACTIVE")
  # 成果物（*.md）が無いタスクディレクトリはスキップ
  # （knowledge-capture の入力が存在せず、フラグは常にノイズになるため）
  if ! ls "$ACTIVE"/*.md >/dev/null 2>&1; then
    continue
  fi
  # 「作りたてで一度も触っていない」タスクもスキップする。design-doc も steering init も
  # 着手前に design.md と tasklist.md を必ず作るため、*.md の存在だけでは着手の証拠にならない
  # （作成直後にセッションを終えると、保存すべき知見ゼロのままフラグが立つ）。
  #
  # **判定は AND**。片方だけに緩めると偽陰性（実作業があったのに立たない）が出る:
  #   - ファイルが増えないまま大量に作業するセッションは実在する（スクリプト・設定の修正など）
  #   - チェックの付け忘れも起こりうる
  # 偽陽性のコストは「余計な確認 1 回」だが、偽陰性のコストは「知見が失われる」で非対称なので、
  # 迷う場合はフラグを立てる側（フェイルセーフ）に倒す。
  OTHER_MD=$(ls "$ACTIVE"/*.md 2>/dev/null | grep -v -e '/design\.md$' -e '/tasklist\.md$')
  # grep -c は 0 件のとき「0 を出力して exit 1」を返す。`|| echo 0` を付けると 0 が二重に
  # 入って整数比較が壊れる（実測）。空のときだけ 0 に落とす。
  CHECKED=$(grep -c '^[[:space:]]*- \[x\]' "$ACTIVE/tasklist.md" 2>/dev/null)
  [ -z "$CHECKED" ] && CHECKED=0
  if [ -z "$OTHER_MD" ] && [ "$CHECKED" -eq 0 ]; then
    continue
  fi
  if [ ! -f "$ACTIVE/capture_done" ] && [ ! -f "$ACTIVE/.capture-needed" ]; then
    touch "$ACTIVE/.capture-needed" &&
      echo "[$TASK_NAME] ナレッジ未保存。次回セッションで knowledge-capture を実行してください。"
  fi
done

exit 0
