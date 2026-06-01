#!/bin/bash
# Stop hook: セッション終了時に raw メモを自動キャプチャ
# Claude Code が Stop hook を実行する際のカレントディレクトリに依存しないよう
# git からプロジェクトルートを明示的に取得する

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
  exit 0
fi

STEERING_DIR="$PROJECT_ROOT/.steering"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

if [ ! -d "$STEERING_DIR" ]; then
  exit 0
fi

# アクティブタスクをすべて処理（archived/ を除外）
find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name "archived" | while read -r ACTIVE; do
  TASK_NAME=$(basename "$ACTIVE")
  LOG_FILE="$ACTIVE/session-log.md"
  CAPTURE_FLAG="$ACTIVE/.capture-needed"
  HASH_FILE="$ACTIVE/.last-log-hash"

  # git の変更をキャプチャ（ステージ済み + 未ステージ両方）
  GIT_STAT=$(cd "$PROJECT_ROOT" && git diff HEAD --stat 2>/dev/null)
  GIT_STATUS=$(cd "$PROJECT_ROOT" && git status --short 2>/dev/null)
  COMBINED="${GIT_STAT}${GIT_STATUS}"
  if [ -z "$COMBINED" ]; then
    COMBINED="no changes detected"
  fi

  # 前回と同じ内容なら記録しない（重複抑制）
  CURRENT_HASH=$(echo "$COMBINED" | md5 -q 2>/dev/null || echo "$COMBINED" | md5sum | cut -d' ' -f1)
  LAST_HASH=$(cat "$HASH_FILE" 2>/dev/null)
  if [ "$CURRENT_HASH" = "$LAST_HASH" ]; then
    continue
  fi
  echo "$CURRENT_HASH" > "$HASH_FILE"

  # session-log.md に追記（なければ作成）
  {
    echo ""
    echo "---"
    echo "## $TIMESTAMP (task: $TASK_NAME)"
    echo "$COMBINED"
  } >> "$LOG_FILE"

  # .capture-needed フラグ:
  # - capture_done が存在しない（knowledge-capture 未実行）
  # - かつ .capture-needed がまだない
  # 場合のみ作成する
  if [ ! -f "$ACTIVE/capture_done" ] && [ ! -f "$CAPTURE_FLAG" ]; then
    touch "$CAPTURE_FLAG"
    echo "📝 [$TASK_NAME] ナレッジ未保存。次回セッションで knowledge-capture を実行してください。"
  fi
done

exit 0
