#!/bin/bash
# PreToolUse(Bash) guard: 承認ゲート対象パスへの素の rm / mv を deny する。
#
# なぜ要るか: permissions の ask（Edit）と guard-gated-write（> / >> / tee）は
# 書き込みだけを塞ぎ、`rm -f docs/knowledge/x.md` や `mv … docs/knowledge/` は素通りする。
# 削除・移動はゲート迂回と等価なので deny する（ask ではない — 誤検知の代償が違う）。
#
# 脅威モデル: 敵対者ではなく「停止契約を滑った善意のエージェント」。完全封鎖ではない。
# 守る形: 先頭トークンが `rm` または `mv` で、オペランドに対象パス断片が含まれるもの。
# 守らない形: `cd … && rm` / `bash -c` / `git rm` / `/bin/rm` / 抽出失敗 — いずれも沈黙
# （フェイルオープン。deny に倒すと通常 Bash が広く死ぬ）。
#
# パス正本（guard-gated-write.sh / permissions Edit ask と手同期）:
#   CLAUDE.md / docs/knowledge/ / docs/decisions/
#
# 判定は tool_input.command の構造抽出のみ。全文検査禁止（transcript_path 等が常時混入）。
# 依存ゼロ（sh 組み込み + grep / sed）。

payload=$(cat)
[ -z "$payload" ] && exit 0

# tool_input.command の値だけを取る（最初の "command": "…"）。無ければ沈黙。
cmd=$(printf '%s' "$payload" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
[ -z "$cmd" ] && exit 0

# JSON エスケープの最低限戻し（\" \\ \/）
cmd=$(printf '%s' "$cmd" | sed 's/\\"/"/g; s/\\\//\//g; s/\\\\/\\/g')

# 先頭トークン（空白区切り）。/bin/rm や git はここに来ない／来ても rm|mv 以外。
first=$(printf '%s' "$cmd" | awk '{print $1}')
case "$first" in
  rm|mv) ;;
  *) exit 0 ;;
esac

# 対象パス断片（write hook の targets と手同期）
targets='CLAUDE\.md|docs/knowledge/|docs/decisions/'
if printf '%s' "$cmd" | grep -qE "($targets)"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"CLAUDE.md / docs/knowledge/ / docs/decisions/ への rm / mv を検出しました（guard-gated-delete hook）。これらは承認制のパスです。削除・移動は書き込みゲートの迂回になります。"}}
EOF
fi

exit 0
