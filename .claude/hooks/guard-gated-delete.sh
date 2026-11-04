#!/bin/bash
# PreToolUse(Bash) guard: 承認ゲート対象パスへの素の rm / mv を deny する。
#
# なぜ要るか: permissions の ask（Edit）と guard-gated-write（> / >> / tee）は
# 書き込みだけを塞ぎ、`rm -f docs/knowledge/x.md` や `mv … docs/knowledge/` は素通りする。
# 削除・移動はゲート迂回と等価なので deny する（ask ではない — 誤検知の代償が違う）。
#
# 脅威モデル: 敵対者ではなく「停止契約を滑った善意のエージェント」。完全封鎖ではない。
# 守る形: 先頭トークンが `rm` または `mv` で、同一単純コマンドのオペランドに対象パスが含まれるもの。
#        改行区切りの複数単純コマンドは各行を判定する（行継続 \+改行は同一コマンドに畳む）。
# 守らない形: `cd … && rm` / `… || …` / `;` / `|` 連鎖 / `bash -c` / `git rm` / `/bin/rm` /
#            先頭の代入（`FOO=1 rm …`）・ラッパー（`env` / `exec` / `sudo`）/ 大文字小文字の違い（`rm CLAUDE.MD`。
#            macOS の既定 FS では実ファイルが消える）/ 抽出失敗 — いずれも沈黙
#            （フェイルオープン。deny に倒すと通常 Bash が広く死ぬ）。沈黙することはフィクスチャで固定している。
#
# 対象パス（意図的に 2 系統。guard-gated-write.sh の GATED_PATHS より狭い。deny は誤検知の代償が大きく、
# `docs/` まで広げると無関係な `rm /tmp/x/docs/y` も止まるため）:
#   CLAUDE.md / docs/knowledge
#   .claude/ の素の rm / mv は sandbox の標準の書き込み禁止が止める（git rm・git restore は excludedCommands で
#   sandbox の外に出て、この hook も沈黙するので、通常の確認だけが残る）。write 側との突合の対象にはしない。
#   delete 側はディレクトリ裸形（末尾 / 無し）もマッチ。CLAUDE.md はトークン境界付き。
#   AFTER 境界は空白・引用に加えグロブ/ブレースメタ * ? [ {（`.` は入れない — CLAUDE.md.bak 沈黙）。
#
# 判定は tool_input.command の構造抽出のみ。全文検査禁止（transcript_path 等が常時混入）。
# JSON 抽出は python3 標準ライブラリ（jq・追加パッケージ無し）。欠如・失敗は沈黙。

payload=$(cat)
[ -z "$payload" ] && exit 0

# tool_input.command のみ（エスケープ済み引用を正しく戻す）
cmd=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    p = json.load(sys.stdin)
    print((p.get("tool_input") or {}).get("command") or "")
except Exception:
    pass
' 2>/dev/null)
[ -z "$cmd" ] && exit 0

# CRLF 正規化 → リテラル \+改行を空白に畳む（引用符は見ない）
# process substitution は使わない（runner の set -e / 古い bash での落ちを避ける）
folded=$(printf '%s' "$cmd" | python3 -c '
import sys
s = sys.stdin.read().replace("\r\n", "\n").replace("\r", "\n")
while True:
    n = s.replace("\\\n", " ")
    if n == s:
        break
    s = n
sys.stdout.write(s)
' 2>/dev/null) || folded=$cmd

# AFTER グロブは文字クラスに生の [ を入れない（GNU grep でパターン不正→ exit 2 → set -e で沈黙しうる）
# deny は最大 1 JSON（ヒットで即終了）
while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue

  first=$(printf '%s' "$line" | awk '{print $1}')
  case "$first" in
    rm|mv) ;;
    *) continue ;;
  esac

  simple=$(printf '%s' "$line" | sed 's/[[:space:]]*&&.*//; s/[[:space:]]*||.*//; s/[[:space:]]*;.*//; s/[[:space:]]*|.*//; s/[[:space:]]*#.*//')

  if printf '%s' "$simple" | grep -qE '(^|[[:space:]"/'\''])CLAUDE\.md([[:space:]"'\'']|\*|\?|\[|\{|$)|(^|[[:space:]"'\'']|/)docs/knowledge(/|[[:space:]"'\'']|\*|\?|\[|\{|$)' 2>/dev/null; then
    cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"CLAUDE.md / docs/knowledge/ への rm / mv を検出しました（guard-gated-delete hook）。これらは承認制のパスです。削除・移動は書き込みゲートの迂回になります。"}}
EOF
    exit 0
  fi
done <<< "$folded"

exit 0
