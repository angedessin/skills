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
  if [ ! -f "$ACTIVE/capture_done" ] && [ ! -f "$ACTIVE/.capture-needed" ]; then
    touch "$ACTIVE/.capture-needed" &&
      echo "[$TASK_NAME] ナレッジ未保存。次回セッションで knowledge-capture を実行してください。"
  fi
done

exit 0
