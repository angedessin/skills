#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ のアクティブタスク一覧を additionalContext で注入する。
# 配置先に依存を増やさないよう、POSIX 標準のコマンドと git だけを使う（git が無ければ閉じ忘れの印を付けない）。

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0

STEERING_DIR="$PROJECT_ROOT/.steering"
[ -d "$STEERING_DIR" ] || exit 0

# 統合ブランチの ref を 1 行ずつ「<ref> <表示名>」で出す。git が無い・管理下でない・失敗したときは何も出さない（印を付けない）
integration_refs() {
  command -v git >/dev/null 2>&1 || return 0
  git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
  head=$(git -C "$PROJECT_ROOT" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null)
  if [ -n "$head" ] && git -C "$PROJECT_ROOT" rev-parse -q --verify "refs/remotes/$head^{commit}" >/dev/null 2>&1; then
    echo "refs/remotes/$head $head"
  fi
  for b in "${head#origin/}" main master develop; do
    [ -n "$b" ] || continue
    if git -C "$PROJECT_ROOT" rev-parse -q --verify "refs/heads/$b^{commit}" >/dev/null 2>&1; then
      echo "refs/heads/$b $b"
    fi
  done
}

# PR ごとにタスクを作る前提なので、統合ブランチの tree に APPROVED のフォルダがあれば閉じずにマージされている
suspect_branch() {
  name=$1
  printf '%s\n' "$refs" | while read -r ref label; do
    [ -n "$ref" ] || continue
    if git -C "$PROJECT_ROOT" show "$ref:.steering/$name/design.md" 2>/dev/null \
      | grep -qE '^Status:[[:space:]]*APPROVED([[:space:]]|$)'; then
      echo "$label"
      break
    fi
  done
}

refs=$(integration_refs)

# アクティブタスク一覧（archived を除く直下ディレクトリ）
suspects=0
tasks=""
while IFS= read -r d; do
  [ -n "$d" ] || continue
  name=$(basename "$d")
  line="  - $name"
  if [ -n "$refs" ]; then
    branch=$(suspect_branch "$name")
    if [ -n "$branch" ]; then
      # ${} で囲む。macOS の bash 3.2 は $var の直後の全角文字のバイトを壊し、後の sed が illegal byte sequence で止まる
      line="${line}（閉じ忘れの疑い: ${branch} に APPROVED のまま入っている）"
      suspects=1
    fi
  fi
  tasks="$tasks$line
"
done <<EOF
$(find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name archived 2>/dev/null | sort)
EOF

msg=""
if [ -n "$tasks" ]; then
  msg="${msg}【アクティブタスク】作業開始前にすべて読み、複数ある場合はどれを再開するかユーザーに確認してください:
$tasks"
  if [ "$suspects" = 1 ]; then
    msg="${msg}閉じ忘れの疑いがあるタスクは、steering で閉じるかユーザーに聞いてください。
"
  fi
fi

[ -z "$msg" ] && exit 0

# `$!{N;ba}` を使う。よくある `:a;N;$!ba;...` は BSD sed で 1 行の入力に何も出力しない。
json_escape() {
  printf '%s' "$1" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | sed -e ':a' -e '$!{N;ba' -e '}' -e 's/\n/\\n/g'
}

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$msg")"
exit 0
